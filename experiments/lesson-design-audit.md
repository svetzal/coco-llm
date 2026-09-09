# Lesson-design audit

This audit applies the project's lesson and demonstration guidance to every
experiment and, now that the talk exists, to every block of the runsheet. The
central question is not whether the result can be explained in speaker notes;
it is whether a learner can see what changed, what stayed fixed, what action
caused the change, and what evidence followed.

Refreshed 2026-09-08 against EXP-018, the steady sample clock, and the
runsheet as built. The first pass, 2026-08-13, stopped at EXP-013, the game
opponent, and predates the deck.

## The experiments

| Experiment | Causal lesson | Audit decision |
| --- | --- | --- |
| EXP-001, the rejected character model | The character model cannot meet the declared time budget. | Keep. The called shot and measured multiplication floor already show claim, evidence, and rejection. |
| EXP-002, the token model | Changing representation reduces the work while preserving the objective. | Keep. Characters-to-tokens, examples, and multiply counts make the changed factor visible. |
| EXP-003, the fan-corpus bias runs | Data selection and order change behaviour while model and budget stay fixed. | Improved twice. The presenter prints the concatenated and interleaved order before the result table, and block 7's figure now pairs what each model read with what it wrote, in the same maker colours, so training composition and output composition sit side by side. |
| EXP-004, the live training run | Training changes model state and therefore output. | Improved. Seed 6809 draws before training and again after, under the labels `BEFORE TRAINING - RANDOM WEIGHTS` and `AFTER TRAINING - LEARNED WEIGHTS`. Block 1 calls that shot out loud before block 2 explains it. |
| EXP-005, the prompted marketing completions | A prompt changes a completion without changing the trained model. | Improved. The persistent title reads `SAME MODEL - CHANGE THE PROMPT`, and block 4 reads the held controls aloud before the four asks: all 380 numbers, the same checksum before and after, the same seed, greedy decoding. |
| EXP-006, the 8 KiB completion workbench | Training can happen elsewhere while useful integer inference happens on the CoCo. | Improved. The persistent title reads `MAC TRAINED - COCO PREDICTS`; the failed quality gate remains visible in the written evidence. Table only. |
| EXP-007, the all-RAM sentence completer | More memory supports a larger, punctuation-aware inference model, not live training. | Improved. The same Mac/CoCo title keeps the training boundary visible. Block 5's three beats each isolate one cause: the ranking, the five-token window, and the stop the first interface hid. |
| EXP-008, the rejected adaptive opponent | A neural learner should be rejected when a tiny table predicts the live player better. | Keep. The reset-and-relearn protocol is causally strong; the null result correctly prevented a decorative 6809 UI. |
| EXP-009, the four-voice synthesizer | Constant-time playback fixes an audible timing defect. | Keep. Heard-before and fixed-after recordings provide a controlled comparison; implementation detail remains optional depth. The residual it accepted, the row-change stall, turned out to be audible after all; EXP-018, the steady sample clock, removed it. |
| EXP-010, the melody continuation | The person supplies an opening figure and the model supplies the continuation. | Improved. The title reads `YOU SEED - MODEL CONTINUES`; labels and colour reinforce, rather than replace, those roles. Since 2026-09-06 it performs through the steady clock, and the playback cursor is written by the same event stream that drives the voices, so what is heard and what is pointed at share one clock. |
| EXP-011, the context-editing attention head | Editing context can change an answer while model weights remain locked. | Keep as the reference pattern. The UI shows the learner's edit, before/after context, unchanged model identity, repeated question, and changed answer. Table only; on stage the context lesson rides block 4's held-fixed line and block 5's editor. |
| EXP-012, the fake episode titles | The model learns the shape of a title; a table supplies the words. | Keep. The split is the lesson and it is visible in the artifact: 400 bytes of model against 1,600 of dictionary and rules, on a corpus where only two word pairs ever repeat. Block 6's explainer draws the shape itself: BALANCE OF TERROR with the names lifted out to leave the gaps, and BALANCE OF BABEL dealt back into them. |
| EXP-013, the game opponent that learns | Learning the rules is the easy half; learning the person never finishes. | Keep. Two counters on screen separate the two, and pressing `R` collapses both in front of the audience. The human number is now on screen rather than only in narration: block 8's explainer slide quotes 52.8% beside the synthetic 80%. |
| EXP-014, the 6309 multiplier benchmark | A newer chip is not faster at everything; it has the one instruction this workload spends half its time inside. | Keep. Three rows on one screen: the same 58,000 multiplications, the same checksum under each, only the kernel and the mode changed. That is the held-and-changed shape with the invariant printed. Measured on the CoCo 3 on 2026-09-05, within 2.2% of the emulator. Not one of the runsheet's ten blocks; its own notes place it as a droppable bonus after block 3. |
| EXP-015, the faster-clock listening test | Sample rate is audible, and the ear decides what a faster clock is worth. | Keep, without a screen. Three builds of one frozen loop, the same tune, the clock the only change, heard in a fixed order through the 1703. The loaded filename is the label, and for a comparison played for the record that is enough. |
| EXP-016, the register-resident loop | Arithmetic can reject a rewrite before it is built. | Keep unbuilt. Same category as EXP-008, the rejected adaptive opponent: the record is the cycle table and the six percent it found, and no UI should be added to make it look like an experiment that ran. |
| EXP-017, the wavetable voices | The waveform changed and the square was preferred; the rate was the gain. | Keep as a verified capability, without a screen. The controlled pair is the square against the triangle on the same machine at the same rate. Refuted for this tune on the 1703, which is a result, not a failure. |
| EXP-018, the steady sample clock | A sample clock that never stretches has no warble, at a fifth of the rate. | Keep, and it is now block 9's performer. Heard-before and heard-after on the same machine, and a stopwatch on the tune's length checked the cycle table against silicon. |

