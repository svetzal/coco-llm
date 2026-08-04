# Demonstration rehearsal notes

These notes are glanceable cues rather than a script. Keep the demonstration
in the foreground, ask the audience to call the result before revealing it,
and treat surprising output as evidence rather than something to defend.

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

> That looks like retrieval. For this prompt it has reconstructed the familiar
> continuation. But it is not looking up an advertisement. The two words
> changed the scores, and greedy inference repeatedly chose the strongest next
> token.

### Second prompt: `ARE YOU`

Ask the room to predict the continuation, then press Enter to reveal
`KEEPING UP IN LITTLE COMPUTERS`.

> That was not one advertising campaign. It begins with Commodore's “Are you
> keeping up” and ends inside Radio Shack's world of “little computers.”
>
> The model learned reusable statistical structure strongly enough to blend
> the campaigns. It did not learn their history or understand either company.

### Teaching point

> The prompt is not a magic instruction channel. It is temporary state. Same
> weights, different context, different scores, different completion.

Two prompts establish the lesson. Use `POWER WITHOUT` → `THE PRICE` as an
optional third result or let the room explore the remaining prompts. Running
all six risks turning the lesson into a memory trick.

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

### Orient to the workbench

Right Arrow is the original CoCo keyboard's Tab-equivalent. It predicts when
the popover is closed and accepts the selected word when it is open. Up and
Down choose, Enter also accepts, Left erases, and Clear resets the editor.

> Black on green is what we type. Green on dark is what the model proposes.
> The text and position carry those roles too; colour is reinforcement.

### First phrase: prefix completion

Type `PRESS TAB TO C`, then press Right Arrow. The `C` masks suggestions that
do not match the prefix, leaving `COMPLETE` as the intended result. Press Right
Arrow again to accept it.

> The model predicted a complete word, but the editor also did ordinary useful
> work: it filtered the vocabulary using the `C` we supplied. Not every useful
> behaviour in an AI interface needs to be attributed to the model.
>
> We typed one letter and accepted the remaining seven. That is the task we
> are testing—not whether the CoCo can hold a conversation.

### Second phrase: ranked alternatives

Press Clear, type `THE COMMODORE`, and press Right Arrow. The frozen test vector
ranks `64`, `VIC`, and `AMIGA` as its top three suggestions.

> One context, three plausible continuations. The model is ranking words, not
> retrieving one required answer. Up and Down expose that distribution as a
> choice for the person.

Accept one suggestion if useful, then stop. The interaction is the lesson;
filling the editor adds little.

### The failed call

> We called our shot before training: the intended held-out word should appear
> in the top three at least 70 percent of the time. We got 59.3 percent. The
> hypothesis failed.
>
> Why show it? Because the same prototype saved 58.8 percent of held-out word
> keystrokes and beat both simple baselines. Failed experiment, useful bounded
> prototype. Those can both be true.

Do not describe 58.8 percent as a measured physical typing improvement. It is
an offline held-out keystroke simulation; physical keyboard latency and
behaviour remain unverified.

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
