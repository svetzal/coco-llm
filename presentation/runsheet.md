# Runsheet

The 45-minute conference talk, with an exhibit table running alongside it.

`learning-journey.md` is the argument. This is the delivery: what happens, in
what order, for how long, and what gets dropped when the room runs long. Where
the two disagree about emphasis, this file wins on stage and the journey wins
in the written record.

## Staging

**The projector shows an emulator. The real machine is at the table.**

Everything on stage runs in XRoar on the laptop, so the projector cable is
never touched and the talk never waits for a 1981 machine to load from an SDC.
The CoCo 1 itself lives at the exhibit table, powered on, all day.

This is a fair trade only if it is said out loud, once, early, and never again:

> What you are seeing is an emulator, running at the actual machine's clock
> speed. Nothing here is sped up. The real one is at table N and I would love
> you to come and press its keys.

Two reasons that stays honest. Every stage target already passes `-ratelimit`,
so XRoar runs the 6809 at roughly 0.89 MHz and a training run takes exactly as
long on the projector as it does on the desk. And the physical machine is forty
feet away in the same room, which is a much stronger claim than a photograph.

The gain is not only convenience. Vintage hardware into a conference projector
is a well-known way to lose the first ten minutes of a talk, and this removes
that failure entirely. The cost is that the object stops being on stage, so the
table has to carry it. Blocks 1 and 9 both point at the table by name.

What this does not license: running unthrottled, using a CoCo 3 in fast mode
without saying so, or describing an emulator run as hardware-measured. The
copy discipline in `exhibit-copy.md` still holds. No runtime claim goes on a
slide until it is measured, and an emulator measurement is labelled as one.

## The budget

45 minutes total. 40 minutes of content, 5 minutes of questions. There is no
slack in that, so every block below has a stated cost and the cut order is
decided in advance rather than in the moment.

| # | Block | Min | Cum | Surface | Arc |
| --- | --- | ---: | ---: | --- | --- |
| 1 | It already works | 3 | 3 | Slide | Mystery |
| 2 | Tokens, and what a parameter is | 3 | 6 | Slides | Mechanism |
| 3 | Random numbers, then not | 12 | 18 | Slides then EXP-004 live training | Mechanism |
| 4 | Change one thing: the prompt | 3 | 21 | CoCo, EXP-005 prompted completions | Mechanism |
| 5 | Change one thing: the context | 5 | 26 | CoCo, EXP-011 attention head | Mechanism |
| 6 | A screen of things that never existed | 3 | 29 | CoCo, EXP-012 fake titles | Delight |
| 7 | Change one thing: the upbringing | 4 | 33 | Slide, EXP-003 fan-corpus bias | Limitation |
| 8 | Now you play it | 5 | 38 | CoCo, EXP-013 game opponent | Agency |
| 9 | Who decided | 2 | 40 | Slide | Agency |
| | Questions | 5 | 45 | | |

Blocks 4, 5 and 7 repeat one sentence deliberately: *we changed exactly one
thing*. That repetition is the spine of the talk. Prompt, context, and training
data are three different stores, they change three different things, and
confusing them is most of what makes these systems feel like magic.

### Cut order

Announced here so it is a decision, not a panic.

1. **Block 6** goes first. It is the delight beat, and the table runs it in a
   loop all day on the real machine.
2. **Block 4** goes second. Block 5 already carries "the model did not change,"
   and the abstract's marketing-language promise survives on the table.
3. **Block 3 shortens, it does not go.** If training is running long, stop the
   walkthrough and let the epochs finish in silence. The run is the promise.
4. **Block 8 never goes.** It is the strongest lesson in the set and the only
   one an audience member performs.

### Changeover cost

Five of nine blocks load a different binary. On real hardware that is 20 to 30
seconds of dead air each, and the original budget spent roughly two minutes on
it. Under the emulator each one is a window switch, so that time comes back as
buffer rather than being spent.

