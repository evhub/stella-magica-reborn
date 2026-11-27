"""Static test suite for Stella Magica Reborn.

Run from the repo root:   python -I tools/validate.py [--vanilla PATH] [--verbose]

Checks (each failure is reported as file:line: message; exit code 1 if any):
  parse        every script file parses; braces balance
  encoding     script files have no BOM; localisation .yml files have a BOM and an l_english header
  duplicates   no object key defined twice inside the mod
  events       every referenced event id exists (mod or vanilla); every mod event id
               matches a namespace declared in its file
  techs        every prerequisite / has_technology tech exists
  modifiers    every key inside modifier blocks is a known 4.6 modifier
               (tools/ref/4.6/modifiers.txt + modifiers generated from mod jobs, resources,
               country types)
  static_mods  every add_modifier / has_modifier target is a defined static modifier
  loc          every localisation key the mod's objects and events need exists, and every
               localisation line uses the `key:0 "text"` format
(Invalid triggers/effects are caught by the in-game load test, tools/ingame_test.py.)
  loc_override no mod localisation key silently replaces a vanilla one
  assets       every texture/icon the mod references exists (mod or vanilla)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdxscript import Node, ParseError, parse  # noqa: E402

DEFAULT_VANILLA = r'C:/Program Files (x86)/Steam/steamapps/common/Stellaris'
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ref', '4.6')

EVENT_TYPES = {'country_event', 'planet_event', 'ship_event', 'fleet_event', 'pop_event', 'leader_event',
               'carrier_event', 'observer_event', 'system_event', 'starbase_event', 'pop_group_event',
               'species_event', 'army_event', 'first_contact_event', 'situation_event', 'agreement_event',
               'event', 'astral_rift_event', 'espionage_operation_event', 'archaeological_site_event',
               'federation_event', 'megastructure_event', 'deposit_event'}
WRAPPERS = {'special_project', 'ship_design', 'part', 'component_set', 'utility_component_template',
            'weapon_component_template', 'strike_craft_component_template', 'namespace', 'spriteTypes',
            'spriteType', 'portraits', 'portrait_groups'}
MODIFIER_BLOCKS = {'modifier', 'planet_modifier', 'country_modifier', 'fleet_modifier', 'army_modifier',
                   'councilor_modifier', 'self_modifier', 'system_modifier', 'pop_modifier', 'sector_modifier',
                   'galcom_modifier', 'federation_modifier', 'advocate_modifier', 'background_planet_modifier',
                   'relay_network_modifier', 'triggered_planet_modifier', 'triggered_country_modifier',
                   'triggered_councilor_modifier', 'triggered_fleet_modifier', 'triggered_self_modifier',
                   'triggered_system_modifier', 'triggered_army_modifier', 'triggered_modifier',
                   'triggered_planet_pop_group_modifier_for_all', 'triggered_planet_pop_group_modifier_for_species',
                   'triggered_pop_group_modifier', 'triggered_species_modifier', 'station_modifier'}
MODIFIER_BLOCK_META = {'potential', 'key', 'mult', 'multiplier', 'should_mult_desc', 'fix_key', 'modifier',
                       'show_trigger_if_true', 'trigger_true_key_override', 'show_if_trigger_false',
                       'show_trigger_if_false', 'trigger_false_key_override', 'icon', 'icon_frame', 'custom_tooltip',
                       'description', 'apply_modifier_to_other_planets', 'stacking',
                       'show_only_custom_tooltip', 'custom_tooltip_with_modifiers'}
# Folders whose files hold modifier definitions directly at the top level of each object.
STATIC_MOD_FOLDERS = {'common/static_modifiers'}


class Ctx:
    def __init__(self, root: str, vanilla: str, verbose: bool):
        self.root = root
        self.vanilla = vanilla
        self.verbose = verbose
        self.errors: list[str] = []
        self.files: dict[str, list[Node]] = {}  # rel path -> parsed
        self.counts: dict[str, int] = defaultdict(int)

    def err(self, check: str, where: str, msg: str):
        self.errors.append(f'[{check}] {where}: {msg}')
        self.counts[check] += 1


# ---------------------------------------------------------------- helpers

def rel(root: str, p: str) -> str:
    return os.path.relpath(p, root).replace(os.sep, '/')


def walk_files(base: str, subdirs, exts):
    for sd in subdirs:
        d = os.path.join(base, sd)
        for dp, _, fs in os.walk(d):
            for fn in fs:
                if fn.lower().endswith(exts):
                    yield os.path.join(dp, fn)


def read_text(p: str) -> str:
    with open(p, 'rb') as f:
        return f.read().decode('utf-8', errors='replace')


def load_list(name: str) -> set[str]:
    p = os.path.join(REF, name)
    with open(p, encoding='utf-8') as f:
        return {ln.strip() for ln in f if ln.strip()}


def top_keys(nodes: list[Node]) -> list[Node]:
    return [n for n in nodes if n.key and n.op == '=' and n.is_block]


_vanilla_cache: dict[str, object] = {}


def vanilla_parsed(ctx: Ctx, folder: str) -> list[tuple[str, list[Node]]]:
    key = 'parsed:' + folder
    if key not in _vanilla_cache:
        out = []
        for p in walk_files(ctx.vanilla, [folder], ('.txt',)):
            try:
                out.append((rel(ctx.vanilla, p), parse(read_text(p))))
            except ParseError:
                pass
        _vanilla_cache[key] = out
    return _vanilla_cache[key]  # type: ignore[return-value]


def vanilla_top_keys(ctx: Ctx, folder: str) -> set[str]:
    return {n.key for _, nodes in vanilla_parsed(ctx, folder) for n in top_keys(nodes)}  # type: ignore[misc]


def mod_objects(ctx: Ctx, folder: str):
    """(relpath, Node) for each top-level object in mod files under folder."""
    for rp, nodes in ctx.files.items():
        if rp.startswith(folder + '/'):
            for n in top_keys(nodes):
                yield rp, n


def vanilla_loc_keys(ctx: Ctx) -> set[str]:
    if 'loc' not in _vanilla_cache:
        keys = set()
        for p in walk_files(ctx.vanilla, ['localisation/english'], ('.yml',)):
            for m in re.finditer(r'^\s*([A-Za-z0-9_.\-]+):\d*\s', read_text(p), re.M):
                keys.add(m.group(1))
        _vanilla_cache['loc'] = keys
    return _vanilla_cache['loc']  # type: ignore[return-value]


def vanilla_event_ids(ctx: Ctx) -> set[str]:
    if 'events' not in _vanilla_cache:
        ids = set()
        for p in walk_files(ctx.vanilla, ['events'], ('.txt',)):
            ids.update(re.findall(r'^\s*id\s*=\s*"?([A-Za-z0-9_.\-]+)"?', read_text(p), re.M))
        _vanilla_cache['events'] = ids
    return _vanilla_cache['events']  # type: ignore[return-value]


def vanilla_sprites(ctx: Ctx) -> set[str]:
    if 'sprites' not in _vanilla_cache:
        names = set()
        for p in walk_files(ctx.vanilla, ['interface', 'gfx'], ('.gfx',)):
            names.update(re.findall(r'name\s*=\s*"([^"]+)"', read_text(p)))
        _vanilla_cache['sprites'] = names
    return _vanilla_cache['sprites']  # type: ignore[return-value]


def exists_asset(ctx: Ctx, relpath: str) -> bool:
    relpath = relpath.replace('\\', '/').lstrip('/')
    for base in (ctx.root, ctx.vanilla):
        if os.path.exists(os.path.join(base, relpath)):
            return True
    return False


# ---------------------------------------------------------------- checks

def check_parse_and_encoding(ctx: Ctx):
    for p in walk_files(ctx.root, ['common', 'events', 'prescripted_countries', 'interface', 'gfx', 'map'],
                        ('.txt', '.gfx', '.gui', '.asset')):
        rp = rel(ctx.root, p)
        raw = open(p, 'rb').read()
        if raw.startswith(b'\xef\xbb\xbf'):
            ctx.err('encoding', rp, 'script file must not start with a UTF-8 BOM')
        try:
            nodes = parse(raw.decode('utf-8', errors='replace'))
        except ParseError as e:
            ctx.err('parse', f'{rp}:{e.line}', str(e))
            continue
        if rp.endswith('.txt') and not rp.startswith(('gfx/', 'map/')):
            ctx.files[rp] = nodes
    for p in walk_files(ctx.root, ['localisation'], ('.yml',)):
        rp = rel(ctx.root, p)
        raw = open(p, 'rb').read()
        for i, ln in enumerate(raw.decode('utf-8', errors='replace').splitlines(), 1):
            if re.match(r'^\s*[A-Za-z0-9_.\-]+:\d*"', ln):
                ctx.err('loc', f'{rp}:{i}', 'localisation line must be `key:0 "text"` (space before the quote)')
        if not raw.startswith(b'\xef\xbb\xbf'):
            ctx.err('encoding', rp, 'localisation file must start with a UTF-8 BOM')
        first = raw.lstrip(b'\xef\xbb\xbf').split(b'\n', 1)[0].strip()
        lang = re.search(r'_l_([a-z_]+)\.yml$', rp)
        if not lang:
            ctx.err('encoding', rp, 'localisation file name must end in _l_<language>.yml')
        elif first != f'l_{lang.group(1)}:'.encode():
            ctx.err('encoding', rp, f'first line must be "l_{lang.group(1)}:" (got {first[:30]!r})')


def check_duplicates(ctx: Ctx):
    seen: dict[tuple[str, str], str] = {}
    for rp, nodes in ctx.files.items():
        folder = rp.rsplit('/', 1)[0]
        if folder in ('common/on_actions',) or rp.startswith('events/'):
            continue
        for n in top_keys(nodes):
            if n.key in WRAPPERS or n.key.startswith('@'):
                continue
            k = (folder, n.key)
            if k in seen:
                ctx.err('duplicates', f'{rp}:{n.line}', f'{n.key} already defined at {seen[k]}')
            else:
                seen[k] = f'{rp}:{n.line}'
    # inner keys of wrapper objects
    inner: dict[str, str] = {}
    for rp, nodes in ctx.files.items():
        for n in nodes:
            if n.key in ('special_project', 'utility_component_template', 'weapon_component_template',
                         'component_set') and n.is_block:
                k = n.scalar('key')
                if k:
                    kk = f'{n.key}:{k}'
                    if kk in inner:
                        ctx.err('duplicates', f'{rp}:{n.line}', f'{n.key} key {k} already defined at {inner[kk]}')
                    inner[kk] = f'{rp}:{n.line}'


def mod_event_ids(ctx: Ctx) -> dict[str, str]:
    ids = {}
    for rp, nodes in ctx.files.items():
        if not rp.startswith('events/'):
            continue
        namespaces = [n.value for n in nodes if n.key == 'namespace']
        for n in nodes:
            if n.key in EVENT_TYPES and n.is_block:
                eid = n.scalar('id')
                if not eid:
                    ctx.err('events', f'{rp}:{n.line}', f'{n.key} without id')
                    continue
                if not any(eid.startswith(ns + '.') for ns in namespaces):
                    ctx.err('events', f'{rp}:{n.line}', f'event id {eid} does not match a namespace in this file')
                if eid in ids:
                    ctx.err('events', f'{rp}:{n.line}', f'duplicate event id {eid} (also {ids[eid]})')
                ids[eid] = f'{rp}:{n.line}'
    return ids


def check_events(ctx: Ctx):
    defined = set(mod_event_ids(ctx)) | vanilla_event_ids(ctx)
    for rp, nodes in ctx.files.items():
        top_event_nodes = {id(n) for n in nodes if rp.startswith('events/') and n.key in EVENT_TYPES}
        for top in nodes:
            for n in top.walk():
                if id(n) in top_event_nodes:
                    continue
                if n.key in EVENT_TYPES and n.is_block:
                    eid = n.scalar('id')
                    if eid and eid not in defined:
                        ctx.err('events', f'{rp}:{n.line}', f'reference to undefined event {eid}')
                if rp.startswith('common/on_actions/') and n.key == 'events' and n.is_block:
                    for eid in n.items():
                        if eid not in defined:
                            ctx.err('events', f'{rp}:{n.line}', f'on_action references undefined event {eid}')


def all_techs(ctx: Ctx) -> set[str]:
    return {n.key for _, n in mod_objects(ctx, 'common/technology')} | vanilla_top_keys(ctx, 'common/technology')


def check_techs(ctx: Ctx):
    techs = all_techs(ctx)
    for rp, nodes in ctx.files.items():
        for top in nodes:
            for n in top.walk():
                if n.key == 'prerequisites' and n.is_block:
                    for t in n.items():
                        if t not in techs:
                            ctx.err('techs', f'{rp}:{n.line}', f'unknown prerequisite tech {t}')
                    for sub in n.value:  # OR = { ... } inside prerequisites
                        if sub.is_block:
                            for t in sub.items():
                                if t not in techs:
                                    ctx.err('techs', f'{rp}:{sub.line}', f'unknown prerequisite tech {t}')
                elif n.key in ('has_technology', 'give_technology', 'add_research_option') and not n.is_block:
                    if n.value not in techs and not n.value.startswith(('event_target', '$')):
                        ctx.err('techs', f'{rp}:{n.line}', f'unknown tech {n.value}')


def known_modifiers(ctx: Ctx) -> set[str]:
    mods = load_list('modifiers.txt')
    jobs = [n.key for _, n in mod_objects(ctx, 'common/pop_jobs')]
    for j in jobs:
        for suf in ('add', 'per_pop', 'per_crime', 'max_workforce_add', 'max_workforce_mult', 'automated_workforce_mult'):
            mods.add(f'job_{j}_{suf}')
        for suf in ('workforce_mult', 'bonus_workforce_mult'):
            mods.add(f'pop_{j}_{suf}')
    for _, n in mod_objects(ctx, 'common/strategic_resources'):
        r = n.key
        for pat in ('country_{r}_produces_add', 'country_{r}_produces_mult', 'country_{r}_upkeep_mult',
                    '{r}_produces_add', '{r}_produces_mult', '{r}_upkeep_add', '{r}_upkeep_mult',
                    '{r}_cost_add', '{r}_cost_mult', 'country_resource_max_{r}_add', 'resource_{r}_mult',
                    '{r}_logistics_mult', '{r}_logistics_add'):
            mods.add(pat.format(r=r))
    for _, n in mod_objects(ctx, 'common/country_types'):
        mods.add(f'damage_vs_country_type_{n.key}_mult')
    return mods


def iter_modifier_blocks(nodes: list[Node], rp: str):
    """Yield (block_node) for every modifier block in the file."""
    for top in nodes:
        for n in top.walk():
            if n.key in MODIFIER_BLOCKS and n.is_block:
                yield n


def check_modifiers(ctx: Ctx):
    mods = known_modifiers(ctx)
    skip_folders = ('common/on_actions/', 'common/solar_system_initializers/', 'common/global_ship_designs/',
                    'common/name_lists/', 'common/species_classes/', 'common/graphical_culture/',
                    'common/portrait_sets/', 'common/portrait_categories/', 'common/prescripted_flags/')
    for rp, nodes in ctx.files.items():
        if rp.startswith(skip_folders) or rp.startswith('prescripted_countries/'):
            continue
        blocks = list(iter_modifier_blocks(nodes, rp))
        if rp.split('/')[0:2] == ['common', 'static_modifiers']:
            blocks += top_keys(nodes)
        for b in blocks:
            # in weights/ai_weight, `modifier = { factor = ... trigger }` is a weight modifier, not a stat block
            if b.key == 'modifier' and (b.get('factor') or b.get('add') or b.get('weight')):
                continue
            # an add_modifier effect block: modifier = <key>
            for c in b.value:
                if c.key is None or c.key in MODIFIER_BLOCK_META or c.is_block:
                    continue
                if c.key.startswith('@'):
                    continue
                if c.key not in mods:
                    ctx.err('modifiers', f'{rp}:{c.line}', f'unknown modifier {c.key}')


def check_static_modifier_refs(ctx: Ctx):
    defined = {n.key for _, n in mod_objects(ctx, 'common/static_modifiers')} | vanilla_top_keys(ctx, 'common/static_modifiers')
    for rp, nodes in ctx.files.items():
        for top in nodes:
            for n in top.walk():
                target = None
                if n.key in ('add_modifier', 'remove_modifier') and n.is_block:
                    target = n.scalar('modifier')
                elif n.key in ('has_modifier', 'remove_modifier') and not n.is_block:
                    target = n.value
                if target and not target.startswith(('$', 'event_target')) and target not in defined:
                    ctx.err('static_mods', f'{rp}:{n.line}', f'undefined static modifier {target}')


LOC_FIELDS_SIMPLE = {'title', 'desc', 'name', 'custom_tooltip', 'fail_text', 'text', 'tooltip', 'response_text',
                     'custom_tooltip_fail', 'trigger_true_key_override', 'trigger_false_key_override'}
LOC_TOKEN = re.compile(r'^[A-Za-z][A-Za-z0-9_.\-]*$')


def mod_loc_keys(ctx: Ctx) -> set[str]:
    keys = set()
    for p in walk_files(ctx.root, ['localisation'], ('.yml',)):
        for m in re.finditer(r'^\s*([A-Za-z0-9_.\-]+):\d*\s', read_text(p), re.M):
            keys.add(m.group(1))
    return keys


def check_loc(ctx: Ctx):
    loc = mod_loc_keys(ctx) | vanilla_loc_keys(ctx)

    def need(key: str, where: str, why: str):
        if key not in loc:
            ctx.err('loc', where, f'missing localisation {key} ({why})')

    # events: title/desc/option names/tooltips
    for rp, nodes in ctx.files.items():
        if not rp.startswith('events/'):
            continue
        for ev in nodes:
            if ev.key not in EVENT_TYPES or not ev.is_block:
                continue
            hidden = ev.scalar('hide_window') == 'yes' or ev.scalar('is_triggered_only') == 'yes' and ev.scalar('hide_window') == 'yes'
            for n in ev.walk():
                if n.key in ('title', 'desc') and not hidden:
                    if not n.is_block and LOC_TOKEN.match(n.value) and n.value not in ('yes', 'no'):
                        need(n.value, f'{rp}:{n.line}', f'event {n.key}')
                    elif n.is_block and n.scalar('text') and LOC_TOKEN.match(n.scalar('text')):
                        need(n.scalar('text'), f'{rp}:{n.line}', f'event {n.key}')
                elif n.key in ('name',) and not n.is_block and LOC_TOKEN.match(n.value):
                    # option names; skip create_* name fields that may be literal or random
                    if n.value not in ('random', 'yes', 'no') and '.' in n.value:
                        need(n.value, f'{rp}:{n.line}', 'option name')
                elif n.key in ('custom_tooltip', 'fail_text') and not n.is_block and LOC_TOKEN.match(n.value):
                    need(n.value, f'{rp}:{n.line}', n.key)

    rules = [
        ('common/technology', lambda k: [k, k + '_desc']),
        ('common/buildings', lambda k: [k, k + '_desc']),
        ('common/pop_jobs', lambda k: [f'job_{k}', f'job_{k}_plural', f'job_{k}_desc', f'mod_job_{k}_add']),
        ('common/governments/civics', lambda k: [k, k + '_desc']),
        ('common/static_modifiers', lambda k: [k]),
        ('common/edicts', lambda k: [f'edict_{k}', f'edict_{k}_desc']),
        ('common/decisions', lambda k: [k, k + '_desc']),
        ('common/ascension_perks', lambda k: [k, k + '_desc']),
        ('common/armies', lambda k: [k, k + '_plural', k + '_desc']),
        ('common/strategic_resources', lambda k: [k, k + '_desc']),
        ('common/opinion_modifiers', lambda k: [k]),
        ('common/traits', lambda k: [k, k + '_desc']),
        ('common/policies', lambda k: [f'policy_{k}', f'policy_{k}_desc']),
        ('common/situations', lambda k: [k, k + '_desc']),
        ('common/relics', lambda k: [k, k + '_desc']),
    ]
    for folder, keys in rules:
        for rp, n in mod_objects(ctx, folder):
            if n.key.startswith('@'):
                continue
            for k in keys(n.key):
                need(k, f'{rp}:{n.line}', folder.split('/')[-1])
    for rp, nodes in ctx.files.items():
        for n in nodes:
            if n.key == 'special_project' and n.is_block:
                k = n.scalar('key')
                if k:
                    need(k, f'{rp}:{n.line}', 'special project')
                    need(k + '_DESC', f'{rp}:{n.line}', 'special project')
            elif n.key in ('utility_component_template', 'weapon_component_template') and n.is_block:
                k = n.scalar('key')
                if k and n.scalar('hidden') != 'yes':
                    need(k, f'{rp}:{n.line}', 'component')


def check_loc_overrides(ctx: Ctx):
    """A mod localisation key that also exists in vanilla silently replaces vanilla's text."""
    vanilla = vanilla_loc_keys(ctx)
    for p in walk_files(ctx.root, ['localisation'], ('.yml',)):
        rp = rel(ctx.root, p)
        for i, ln in enumerate(read_text(p).splitlines(), 1):
            m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s', ln)
            if m and m.group(1) in vanilla and m.group(1) not in LOC_OVERRIDE_ALLOWED:
                ctx.err('loc_override', f'{rp}:{i}', f'{m.group(1)} overrides vanilla localisation')


