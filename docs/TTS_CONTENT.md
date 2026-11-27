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
| 2. The Cephalopod War | enforcement campaigns against magic-using (Magical Legacy) empires: mothership and raiding swarms, reinforcement cycle, victory, wreck study, Cephalopod Analysis tech | passed |
| 3. Contracts and wishes | periodic contracts with four wishes (prosperity, healing, protection, knowledge); a demon outbreak risk when grief cubes run out | passed |
| 4. The Church of Hope | recognised by event (any Magical Legacy empire, any ethics), Theology of Hope tech, Church of Hope and Priest of Hope job, Priestess of Hope trait, visions of the Goddess; faith halves demon outbreak risk | passed |
| 5. Familiar faces | Shizuki Ryouko joins MagOps; her teleporter strike on the Cephalopod mothership; an MSY mentor | passed |
| 6. Policy and society | Magical Girl Disclosure policy; Grief Cube Rationing and MSY Recruitment Drive edicts | passed |
| 7. Ship components | TacComp Fire Control and Soul Gem Resonator; also a fix so the original magitech components work again | passed |
| 8. Origin | The Unified Earth (includes Governance, so all TtS content fits the starting 2 civic points) | passed |
| 9. The Thinkers | the Cephalopods as a real AI empire, always spawned: the /Thinker-preserving Tentacle (Fanatic Purifiers, aquatic molluscoids on the Great Sea), Thinker traits Mind Backups, Empathize-Opening and Emotionless, origin Consensus Vanguard (better shields, regenerating armor, range, early techs), hyphenated star-name name list; they launch the wave 2 campaigns from year 60. Also the United Earth preset empire | passed (load); galaxy spawn not yet playtested |
| 10. The Consensus | Vol IV arc: Peace-cultivating of /Ahimsa-extending contacts Ryouko with Homura's claim that /Thinker-preserving is compromised; Ryouko travels to the Thinker galaxy and seeks the support of /Somatic-diversity (share soul gem research) and /Eukleia-chasing (ceremonial duel or Martial Debate); with enough support the Consensus withdraws its mandate (no more campaigns, /Thinker-preserving censured, Consensus Envoy trait, Contact with the Consensus). Ryouko now appears for any species | passed |
| 11. The MSY and the Mitakihara Four | MSY Divisions tech: Soul Guard army, Black Heart Operations and Consult the Far Seers edicts; legendary leaders Tomoe Mami (Field Marshal, flagship HSS Georgy Konstantinovich Zhukov), Chitose Yuma (Leadership Committee), Kuroi Kana (Director of the Black Heart) and Sakura Kyouko (the Church's first priestess); the Ribbon Chamber (unique; doubles visions of the Goddess); Version Two Tactical Computers tech; United Earth name list | passed |
| 12. The war grows | named magical girl leaders (Ryouko, Mami, Yuma, Kana, Kyouko) never age; when one falls, 70% chance her soul gem is recovered and she is restored in a new body, otherwise the Goddess takes her home; a Cephalopod campaign that lasts three reinforcement cycles escalates into the Incursion (heavy battle group), answered by convening the Emergency Defense Council or holding the line | passed |
| 13. The Grief Cube Crisis | a 4.x situation started automatically by a grief cube deficit: four stages weaken armies, morale and order and let demons through; approaches Ration the Cubes, Emergency Hunts or Deal with the Incubators; a recognised Church of Hope slows it; at the end, Mass Despair | passed |
| 14. The Incubators | Kyubey calls every decade or so: a proposal to expand contracting (grief cubes and a Contract Boom, or refuse) or a request for spent cubes (traded for physics research); an Incubator turns up at the Ribbon Chamber to observe the visions; during a Cephalopod campaign the Incubators share intelligence on the Thinkers | passed |

Every wave passed `tools/validate.py` and `tools/test_validator.py` before it was committed.

## Ideas for later waves

- A MagOps tradition tree or ascension perk. Needs icon art.
- More Cephalopod War events: refugees, captured technology, a second invasion wave.

## Testing

- `python -I tools/validate.py`: static checks for parsing, encoding, duplicate keys, event,
  tech and static modifier references, modifier names, localisation coverage and assets.
- `python -I tools/test_validator.py`: proves the validator still catches seeded mistakes.
- `python -I tools/ingame_test.py`: loads the mod on vanilla 4.6 and fails on any new error or crash.
