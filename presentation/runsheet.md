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
| 1 | Watch it work | 2 | 1 | 1 | Slides + EXP-004 launched live | Mystery |
| 2 | How it works, on slides | 9 | 4 | 5 | Slides | Mechanism |
| 3 | A little 6809 assembly | 8 | 10 | 15 | EXP-004 live training | Mechanism |
| 4 | Change one thing: the prompt | 4 | 3 | 18 | CoCo, EXP-005 prompted completions | Mechanism |
| 5 | Change one thing: the size | 4 | 5 | 23 | CoCo, EXP-007 all-RAM completion | Mechanism |
| 6 | A screen of things that never existed | 3 | 3 | 26 | CoCo, EXP-012 fake titles | Delight |
| 7 | Change one thing: the training data | 2 | 4 | 30 | Slide, EXP-003 fan-corpus bias | Limitation |
| 8 | Now you play it | 2 | 5 | 35 | CoCo, EXP-013 game opponent | Agency |
| 9 | A token is a note | 4 | 4 | 39 | CoCo, EXP-010 melody continuation | Delight |
| 10 | Wrap up | 2 | 2 | 41 | Slide | Recap and coordinates |
| | Reserve, held for block 3 | | 1 | 42 | | |
| | Questions | | 7 | 49 | | |

**The music block books 3 minutes the 45 did not have.** The table above now
sums to 48. Something gives: three minutes out of questions, a minute each
from blocks 3, 5 and 8, or the music block itself if a rehearsal shows the
tune cannot earn its time. Decide at rehearsal, not on stage.

Blocks 2 and 3 were one block when this file was written. Building the figures
split them: eight slides now carry the explanation that used to be narrated
over the training run.

**Block 3 now holds 10 minutes and there is 1 more in reserve behind it.**
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
| Where do the numbers live? | 25 | The embedding tables, named at first sight; the same token holds a different row per position |
| Why three? | 30 | The cost of each embedding width, and that six would have fitted |
| What is a parameter? | 25 | 2x29x3 + 29x3 + 29 = 290, and the definition |
| One step | 40 | Predict, then correct, with the nudge number by number |
| Do it again. And again. | 40 | Repeating, inventing, reciting: three failures that go in order |
| What did it cost? | 20 | Time and memory, and what learning costs over using |

These are seconds, not minutes, and that is the measurement talking. Eight
figures that each carry one idea go faster than they look on paper. If the room
asks questions the block stretches, and that is what it is for.

Blocks 4 and 7 repeat one sentence deliberately: *we changed exactly one
thing*. That repetition is the spine of the talk, and block 5 carries the
sentence inside its evidence: the is-bigger-better question is answered by
a controlled pair where only the size moved. The prompt, the size, and the
training data are three different levers, and each one traces to a person
who set it. The store separation the spine used to carry — context is not
weights — now lives in block 4's held-fixed line and block 5's context
tie, and EXP-011, the context-editing attention head, demonstrates it
one-on-one at the table.

### Cut order

Announced here so it is a decision, not a panic.

1. **Block 6** goes first, the fake titles. It is the delight beat, and the
   table shows it all day on the real machine, one screen of sixteen until
   somebody presses a key.

   Inside block 2, the first slide to drop is **What did it cost?**, then **Why
   three?**. Both answer questions rather than advance the argument, and both
   have their evidence written up in EXP-002 for anyone who asks at the table.
   **Never drop "Do it again. And again."** It is where the talk's central
   claim is measured.
2. **Block 5's demo shortens to its slide** second. The size comparison is
   the lesson and it survives as one held-and-changed figure; the typing
   demo is the part that costs minutes, and EXP-007 runs all day at the
   table for anyone who wants their sentences finished.
3. **Block 3 shortens, it does not go.** The run already happened, launched
   at block 1 and trained behind block 2; what shortens is the code walk,
   starting with the sign correction. The comparison is the promise and it
   stays.
4. **Block 8 never goes.** It is the strongest lesson in the set and the only
   one an audience member performs.

### Changeover cost

Six of ten blocks load a different binary. On real hardware that is 20 to 30
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
- EXP-007, block 5 — parks at the completion editor, in the 64K all-RAM map.
- EXP-012, block 6 — parks showing titles.
- EXP-013, block 8 — parks at the RPSLS keys. Press `R` if anyone played it
  during setup.
