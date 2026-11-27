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
