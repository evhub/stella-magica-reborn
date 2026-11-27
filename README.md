# Stella Magica Reborn

An unofficial port of **Stella Magica** to **Stellaris 4.6 (Corona Borealis)**.

Stella Magica was a magical-girl themed Stellaris mod (events, technologies,
leaders, a crisis, ship components and a special species) built for Stellaris
**2.2**. It has been abandoned and no source repository exists, so this port
starts from the files published on the Steam Workshop:

- Original: Steam Workshop item [1681924214](https://steamcommunity.com/sharedfiles/filedetails/?id=1681924214)
- All original content, art and writing belong to the original author.

The first content commit in this repository is the original mod exactly as
downloaded from the Workshop, so `git diff` against it shows every change made
during the port.

## Status

**Loads on vanilla Stellaris 4.6.0 with zero errors of its own.** Its error.log is identical
to a vanilla-only load. The original mod crashed 4.6 during loading, with 700+ errors.

This has **not been playtested** yet. Loading proves the scripts parse and reference
things that exist, but not that events fire in the right order or that the balance
still feels right. See "Playtesting checklist" below.

Every porting change is marked in the files with a `# PORT` comment explaining why.

### What changed from the 2.2 original

- **Jobs:** rewritten for the 4.x pop-group economy. Per-job outputs are unchanged.
  Defense armies now come from the job, as with vanilla soldiers.
- **Buildings:** building sets added. Job counts are in 4.x workforce units
  (100 = 1 job).
- **Leader traits:** classes mapped admiral/general -> commander and
  governor/ruler -> official. Bonuses use fleet/army/planet/council modifier blocks.
  The ruler trait applies only while ruling.
- **Technologies:** `research_leader` expertise checks became council expertise checks.
- **Events:** fixed parse cascades that corrupted most crisis and dimension events.
  Updated leader creation, the bombardment handler (now a carrier event) and
  removed or renamed triggers and effects.
- **Species:** portraits moved to `portrait_sets`, plus a portrait category for
  playable Incubators.
- **Prescripted empires:** country flags come from `prescripted_flags`. The ruler class
  is now official. The Incubator empire no longer needs Utopia, because hive minds have
  no DLC requirement in 4.6.
- **Interface:** the top bar and sector resource groups were rebuilt from the 4.6 files,
  with grief cubes added.
- **Smaller syntax and renamed-key fixes** in name lists, armies, AI budget, deposits,
  components, country types, initializers and flags.

### Bugs in the original that were fixed

- The magitech ascension perk was visible to everyone (`NOT` -> `NOR`), and it can now
  only be taken once.
- Tech weight bonuses checked expertise traits that never existed (`field_materials`,
  and others).
- The Fervent crisis spawn check never excluded player or fallen empire space.
- The Fervent constructor cap stopped the whole reinforcement cycle.
- The leader-death "alive" flags were never cleared.
- Three event options pointed at misspelled localisation keys.
- An initializer was missing its `=`.

### Known leftovers

- `stella_leader.9` is unreachable in the original as well: the `ultra_madoka_spawned`
  flag is never set.
- `common/species_name/` was never loaded, even in 2.2, and the author's comment
  says it isn't needed. It is left as-is.

## Playing with all the content

**Quickest:** in the empire selection screen, pick the preset **United Earth (To the Stars)**.

**Or build your own** with these settings:

| Setting | Choose | Why |
|---|---|---|
| Origin | **The Unified Earth** | Includes **Governance** (no civic slot needed) and starts with Cortical Implants |
| Ethics | Anything **except Fanatic Xenophobe or Gestalt** | Those block Magical Legacy |
| Civic 1 | **Magical Legacy** | Unlocks the original Stella Magica story and most TtS content: contracts and wishes, MagOps, Ryouko and the Consensus arc, the disclosure policy, rationing, the Church of Hope |
| Civic 2 | **Mahou Shoujo Youkai** | Needs Magical Legacy. Unlocks the MSY office, recruitment drive and mentor event |

That build unlocks everything and still fits the 2 civic points you start with. A few years in, an
event asks whether to **recognise the Church of Hope**: say yes to unlock its tech, churches and
visions (any ethics can).

Without The Unified Earth origin, take the **Governance** civic instead. It needs Democratic or
Oligarchic authority and a third civic point.

**The Cephalopods need no setup.** Their empire, the /Thinker-preserving Tentacle, always spawns at
game start. From year 60 they send enforcement fleets against empires with **Magical Legacy**, so the
build above makes you a target. They are Fanatic Purifiers: they never negotiate. They show up in your
galaxy even if you don't build for TtS.

## New content: To the Stars

Beyond the port, the mod adds new content inspired by Hieronym's Madoka Magica fanfic
*To the Stars*: the MSY and Governance, the Cephalopod War, contracts and wishes, the Church of
Hope, Shizuki Ryouko and her mission to the Thinker Consensus, a disclosure policy, new ship components and an origin. All of it uses the
`tts_` prefix. See [docs/TTS_CONTENT.md](docs/TTS_CONTENT.md).

## Tests

- `python -I tools/validate.py`: static checks (parsing, encoding, references, modifiers,
  localisation, ship designs, assets).
- `python -I tools/test_validator.py`: proves the validator still catches seeded mistakes.
- `python -I tools/ingame_test.py`: loads the mod on vanilla Stellaris and fails on any new
  error or crash. Close the game first.

## Compatibility

Tested (loaded and played) in a 79-mod playset that includes Gigastructures, NSC3, UI Overhaul Dynamic,
Stellar AI, Real Space, Planetary Diversity, 圆环的庇护, the Mass Effect mods and others.
It loads without crashing, and no errors point at Stella's own files.

- **No shared objects.** None of Stella's traits, techs, buildings, jobs, components,
  ship designs, special projects or localisation keys are defined by any of those mods.
  All of its event namespaces start with `stella_`.
- **Resource bars.** The resource key is `grief_cube`, the same key
  [Universal Resource Patch](https://steamcommunity.com/sharedfiles/filedetails/?id=1595876588)
  (URP) already lists. Adding a resource to the top bar means overriding
  `interface/resource_groups/topbar_other_resource_groups.txt`, and only the
  **last-loaded** copy of that file is used. That was verified in-game. Gigastructures,
  Ethics and Civics Classic and Stella all override it.
  - **With URP:** load URP **after** all of those mods, at the bottom of the playset.
    Its list covers vanilla, Gigastructures, EaC and grief cubes, so everything shows.
  - **Without URP:** Stella's own copy (vanilla 4.6 plus grief cubes) is used if Stella
    loads after the other overriding mods. Otherwise grief cubes won't appear in the
    top bar. They still work, and are shown in costs and tooltips.
  - Because the key is shared, another mod that also defines `grief_cube` (the old
    Madoka Magica NEW did) would conflict with this one.
- **Universal Game Rules Patch.** It replaces the vanilla `has_upgraded_capital` triggers
  with versions that reference Ancient Cache of Technologies buildings. Without ACOT, this
  logs harmless errors wherever any building checks capital tier, Stella's Magi Center
  included. That is not a Stella bug.

## Playtesting checklist

Start a game as the "humans_stella" prescripted empire, which has the Magical Legacy
civic, or as the Incubators. Then check:

1. The opening story event (`stella_story.0`) appears, and the debug options event
   (`stella_debug.2`) offers its settings.
2. Grief Cube Studies appears, and grief cubes show in the top bar once you can see them.
3. Magi Organization Center: it can be built, its jobs fill, it produces grief cubes,
   and the Grief Cube Distribution decision works.
4. The magi leaders the story creates get their traits, and those traits show icons.
5. Console shortcuts for testing: `event stella_story.0`, `event stella_crisis.8`
   (spawns the Fervent), and `research_technology stella_tech_grief_studies`.

**To the Stars content** (play the United Earth preset). Turn on `debugtooltip` to see event IDs:

6. The Cephalopod empire (/Thinker-preserving Tentacle) exists in the galaxy at game start.
7. Cephalopod War: `event stella_tts_ceph.2` (run as the Cephalopods: `play` their country ID
   first, then `play` back) launches a campaign against a Magical Legacy empire. Kill the
   mothership and the wreck special project should appear.
8. Characters: `event stella_tts_faces.2` (Ryouko), `event stella_tts_four.2` (Mami),
   `event stella_tts_four.4` (Yuma), `event stella_tts_four.6` (Kana).
9. The Consensus arc: `event stella_tts_cons.2` (needs Ryouko and the Cephalopod empire alive).
10. Church of Hope: `event stella_tts_hope.10`. Incubators: `event stella_tts_qb.2`.
    Governance: `event stella_tts_gov.2`. Hidden war: `event stella_tts_hidden.2`.
11. Soul gems: kill a magical girl leader (`kill_leader` on Ryouko); her soul gem should
    usually be recovered a month later.
12. Grief Cube Crisis: run a grief cube deficit; the situation should start on its own.

## Installing locally

1. Create `Documents/Paradox Interactive/Stellaris/mod/stella_magica_reborn.mod`
   with:

   ```
   name="Stella Magica Reborn"
   path="C:/Users/<you>/OneDrive/Documents/GitHub/stella-magica-reborn"
   supported_version="v4.6.*"
   ```

2. Enable "Stella Magica Reborn" in the Paradox launcher playset.

## Publishing

This is a port of someone else's work. Please get the original author's
permission (or at least credit them prominently) before re-uploading it to the
Workshop or anywhere else.