- EXP-010, block 9 — parks at `YOU SEED - MODEL CONTINUES`, waiting for a
  figure. Nothing plays until Enter.

The windows look identical. Arrange them in block order. **EXP-004 is the
exception. It launches live, in front of the room, with `make block1` as
the talk opens**: it starts training the moment it loads, so the launch is
the reset, and it trains while block 2 explains it. Keep a terminal at the
repository root ready for that command; `make block3` relaunches a fresh
run if that window dies. Rehearse the switching, not only the demos.

Every block has a command, `make block1` through `make block10`. The
slide-only blocks print what the block is; each demo block's target prints
its keys and launches its emulator, which makes it the rehearsal path and
the relaunch for a window that dies mid-talk. Every launch **detaches from
the terminal**: the prompt comes straight back, and no Ctrl-C, closed
terminal window, or stray keystroke on the laptop can kill a running
emulator. Quitting one is done from XRoar itself, deliberately. The deck's speaker notes
carry the same cues, and every slide's notes open with a block marker —
`BLOCK 3 OF 10 - A LITTLE 6809 ASSEMBLY - SLIDE 2/7` — so the speaker view always
says where you are.

## The blocks

### 1. Watch it work

**On screen:** the block 1 launch, then a photograph of the CoCo 3
at the exhibit table with a screen of EXP-012's fake episode titles, full
screen, no explanation.

Open by launching the experiment the next block explains: `make block1`
opens the deck in the browser and starts EXP-004, the live training run,
in front of the room — the emulator launches second so it takes focus,
with the deck ready underneath. EXP-004 resets to random weights and
starts training the moment it loads. Call the shot out loud — seed 6809
draws nonsense from these random weights right now, and after 1,160
corrections the same seed will draw names — then switch to the deck and
press `S` for the speaker view. It trains, at the 1981 clock rate, while
block 2 explains exactly what it is doing.

Then the photograph. Read three titles. Say that none of them were ever
filmed, that the Mac trained this one, and that the CoCo 1 behind this
window, from 1981 with 32 kilobytes, started from random numbers a few
seconds ago. The Mac's part is said, not hidden.

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
   the cost of each width, with the first slide's choice priced as the
   callback: character tokens instead of word tokens would cost 12.8 million
   multiplies against a 180-second budget, and we built that one first and
   rejected it. Then the admission that **six would have fitted**. Three is
   a decision, not a limit. Hold that for block 10.
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
   failures, each named by its tag, and they go away in order. REPEATS: 41%
   of draws at epoch 0, 9% at epoch 5, 1% at epoch 20. IN THE CORPUS is
   lifted from the training data. What is left at epoch 20 is the argument:
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

### 3. A little 6809 assembly

**On screen:** the EXP-004 window that block 1 launched, now parked at the
training boundary, then three assembly reveals, then the comparison.

Eight slides, ten minutes. The run started in front of the room at block 1
and trained while block 2 explained it — measured at one to two minutes, it
is parked at `PRESS ANY KEY` by now. Nobody narrated a progress counter,
and nobody had to.

| Slide | Sec | What happens |
| --- | ---: | --- |
| Watch it learn | 120 | Return to the machine; say what ran: 58 examples, 20 epochs, 1,160 corrections |
| One signed multiply from two unsigned | 90 | The optimisation that made this possible |
| And the correction that makes it signed | 60 | Optional depth, first to drop |
| Why one subtraction is enough | 50 | The unsigned error, and where it lives |
| The learning rate, in eight instructions | 40 | Callback: the 1/16 from block 2, physically |
| Divide by two, four times over | 50 | The bits, then the landing: four halvings is the 0.0625 from One step |
| Back to the machine | 180 | The pause, the audience's choice, the comparison |
| How it picks the next token | 45 | The byte, the line of 256, the stretch it lands on: seed 6809's three draws, the name the room just saw |

The three code slides are the deck's only assembly, and they are extracted
from the source that assembles by `tools/extract_code_excerpts.py` rather than
retyped, so a later change to the model cannot leave a slide quietly lying.
Highlights are matched by instruction, not line number, for the same reason.
The tool enforces the journey's five-to-twelve-line limit and refuses to emit
an excerpt outside it.

