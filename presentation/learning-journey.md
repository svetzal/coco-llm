# Learning journey

## Working promise

In this session, a 45-year-old computer will begin with random numbers and learn
to invent plausible vintage-computer names. We will watch every important part
of that happen.

The audience should leave able to explain:

1. what a token is;
2. what a language model predicts;
3. what training changes;
4. why fluent output is not the same as understanding;
5. why limited models can still be extraordinarily useful;
6. where human purpose, judgement, and accountability remain essential.

## Sustained example

The model sees names such as:

```text
COMMODORE AMIGA
TANDY COLOR COMPUTER
APPLE LISA
ATARI MEGA ST
ACORN ARCHIMEDES
SINCLAIR ZX SPECTRUM
```

After training, it may invent names such as:

```text
COMMODORE COLOR ST
TANDY SPECTRA 80
ACORN AMIGA II
```

The exact output must always come from a real run. Illustrative names should be
labelled as examples until the implementation generates its own.

## Question-driven progression

### Can a 45-year-old computer learn?

Fair warning: we are going to use the phrase "language model" generously and
the word "large" recklessly.

Show the CoCo 1, its processor, clock rate, available memory, and blank model.
Generate from random weights. The machine emits nonsense.

The first reveal: the model contains no words, rules, facts, or vintage-computer
database. It begins as numbers.

### What does a language model actually do?

Turn a name into tokens:

```text
COMMODORE AMIGA → COMMODORE | AMIGA | <END>
```

Then give the model one token:

```text
COMMODORE → ?
```

Ask the audience what might come next: `AMIGA`, `64`, `PET`, perhaps something
unexpected. Their guesses are a probability distribution derived from
experience. The model's job is the same narrow task: assign scores to possible
next tokens.

The words are less mysterious when attached to this one example:

- a **token** is one item the model can read or predict, such as `COMMODORE`;
- the **context** is the two tokens it can currently see;
- a **parameter** is one adjustable number that influences its predictions;
- a **logit** is merely a raw scoreboard value for one possible next token.

Do not ask the audience to memorize the vocabulary. Keep returning to the
computer-name example until the terms become convenient shorthand.

### How does a scoreboard become a probability?

Suppose the model gives three possible next tokens these raw scores:

| Token | Raw score |
| --- | ---: |
| `AMIGA` | 3 |
| `64` | 2 |
| `PET` | 1 |

Those are logits. A score of 3 does not mean 3%, three votes, or three units of
confidence. The scores do not yet have a human-friendly scale.

**Softmax turns the scoreboard into shares of 100%.** For these illustrative
scores, the result is approximately:

| Token | Softmax probability |
| --- | ---: |
| `AMIGA` | 67% |
| `64` | 24% |
| `PET` | 9% |

Softmax preserves the ordering, makes every share positive, and makes all the
shares add to 100%. It also emphasizes the lead: a modest score advantage can
become a much clearer probability advantage.

Why call it “soft” max? A hard maximum would give the winner everything and
discard every alternative. Softmax lets the strongest choice lead while the
other choices remain possible.

Here is the precision-versus-accuracy moment: these numbers are a
**distribution over the model's available choices**, not a measurement of
truth and not proof that the model understands Commodore. Softmax does not
choose a token either. Sampling can draw from the distribution; greedy
inference can take the largest share.

The CoCo calculates an integer approximation using a small lookup table and
fixed-point arithmetic. It is doing the same conceptual job without floating
point or the full exponential function.

If the room wants the formula, reveal it only after the intuition:

```text
probability(token) = exp(score(token)) / sum(exp(every score))
```

Read that aloud as: make every score a positive weight, then divide each weight
by the total. The formula should confirm the story, not become an entrance exam.

### Where does learning happen?

Reveal the expected token. Compare it with the prediction.

```text
CONTEXT:   <END> COMMODORE
EXPECTED:  AMIGA
PREDICTED: PET
```

Call the shot first: which numbers should move? The model gave too much
probability to `PET` and too little to `AMIGA`.

Now name the complete training step:

```text
forward pass → softmax → compare → backpropagate → update
```

Show the same path in both directions:

```text
PREDICT: context → embeddings → scores → probabilities
LEARN:   expected answer → error → output weights → embeddings
```

Walk it slowly:

1. The **forward pass** uses the current parameters to produce raw scores.
2. **Softmax** turns those scores into next-token probabilities.
3. Comparison with the known answer produces a numerical error.
4. **Backpropagation** works backward through the calculation to determine how
   much each contributing parameter was responsible for that error.
5. The update nudges each parameter a small distance in the direction that
   would have made `AMIGA` more likely.

Backpropagation does not mean “the computer thinks about why it was wrong.” It
is bookkeeping with multiplication and addition. We know the expected answer
because the training example supplied it; backpropagation follows the same
connections backward and distributes correction signals.