# Vanilla keys the mod deliberately redefines (none yet).
LOC_OVERRIDE_ALLOWED: set[str] = set()


def check_assets(ctx: Ctx):
    sprites = vanilla_sprites(ctx)
    for p in walk_files(ctx.root, ['interface', 'gfx'], ('.gfx',)):
        txt = read_text(p)
        sprites.update(re.findall(r'name\s*=\s*"([^"]+)"', txt))
        rp = rel(ctx.root, p)
        for m in re.finditer(r'(texturefile|effectFile|animationmaskfile|animationtexturefile)\s*=\s*"([^"]+)"', txt):
            if not exists_asset(ctx, m.group(2)):
                line = txt[:m.start()].count('\n') + 1
                ctx.err('assets', f'{rp}:{line}', f'missing file {m.group(2)}')
    icon_dirs = [('common/technology', 'gfx/interface/icons/technologies/{k}.dds'),
                 ('common/buildings', 'gfx/interface/icons/buildings/{k}.dds'),
                 ('common/governments/civics', 'gfx/interface/icons/governments/civics/{k}.dds'),
                 ('common/ascension_perks', 'gfx/interface/icons/ascension_perks/{k}.dds'),
                 ('common/decisions', 'gfx/interface/icons/decisions/{k}.dds')]
    for folder, pat in icon_dirs:
        for rp, n in mod_objects(ctx, folder):
            if n.key.startswith('@'):
                continue
            icon = n.scalar('icon')
            if icon and icon.startswith('GFX_'):
                if icon not in sprites:
                    ctx.err('assets', f'{rp}:{n.line}', f'undefined sprite {icon}')
                continue
            if icon and '/' in icon:
                if not exists_asset(ctx, icon):
                    ctx.err('assets', f'{rp}:{n.line}', f'missing icon {icon}')
                continue
            path = pat.format(k=icon or n.key)
            if not exists_asset(ctx, path):
                ctx.err('assets', f'{rp}:{n.line}', f'missing icon {path}')
    # jobs: icon and planet-view building_icon come from swappable_data.default
    for rp, n in mod_objects(ctx, 'common/pop_jobs'):
        sd = n.get('swappable_data')
        default = sd.get('default') if sd else None
        icon = (default.scalar('icon') if default else None) or n.key
        if not exists_asset(ctx, f'gfx/interface/icons/jobs/job_{icon}.dds'):
            ctx.err('assets', f'{rp}:{n.line}', f'missing job icon gfx/interface/icons/jobs/job_{icon}.dds')
        bi = default.scalar('building_icon') if default else None
        if bi and not exists_asset(ctx, f'gfx/interface/icons/buildings/{bi}.dds'):
            ctx.err('assets', f'{rp}:{n.line}', f'missing building_icon gfx/interface/icons/buildings/{bi}.dds')
    for rp, nodes in ctx.files.items():
        if rp.startswith('common/pop_jobs/'):
            continue
        for top in nodes:
            for n in top.walk():
                if not n.is_block and n.key in ('icon', 'picture', 'ICON') and isinstance(n.value, str):
                    v = n.value
                    if v.startswith('GFX_') and v not in sprites:
                        ctx.err('assets', f'{rp}:{n.line}', f'undefined sprite {v}')
                    elif v.startswith('gfx/') and not exists_asset(ctx, v):
                        ctx.err('assets', f'{rp}:{n.line}', f'missing file {v}')