## EXP-013's causal chain

EXP-013, the game opponent, is the strongest lesson in the set, so it is worth
writing out against the five-step pattern below.

1. **Fixed:** the machine is never told which move beats which, and the screen
   says so - `RULES 0/25` before a round is played.
2. **The learner's action:** every throw is a move the audience chose, and
   `IT EXPECTS <MOVE>` states the machine's guess *before* they commit to it.
3. **The changed state, in place:** `RULES n/25` climbs as cells are proved and
   `MEMORY n/rounds` counts what it has to go on. Both are on screen
   permanently; neither needs narration.
4. **The controlled comparison:** `R` empties both tables mid-session. The
   expectation drops to `IT HAS NO IDEA YET`, both counters fall to zero, and
   the audience watches them climb again. EXP-008, the rejected adaptive
   opponent, required this key and called it the falsifiability demonstration -
   without it nobody can distinguish a machine that learned from a difficulty
   curve that ramped.
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

**And the recorded session says to go further than that.** A player who is
merely *trying* - not randomising, just avoiding repeats - holds it to 52.8%.
The number to say on stage is that one, with the 80% offered as what it does to
a player with a habit. Claiming 80% for a person would be claiming the average
of a player set that turned out to encode an assumption about people. Block 8
now says exactly this, on a slide.

## The talk's blocks

The runsheet and the deck were built after the first pass of this audit, so
this section checks them the same way. The deck gives every demo block one
shape: the cue slide states the call, the machine takes the shot, and an
explainer slide lands the lesson on screen. The recurring slide "What it read"
quotes each model's corpus verbatim before its results, which is the guidance's
"establish the input first" made into a habit the room learns to expect.