Keep one distinction explicit: **backpropagation calculates which direction
and how much; the update step changes the parameters.** People often use
“backprop” casually for the whole learning process, but the separation helps
make the mechanism visible.

Repeat that process for every example. One complete trip through the training
examples is an **epoch**. Then run the optimized training loop.

On the live CoCo screen, the epoch and actual example occupy separate rows:

```text
EPOCH 03 / 20
# ACORN > ARCHIMEDES
```

The full-width example row shows both context tokens and the expected target.
It is overwritten for every update, becoming a rapid visual trace of the
evidence currently changing the model. Pause on one example when explaining
the loop, then let the complete corpus flow past. The title is left-aligned in
green on a dark bar. Context tokens are black on green, while the expected
token is green on a dark field. `#` is the visible boundary token.

After the keypress, twelve rows make the same distinction explicit:

```text
# # > COMMODORE 128 #
# # > TANDY COMPUTER #
```

The seed is black-on-green. Every token selected by inference, including the
ending `#`, is green-on-dark. A final-column `+` honestly marks an output that
is wider than the screen rather than allowing it to corrupt the following row.

The model does not receive a grammar lesson. It repeatedly discovers which
small numerical changes make the next prediction less wrong.

### What actually changes when we change the lesson?

Put the EXP-004 and EXP-005 assembly drivers beside each other. Both say:
initialize the screen, initialize the same model machinery, train, verify, then
hand control to the demonstration. That is the boring part—and boring is good.

The interesting lines name the human choices. EXP-004 uses the narrow multiply
its measured values permit, starts from `# #`, prevents an immediate ending,
and samples a gallery. EXP-005 needs the wider multiply, accepts the audience's
two-word context, permits an immediate ending, and greedily picks the strongest
continuation.

So what made the second model behave differently? Not a mysterious new
intelligence hidden in the engine. We changed the vocabulary, examples,
numerical range, prompt, and selection policy. Call your shot: which one of
those choices do you expect to matter next?

### How do we make that finish before everyone goes home?

The first correct assembly version multiplies a signed 8-bit value by a signed
16-bit value one bit at a time. It is easy to explain and exactly matches the
reference model. It also makes the complete run execute about 38.6 million
instructions.

The 6809 has a fast `MUL` instruction, but it multiplies two **unsigned** bytes.
Can we use it without changing the mathematics?

Split the 16-bit operand into high and low bytes:

```text
low product  = 8-bit value × low byte
high product = 8-bit value × high byte, shifted left by eight
```

Two `MUL` instructions form the low 16 bits. If the 8-bit value is negative,
its unsigned representation is 256 too large, so subtract the multiplier's low
byte from the result's high byte. The measured products all fit in a signed
16-bit result.

The complete model remains bit-for-bit identical. The optimized engine executes
about 15.8 million instructions before the per-example display is added, and
about 16.4 million with the full live display and named experiment-policy
calls. Its stock-clock projection remains about 75 seconds.

This is a useful engineering reveal: the learning algorithm did not change.
The representation of the arithmetic changed because a person understood both
the mathematics and the machine. Correctness tests let us optimize aggressively
without quietly changing what the model learns.

### Can we train it to have a favourite?

Use the same blank model five times. Keep its architecture, initial numbers,
training budget, vocabulary, and generation seeds fixed.

Change only the training examples:

```text
APPLE FAN
COMMODORE FAN
TANDY FAN
```

Ask the audience to call the result before each run. Then generate twenty names
and count their first tokens.

The Apple model begins sixteen names with `APPLE`. The Commodore model begins
fifteen with `COMMODORE`. The Tandy model begins fourteen with `TANDY`.

The model has no brand loyalty. But the training process absolutely has a point
of view. Think about that a minute.

Now combine equal sets of Apple, Commodore, and Tandy examples. Surely that
fixes it?

Not if we concatenate them. Online training sees the Tandy block last in every
epoch, and fourteen of twenty generated names still begin with `TANDY`.

Interleave the exact same examples and train again. The output now includes all
three manufacturers, and loss falls much further.

The reveal is not merely "biased data makes a biased model." Representation,
repetition, order, initialization, and sampling all participate in the observed
result. Including everyone in the input does not guarantee balance in the
output.

Ask: who selected the data, chose the order, defined success, and decided the
result was acceptable? Those are human decisions hiding behind model
behaviour.

### What are embeddings and layers doing?

Return to the same `COMMODORE` example. Show its three learned values in each
context position, the summed context vector, and the output scores.

The numbers are useful because of relationships learned during training, not
because any individual number has a human-readable definition.

Ask: where is the concept of Commodore stored? It is not in one parameter. In
this tiny model, even the appearance of a concept may be our interpretation of
learned token relationships.

### Is this how modern LLMs work?

Yes at the level of the central task:

- tokenize context;
- predict the next token;
- measure error;
- adjust parameters;
- generate by repeating predictions.

