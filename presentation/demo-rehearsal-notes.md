# Demonstration rehearsal notes

These notes are glanceable cues rather than a script. Keep the demonstration
in the foreground. Ask the audience to call the result before you reveal it.
Treat surprising output as evidence, not something to defend.

## EXP-004: the CoCo learns

### Question

Can this 45-year-old machine actually train a model?

### Before launch

> This is a real run. The CoCo initializes random weights, works through 58
> examples twenty times, and updates the model itself. No Mac-trained weights
> are involved.
>
> Before training, expect nonsense. Afterwards, we will hold generation seed
> 6809 still and change only the weights.

### During training

Point to the example row: two context tokens, then the expected next token.

> The model predicts. We measure how wrong it was. Backpropagation calculates
> the correction; the update changes the weights. One trip through every
> example is an epoch.

### At `PRESS ANY KEY`

> What are we holding fixed? Generation seed 6809. What changed? The model's
> weights. Call your shot: should the two outputs look the same?

### On the comparison screen

Point to the same seed, random weights, and learned weights in that order.

> Well, clearly we haven't threatened OpenAI's market position.
>
> But what actually changed? Before training, it rambles. After training, nine
> of these eleven attempts produce two tokens and stop.
>
> Did it learn that the Lisa belongs to Apple? Nope. It learned the shape
> “manufacturer, model, stop” more strongly than it learned the relationships.
>
> Training succeeded. Intelligence did not suddenly emerge. Those are
> different claims.

The laugh is the teaching moment: plausible structure is not knowledge, and
technical success is not the same as useful quality.

### Transition

> Training changes the weights. Once the weights are fixed, can we steer the
> result without training again? Is the starting context an opportunity?

## EXP-005: prompting steers completion

### EXP-005 question

If the weights stop changing, what can the starting context change?

`SAME MODEL` means the same EXP-005 weights across all six prompts, not the same
weights or vocabulary used by EXP-004.

### Before EXP-005 launch

> We are giving the same learning machinery a more coherent little corpus:
> fragments from real 1980s computer advertising.
>
> This model trains on the CoCo too. Once it reaches the prompt screen,
> training is over. We will choose among six prepared prompts; the audience
> changes the context and the model supplies what comes next.

### During EXP-005 training

> Same learning process as before. Different examples, a slightly larger
> vocabulary, and eighty epochs. The interesting part begins when the weights
> stop moving.

### At EXP-005 `PRESS ANY KEY`

> Right now the model is trained. From here on, we will not update a single
> weight. Watch the title: `SAME MODEL - CHANGE THE PROMPT`.
>
> What can cause a different answer now? Only the two words we place into
> context.

### First prompt: `I ADORE`

> Fair warning, this one will divide the room by age. Anybody want to call the
> next words?

Press Enter to reveal `MY 64`.

> That's Commodore's own jingle — "I Adore My 64" ran on radio and
> television. It looks like retrieval. For this prompt it has reconstructed
> the familiar continuation. But it is not looking up an advertisement. The
> two words changed the scores, and greedy inference repeatedly chose the
> strongest next token.

### Second prompt: `ARE YOU`

Ask the room to predict the continuation, then press Enter to reveal
`KEEPING UP IN LITTLE COMPUTERS`.

> That was not one advertising campaign. It begins with Commodore's “Are You
> Keeping Up with the Commodore” and ends inside Radio Shack's “The Biggest
> Name in Little Computers.”
>
> The model learned reusable statistical structure strongly enough to blend
> the campaigns. It did not learn their history or understand either company.

### Teaching point

> The prompt is not a magic instruction channel. It is temporary state. Same
> weights, different context, different scores, different completion.

If temperature comes up: greedy decoding is temperature zero — always the
top-scoring token, which is why the same prompt repeats its answer exactly.
Turning temperature up means sometimes taking a lower scorer. The d20 on the
table is that dial, made of plastic.