Each code slide now carries a register column: the state after every
instruction, computed from the exported traces by `make_deck_figures.py`,
which refuses to splice if the excerpt's instructions drift from the walk.
The multiply and the shifts walk one captured update — SINCLAIR's weight at
epoch 5, context 26 times error -244, ending on the -6344 the shifts then
divide — and the sign correction walks the worked example its bit slide
draws. One training step, traced end to end across the block.

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

The machine waits at `PRESS ANY KEY` for as long as the code takes: the
pause belongs to the audience anyway. Walk the code at its own speed. If
the room is restless, drop the sign correction — that is what it is there
for.

**This block's length is no longer the plan's largest open risk.** Measured
under the emulator, launch to the training boundary is one to two minutes,
and the launch moved to block 1, so the nine minutes here hold only the
code slides, the comparison, and room to breathe. What hardware timing
would add is a printable number, not a planning one. See "Open decisions".

If training does not improve, say so and inspect the evidence with the room.
A previously recorded run may be shown as a labelled comparison and never as a
substitute.

### 4. Change one thing: the prompt

**On screen:** the second model's vocabulary, then the held-fixed line and
four asks, then EXP-005 in XRoar.

The block opens with "A second model", because the coming claim is only
airtight if the room knows what already changed. Same architecture, same
training loop, same machine, retrained on eight lines of 1980s advertising:
all 38 tokens on screen, with the five survivors from the first model
highlighted — 64, COLOR, COMMODORE, COMPUTER, and the boundary. The
callback does the teaching: COMMODORE was 13 in the first model and is 9
in this one, an alphabetical accident both times. The numbers line carries
the rest: 29 tokens to 38, 290 parameters to 380, 58 examples to 53, 20
epochs to 80. The machinery did not change. The reading material did.

Then "The same arithmetic, again": the parameter count and the training
bill, redone at 38 tokens in the exact shape of block 2's What a parameter
is and What it cost. The second exposure is the point — the room can now
do the arithmetic themselves, 2 x 38 x 3 plus 38 x 3 plus 38, and watch
the whole bill (1,450,080 multiplies, 4.8 times the first run; 760 bytes
of weights, up from 580) follow from exactly two decisions: the vocabulary
and the epochs. The 17.8 seconds is a MUL floor and is labelled one.

The vocabulary slide's last fragment names the elephant: eighty epochs on
eight lines is overfitting, and it is the assignment. Five of the six prompted
completions are corpus lines verbatim, exactly as EXP-005, the prompted
marketing completions, called its shot — five recognizable continuations,
at least one blend. Recitation was block 2's failure mode because that
model's job was inventing; this model's job is slogans the room
recognizes. Whether overfitting is a bug is a decision about the task,
and that lands in block 10's lap where it belongs.

Then the experiment. The slide teaches; the machine proves it. Read the
controls out loud first:
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

### 5. Change one thing: the size

**On screen:** the vocabulary budget, then the call and EXP-007 in XRoar,
then the held-and-changed size comparison.

The block opens with "One byte of vocabulary" — tokenizing, round three,
with a physical ceiling. A token identifier is one byte, so the whole
vocabulary caps at 255 seats: one for the boundary, six for punctuation
(each mark a token of its own, occupying a context position like any
word — which is how a model can learn that sentences stop), and 248 for
words, 71 more than EXP-006 had. `RUN THE PROGRAM.` tokenizes to four
tokens on screen, and the demo pays it off two slides later when the
period predicts the stop. The closing line is the first slide's, matured:
a token is what we chose.

The block promotes the practical branch to the stage. The call: a model
over a hundred times the size of the one that trained live will rank your
next word before you type it, on the same machine. The title on screen does
the framing: `MAC TRAINED - COCO PREDICTS` — the P in GPT, running. 16,193
packed bytes expand to 32,385 parameters into the RAM where BASIC's ROM
normally sits.

Three beats at the machine, rehearsed tight:

1. **The job.** Type `THE MODEL CAN`, predict, and it ranks `SUGGEST`,
   `BE`, `REMEMBER`. Accept one. This is the room's phone keyboard, in
   1981.
2. **The window.** `I KNOW THE OLD MODEL CAN` and `WE KNOW THE OLD MODEL
   CAN` produce the same suggestions, because the model sees exactly five
   tokens and the first word fell out of the window. When a long chat
   forgets its start, this is why, watched live.