# ---------------------------------------------------------------- main

CHECKS = {
    'duplicates': check_duplicates,
    'events': check_events,
    'techs': check_techs,
    'modifiers': check_modifiers,
    'static_mods': check_static_modifier_refs,
    'loc': check_loc,
    'loc_override': check_loc_overrides,
    'assets': check_assets,
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--vanilla', default=os.environ.get('STELLARIS_DIR', DEFAULT_VANILLA))
    ap.add_argument('--only', nargs='*', help='run only these checks')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args(argv)
    if not os.path.isdir(a.vanilla):
        print(f'vanilla Stellaris not found at {a.vanilla} (use --vanilla or STELLARIS_DIR)')
        return 2
    sys.stdout.reconfigure(encoding='utf-8')
    ctx = Ctx(a.root, a.vanilla, a.verbose)
    check_parse_and_encoding(ctx)
    for name, fn in CHECKS.items():
        if a.only and name not in a.only:
            continue
        fn(ctx)
    for e in ctx.errors:
        print(e)
    summary = ', '.join(f'{k}={v}' for k, v in sorted(ctx.counts.items())) or 'none'
    print(f'\n{len(ctx.errors)} problem(s): {summary}  ({len(ctx.files)} script files checked)')
    return 1 if ctx.errors else 0


if __name__ == '__main__':
    sys.exit(main())