Two prompts establish the lesson. Use `POWER WITHOUT` → `THE PRICE` — Atari's
ST-era slogan — as an optional third result, or let the room explore the
remaining prompts: `WHY BUY` → `JUST A VIDEO GAME` is Commodore's Shatner-era
VIC-20 line, `THE COMPUTER` → `FOR THE REST OF US` is the 1984 Macintosh
launch, and `GET YOUR` → `START IN COLOR COMPUTING` sold Radio Shack's MC-10.
Running all six risks turning the lesson into a memory trick. Sources for
every line are cited in EXP-005, the prompted marketing completions.

### Transition to EXP-006

> So far, the CoCo has done the training itself. That's delightful—and
> spectacularly impractical. What if a modern machine trains a larger model,
> then hands the old machine only the weights needed to predict? Is that an
> opportunity?

## EXP-006: pretrained completion

### EXP-006 question

Can a model trained on the Mac save typing on a stock CoCo?

### Before EXP-006 launch

> This time there will be no epoch counter. The Mac has already trained 8,188
> one-byte parameters. The CoCo receives those frozen weights and ranks 178
> possible next words using four words of context.
>
> Point to the title when it appears: `MAC TRAINED - COCO PREDICTS`. We are not
> disguising where the expensive work happened.

Two industry words are sitting right here, so hand them over. Pretrained is
the P in GPT — somebody paid for the training once, somewhere else, and this
machine only does inference. And squeezing each trained weight into a single
byte, rounded and clipped, is quantization — the same trade that puts a
4-bit model on a phone, made for the same reason: the small machine has to
hold it.

### Orient to the workbench

Right Arrow is the original CoCo keyboard's Tab-equivalent:

- Right Arrow, popover closed: predict.
- Right Arrow, popover open: accept the selected word.
- Up and Down: choose a word. Enter also accepts.
- Left: erase. Clear: reset the editor.

> Black on green is what we type. Green on dark is what the model proposes.
> The text and position carry those roles too; colour is reinforcement.

### First phrase: prefix completion

Type `PRESS TAB TO C`. Press Right Arrow. The `C` masks suggestions that do
not match the prefix, so `COMPLETE` is the intended result. Press Right Arrow
again to accept it.

> The model predicted a complete word, but the editor also did ordinary useful
> work: it filtered the vocabulary using the `C` we supplied. Not every useful
> behaviour in an AI interface needs to be attributed to the model.
>
> We typed one letter and accepted the remaining seven. That is the task we
> are testing—not whether the CoCo can hold a conversation.

### Second phrase: ranked alternatives

Press Clear. Type `THE COMMODORE`. Press Right Arrow. The frozen test vector
ranks `64`, `VIC`, and `AMIGA` as its top three suggestions.

> One context, three plausible continuations. The model is ranking words, not
> retrieving one required answer. Up and Down expose that distribution as a
> choice for the person.

Accept one suggestion if it is useful, then stop. The interaction is the
lesson. Filling the editor adds little.

### The failed call

> We called our shot before training: the intended held-out word should appear
> in the top three at least 70 percent of the time. We got 59.3 percent. The
> hypothesis failed.
>
> Why show it? Because the same prototype saved 58.8 percent of held-out word
> keystrokes and beat both simple baselines. Failed experiment, useful bounded
> prototype. Those can both be true.

Do not describe 58.8 percent as a measured physical typing improvement. It
is an offline simulation on held-out text. Nobody has measured the physical
keyboard's latency or behaviour yet.

### Teaching point for EXP-006

> Inference does not require softmax here. Softmax changes scores into
> probabilities, but it cannot change their order. To choose the largest three,
> the CoCo can rank the raw integer scores.

Keep this arithmetic as optional depth. The primary lesson is the visible
division of work: modern training, vintage inference, bounded human utility.

### Transition to EXP-007

> We limited this model to 8 KiB and four words of context. What happens if we
> use the RAM normally hidden beneath the CoCo's ROM? More vocabulary, more
> context, and punctuation become possible. Bigger is not the same as smarter,
> so let's call another shot.

## EXP-007: all-RAM sentence completion

### EXP-007 question

What does four times the model memory buy us—and what does it not buy us?

### Before EXP-007 launch

