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

45 minutes total: **36 minutes of content, 2 minutes of reserve, 7 for
questions.**

That reserve exists because of a measurement. Blocks 1 and 2 were budgeted at
11 minutes on the assumption that eight figure slides need a minute each. Walked
through, they take 2 to 3 minutes, or 3 to 5 with questions from the room. They
now hold 5, and the six minutes that recovered went to the live training run,
which had been squeezed twice to pay for those slides.

The run has since been wall-clocked under the emulator: launch to `PRESS ANY
KEY` in one to two minutes (an emulator measurement — see block 3). So block
3's room is no longer covering an unknown; it is genuine slack, and the
reserve behind it is genuine reserve. Do not spend it in advance anyway. It
is there for questions.

| # | Block | Slides | Min | Cum | Surface | Arc |
| --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | It already works | 1 | 1 | 1 | Slide | Mystery |
| 2 | How it works, on slides | 8 | 4 | 5 | Slides | Mechanism |
| 3 | How it works, on the machine | 1 | 9 | 14 | EXP-004 live training | Mechanism |
| 4 | Change one thing: the prompt | 1 | 3 | 17 | CoCo, EXP-005 prompted completions | Mechanism |
| 5 | Change one thing: the context | 1 | 5 | 22 | CoCo, EXP-011 attention head | Mechanism |
| 6 | A screen of things that never existed | 1 | 3 | 25 | CoCo, EXP-012 fake titles | Delight |
| 7 | Change one thing: the upbringing | 1 | 4 | 29 | Slide, EXP-003 fan-corpus bias | Limitation |
| 8 | Now you play it | 1 | 5 | 34 | CoCo, EXP-013 game opponent | Agency |
| 9 | Who decided | 1 | 2 | 36 | Slide | Agency |
| | Reserve, held for block 3 | | 2 | 38 | | |
| | Questions | | 7 | 45 | | |

Blocks 2 and 3 were one block when this file was written. Building the figures
split them: eight slides now carry the explanation that used to be narrated
over the training run.

**Block 3 now holds 9 minutes and there are 2 more in reserve behind it.**
That is more room than the run needs. Wall-clocked under XRoar at
`-ratelimit` on 2026-08-29, launch to `PRESS ANY KEY` took **49 seconds**
windowed and 96 headless — emulator measurements, labelled as such, with the
two bracketing the 75-second cycle projection and physical hardware still the
authority. The risk has flipped: the machine will be parked at the training
boundary before the code slides are half done, and the block's room is for
the comparison and the room's questions rather than for an unknown.

Block 2, slide by slide:

| Slide | Sec | What it settles |
| --- | ---: | --- |
| What is a word? | 40 | Tokenizing, tokens, and the context window, named where they first appear |
| Thirteen doesn't mean anything | 20 | An identifier is a name; arithmetic on it proves nothing |
| Where the numbers live | 25 | The embedding tables, named at first sight; the same token holds a different row per position |
| Why three? | 30 | The cost of each embedding width, and that six would have fitted |
| What a parameter is | 25 | 2x29x3 + 29x3 + 29 = 290, and the definition |
| One step | 40 | Predict, then correct, with the nudge number by number |
| Do it again. And again. | 40 | Repeating, inventing, reciting: three failures that go in order |
| What it cost | 20 | Time and memory, and what learning costs over using |

These are seconds, not minutes, and that is the measurement talking. Eight
figures that each carry one idea go faster than they look on paper. If the room
asks questions the block stretches, and that is what it is for.

Blocks 4, 5 and 7 repeat one sentence deliberately: *we changed exactly one
thing*. That repetition is the spine of the talk. Prompt, context, and training
data are three different stores, they change three different things, and
confusing them is most of what makes these systems feel like magic.

### Cut order

Announced here so it is a decision, not a panic.

1. **Block 6** goes first, the fake titles. It is the delight beat, and the
   table runs it in a loop all day on the real machine.

   Inside block 2, the first slide to drop is **What it cost**, then **Why
   three?**. Both answer questions rather than advance the argument, and both
   have their evidence written up in EXP-002 for anyone who asks at the table.
   **Never drop "Do it again. And again."** It is where the talk's central
   claim is measured.
2. **Block 4** goes second. Block 5 already carries "the model did not change,"
   and the abstract's marketing-language promise survives on the table.
