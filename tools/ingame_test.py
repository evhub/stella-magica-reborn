"""In-game load test: load the mod on vanilla Stellaris and fail if it adds any error.

    python -I tools/ingame_test.py              # mod alone vs. cached vanilla baseline
    python -I tools/ingame_test.py --baseline   # (re)record the vanilla baseline first
    python -I tools/ingame_test.py --mods stella_magica_reborn.mod ugc_123.mod

How it works:
  1. backs up dlc_load.json and the saved empire designs (user_empire_designs*.txt), restores
     both afterwards, and writes the requested mod list. The game strips modded parts it can't
     find from saved empires when it starts, so a run with fewer mods would damage them.
  2. ensures mod/stella_magica_reborn.mod (a dev descriptor pointing at this repo) exists
  3. launches stellaris.exe directly and waits until loading finishes - detected by the
     game writing logs/script_documentation/effects.log - or a crash report appears
  4. closes the game and compares error.log (timestamps stripped) with the vanilla baseline
Exit code: 0 = no new errors, 1 = new errors or crash, 2 = setup problem.
Windows only (uses tasklist/taskkill). Close the Paradox launcher/game before running.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'tools', '.cache')
DEFAULT_GAME = r'C:/Program Files (x86)/Steam/steamapps/common/Stellaris'
DEV_DESCRIPTOR = 'stella_magica_reborn.mod'


def user_dir() -> str:
    home = os.path.expanduser('~')
    for base in (os.path.join(home, 'OneDrive', 'Documents'), os.path.join(home, 'Documents')):
        p = os.path.join(base, 'Paradox Interactive', 'Stellaris')
        if os.path.isdir(p):
            return p
    raise SystemExit('Stellaris user directory not found')


def game_running() -> bool:
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq stellaris.exe'], capture_output=True, text=True).stdout
    return 'stellaris.exe' in out.lower()


def kill_game():
    subprocess.run(['taskkill', '/F', '/IM', 'stellaris.exe'], capture_output=True)
    for name in ('CrashReporter.exe', 'crashreporter.exe'):
        subprocess.run(['taskkill', '/F', '/IM', name], capture_output=True)


def write_dlc_load(ud: str, mods: list[str]):
    data = {'enabled_mods': [f'mod/{m}' for m in mods], 'disabled_dlcs': []}
    with open(os.path.join(ud, 'dlc_load.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def ensure_dev_descriptor(ud: str):
    p = os.path.join(ud, 'mod', DEV_DESCRIPTOR)
    if not os.path.exists(p):
        with open(p, 'w', encoding='utf-8') as f:
            f.write('name="Stella Magica Reborn (dev)"\n'
                    f'path="{REPO.replace(os.sep, "/")}"\n'
                    'supported_version="v4.6.*"\n')
        print(f'created dev descriptor {p}')


def normalize(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path, 'rb') as f:
        lines = f.read().decode('utf-8', errors='replace').splitlines()
    out = []
    for ln in lines:
        ln = re.sub(r'^\[\d\d:\d\d:\d\d\]', '', ln).rstrip()
        if ln:
            out.append(ln)
    return out


def run_game(game: str, ud: str, timeout: int) -> tuple[str, list[str]]:
    """Returns (result, normalized error lines). result: ok | crash | exited | timeout."""
    docs = os.path.join(ud, 'logs', 'script_documentation', 'effects.log')
    crashes = os.path.join(ud, 'crashes')
    before = set(os.listdir(crashes)) if os.path.isdir(crashes) else set()
    start = time.time()
    subprocess.Popen([os.path.join(game, 'stellaris.exe'), '-gdpr-compliant'], cwd=game)
    time.sleep(15)
    result = 'timeout'
    while time.time() - start < timeout:
        time.sleep(5)
        now = set(os.listdir(crashes)) if os.path.isdir(crashes) else set()
        if now - before:
            result = 'crash'
            time.sleep(10)
            break
        if not game_running():
            # closed by hand: still usable if loading had already finished
            done = os.path.exists(docs) and os.path.getmtime(docs) > start and os.path.getsize(docs) > 0
            result = 'ok' if done else 'exited'
            break
        if os.path.exists(docs) and os.path.getmtime(docs) > start and os.path.getsize(docs) > 0:
            result = 'ok'
            time.sleep(20)  # let main-menu stage errors flush
            break
    kill_game()
    time.sleep(3)
    log = os.path.join(ud, 'logs', 'error.log')
    if result == 'crash':
        new = sorted((set(os.listdir(crashes)) - before))
        print(f'CRASH: {os.path.join(crashes, new[-1])}')
    return result, normalize(log)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', default=os.environ.get('STELLARIS_DIR', DEFAULT_GAME))
    ap.add_argument('--mods', nargs='*', default=[DEV_DESCRIPTOR])
    ap.add_argument('--baseline', action='store_true', help='record the vanilla baseline first')
    ap.add_argument('--timeout', type=int, default=900)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    if game_running():
        print('Stellaris is already running; close it first.')
        return 2
    ud = user_dir()
    os.makedirs(CACHE, exist_ok=True)
    baseline_path = os.path.join(CACHE, 'vanilla_errors.txt')
    dlc = os.path.join(ud, 'dlc_load.json')
    backup = os.path.join(CACHE, 'dlc_load.json.bak')
    shutil.copy2(dlc, backup)
    designs = [n for n in os.listdir(ud) if n.startswith('user_empire_designs') and n.endswith('.txt')]
    for n in designs:
        shutil.copy2(os.path.join(ud, n), os.path.join(CACHE, n + '.bak'))
    try:
        ensure_dev_descriptor(ud)
        if a.baseline or not os.path.exists(baseline_path):
            print('recording vanilla baseline...')
            write_dlc_load(ud, [])
            res, lines = run_game(a.game, ud, a.timeout)
            if res != 'ok':
                print(f'baseline run failed: {res}')
                return 2
            with open(baseline_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(set(lines))))
            print(f'baseline: {len(set(lines))} distinct lines')
        with open(baseline_path, encoding='utf-8') as f:
            base = set(f.read().splitlines())
        print(f'loading with mods: {", ".join(a.mods)}')
        write_dlc_load(ud, a.mods)
        res, lines = run_game(a.game, ud, a.timeout)
        # errors from the user's saved empire designs depend on their other mods, not on this one
        new = sorted(l for l in set(lines) - base
                     if 'user_empire_designs' not in l and not l.startswith('[empire_design.cpp'))
        with open(os.path.join(CACHE, 'last_new_errors.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(new))
        for ln in new[:200]:
            print('  ' + ln[:300])
        if len(new) > 200:
            print(f'  ... {len(new) - 200} more (tools/.cache/last_new_errors.txt)')
        print(f'\nresult: {res}; {len(new)} new error line(s) vs vanilla')
        return 0 if res == 'ok' and not new else 1
    finally:
        kill_game()  # the game must not be running when its files are restored
        shutil.copy2(backup, dlc)
        for n in designs:
            shutil.copy2(os.path.join(CACHE, n + '.bak'), os.path.join(ud, n))
        print('restored dlc_load.json and saved empire designs')


if __name__ == '__main__':
    sys.exit(main())