| Block | What is held, what moves, where the lesson lands | Audit decision |
| --- | --- | --- |
| 1. Watch it work | Random weights and seed 6809 held; training is the action; the promise is paid when block 3 draws names from the same seed. | Keep. The photograph of a real run does not exist yet, so today the block is a launch and a called shot. That is honest, and it is enough until the photograph is taken. |
| 2. How it works, on slides | No machine. Lookup, addition, and the nudge per number, drawn from real model traces, while the launched run trains underneath. | Keep. This is the optional-depth mechanism view, placed where the guidance puts it: after the input is on screen and before the outcome is claimed. |
| 3. A little 6809 assembly | One captured training step, registers on screen end to end; then the run finishes and the seed draws names. | Keep. The step is the mechanism made visible. The block has never been timed on hardware, and that number is the exhibit-copy gate. |
| 4. Change one thing: the prompt | 380 numbers, the checksum before and after, the seed, and greedy decoding held; the prompt moves; four answers on a slide, then one chosen live. | Keep as the stage's reference pattern. The held-fixed line is read aloud before the asks, and the checksum is the invariant test the guidance asks for. |
| 5. Change one thing: the size | Task and held-out sentences held; vocabulary, window and parameter count move; three beats at the machine each isolate one cause. | Keep. Both called shots missed and stay on the record. The physical keyboard is unmeasured and the notes say so wherever the numbers appear. |
| 6. A screen of things that never existed | Dictionary and rules held; one keystroke; sixteen titles; the byte split and the shape figure on the explainer. | Keep. The rules are laid out beside the failure each one vetoes, so every veto reads as a decision a person wrote down. The one place the talk leaves the vintage-computer example. |
| 7. Change one thing: the training data | Architecture, seeds, budget and vocabulary held, and for the last two bars the same 54 names; only the file order moves; what each model read beside what it wrote. | Keep, as a slide. EXP-003, the fan-corpus bias runs, has no 6809 build, and the bars carry a five-way comparison a live run could not show in two minutes. Do not build a CoCo version to make the block look like its neighbours. |
| 8. Now you play it | The rules never told, `RULES 0/25` on screen; the room's throws are the action; both counters climb, `R` drops them, they climb again; the honest number closes it. | Keep. The strongest lesson in the set, and the human number now lands on screen. |
| 9. A token is a note | The 3,044-byte model and the band that is rules held; the seed a person enters is the action; the continuation is composed, then performed, with the cursor and the voices driven by one clock. | Keep. The roles are named on the machine. There is no held-and-changed comparison and none is owed; the lesson is who supplies what, not a delta. No figure yet. |
| 10. Who decided? | Slides. Task, data, budget, success criterion, and what counts as good enough, each traced to a person. | Keep. The close names the decisions the blocks showed being made. |

Two things the block pass adds to the experiment pass. First, blocks 4 and 7
say the same sentence on purpose, *we changed exactly one thing*, and the
figures back it: a held-fixed line read aloud in block 4, and paired bars in
block 7. That repetition is the controlled comparison carried across blocks,
and it should survive any cut. Second, the invariant is stated on screen in
block 4 and only in words in block 7. Block 7's figure holds the controls in
its caption rather than in a printed checksum; that is acceptable for a slide
that shows twenty draws, but if the block ever moves to the machine the checksum
goes with it.

## Pattern carried forward

For any new interactive lesson, put this causal chain in the artifact:

1. name the state that will remain fixed;
2. show the learner's action at the moment it occurs;
3. show the changed state in place;
4. repeat the same query, seed, or task when a controlled comparison is useful;
5. show the resulting behaviour without requiring narration to explain it.

On stage the same chain has a slide shape: a corpus slide before any result,
a cue slide that states the call, the machine taking the shot, and an
explainer that lands the lesson on screen. For a listening experiment the
chain is the same with the screen removed: one frozen loop, one tune, one
variable, a fixed listening order, and the words and recording as the record.

Mechanism views remain valuable, but only after the causal story is legible.
Colour may reinforce roles; text, position, or symbols must also name them.

## What a parity test cannot tell you

EXP-012, the fake episode titles, and EXP-013, the game opponent, are both
verified cell by cell against a Mac reference, and that caught a great deal: a
register clobbered where a column was being tracked, uninitialised tallies
reporting 255 rounds on a fresh board, a random generator whose last step
assembled the two halves of a word the wrong way round, and a score that
truncated where the reference rounded.

