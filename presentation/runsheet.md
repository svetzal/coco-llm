# Runsheet

The 45-minute conference talk, with an exhibit table running alongside it.

`learning-journey.md` is the argument. This is the delivery: what happens, in
what order, for how long, and what gets dropped when the room runs long. Where
the two disagree about emphasis, this file wins on stage and the journey wins
in the written record.

## The budget

45 minutes total. 40 minutes of content, 5 minutes of questions. There is no
slack in that, so every block below has a stated cost and the cut order is
decided in advance rather than in the moment.

| # | Block | Min | Cum | Surface | Arc |
| --- | --- | ---: | ---: | --- | --- |
| 1 | It already works | 3 | 3 | Slide | Mystery |
| 2 | What the machine thinks a word is | 4 | 7 | Slide + room | Mechanism |
| 3 | Random numbers, then not | 11 | 18 | CoCo, EXP-004 | Mechanism |
| 4 | Change one thing: the prompt | 3 | 21 | CoCo, EXP-005 | Mechanism |
| 5 | Change one thing: the context | 5 | 26 | CoCo, EXP-011 | Mechanism |
| 6 | A screen of things that never existed | 3 | 29 | CoCo, EXP-012 | Delight |
| 7 | Change one thing: the upbringing | 4 | 33 | Slide, EXP-003 | Limitation |
| 8 | Now you play it | 5 | 38 | CoCo, EXP-013 | Agency |
| 9 | Who decided | 2 | 40 | Slide | Agency |
| | Questions | 5 | 45 | | |

Blocks 4, 5 and 7 repeat one sentence deliberately: *we changed exactly one
thing*. That repetition is the spine of the talk. Prompt, context, and training
data are three different stores, they change three different things, and
confusing them is most of what makes these systems feel like magic.

### Cut order

Announced here so it is a decision, not a panic.

1. **Block 6** goes first. It is the delight beat and it costs a machine
   changeover for three minutes. The table has it running all day.
2. **Block 4** goes second. Block 5 already carries "the model did not change,"
   and the abstract's marketing-language promise survives on the table.
3. **Block 3 shortens, it does not go.** If training is running long, stop the
   walkthrough and let the epochs finish in silence. The run is the promise.
4. **Block 8 never goes.** It is the strongest lesson in the set and the only
   one an audience member performs.

### Changeover cost

Five of nine blocks put a different binary on the machine. Each changeover is
20 to 30 seconds of dead air, so the budget above already spends roughly two
minutes on loading. Rehearse the changeovers, not only the demos. Where two
machines are available, stage the next binary on the second one and cut to it.

## The blocks

### 1. It already works

**On screen:** a photograph of a real trained run, full screen, no explanation.

Say the names. Say that none of them were ever made. Say the machine is from
1981, has 32 kilobytes, and started from random numbers about three minutes
before that photograph was taken.

Then make the promise: by the end of this you will know exactly how it did
that, and you will be unimpressed by it in precisely the right way.

Copy discipline applies. The photograph is of a genuine run or it does not go
on the slide.

### 2. What the machine thinks a word is

**On screen:** the 29 token values from EXP-004, then `COMMODORE AMIGA` encoded.

One idea: the machine does not have words, it has numbers, and someone chose
which numbers. Show the encoding, then show the three sliding two-token
examples that one name produces.

Ask the room for a word that is not in the vocabulary. There is no graceful
answer and that is the point. The table has the full tokenizer exercise for
anyone who wants to argue about it afterwards.

### 3. Random numbers, then not

**On screen:** EXP-004, live, on the CoCo.

The centrepiece and the reason the talk exists. Reset to random weights, seed
6809, generate visible nonsense. Start the training loop. While the epochs run,
walk one training step: scores, softmax, error, backpropagation, update. Reach
the declared boundary, pause at `PRESS ANY KEY`, and let someone in the room
decide when to run inference. Repeat seed 6809 and compare.

Reveal the two unsigned `MUL` operations only if the run gives you the time.
It is the best code beat in the talk and it is also the first thing to drop.

**This block's length is currently unmeasured on physical hardware.** See
"Open decisions" below. Eleven minutes is a planning figure, not a measurement.

If training does not improve, say so and inspect the evidence with the room.
A previously recorded run may be shown as a labelled comparison and never as a
substitute.

### 4. Change one thing: the prompt

**On screen:** EXP-005, title reading `SAME MODEL - CHANGE THE PROMPT`.

Ask what stayed fixed. Take `ARE YOU` and ask the room to call the completion
before showing `KEEPING UP IN LITTLE COMPUTERS`. It blended two campaigns into
something plausible without understanding either one.

### 5. Change one thing: the context

**On screen:** EXP-011, weights labelled locked, context labelled temporary.

This is the block with the most direct bearing on what people already use, so
protect its time. Retrieve `LISA = CODE 2`. Open the editor, type `6`, show
`BEFORE`, `AFTER`, and `MODEL 751B DID NOT CHANGE`. Ask the same question and
get the new answer.

The line to land:

> Training changes the weights. Prompting changes the context. Attention uses
> the context to produce this answer.

Then name the omission out loud. This is key-value attention, not a
transformer. We isolated one mechanism so it could be watched.