3. **The stop.** `RUN THE PROGRAM.` predicts the end-of-phrase token — and
   the first interface hid it, showed the runner-up, and made the model
   look foolish. The interface was fixed; nothing retrained. Some apparent
   AI failures are product-policy failures.

Then the slide, "Eighty-five times bigger", anchored to the talk's own
flow: the last model the room met was block 4's 380-parameter marketing
model, and the rows step the advancement from it — parameters 380 to
32,385, vocabulary 38 to 255, window 2 tokens to 5, and training moved
off the machine entirely. Then the question the rows plant: is bigger
better? The answer is measured, cited as a controlled pair — an 8 KiB
completer built first against this 32 KiB one, same task, same held-out
sentences. Right word in the top three, 59.3% then 60.0%; typing saved,
58.8% down to 51.7%. Both called shots missed (70% top-three called,
59.3 got; a 60% typing-saved gate called, 51.7 got), and both misses
stay on the record. Both scores are offline simulations; the physical
keyboard is unmeasured, and the notes say so wherever the numbers
appear.

The context tie survives from the old block in one breath: everything
typed into the editor is context, the ranking moves with it, and nothing
retrains — system prompts, retrieval, and memory features are the same
move at scale. EXP-011, the context-editing attention head, demonstrates
that mechanism one-on-one at the table, where a patient visitor can watch
a fact change while the weights stay locked.

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

The block runs corpus, call, demo, explainer. The cue slide calls the
shot — 400 bytes that never learned a word are about to deal plausible
titles — the machine deals them, and the explainer slide "Improved With Simple
Rules" opens with a picture of the shape itself: BALANCE OF TERROR read from
the corpus, the names lifted out to leave ___ OF ___, and BALANCE OF BABEL
dealt back out of the gaps (both titles are real — the figure is derived from
the corpus file and the exported demo screen). Under it, the three-way split: 400 bytes of learned shape, 1,333 of
hand-written dictionary, and 258 of rules, with the rules laid out row by
row alongside the failure each one vetoes — the transition mask (else
TRISKELION THE MAN TRAP), the slot grammar (refuses A TRIBBLES and THE
GOTHOS), and the fingerprints that keep it from dealing a real title. The
landing: the model proposes, the rules dispose, the dictionary supplies —
and every veto is a decision a person wrote down.

Note the second scenario cost. This is the one place the talk leaves the
vintage-computer example, so get in and out.

### 7. Change one thing: the training data

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
model that only ever saw Tandy machines. (The thin slice in what the tandy fan
wrote is explained on the slide itself: one draw of twenty came out COMMODORE —
the bias is a lean, not a wall, the words were in the vocabulary.) Each row now
pairs two bars in the same maker colours — the training data, then the 20 names it
wrote by first word — so the training composition and the output composition
sit side by side: solid colour in, solid colour out; three blocks end to end
in, one colour out; fifty-four stripes in, a spread out. Tandy went last, and last is what
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

Then the explainer slide, "The honest number", which is the honest ending
and now lives on screen rather than only in narration:

> Against six synthetic players with habits it scores 80%. Against a recorded
> 200-round session with a person who was trying, it scores 52.8%. It reads a
> person better than chance, three sigma better, and nowhere near well enough
> to win.

That gap is the talk in one number. Five of those six synthetic players had a
habit and one did not, and a person plays like the one that did not. The test
set encoded an assumption about people, and reporting its average hid that.

100 bytes. No neural network. A tiny table beat every model we tried, which is
why there is no model here at all.

### 9. A token is a note

**On screen:** slides, then the CoCo composing and performing (EXP-010, the
melody continuation, performed by EXP-018, the steady sample clock, since
2026-09-06).

`make stage` parks the 6309 build at `YOU SEED - MODEL CONTINUES`; `make
block9` relaunches it. It waits for a figure: keys 1 to 7 enter scale degrees, `-`
holds, `.` rests, `0` erases, `M` flips major and minor, `S` steps the
speed, and Enter composes and then performs. Enter the eight-note figure
yourself, or hand the keys to the room. THINKING is the composer and takes a
moment; PLAYING is the tune. The corpus slide runs the recurring "What it
read" pattern one last time: 376 public-domain fiddle tunes from Ryan's
Mammoth Collection (1883), a token per sixteenth note, 313 read and 63 held
back. The explainer steps the same split as the fake titles - the seed a
person wrote, the melody the 3,044-byte model composes, the band that is
rules, and the compose-then-perform shape the four-voice player forces.

