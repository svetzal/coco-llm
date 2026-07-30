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

Introduce tokens, context, logits, probabilities, and sampling only as the live
example needs them.

### Where does learning happen?

Reveal the expected token. Compare it with the prediction.

```text
CONTEXT:   <END> COMMODORE
EXPECTED:  AMIGA
PREDICTED: PET
```

Walk one example slowly:

```text
predict → compare → send error backward → adjust numbers
```

Then run the optimized training loop.

The model does not receive a grammar lesson. It repeatedly discovers which
small numerical changes make the next prediction less wrong.

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
6. Explain embeddings and backpropagation while epochs run.
7. Sample after each epoch.
8. Stop at the predeclared quality or time boundary.
9. Test the model outside its competence.
10. Reveal the final model size, memory use, and elapsed time.

Failure is part of the demonstration. If the model does not improve, inspect
the evidence with the audience and use a previously recorded run only as a
clearly labelled comparison.

## Presentation stance

The emotional movement is:

```text
mystery → mechanism → delight → limitation → agency
```

Do not argue that language models are harmless or that no job will change.
Demonstrate something more durable: the mechanism is understandable, its
limitations are observable, and people can make intentional choices about
where it belongs.
