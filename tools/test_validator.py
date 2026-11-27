"""Self-test for tools/validate.py: copies the mod to a temp dir, seeds known-bad content,
and checks that every seeded problem is reported (and that the clean mod reports none).

    python -I tools/test_validator.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
DIRS = ['common', 'events', 'localisation', 'interface', 'gfx', 'prescripted_countries']

SEEDS = {
    'localisation/english/zz_seed_l_english.yml': '﻿l_english:\r\n zz_seed_bad:"no space"\r\n',
    'common/technology/zz_seed.txt': (
        'zz_seed_tech = {\r\n\tarea = physics\r\n\tprerequisites = { "tech_zz_missing" }\r\n'
        '\tmodifier = { zz_not_a_modifier = 1 }\r\n}\r\n'),
    'events/zz_seed.txt': (
        'namespace = zz_seed\r\ncountry_event = {\r\n\tid = zz_seed.1\r\n\ttitle = zz_seed.1.name\r\n'
        '\tdesc = zz_seed.1.desc\r\n\tis_triggered_only = yes\r\n\timmediate = {\r\n'
        '\t\tcountry_event = { id = zz_seed.999 }\r\n\t\tadd_modifier = { modifier = zz_missing_mod }\r\n'
        '\t}\r\n\toption = { name = zz_seed.1.a }\r\n}\r\n'),
    'common/static_modifiers/zz_seed.txt': 'zz_seed_unclosed = {\r\n\tplanet_crime_add = 1\r\n',
}
EXPECT = [
    '[loc] localisation/english/zz_seed_l_english.yml:2',
    '[techs] common/technology/zz_seed.txt:3: unknown prerequisite tech tech_zz_missing',
    '[modifiers] common/technology/zz_seed.txt:4: unknown modifier zz_not_a_modifier',
    'missing localisation zz_seed_tech (technology)',
    'missing icon gfx/interface/icons/technologies/zz_seed_tech.dds',
    'reference to undefined event zz_seed.999',
    'undefined static modifier zz_missing_mod',
    'missing localisation zz_seed.1.name',
    'missing localisation zz_seed.1.a',
    '[parse] common/static_modifiers/zz_seed.txt',
]


def run(root):
    p = subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'validate.py'), '--root', root],
                       capture_output=True, text=True, encoding='utf-8')
    return p.returncode, p.stdout


def main() -> int:
    code, out = run(REPO)
    if code != 0:
        print('FAIL: the clean mod does not validate:\n' + out)
        return 1
    tmp = tempfile.mkdtemp(prefix='stella_vt_')
    try:
        for d in DIRS:
            if os.path.isdir(os.path.join(REPO, d)):
                shutil.copytree(os.path.join(REPO, d), os.path.join(tmp, d))
        for rel, text in SEEDS.items():
            path = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(text.encode('utf-8'))
        code, out = run(tmp)
        missing = [e for e in EXPECT if e not in out]
        if code == 0 or missing:
            print('FAIL: validator missed seeded problems:')
            for m in missing:
                print('  - ' + m)
            print(out)
            return 1
        print(f'OK: clean mod passes; all {len(EXPECT)} seeded problems detected')
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
