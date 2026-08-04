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