> The Mac trained this model too. The CoCo receives 16,193 packed bytes,
> switches into its 64 KiB all-RAM map, and expands them into 32,385 working
> parameters underneath the address range normally occupied by BASIC ROM.
>
> This buys us all 255 token identifiers, five tokens of context, and real
> punctuation tokens. It does not make the machine understand sentences.

Point again to `MAC TRAINED - COCO PREDICTS`. The provenance stays fixed.
The memory layout and the inference task changed.

### First phrase: a larger context

Type `THE MODEL CAN`. Press Right Arrow. The frozen test vector ranks
`SUGGEST`, `BE`, and `REMEMBER`.

> We have a broader sentence corpus now, but this is still the same basic act:
> combine recent-token embeddings, score every possible next token, and let a
> person choose.

Accept `SUGGEST` only if it helps the flow. Do not build a long sentence merely
to show that the editor can hold one.

### Second phrase: punctuation and stopping

Press Clear. Type `RUN THE PROGRAM.` with the period attached normally.
Press Right Arrow. The top suggestion should be `<END>`, followed by `THEN`
and `?`. Accept `<END>`. The sentence stays unchanged and the status reads
`END OF PHRASE`.

> The period is a token in the five-token context. And `<END>` is the model
> saying, “This phrase should stop here.” It is not a character we need to add
> to the sentence.

### The interface failure

> Our first interface hid `<END>` because token zero also meant “no
> suggestion.” So when the model's first choice was “stop,” the screen showed
> the runner-up—often another punctuation mark.
>
> The model said “stop.” Our product said, “Pick something else,” and then made
> the model look foolish.
>
> We fixed the interface and did not retrain a single weight. Some apparent AI
> failures are product-policy failures. Think about that a minute.

This before-and-after is recorded evidence, not a reason to reproduce the
misleading UI during the live demonstration.

### The bigger-model call

> Four times as many parameters: did it become four times better? Top-three
> accuracy moved from 59.3 to 60.0 percent. Simulated keystroke savings fell
> from 58.8 to 51.7 percent.
>
> What did the memory buy? A broader 255-token vocabulary, another context
> position, punctuation, and a more expressive task. It did not buy a general
> quality improvement.
>
> Bigger can mean capable of attempting more—not reliably better at what it
> already did.

The current model still misses its declared 60 percent keystroke-savings gate.
Keep that rejection visible. Physical keyboard latency and behaviour also
remain unverified.

### Optional mechanism: RAM beneath ROM

> Loading directly above `$7FFF` in the normal map wraps into lower RAM and
> paints the screen with model bytes. So the CoCo loads packed nibbles below
> ROM, masks interrupts, enters the contiguous all-RAM map, and expands the
> model at `$8000-$FE80`.
>
> When it needs the BASIC keyboard routine, it briefly restores the ROM map,
> reads a key, and switches the model back into view. Vintage-computer memory
> management in service of a tiny language model. Because apparently this is
> how I relax.

Keep this as optional depth. The central lesson is that model capability,
quality metrics, and product policy are three different things.

### Transition to EXP-011

> These completion models can only use the last four or five token identifiers.
> What if I give the machine a fact right now, after training, and then change
> that fact in front of you? Can it use temporary context without changing its
> weights?

## EXP-011: edit context without training

### EXP-011 question

Can the CoCo use a fact supplied right now, then use a changed fact without
retraining?

### Before EXP-011 launch

> The 160 model bytes learned how to match a question with a context record.
> They did not learn Lisa's answer. These eight key-value records are temporary
> context in RAM, and their assignments can change every time.
>
> We are going to ask one question, edit one visible context value, and ask the
> same question again. Watch what changes—and what does not.

### Beat 1: read the current context

Point to these three elements before pressing anything:

1. `TEMPORARY CONTEXT IN RAM`;
2. `LISA = CODE 2`; and
3. `MODEL 751B WEIGHTS LOCKED`.

> This table is the information available for this interaction. It currently
> says Lisa is code two. Above it, model 751B's weights are locked.

Ask the room what answer it expects. Press Enter.

### Beat 2: answer from context

Point to `QUESTION: LISA`, the starred best match, `ANSWER: CODE 2`, and
`MODEL 751B DID NOT CHANGE`.