No at the level of architecture and scale. This model has a fixed, two-token
window and a small additive network. Modern generative models normally use
transformer attention, much larger vocabularies, longer contexts, extensive
training data, and vastly more parameters and computation.

The CoCo model is a working cross-section, not a miniature claim to ChatGPT.

### Does it understand vintage computers?

Generate plausible names.

Then ask it questions, request a reliable fact, or point out that it cannot know
whether an invented machine ever existed.

The model can learn that `AMIGA` plausibly follows `COMMODORE` without knowing
that either was a product or company. Think about that a minute.

Plausibility is the product. Truth requires another system: sources, tools,
tests, or a person who understands the stakes.

### If it is so limited, why is it useful?

Return to the task it was actually trained to perform. Within that boundary it
can generate useful, surprising candidates cheaply.

Modern language models apply the same predictive machinery at a scale where
many useful behaviours emerge. Their breadth makes it easy to mistake
plausibility for general competence.

The practical move is to give a model:

- a bounded job;
- relevant context;
- a way to check the result.

Call your shot, take your shot, inspect what happened. Is that an opportunity?

### Is it going to replace me?

The honest answer is more useful than either reassurance or panic.

Language models can replace or accelerate portions of work. They do not bring
their own purpose, care about consequences, accept accountability, recognize
all the context they are missing, or decide which outcomes matter.

The CoCo can invent a computer name. A person chose the problem, assembled the
examples, designed the model, judged the output, and decided what the
demonstration meant.

The durable human skill is not typing every token personally. It is framing
problems, supplying context, noticing what is missing, evaluating consequences,
and taking responsibility for the result.

### What should we try next?

Close by returning to the random output from the beginning and comparing it
with the final generated names.

Invite people to:

- alter the training corpus and predict what will change;
- choose a fan corpus, then try to identify the trained model from its output;
- compare concatenated and interleaved versions of the same examples;
- inspect the assembly and fixed-point arithmetic;
- try a deliberately bad or biased corpus;
- add a bounded language-model task of their own;
- question every claim the model and presenter make.

Learning starts by admitting what we do not yet understand. That is true for
the model, and it is true for us.

## Live-demo spine

The talk should have one genuine run, not a sequence of canned simulations:

1. Reset deterministic random weights.
2. Generate visible nonsense.
3. Inspect one next-token prediction.
4. Train that example one step at a time.
5. Start the optimized loop.
6. Reveal how two unsigned `MUL` operations replaced the slow signed routine.
7. Walk one training step—scores, softmax, error, backpropagation, update—while
   the epochs run.
8. Reach the predeclared training boundary and pause at `PRESS ANY KEY`.
9. Let the audience choose when to begin inference.
10. Fill the screen with twelve deterministic inference samples.
11. Compare the controlled Apple-, Commodore-, and Tandy-fan models.
12. Reveal the ordering effect in concatenated versus interleaved balanced data.
13. Ask which human choices created each observed behaviour.
14. Test the model outside its competence.
15. Reveal the final model size, memory use, and elapsed time.

The main model must train genuinely during the talk. Depending on the measured
hardware runtime, the five controlled bias runs may be retrained live or loaded
from deterministic checkpoints. In either case, disclose which work is
happening live and let the audience verify that architecture, initial weights,
training budget, vocabulary, and sampling seeds are held constant.

Failure is part of the demonstration. If the model does not improve, inspect
the evidence with the audience and use a previously recorded run only as a
clearly labelled comparison.

## Conversation-driven branches

The runnable presentation experiments begin with the first complete 6809
training loop. Run `make present` to see the choices, then follow the room:

- “But does the CoCo actually train?” — `make present EXP=4`
- “Can my starting words steer it?” — `make present EXP=5`

EXP-004 is the hardware centerpiece and controls its own pause before
inference. Do not cue it from the cycle-model runtime projection; rehearse and
measure the actual presentation hardware.

EXP-005 begins from `I ADORE` rather than `# #`, then reveals `MY 64` as the
model's completion. Ask the room to call the next words before showing the
result. The strongest second reveal is `ARE YOU` becoming `KEEPING UP IN LITTLE
COMPUTERS`: the model blends two campaigns into something plausible. It can
predict the shape without understanding either advertisement. Think about that
a minute.

EXP-005 trains and performs all six prompted completions in 6809 assembly.
After the training pause, let someone choose with the CoCo arrow keys and press
Enter. Each result remains visible and the selector advances, which makes it
easy to follow the room rather than commit to a scripted order. Its physical
stock-rate runtime still needs direct measurement. EXP-001 through EXP-003
remain engineering evidence rather than entries in the stage menu.

## Presentation stance

The emotional movement is:

```text
mystery → mechanism → delight → limitation → agency
```

Do not argue that language models are harmless or that no job will change.
Demonstrate something more durable: the mechanism is understandable, its
limitations are observable, and people can make intentional choices about
where it belongs.