3. **Block 3 shortens, it does not go.** If training is running long, let the
   epochs finish in silence; block 2 has already done the explaining. The run
   is the promise.
4. **Block 8 never goes.** It is the strongest lesson in the set and the only
   one an audience member performs.

### Changeover cost

Five of nine blocks load a different binary. On real hardware that is 20 to 30
seconds of dead air each, and the original budget spent roughly two minutes on
it. Under the emulator each one is a window switch, so that time comes back as
buffer rather than being spent.

Do not spend it. Block 3, the live training run, now has an emulator wall
clock — one to two minutes to the training boundary — so the recovered two
minutes is genuine margin rather than cover for an unknown.

Before the talk, run `make stage`. It launches and parks four XRoar
instances, so each changeover is a window switch and not a `make` invocation
on the projector:

- EXP-005, block 4 — trains itself on load and parks at `PRESS ANY KEY`.
- EXP-011, block 5 — parks at the context table.
- EXP-012, block 6 — parks showing titles.
- EXP-013, block 8 — parks at the RPSLS keys. Press `R` if anyone played it
  during setup.

The windows look identical. Arrange them in block order. **EXP-004 is the
exception. Launch it live** with `make present EXP=4` at the top of block 3:
it starts training the moment it loads, so the launch is the reset, and an
early launch would burn the run. Keep a terminal at the repository root
ready for that command. Rehearse the switching, not only the demos. The
same launch cues are in the deck's speaker notes on each cue slide.

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

### 2. How it works, on slides

Eight slides, eight minutes, no machine. This block did not exist when the
runsheet was written: it is the explanation that used to be narrated over the
live training run, moved onto figures so the run can be watched instead of
talked over.

Every number in every figure is exported from the reference model by
`tools/export_deck_traces.py`, so a figure cannot drift from the machine.

1. **What is a word?** Name both terms the room arrived with. Cutting text into
   countable pieces is **tokenizing**; the pieces are **tokens**; here a token
   is a whole word because we chose that. Then, on the sliding rows, the two
   boxes it looks at are the **context window**, two tokens wide, and it
   slides. Say once that a model advertising a 200,000-token window means this,
   wider — and that the sliding is why a long chat seems to forget its own
   beginning: the start fell out of the window. Ask for a word outside the
   vocabulary; there is no graceful answer.
2. **Thirteen doesn't mean anything.** An identifier is a name, not a
   description. `ZX80` is 27 and `ZX81` is 28 by alphabetical accident, and
   `APPLE` 8 sits beside `ARCHIMEDES` 9 for the same reason. Arithmetic on it
   proves nothing, which is the problem the next slide solves.
3. **Where the numbers live.** The fix for arithmetic on names: every token
   gets three comparable numbers per window position, and here they all are,
   with the two fetched rows lit. Name each row an **embedding** here, at
   first sight — the room has heard the word sold, and a row of numbers is
   all it is. A context window of two means two tables. `COMMODORE` holds a
   different row in each, which is the whole of what positional means. 174
   of the model's 290 parameters are these tables.
4. **Why three?** The question the tables plant, answered before the room
   asks it. One number puts a word on a line; three put it in a space. Then
   the cost of each width, and the admission that **six would have fitted**.
   Three is a decision, not a limit. Hold that for block 9.
5. **What a parameter is.** `2 x 29 x 3` plus `29 x 3` plus `29` is 290,
   counted out. Then the definition: one number training is allowed to change.
   Then GPT-3's 175 billion, without editorial.
6. **One step.** Predict, then correct. The three numbers are looked up and
   added, not calculated. AMIGA gets 3.5%, barely better than 1 in 29. Then
   the nudge, number by number, inside a box labelled with the token that owns
   it. The sign of every change is the sign of its incoming number. Three
   things set the size and the slide names each: a learning rate of 1/16 that
   we chose (four shift instructions on the 6809), how wrong it was, and how
   much that weight contributed. The middle term is self-correcting, so the
   nudges shrink as the model improves without anyone turning them down.
   AMIGA moves to 3.7%. Almost nothing, and there are 1,160 steps in a run.