> Attention matched the question with the Lisa record and copied its value.
> The answer came from visible context. Nothing trained.
>
> What would it look like to change context rather than train the model?

Press `E`.

### Beat 3: edit the context

The editor shows `BEFORE: LISA = CODE 2` and asks for a new code.

> This is the missing action. I am changing information supplied to the model.
> I am not changing the model.

Type `6`. Pause on the confirmation screen and point in this order:

1. `BEFORE: LISA = CODE 2`;
2. `AFTER: LISA = CODE 6`; and
3. `MODEL 751B DID NOT CHANGE`.

> We can account for the change. I typed six. One byte in context RAM changed.
> The 160 model bytes did not.

Press Enter. The same `QUESTION: LISA` now produces `ANSWER: CODE 6`.

### Central line

> Training changes the weights. Prompting changes the context. Attention uses
> the context to produce this answer.

Pause. Do not dilute the comparison with mechanism immediately.

### Optional depth: replay the scores

Press `V` only if the room asks how the model selected Lisa. The slow view
reveals one stored score per Enter press and marks the best record so far.

> The answer arrived too quickly to watch. This is a replay of work already
> completed—not the processor pretending to think.
>
> Attention selected the Lisa record by its key, then copied the value we just
> typed.

Press Clear to return. Do not imply that inference needed the paced replay.

### Evidence and limit

> A parameter-only lookup scores about chance because Lisa's value changes
> between examples. An optimistic four-record window reaches 56 percent. This
> tiny attention head searches all eight records and recalled every novel
> binding in our two controlled test batches.
>
> But relevant is not the same as true. If I type the wrong value into context,
> attention will use it just as faithfully. Is that an opportunity? It is
> certainly a reason to care about what we put into context.

Call this content-addressed key-value attention, not a transformer. It has no
residual stream, normalization, feed-forward layer, or stack of causal
self-attention blocks. The isolated mechanism is the point.

Then the tie to what the room already uses, one breath: system prompts,
retrieval (the RAG in every vendor deck), and memory features are all this
same move — put a fact into context and leave the weights alone. The caution
transfers whole: type the wrong code and attention retrieves the wrong code
with total confidence. And the needle-in-a-haystack scores labs advertise are
this exact game, played against a phone book instead of eight records.

### Closing the demonstration sequence

> What did this old computer let us separate?
>
> Training changed weights. Prompts changed starting context. Pretrained
> inference used frozen weights. Attention selected temporary information. And
> none of those operations supplied understanding, truth, purpose, or judgment.
>
> Those parts still belong to us.

End on agency rather than on parameter count. The machine made the mechanisms
small enough to inspect; the audience's job is to carry that discernment back
to systems whose scale normally hides them.

### EXP-011 recovery

- If a key does nothing, click the XRoar window once. Try again.
- If Lisa is not selected, use Up or Down until the question says `LISA`.
- Clear cancels the editor or returns from an answer.
- After the edit, Enter asks again. Clear returns to the context table.

## EXP-012: fake episode titles

On stage this is block 6, the delight beat after the context edit. It is also
the first block to cut, so rehearse it tight: in and out in three minutes. At
the table it runs unattended in a loop all day.

### EXP-012 question

Can 400 bytes learn the shape of a title without learning a single word?

### Before EXP-012 launch

Launch with `make present EXP=12`. The screen fills with sixteen titles on
load. Any key deals another sixteen.

> This is the one place we leave the vintage computers for a few minutes. This
> model read the titles of every original Star Trek episode. All 79 of them.
> Every title on this screen is fake.

Deal one fresh screen in front of them, so the room watches the invention
happen rather than hears that it did.

### The split

On stage this is the "Where the trick lives" explainer slide. Advance to it
after dealing.

> Here's the thing. The model in there is 400 bytes, and it holds the shape
> of a title: THE-something-OF-something. The words live somewhere else, in
> 1,591 bytes of dictionary and rules that never learned anything. The model
> never learned what a Gothos is. It learned that something goes there.

### The corpus number

