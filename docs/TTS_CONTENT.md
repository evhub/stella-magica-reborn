# To the Stars content plan

This is new content inspired by Hieronym's *To the Stars* (TtS), a long Madoka Magica fanfic
set centuries after the anime, in which humanity, governed with AI help and supported by an
organized magical girl society, fights an alien war.

This is **original game content written in the spirit of the fic**, not a reproduction of it.
Names and concepts come from the story; all text is new. Where the fic's details are uncertain,
the content makes its own choices. Every TtS object uses the `tts_` prefix (events use the
`stella_tts_*` namespaces) so it is easy to find and can't collide with the original mod.

## What's in the mod

| Wave | Content | In-game load test |
|---|---|---|
| 1. Institutions | civics Governance and Mahou Shoujo Youkai, techs Cortical Implants, TacComp, MSY Logistics and MagOps Doctrine, MSY Regional Office and MSY Liaison job, MagOps Squad army, leader traits TacComp, Teleporter, Clairvoyant, Healer and MSY Veteran, founding events | passed |
| 2. The Cephalopod War | a silent mid-game alien invader: mothership and raiding swarms, reinforcement cycle, victory, wreck study, Cephalopod Analysis tech | pending |
| 3. Contracts and wishes | periodic contracts with four wishes (prosperity, healing, protection, knowledge); a demon outbreak risk when grief cubes run out | pending |
| 4. The Cult of Hope | civic, Theology of Hope tech, Church of Hope and Priest of Hope job, Priestess of Hope trait, visions of the Goddess; faith halves demon outbreak risk | pending |
| 5. Familiar faces | Shizuki Ryouko joins MagOps; her teleporter strike on the Cephalopod mothership; an MSY mentor | pending |
| 6. Policy and society | Magical Girl Disclosure policy; Grief Cube Rationing and MSY Recruitment Drive edicts | pending |
| 7. Ship components | TacComp Fire Control and Soul Gem Resonator; also a fix so the original magitech components work again | pending |
| 8. Origin | The Unified Earth | pending |

Every wave passed `tools/validate.py` and `tools/test_validator.py` before it was committed.

## Ideas for later waves

- Situations (4.x): a grief cube shortage track with escalating consequences.
- A MagOps tradition tree or ascension perk. Needs icon art.
- Incubator diplomacy events for empires that meet the Incubators prescripted empire.
- More Cephalopod War events: refugees, captured technology, a second invasion wave.

## Testing

- `python -I tools/validate.py`: static checks for parsing, encoding, duplicate keys, event,
  tech and static modifier references, modifier names, localisation coverage and assets.
- `python -I tools/test_validator.py`: proves the validator still catches seeded mistakes.
- `python -I tools/ingame_test.py`: loads the mod on vanilla 4.6 and fails on any new error or crash.