Do not spend it. Block 3, the live training run, has never been timed, and its
eleven minutes is a planning figure. The recovered two minutes is the margin
that absorbs being wrong about it.

Have all five XRoar instances launched and parked before the talk starts, one
per block, so a changeover is a window switch and not a `make` invocation on
the projector. Rehearse the switching, not only the demos.

## The blocks

### 1. It already works

**On screen:** a photograph of the physical CoCo 1 showing a real trained run,
full screen, no explanation.

Say the names. Say that none of them were ever made. Say the machine is from
1981, has 32 kilobytes, and started from random numbers about three minutes
before that photograph was taken.

Then make the promise: by the end of this you will know exactly how it did
that, and you will be unimpressed by it in precisely the right way.

Then the disclosure, in one breath, and then never again:

> That machine is at table N. What I am about to project is its emulator,
> running at its clock speed. Nothing here is sped up, and I would much rather
> spend these forty minutes on the model than on a video cable.

The photograph now carries two jobs. It is the mystery, and it is the evidence
that the physical object exists and is in the building. Frame it so the machine
is recognisably a CoCo 1 and not a screen grab.

Copy discipline applies. The photograph is of a genuine run or it does not go
on the slide.

### 2. Tokens, and what a parameter is

**On screen:** the 29 token values from EXP-004, the live training run, then
`COMMODORE AMIGA` encoded.

Name the mechanism out loud. Cutting text into countable pieces is
**tokenizing** and the pieces are **tokens**; most of the room has heard the
word and never had it explained. Here a token is a whole word because we chose
that.

Show the encoding, then the three sliding two-token examples one name produces.

Ask the room for a word that is not in the vocabulary. There is no graceful
answer and that is the point. The table has the full tokenizer exercise for
anyone who wants to argue about it afterwards.

Blocks 2 and 3 now share fifteen minutes and the boundary between them moved
once the figures were built. Treat them as one run at mechanism and watch the
combined total rather than each one.

### 3. Random numbers, then not

**On screen:** five figures, then EXP-004, the live training run, on the CoCo.

The block opens with four minutes of slides that used to be narration over the
training run:

1. **Thirteen doesn't mean anything.** An identifier is a name. `ZX80` is 27
   and `ZX81` is 28 by alphabetical accident, and `APPLE` 8 sits beside
   `ARCHIMEDES` 9 for the same reason. Arithmetic on it proves nothing.
2. **Why three?** One number puts a word on a line, three put it in a space.
   Then the cost of each width, and the admission that six would have fit.
   Three is a decision, not a limit.
3. **Where the numbers live.** Both lookup tables, all 29 words, with the two
   fetched rows lit. `COMMODORE` holds a different row in each slot, which is
   the whole of what positional means.
4. **What a parameter is.** 2x29x3 plus 29x3 plus 29 is 290, counted out. Then
   the definition: one number training is allowed to change. Then GPT-3's 175
   billion, without editorial.
5. **One step**, and **do it again**.

Because that explanation is now front-loaded, the live run needs less talking
over it and holds seven and a quarter minutes rather than nine. That is the
figure to revisit the moment training is actually timed.

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

**On screen:** EXP-005, the prompted marketing completions, title reading
`SAME MODEL - CHANGE THE PROMPT`.

Ask what stayed fixed. Take `ARE YOU` and ask the room to call the completion
before showing `KEEPING UP IN LITTLE COMPUTERS`. It blended two campaigns into
something plausible without understanding either one.

### 5. Change one thing: the context

**On screen:** EXP-011, the context-editing attention head, weights labelled
locked and context labelled temporary.

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

**On screen:** EXP-012, the fake episode titles, one keystroke, sixteen of them.

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

**On screen:** EXP-013, the game opponent that learns, and someone from the room
calling throws.

Volunteer at the laptop or calling numbers from their seat, either works. The
laptop keyboard is the easier one to drive and the whole room can read the
screen. Whoever plays gets the invitation on the spot: the real machine is at
the table and it will happily lose to them again.

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

