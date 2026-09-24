# evals

The evaluation set for the sentence reader. [README.md](README.md) says how to run it, how a case is written and what a run costs.

- **Every sentence is made up.** A real user's words never enter this folder, reworded or not, without their consent in writing (ADR 0005). This repository is public.
- A case says what a careful person would do with the sentence, never what a reader does today. If a reader gets it wrong, the run fails until the reader is put right.
- Do not weaken a case, lower a floor or raise a ceiling to make a change pass. Raise it with the founder instead.
- An id is never reused or renumbered. Add a case at the end of its file.
- Places and areas are names of the synthetic release. `score.py --check` refuses any other.
- Where two readings of a sentence are fair, the case accepts both. It does not pick one.
- `score.py` and `controls.py` import the standard library and `burro_core` only. `model_reader.py` is the one file that imports the API.
- The scorer prints counts, ids and the sentences of cases. It never prints what a reader answered, and of an error only the name of its class.
- After a change here, run `uv run python evals/reader/score.py --check` and `uv run pytest evals/reader`.
- When a floor moves, write `reader/baseline/` and `reader/BASELINE.md` again, with the date, the engine version and the hash the scorer prints.
