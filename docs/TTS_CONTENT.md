# To the Stars content plan

This is new content inspired by Hieronym's *To the Stars* (TtS), a long Madoka Magica fanfic
set centuries after the anime, in which humanity, governed with AI help and supported by an
organized magical girl society, fights an alien war.

This is **original game content written in the spirit of the fic**, not a reproduction of it.
Names and concepts come from the story; all text is new. Where the fic's details are uncertain,
the content makes its own choices. Every TtS object uses the `tts_` prefix (events use the
`stella_tts_*` namespaces) so it is easy to find and can't collide with the original mod.

## Waves

Each wave is added, validated (`tools/validate.py`), load-tested in game
(`tools/ingame_test.py`), committed and pushed before the next one starts.

1. **Institutions.** The MSY (magical girl mutual aid, grief cube logistics) and Governance
   (AI-advised representative government): civics, MSY office building and job, techs
   (cortical implants, TacComp, MagOps doctrine), MagOps armies, and new magical girl leader traits.
2. **The Cephalopod War.** A mid-game alien threat that attacks without warning or
   communication. It brings raids, a forward base to destroy, wreckage research, and rewards.
3. **Contracts and wishes.** Magical-legacy empires periodically see girls contract with the
   Incubators. Each wish is a choice with lasting consequences, and some produce leaders.
4. **The Cult of Hope.** A faith in the Goddess (the Law of Cycles): civic, church building and
   job, and events.
5. **Familiar faces.** Story events with Tomoe Mami, Sakura Kyouko, Akemi Homura, Chitose Yuma
   and the original character Shizuki Ryouko, using the mod's existing portraits where they exist.
6. **Policy and society.** Public disclosure of magical girls, grief cube rationing edicts,
   council agendas and situations.

## Testing

- `python -I tools/validate.py`: static checks for parsing, encoding, duplicate keys, event,
  tech and static modifier references, modifier names, localisation coverage and assets.
- `python -I tools/test_validator.py`: proves the validator still catches seeded mistakes.
- `python -I tools/ingame_test.py`: loads the mod on vanilla 4.6 and fails on any new error or crash.