The table is not the overflow bin, and since the talk projects an emulator it
now holds the only real hardware in the building. That is a promotion. It gets
the physical CoCo 1, plus everything that needs a keyboard, a patient visitor,
and more than ninety seconds, which is exactly the material a stage handles
badly.

| Item | Why it belongs there |
| --- | --- |
| The physical CoCo 1 | The claim the whole talk rests on. Powered on, all day, touchable. |
| EXP-006, the 8 KiB completion workbench | One person types for two minutes. Unwatchable from row 12. |
| EXP-007, the all-RAM sentence completer | Same, plus the `<END>` interface-failure story needs a conversation. |
| EXP-013, the playable game opponent | Also on stage. On the table people play until it beats them. |
| EXP-012, the fake title generator | Runs unattended in a loop. Good attractor. |
| The four table exercises | Already designed against a 10-second to 15-minute ladder. |
| EXP-009 and EXP-010, the four-voice synthesizer and melody continuation | Not stage-ready. Worth playing for anyone who asks. |

`table-exercises.md` currently assumes the table is the only surface. It needs
a pass to say which demo is running on which machine and when the presenter is
absent. The hardware contract already provides two machines, a CoCo 1 and a
CoCo 3, and with the projector out of the picture the CoCo 3's HDMI output no
longer buys anything on stage. Both can be at the table, which means one can
run the title generator in a loop while a visitor plays the other.

## Open decisions

These block locking the runsheet. Each one is a question for Stacey, not a task
to be worked around.

1. **How long does EXP-004, the live training run, actually take?** Block 3 is
   eleven minutes of a forty-minute talk and has never been timed. Everything
   downstream floats until it is. This is the single largest risk in the plan,
   and projecting the emulator makes it cheap to settle: XRoar at `-ratelimit`
   runs the same clock, and the run can be trapped and wall-clocked on the
   laptop without touching hardware. Worth doing before any slide is made.
2. **Does the abstract still describe the talk?** It promises invented computer
   names and 1980s marketing phrases. Blocks 5, 6 and 8 are none of those
   things, and block 8 is the strongest beat in the set. Either the abstract
   is restated or blocks 5 and 8 are shrunk to honour it.
3. **Is XRoar legible from the back row?** A 32 by 16 character screen scaled
   onto a conference projector has never been checked, and no stage target
   passes any scaling or geometry flag. This replaces the old one-machine
   question and is now the only display risk left.
4. **Is the audience volunteer in block 8 planned or found?** A planted player
   is faster and reads as a plant. A real one is slower and carries the point.
5. **Is there a handout?** One page, one QR code to the repository, and the
   three stores from blocks 4, 5 and 7 named on it. Cheap, and it is what
   people take home. It is also where the table number goes.

## What has to be built

In dependency order. Items 1 and 2 block rehearsal, which blocks everything.

1. **Stage launchers for EXP-012 (fake titles) and EXP-013 (game opponent).**
   `make present` stops at EXP-011, the attention head, so two of the nine
   blocks have no launcher and no rehearsal path.
2. **Rehearsal notes for blocks 6 and 8.** `demo-rehearsal-notes.md` stops at
   EXP-011, the attention head, as well.
3. **Timing for EXP-004, the live training run**, trapped and wall-clocked
   under XRoar at `-ratelimit`. See open decision 1. Now cheap, and it sets
   the length of the largest block in the talk.
4. **A projector legibility check** for XRoar, and whatever scaling flags the
   stage targets turn out to need. See open decision 3.
5. **Slide source for blocks 1, 2, 7 and 9.** The four blocks with no emulator
   on screen, and the only ones that need a deck at all.
6. **The photograph in block 1**, of the physical machine, from a genuine run.
7. **The handout**, if decision 5 says yes.
8. **A table plan** revising `table-exercises.md` for two surfaces and two
   physical machines.