> Why so small? Because there was nothing to generalize from. Across all 79
> real titles, only two adjacent word pairs ever repeat. No phrase habits, no
> house style at the word level. A shape, and a bag of words. So that is what
> we built, and it is exactly as clever as it needs to be. Think about that a
> minute.

### Teaching point for EXP-012

> When output looks creative, ask what is holding the shape and what is
> holding the words. Here the split is two visible tables. In a large model
> the same split exists; you just can't point at it.
>
> And this is hallucination as a product. Ask this machinery for facts and
> every one of these screens is an error. Ask it for invention and they are
> the deliverable. Same machinery — which one you get was a decision a person
> made about the task.

### Transition to the bias slide (stage) or the table

> Everything so far came out of what the model read. So what happens when two
> models read different things? Or the same things, in a different order?

### EXP-012 recovery

- If a key deals nothing, click the XRoar window once. Press again.
- There is no failure state. Every screen is a fresh deal. If a title lands
  strangely, read it out — the misses teach the split as well as the hits.

## EXP-013: the game opponent that learns

On stage this is block 8, and it never gets cut. Someone from the room
plays. That is the point, so resist playing it yourself.

### EXP-013 question

Can 100 bytes learn the rules of a game, and the person across from it,
starting from nothing?

### Before EXP-013 launch

Launch with `make present EXP=13`. Keys are on screen: 1 ROCK, 2 SPOCK,
3 PAPER, 4 LIZARD, 5 SCISSORS. `R` makes it forget everything.

> Rock, paper, scissors, lizard, Spock. Five throws instead of three. And fair
> warning: the machine does not know the rules. I did not tell it what beats
> what. RULES 0 out of 25 — that is it admitting it.

### During play

A volunteer at the laptop works, and so does calling numbers from a seat.
The laptop keyboard is easier to drive, and the whole room can read the
screen.

> Watch the top line. IT EXPECTS — it calls its shot before every round. You
> get to watch a prediction get made, and then get judged, live. Call your
> shot, take your shot.

Play six or eight rounds. Point at the counters as they move: RULES filling
in as outcomes teach it what beats what, MEMORY saying how little it has on
the player.

> Around twenty-five rounds it will have the rules cold. It will never finish
> learning you.

Watch where RULES stops. Against a player with habits it stalls around seven
to thirteen of twenty-five, because the machine only ever learns a winning
answer to the moves you actually throw. Say that out loud: where the counter
stops is a readout of how varied the volunteer is, not of the machine.

### The reset

Press `R` in front of them, or better, have the volunteer press it. The
expectation line drops to `IT HAS NO IDEA YET` and both counters fall to
zero.

> Gone. Rules, habits, everything. That is the entire difference between this
> thing and an opponent someone programmed — what it knows, it learned from
> you, and one keystroke takes it all back.

If someone challenges it: a person who genuinely randomises cannot be beaten,
and say so rather than hope nobody tries. Reading the expectation line and
playing against it beats the machine too — that is not a flaw, it is what a
100-byte model of you deserves.

### The honest number

On stage this is "The honest number" explainer slide. Advance to it after
the reset beat.

> Against six synthetic players with habits, it scores 80%. We recorded a
> 200-round session against a person who was trying: 52.8%. It reads a person
> better than chance — three sigma better — and nowhere near well enough to
> win.
>
> Five of those six synthetic players had a habit. One did not. A person plays
> like the one that did not. Our test set encoded an assumption about people,
> and reporting the average hid it. Think about what your benchmarks are
> quietly assuming.

### Teaching point for EXP-013

> 100 bytes. Two tables. No neural network anywhere in there — we tried
> models, and a tiny table beat every one of them. Matching the machinery to
> the job is a decision a person makes, and "no model" was the right call
> here.

Invite whoever played to the table: the real machine will happily lose to
them again.

### EXP-013 recovery

- If a key does nothing, click the XRoar window once. Try again.
- Only 1-5 and R do anything. There is no way to wedge it.
- If the opponent starts winning heavily and the room deflates, press R.
  Let the volunteer watch it fall back to guessing. The recovery is a better
  lesson than the streak.