It did not catch the screen being inverted, and could not have. **A parity test
proves agreement, not correctness.** Where the reference is as free to guess as
the port - which character set is which, what a blank cell is, what colour a
value draws - both can agree and both be wrong. EXP-013 drew its body reversed
and its title bar plain while reporting 512 of 512 cells matching, and it took
looking at the emulator to see it.

The sound experiments then repeated the lesson through a different sense.
EXP-015, the faster-clock listening test, found the standalone player had been
silently broken since 2026-08-02, and EXP-017, the wavetable voices, found a
tempo cell read before anything wrote it. Neither fault is visible to a
200-sample parity check; both were caught by playing whole tunes under XRoar
with RAM set to all ones at power-on, which every player now does. Then the
1703 found what the emulator had not. The emulator session on 2026-09-06 heard
the rate gain, and the machine heard the rate gain and an 8 Hz warble on the
melody voice that no test had predicted. EXP-018, the steady sample clock,
traced it to a stall EXP-009, the four-voice synthesizer, had measured and
accepted. The same weekend XRoar's 6309, which XRoar itself labels unverified,
agreed with silicon within 2.2% on EXP-014, the multiplier benchmark, and the
steady tune ran to the stopwatch. The emulator earned its trust, but it earned
it on the machine, not by argument.

Three things follow, and all three are now in the code or the Makefile:

- Anything only the target machine can settle has to be *seen*, or heard,
  there before it is believed. Reasoning about a display from its documentation
  is how the screen was got wrong twice in a row, and reasoning about a stall
  from a cycle table is how the warble was accepted.
- Conventions that several experiments share belong in one file rather than
  being re-derived per experiment. `src/6809/text_screen.asm` now owns the two
  character sets and `screen_title_bar`; it exists because the same decision
  was made independently three times and the third one was wrong.
- Anything that plays a tune runs it to the end under hostile RAM beside its
  parity test. The parity test proves the loop; the whole-tune run proves the
  cells around it were written before they were read.

## Remaining evidence boundaries

- EXP-003, the fan-corpus bias runs, has no 6809 implementation. Block 7 is a
  slide for that reason, and the block pass above says to leave it one.
- EXP-004, the live training run, EXP-006, the 8 KiB completion workbench,
  EXP-007, the all-RAM sentence completer, and EXP-011, the context-editing
  attention head, still need the physical hardware validation recorded in
  their experiment notes. EXP-004's hardware time is the printable number and
  the exhibit-copy gate.
- EXP-010, the melody continuation, has been heard on the CoCo 3 through the
  1703, on 2026-09-06, through the steady clock. The CoCo 1 has not been heard
  yet, and the CoCo 1 pair for EXP-018, the steady sample clock, was not
  recorded.
- EXP-014, the 6309 multiplier benchmark, still lacks its CoCo 1 baseline run
  and the training-run timing that would settle how much of the whole run the
  multiply is.
- EXP-015, the faster-clock listening test, recorded the sound and not the
  pitch or the tune's length, so its first two hypotheses are still open.
  EXP-017, the wavetable voices, has not been heard on the CoCo 1.
- EXP-008, the rejected adaptive opponent, EXP-009, the four-voice
  synthesizer, and EXP-016, the register-resident loop, should not acquire
  additional UI merely to make every experiment look alike. If a listening
  pair from EXP-015 or EXP-017 is ever played for a visitor rather than for
  the record, the screen should say which build is playing; today the loaded
  filename is the only label.
- EXP-013, the game opponent, has one recorded human session, one player who
  could see the prediction, scoring 52.8% where the synthetic players said
  80%. A second recording from someone who has not been told what to avoid is
  the obvious next one.
- Block 1's photograph of a genuine run on the physical CoCo 1 has not been
  taken, and block 9 has no figure. Both are on the runsheet's build list, not
  findings of this audit.