The stage build is the 6309 one: `make stage` parks it and `make block9`
relaunches it, a CoCo 3 in native mode at 11,188 Hz, which is the machine at
the table (the CoCo 1 has no video cable for this show, so it is not on the
booth). The staging rule above forbids a CoCo 3 in fast mode without saying
so: name it in one sentence at the switch, and the block's closing slide,
"The chip in the CoCo 3", then shows what that chip measured: EXP-014's rows,
the sign correction that MULD deletes, the registers that bought six percent
and were not built, and the two sample rates. The block opens on the book's
own 1883 title page, one beat, before the corpus slide. `make block9-coco1` is the CoCo 1 build at 4,566 Hz, the fallback; if
it is the one playing, say that instead. The steady-clock performer has been
heard on the CoCo 3 and preferred; on the CoCo 1 it has not been heard yet.

The landing sets up the close: the loop never knew it was doing words, and
what a token stands for was a person's decision.

### 10. Wrap up

**On screen:** slides.

Two slides. First the recap, one line per block, read at speed without
re-explaining any of them. It lands on the last line: someone chose the task,
the data, the budget, and what counts as good enough. Not "language models
are harmless" and not "no job will change." The durable claim is smaller: the
mechanism is understandable, the limitations are observable, and every one
of them traces back to a person who decided something.

Then the coordinates, left up for questions: the repository with every
experiment and this deck, email, and the web site.

Close on the table. Say what is running there and that you will be at it.

## What moves to the table

**Everything the hardware loads is staged by one command.** `make sdcard`
builds `build/sdcard/`: five RS-DOS disk images (the talk and table demos on
`COCOLLM.DSK`, then the hardware experiments EXP-014, EXP-015, EXP-017 and
EXP-018 on their own), the same files loose in a directory per disk for the
CoCo SDC's directory mounts, and a `MANIFEST.md` whose load addresses and
`PCLEAR`/`CLEAR` recipes are read out of the binaries rather than remembered.
`make sdcard-install DEST=/Volumes/COCO` copies it to the mounted card and
verifies every byte. `tools/make_sdcard.py` owns the list of disks.

**Where everything is.** One row per thing the talk or the signage promises
is at the table. The file names are the ones on `COCOLLM.DSK`; the manifest
beside the disks carries each one's load recipe, read from the binary. The
table's CoCo 1 is a 32K machine on a small television and the CoCo 3, with
a 6309 fitted, is on the Commodore 1703; the signage says so on its "Two
machines, one program" slide, so this layout has to match it.

| What | File | Machine | Leave it |
| --- | --- | --- | --- |
| EXP-004, the live training run | `LLM04` | CoCo 1 | Training, or on the comparison screen. It halts there; `RESET` then `EXEC &H2000` trains again from random weights without reloading (untested on hardware; if it does not, `LOADM` again). The signage says this machine "trains it live". |
| EXP-013, the game opponent that learns | `RPSLS` | either | At the keys, `R` pressed. "Come and beat it" is on the signage. |
| EXP-012, the fake episode titles | `TITLES` | either | Showing a screen. It does not redeal until a key is pressed, so an unattended machine shows one screen all day. |
| EXP-005, the prompted marketing completions | `LLM05` | either | At the prompt selector. The signage says "you type the first two words". |
| EXP-011, the context-editing attention head | `ATTN` | either | At the context table, Lisa selected. The signage's context slide is this demo. |
| EXP-006, the 8 KiB completion workbench | `LLM06` | either, 32K | At the editor. Table only; block 5's notes say it runs here all day. |
| EXP-007, the all-RAM sentence completer | `LLM07` | CoCo 3 only | At the editor. It needs 64K and the table's CoCo 1 has 32K. |
| EXP-010, the melody continuation | `MELODY`, `MELODY39` | `MELODY` either, `MELODY39` CoCo 3 | At `YOU SEED`. `MELODY39` is the one the CoCo 3 has been heard playing. |
| EXP-009, the four-voice synthesizer | `MUSIC` | either | Plays once and stops. |
| EXP-014, the 6309 multiplier benchmark | `BENCH309.DSK` | CoCo 3 | The signage's "How much faster is the 6309?" numbers came from this disk on 2026-09-05. Its session sheet is `experiments/EXP-014-hardware-session.md`. |
| EXP-015, EXP-017, EXP-018, the listening tests | `MUSIC015.DSK`, `WAVE017.DSK`, `STEADY18.DSK` | see each sheet | Not promised anywhere; on the card for anyone who asks what the CoCo 3 sounded like. |