The score replay (`V`) is optional depth and is not in the budget.

### 6. A screen of things that never existed

**On screen:** EXP-012, one keystroke, sixteen invented Star Trek titles.

The lesson is the split, and it is visible in the sizes: 400 bytes of model
holding the shape of a title, against 1,600 bytes of dictionary and rules
holding the words. The model never learned what a Gothos is. It learned that
something goes there.

Say the corpus number, because it reframes the whole demo: across all 79 real
titles, only two adjacent word pairs ever repeat. There was nothing to
generalize from. It memorized a shape.

Note the second scenario cost. This is the one place the talk leaves the
vintage-computer example, so get in and out.

### 7. Change one thing: the upbringing

**On screen:** slides. The three fan corpora and the two orderings.

Same architecture, same initial weights, same budget, same vocabulary, same
sampling seed. Different data. Different machine.

Then the harder half: the same balanced examples concatenated and interleaved
produce different behaviour. Order is a choice too, and nobody set out to make
it one.

Ask which human decision produced each behaviour on screen. Do not answer it
for them.

### 8. Now you play it

**On screen:** EXP-013 on the CoCo, and someone from the room at the keyboard.

It does not know the rules. `RULES 0/25` says so before a round is played. It
does not know the player either, and `MEMORY n/rounds` says how little it has
to go on. Both counters stay on screen and neither needs narration.

Play six or eight rounds. It states its expectation before each throw, so the
audience watches a prediction get made and then judged. Somewhere around
twenty-five rounds it has the rules; it will never finish learning the person.

Press `R` in front of them and let it fall over.

Then quote the human number, which is the honest ending:

> Against six synthetic players with habits it scores 80%. Against a recorded
> 200-round session with a person who was trying, it scores 52.8%. It reads a
> person better than chance, three sigma better, and nowhere near well enough
> to win.

That gap is the talk in one number. Five of those six synthetic players had a
habit and one did not, and a person plays like the one that did not. The test
set encoded an assumption about people, and reporting its average hid that.

100 bytes. No neural network. A tiny table beat every model we tried, which is
why there is no model here at all.

### 9. Who decided

**On screen:** slides.

Not "language models are harmless" and not "no job will change." The durable
claim is smaller: the mechanism is understandable, the limitations are
observable, and every one of them traces back to a person who decided
something. Task, data, budget, success criterion, and what counts as good
enough.

Close on the table. Say what is running there and that you will be at it.

## What moves to the table

The table is not the overflow bin. It gets everything that needs a keyboard,
a patient visitor, and more than ninety seconds, which is exactly the material
a stage handles badly.

| Item | Why it belongs there |
| --- | --- |
| EXP-006 completion workbench | One person types for two minutes. Unwatchable from row 12. |
| EXP-007 sentence completion | Same, plus the `<END>` interface-failure story needs a conversation. |
| EXP-013 playable opponent | Also on stage. On the table people play until it beats them. |
| EXP-012 title generator | Runs unattended in a loop. Good attractor. |
| The four table exercises | Already designed against a 10-second to 15-minute ladder. |
| EXP-009 and EXP-010 music | Not stage-ready. Worth playing for anyone who asks. |

`table-exercises.md` currently assumes the table is the only surface. It needs
a pass to say which demo is running on which machine and when the presenter is
absent.

## Open decisions

These block locking the runsheet. Each one is a question for Stacey, not a task
to be worked around.

1. **How long does EXP-004 actually train on a physical CoCo 1?** Block 3 is
   eleven minutes of a forty-minute talk and its true length has never been
   measured on hardware. Everything downstream floats until it is. This is the
   single largest risk in the plan.
2. **Does the abstract still describe the talk?** It promises invented computer
   names and 1980s marketing phrases. Blocks 5, 6 and 8 are none of those
   things, and block 8 is the strongest beat in the set. Either the abstract
   is restated or blocks 5 and 8 are shrunk to honour it.
3. **One machine or two?** Five changeovers on one machine costs roughly two
   minutes of silence. A second machine buys that back and provides the backup
   the hardware contract already asks for.
4. **Is the audience volunteer in block 8 planned or found?** A planted player
   is faster and reads as a plant. A real one is slower and carries the point.
5. **Is there a handout?** One page, one QR code to the repository, and the
   three stores from blocks 4, 5 and 7 named on it. Cheap, and it is what
   people take home.

## What has to be built

In dependency order. Items 1 and 2 block rehearsal, which blocks everything.

1. **Stage launchers for EXP-012 and EXP-013.** `make present` stops at
   EXP-011, so two of the nine blocks have no launcher and no rehearsal path.
2. **Rehearsal notes for blocks 6 and 8.** `demo-rehearsal-notes.md` stops at
   EXP-011 as well.
3. **Physical timing for EXP-004.** See open decision 1.
4. **Slide source for blocks 1, 2, 7 and 9.** The four blocks with no CoCo on
   screen, and the only ones that need a deck at all.
5. **The photograph in block 1.** From a genuine run.
6. **The handout**, if decision 5 says yes.
7. **A table plan** revising `table-exercises.md` for two surfaces.
