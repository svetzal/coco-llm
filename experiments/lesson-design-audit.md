# Lesson-design audit

This audit applies the project's lesson and demonstration guidance to every
experiment. The central question is not whether the result can be explained in
speaker notes; it is whether a learner can see what changed, what stayed fixed,
what action caused the change, and what evidence followed.

| Experiment | Causal lesson | Audit decision |
| --- | --- | --- |
| EXP-001 | The character model cannot meet the declared time budget. | Keep. The called shot and measured multiplication floor already show claim, evidence, and rejection. |
| EXP-002 | Changing representation reduces the work while preserving the objective. | Keep. Characters-to-tokens, examples, and multiply counts make the changed factor visible. |
| EXP-003 | Data selection and order change behaviour while model and budget stay fixed. | Improve. The presenter now prints the concatenated and interleaved order before the result table, followed by the held controls. |
| EXP-004 | Training changes model state and therefore output. | Improve. The CoCo now generates with seed 6809 before training, repeats seed 6809 after training, and labels random versus learned weights on screen. |
| EXP-005 | A prompt changes a completion without changing the trained model. | Improve. The persistent title reads `SAME MODEL - CHANGE THE PROMPT`. |
| EXP-006 | Training can happen elsewhere while useful integer inference happens on the CoCo. | Improve. The persistent title reads `MAC TRAINED - COCO PREDICTS`; the failed quality gate remains visible in the written evidence. |
| EXP-007 | More memory supports a larger, punctuation-aware inference model, not live training. | Improve. The same Mac/CoCo title keeps the training boundary visible while the all-RAM mechanism is explored. |
| EXP-008 | A neural learner should be rejected when a tiny table predicts the live player better. | Keep. The reset-and-relearn protocol is causally strong; the null result correctly prevented a decorative 6809 UI. |
| EXP-009 | Constant-time playback fixes an audible timing defect. | Keep. Heard-before and fixed-after recordings provide a controlled comparison; implementation detail remains optional depth. |
| EXP-010 | The person supplies an opening figure and the model supplies the continuation. | Improve. The title now reads `YOU SEED - MODEL CONTINUES`; labels and colour reinforce, rather than replace, those roles. |
| EXP-011 | Editing context can change an answer while model weights remain locked. | Keep as the reference pattern. The UI shows the learner's edit, before/after context, unchanged model identity, repeated question, and changed answer. |
| EXP-012 | The model learns the shape of a title; a table supplies the words. | Keep. The split is the lesson and it is visible in the artifact: 400 bytes of model against 1,600 of dictionary and rules, on a corpus where only two word pairs ever repeat. |
| EXP-013 | Learning the rules is the easy half; learning the person never finishes. | Keep. Two counters on screen separate them, and pressing `R` collapses both in front of the audience. |

## EXP-013's causal chain

This is the strongest lesson in the set, so it is worth writing out against the
five-step pattern below.

1. **Fixed:** the machine is never told which move beats which, and the screen
   says so - `RULES 0/25` before a round is played.
2. **The learner's action:** every throw is a move the audience chose, and
   `IT EXPECTS <MOVE>` states the machine's guess *before* they commit to it.
3. **The changed state, in place:** `RULES n/25` climbs as cells are proved and
   `MEMORY n/rounds` counts what it has to go on. Both are on screen
   permanently; neither needs narration.
4. **The controlled comparison:** `R` empties both tables mid-session. The
   expectation drops to `IT HAS NO IDEA YET`, both counters fall to zero, and
   the audience watches them climb again. EXP-008 required this key and called
   it the falsifiability demonstration - without it nobody can distinguish a
   machine that learned from a difficulty curve that ramped.
5. **The behaviour:** it starts losing and ends winning, and a player who reads
   the expectation line can beat it back.

The two counters are the point rather than decoration. **`RULES` stops climbing
well short of 25** - around seven to thirteen against a habitual player - because
the machine only ever learns a winning answer to the moves you actually throw.
Where it stops is therefore a readout of how varied *you* are, which is a better
thing to put in front of an audience than an accuracy percentage, and it is the
claim the demo should make out loud.

The honest framing is not "it learns the rules". Learning the rules is over in a
couple of dozen rounds and never finishes completely; the half that never
finishes at all is learning the player. That also answers the obvious challenge:
a person who genuinely randomises cannot be beaten, and the demo should say so
rather than hope nobody tries it.

## Pattern carried forward

For any new interactive lesson, put this causal chain in the artifact:

1. name the state that will remain fixed;
2. show the learner's action at the moment it occurs;
3. show the changed state in place;
4. repeat the same query, seed, or task when a controlled comparison is useful;
5. show the resulting behaviour without requiring narration to explain it.

Mechanism views remain valuable, but only after the causal story is legible.
Colour may reinforce roles; text, position, or symbols must also name them.

## What a parity test cannot tell you

EXP-012 and EXP-013 are both verified cell by cell against a Mac reference, and
that caught a great deal: a register clobbered where a column was being
tracked, uninitialised tallies reporting 255 rounds on a fresh board, a random
generator whose last step assembled the two halves of a word the wrong way
round, and a score that truncated where the reference rounded.

It did not catch the screen being inverted, and could not have. **A parity test
proves agreement, not correctness.** Where the reference is as free to guess as
the port - which character set is which, what a blank cell is, what colour a
value draws - both can agree and both be wrong. EXP-013 drew its body reversed
and its title bar plain while reporting 512 of 512 cells matching, and it took
looking at the emulator to see it.

Two things follow, and both are now in the code:

- Anything only the target machine can settle has to be *seen* there before it
  is believed. Reasoning about a display from its documentation is how this was
  got wrong twice in a row.
- Conventions that several experiments share belong in one file rather than
  being re-derived per experiment. `src/6809/text_screen.asm` now owns the two
  character sets and `screen_title_bar`; it exists because the same decision
  was made independently three times and the third one was wrong.

## Remaining evidence boundaries

- EXP-003 still needs a matching 6809 implementation before it becomes a live
  hardware experiment.
- EXP-004, EXP-006, EXP-007, EXP-010, and EXP-011 still need the physical
  hardware validation already recorded in their experiment notes.
- EXP-008's rejection and EXP-009's timing fix should not acquire additional UI
  merely to make every experiment look alike.
- EXP-013 has been played by a human on the emulator and holds up as a game.
  What it lacks is a *recorded* session: its numbers are measured against six
  synthetic players invented by the person who wants the agent to win, and
  nothing has been written down that could score them. That is the exact
  failure EXP-008 recorded first-hand - its synthetic phase passed on players
  its human phase then failed on - and EXP-008 could only settle it because it
  had the move streams on disk.