7. **Do it again. And again.** The strongest slide in the block. Three
   failures, three colours, and they go away in order. Orange is repeating a
   token: 41% of draws at epoch 0, 9% at epoch 5, 1% at epoch 20. Red is
   lifted from the corpus. What is left at epoch 20 is the argument:
   *different* tokens that sit together plausibly, `SINCLAIR AMIGA`,
   `COMMODORE ATARI`, neither of which existed. The machine has no idea what
   those words mean; it knows which tokens follow which, and that alone is
   enough — and when a big model does it with facts the industry calls it
   **hallucination**, so hand the room that word here, where the mechanism is
   on screen. Epoch 60's recitation gets its industry name too:
   **overfitting**. Then the trap: epoch 0 is 100% new and 0% the right
   shape. New is easy. If asked why not train longer for more recognizable names, the answer
   is on screen: right shape is already 98% at epoch 20 and saturates at 13.
   Longer training buys recitation, not recognizability.
8. **What it cost.** 2,516 bytes run the finished model; another 730 buys
   having learned it, and every one of those is dead weight afterwards. Same
   division of labour EXP-006 and EXP-007 exploit by training on the Mac, and
   the same one behind every model the room has used: somebody paid for the
   training, once, somewhere else. Then the memory and the 4K comparison.

**No runtime claim anywhere in this block.** The three-minute target has a
cycle-model projection behind it and no hardware measurement, and the slides
say so.

### 3. How it works, on the machine

**On screen:** EXP-004 in XRoar, then three assembly reveals while it trains,
then back to XRoar.

Five slides, nine minutes, and the structure exists to solve a problem: the
training run takes minutes and nobody should narrate a progress counter for
that long. So the run starts, and the talk cuts to the code that is executing
while it executes.

| Slide | Sec | What happens |
| --- | ---: | --- |
| Watch it learn | 120 | Reset, seed 6809, read the nonsense out, start training |
| One signed multiply from two unsigned | 90 | The optimisation that made this possible |
| And the correction that makes it signed | 60 | Optional depth, first to drop |
| Why one subtraction is enough | 50 | The unsigned error, and where it lives |
| The learning rate, in eight instructions | 40 | Callback: the 1/16 from block 2, physically |
| Divide by two, four times over | 50 | The same eight instructions, acting on the bits |
| Back to the machine | 180 | The pause, the audience's choice, the comparison |

The three code slides are the deck's only assembly, and they are extracted
from the source that assembles by `tools/extract_code_excerpts.py` rather than
retyped, so a later change to the model cannot leave a slide quietly lying.
Highlights are matched by instruction, not line number, for the same reason.
The tool enforces the journey's five-to-twelve-line limit and refuses to emit
an excerpt outside it.

The best beat is the middle one, and it is a human point rather than a
technical one: the first version multiplied a bit at a time and needed 38.6
million instructions. This version needs 15.8 million and produces
bit-for-bit identical output. The learning algorithm did not change. Somebody
understood both the mathematics and the machine. The tests are what made
changing it safe.

Two of those six slides show bits rather than mnemonics, and they are the
ones that make the code mean something.

**Why one subtraction is enough.** MUL takes unsigned bytes, so -121 arrives
as 135, which is exactly 256 too big, and the product is too big by 256 times
the multiplier. In the low sixteen bits, 256 times anything is that thing
moved into the high byte, so the entire error is the multiplier's low byte
sitting one byte up. Point at the two bit rows: **the low bytes are
identical.** Only the high half moved. That is the proof, and it is on the
screen rather than in the narration. Say clearly that these are worked
numbers, chosen inside EXP-004's measured product range, not a captured
training step.

**Divide by two, four times over** is where the code stops being a
screenshot. It takes a real weight update out of training, SINCLAIR's third
weight at epoch 5, and shows the eight instructions moving its bits:
-6344, -3172, -1586, -793, -397, with the bits that fall off the right in red.

Say the convention before relying on it: **two's complement, a leading 1 means
negative.** Do not assume the room knows, and do not ask them to watch a bit
whose meaning has not been given.

Then make the connection back two slides, because it is the same idea twice.
These sixteen bits read as **59,192** taken unsigned and **-6344** taken
signed. Nothing in the bits says which. **The instruction you choose decides.**
That is exactly why `MUL` needed a correction: `MUL` reads unsigned, so it read
-121 as 135. `ASRA` reads signed, so it preserves the top bit. `LSRA` would put
a 0 there instead and -6344 would become 29,596.