Only two machines, so two of these run at once. When the presenter is on
stage: the CoCo 1 on `LLM04` (or `TITLES` once a run has finished, since
neither needs a hand) and the CoCo 3 on `RPSLS` with `R` pressed, which is
the one a visitor can play without instructions. Everything else is a
`LOADM` away when Stacey is back at the table.


The table is not the overflow bin, and since the talk projects an emulator it
now holds the only real hardware in the building. That is a promotion. It gets
the physical CoCo 1, plus everything that needs a keyboard, a patient visitor,
and more than ninety seconds, which is exactly the material a stage handles
badly.

| Item | Why it belongs there |
| --- | --- |
| The physical CoCo 1 | The claim the whole talk rests on. Powered on, all day, touchable. |
| EXP-006, the 8 KiB completion workbench | One person types for two minutes. Unwatchable from row 12. |
| EXP-007, the all-RAM sentence completer | Also on stage, rehearsed tight. On the table a visitor explores at their own pace, and the `<END>` interface-failure story gets a conversation. |
| EXP-011, the context-editing attention head | Needs a keyboard, a patient visitor, and more than ninety seconds — the table's own criterion. The fact-edit lands one-on-one. |
| EXP-013, the playable game opponent | Also on stage. On the table people play until it beats them. |
| EXP-012, the fake title generator | Shows sixteen titles until a key deals sixteen more. Good attractor, but it does not redeal on its own. |
| The four table exercises | Already designed against a 10-second to 15-minute ladder. |
| EXP-009 and EXP-010, the four-voice synthesizer and melody continuation | On stage as block 9 (`make block9`); at the table `MELODY39` on the CoCo 3 is the one that has been heard and preferred. |

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
4. **A slide for block 1**, the one still without a figure. Block 7,
   the bias comparison, carries the five stacked bars and block 9 carries
   its corpus slide and explainer.
5. **The photograph in block 1**, of the physical machine, from a genuine run.
6. **The handout**, if decision 5 says yes.
7. **A table plan** revising `table-exercises.md` for two surfaces and two
   physical machines.

## Deck state

Thirty-six content slides plus nine chapter cards. The speaker view's
total is the 36 minutes of content, and the per-slide timings sum to 42.5
minutes, which is the budget table's 39 plus the cards and a little air; the
music block's three minutes are still the open question above. Six of the
slides are one recurring slide, "The training data": each
model's training corpus quoted verbatim from its data file by the figure
tool, in one shared style — the 18 names, the 8 advertising lines, the
EXP-007 sentences, the real episode titles, and, plural for the first
time, block 7's three fan collections, where the motif pays off: by then
the room reads the slide before the title. Block 8 pointedly has none —
no corpus, no model, and that is its lesson. A card in the block's palette colour opens every block after the
first — number, title, arc word, ten seconds each — and its speaker notes
carry the spoken segue, so a section change is a hard colour cut rather
than another wall of text. The cards' eighty seconds ride the changeover
buffer the emulator staging recovered. Every slide wears the machine's
reversed title bar naming its block, with the block colour as a band
beneath it; the deck body is the machine's own black-on-green, flipped
from the old dark theme because projectors want a bright field. The demo blocks follow one
shape: the cue slide states **the call** — the block's falsifiable
hypothesis — the machine takes the shot, and blocks 6 and 8 close on an
explainer slide (the byte split; the honest number) so the lesson lands on
screen rather than only in narration. Blocks 4 and 5 fold the same shape
into their held-and-changed figures. The generated figures:

```sh
make deck-figures
```

Block 1 is the one with no figure yet; block 7 carries the bias bars and
block 9 its corpus and explainer. Blocks 3, 4, 5, 6, 8 and 9 run in XRoar
and their slides are cues, each cue slide's speaker notes naming the window
switch or `make` command it needs.