Then two things to point at, in order. The left edge: the sign bit copies
itself downward one more each step, which is what "arithmetic" shift means.
Then the middle: bits cross the gap between A and B, which is the whole reason
there are two different instructions rather than two `ASR`s.

The value is chosen for being legible, and the exporter searches for one:
negative, with bits set in both bytes. A gradient whose high byte is all zeros
teaches nothing. It comes from `FixedTokenLanguageModel`, the integer
reference the 6809 matches bit for bit, whose `gradient >> 4` is literally
these eight instructions.

On the measured pace, training reaches `PRESS ANY KEY` during the first or
second code slide, and that is fine: the machine parks there harmlessly, and
the pause belongs to the audience anyway. Walk the code at its own speed. If
the room is restless, drop the sign correction — that is what it is there
for — and come back sooner.

**This block's length is no longer the plan's largest open risk.** Measured
under the emulator, launch to the training boundary is one to two minutes,
so the nine minutes hold the launch, the code slides, the comparison, and
room to breathe. What hardware timing would add is a printable number, not a
planning one. See "Open decisions".

If training does not improve, say so and inspect the evidence with the room.
A previously recorded run may be shown as a labelled comparison and never as a
substitute.

### 4. Change one thing: the prompt

**On screen:** the held-fixed line and four asks, then EXP-005 in XRoar.

The slide teaches; the machine proves it. Read the controls out loud first:
all 380 numbers, the same checksum before and after, the same seed, the same
greedy decoding. Nothing about the model differs between the four answers.

| asked | it said |
| --- | --- |
| nothing | WHY BUY JUST A VIDEO GAME |
| I ADORE | MY 64 |
| ARE YOU | KEEPING UP IN LITTLE COMPUTERS |
| THE COMPUTER | FOR THE REST OF US |

The definition to land: **a prompt is not training. It is the first few tokens
of the answer, handed over before the machine starts.** People conflate the two
constantly, and this is the cheapest place in the talk to separate them.

Then go to the machine and let someone choose a prompt live, so it is not
just a table on a slide. The strongest live reveal is `ARE YOU` becoming
`KEEPING UP IN LITTLE COMPUTERS`: it blended two campaigns into something
plausible without understanding either.

If temperature comes up: greedy decoding is temperature zero, which is why a
repeated prompt repeats its answer. The d20 at the exhibit table is the
temperature dial, made of plastic.

### 5. Change one thing: the context

**On screen:** the same held-and-changed shape, then EXP-011 in XRoar.

Held: model 751B with its weights locked, the same question asked again word
for word, seven of the eight context records untouched. Changed: one record,
`LISA = CODE 2` to `LISA = CODE 6`. The answer moves with it.

Say what that means against the previous block. There we changed the prompt
and the model stayed put; here we changed a stored fact and the model stayed
put. **Two different things a person can change, and neither of them is the
weights.**

Then the machine, so the room watches a person type the digit rather than
reading that someone did. `BEFORE`, `AFTER`, and `MODEL 751B DID NOT CHANGE`
are on the CoCo's own screen.

The line to land:

> Training changes the weights. Prompting changes the context. Attention uses
> the context to produce this answer.

Then name the omission: this is key-value attention, not a transformer. We
isolated one mechanism so it could be watched. Worth one breath after it:
system prompts, retrieval (RAG), and memory features are all this same move —
a fact placed in context, weights untouched — and attention will use a wrong
fact just as faithfully. The score replay (`V`) is optional depth and is not
in the budget.

### 6. A screen of things that never existed

**On screen:** EXP-012, the fake episode titles, one keystroke, sixteen of them.

The lesson is the split, and it is visible in the sizes: 400 bytes of model
holding the shape of a title, against 1,600 bytes of dictionary and rules
holding the words. The model never learned what a Gothos is. It learned that
something goes there.

Say the corpus number, because it reframes the whole demo: across all 79 real
titles, only two adjacent word pairs ever repeat. There was nothing to
generalize from. It memorized a shape.

One callback earns its sentence: this is hallucination as a product. Asked
for facts, these screens would be errors; asked for invention, they are the
deliverable. Which one you get was a decision about the task.

Note the second scenario cost. This is the one place the talk leaves the
vintage-computer example, so get in and out.

### 7. Change one thing: the upbringing

**On screen:** EXP-003, the fan-corpus bias runs, as five stacked bars.

Each bar is where the first generated token came from over 20 draws. The
segments label themselves, so there is no legend and nobody has to hold a
colour mapping in their head.

The first three are one collection each, with the architecture, starting
numbers, training budget, vocabulary and sampling seeds all held. Each model
comes out a fan of whoever raised it: 16 of 20, 15 of 20, 14 of 20.

The last two are the reason the slide exists. **They train on the same 54
names.** Balanced, eighteen from each maker. The only difference is whether
the three collections were laid end to end or shuffled together.

Concatenated, it comes out a Tandy fan at 14 of 20, indistinguishable from the
model that only ever saw Tandy machines. Tandy went last, and last is what
stuck. Interleaved, the same data spreads: 10, 6, 3.

Land it plainly. Nobody chose to make that fourth model a Tandy fan. Nobody
wrote a preference into it. Somebody decided how to lay the files out, that
was the decision, and they almost certainly did not know they were making it.

Worth one more beat if there is time: concatenated ends at loss 2.18 and
interleaved at 0.88. The bad ordering trained worse as well as more narrowly.

Ask which human decision produced each row. Do not answer it.

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

1. ~~How long does EXP-004, the live training run, actually take?~~ Settled
   at emulator confidence (2026-08-29): trapped at `wait_for_key` under
   `-ratelimit`, launch to `PRESS ANY KEY` took 49 seconds windowed and 96
   headless, bracketing the 75-second cycle projection. Recorded in EXP-004,
   the live training run's, experiment notes. What remains is the hardware
   number, which is the printable one and the exhibit-copy gate, not a
   planning input.
2. **Does the abstract still describe the talk?** It promises invented computer
   names and 1980s marketing phrases. Blocks 5, 6 and 8 are none of those
   things, and block 8 is the strongest beat in the set. Either the abstract
   is restated or blocks 5 and 8 are shrunk to honour it. Now more pressing
   than when this was written: block 2 grew to eight slides and the talk's
   centre of gravity has moved from *watch it train* to *here is exactly how
   it works, and here is it training*.
3. **Is any of it legible from the back row?** Two things to check, not one.
   XRoar's 32 by 16 screen scaled onto a conference projector, where no stage
   target passes a scaling or geometry flag. And the deck's own figures: the
   lookup tables run at 0.4em and the epoch rows carry three percentage
   columns. Both were designed on a laptop.
4. **Is the audience volunteer in block 8 planned or found?** A planted player
   is faster and reads as a plant. A real one is slower and carries the point.
5. **Is there a handout?** One page, one QR code to the repository, and the
   three stores from blocks 4, 5 and 7 named on it. Cheap, and it is what
   people take home. It is also where the table number goes.

## What has to be built

In dependency order. The launcher and rehearsal-note gaps that blocked
rehearsing half the talk are closed; what remains is legibility, the two
missing figures, and the physical-world items.

1. ~~Stage launchers for EXP-012 (fake titles) and EXP-013 (game opponent).~~
   Done: `make present` now lists and launches both.
2. ~~Rehearsal notes for blocks 6 and 8.~~ Done: `demo-rehearsal-notes.md`
   covers EXP-012, the fake titles, and EXP-013, the game opponent.
3. **A projector legibility check** for XRoar and for the deck, and whatever
   scaling flags the stage targets turn out to need. See open decision 3.
4. **Slides for blocks 1 and 9**, the two still without a figure. Block 7,
   the bias comparison, now carries the five stacked bars.
5. **The photograph in block 1**, of the physical machine, from a genuine run.
6. **The handout**, if decision 5 says yes.
7. **A table plan** revising `table-exercises.md` for two surfaces and two
   physical machines.

## Deck state

Sixteen slides, exactly 40 minutes. Eight figures, all generated:

```sh
uv run python tools/export_deck_traces.py      # run the model, write the numbers
uv run python tools/measure_train_vs_infer.py  # classify the image by job
uv run python tools/make_deck_figures.py       # draw them, splice them in
```

Blocks 1 and 9 are the two with no figure yet; block 7 now carries the bias
bars. Blocks 3, 4, 5, 6 and 8 run in XRoar and their slides are cues, each
cue slide's speaker notes naming the `make present` command or window switch
it needs.
