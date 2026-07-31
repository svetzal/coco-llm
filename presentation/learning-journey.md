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

## Assembly reveal discipline

The 6809 source is evidence, not decoration. For every major concept:

1. explain the idea using the sustained computer-name example;
2. reveal roughly five to twelve executable lines of the actual assembly;
3. return immediately to the visible behaviour on the CoCo.

Use large, retyped code rather than screenshots of an editor. Label every
excerpt with its source file and routine. Highlight only the two or three lines
currently being discussed. Presentation comments may be added for clarity, but
mark omitted source with `...` and never imply that pseudocode is executing.
When the final deck tooling supports source imports, pull excerpts directly
from these files so later assembly changes cannot silently make the slides lie.

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

Fair warning: we are going to use the phrase "language model" generously and
the word "large" recklessly.

### What does the CoCo think a word is?

Before asking whether the machine can learn `COMMODORE AMIGA`, ask a more basic
question: where do the letters go?

They do not go into the model. Our tokenizer looks up each word in a fixed
29-entry vocabulary and replaces it with a one-byte token value. Start with
just three entries:

```text
$00 = <END>
$07 = AMIGA
$0D = COMMODORE
```

Then reveal the complete EXP-004 vocabulary. The hexadecimal values are the
actual bytes used by the 6809:

| Value | Token | Value | Token | Value | Token |
| ---: | --- | ---: | --- | ---: | --- |
| `$00` | `<END>` | `$0A` | `ATARI` | `$14` | `PET` |
| `$01` | `100` | `$0B` | `BBC` | `$15` | `SINCLAIR` |
| `$02` | `128` | `$0C` | `COLOR` | `$16` | `SPECTRUM` |
| `$03` | `400` | `$0D` | `COMMODORE` | `$17` | `ST` |
| `$04` | `64` | `$0E` | `COMPUTER` | `$18` | `TANDY` |
| `$05` | `800` | `$0F` | `II` | `$19` | `TRS-80` |
| `$06` | `ACORN` | `$10` | `LISA` | `$1A` | `ZX` |
| `$07` | `AMIGA` | `$11` | `MACINTOSH` | `$1B` | `ZX80` |
| `$08` | `APPLE` | `$12` | `MICRO` | `$1C` | `ZX81` |
| `$09` | `ARCHIMEDES` | `$13` | `MODEL` | &nbsp; | &nbsp; |

Then show how the CoCo turns the token value in `A` into the address of its
display text. The pointer table contains two-byte addresses, so `MUL` doubles
the token value:

```asm
; screen.asm — print_token_id_text
print_token_id_text
        ldb     #2
        mul                     ; D = token value * 2
        ldu     #token_pointers
        leau    d,u
        ldu     ,u              ; U = address of token text
        lbsr    print_black_on_green
        rts
```

That is the whole bridge from `$0D` to the characters in `COMMODORE`: use the
number as an index, fetch a pointer, print the bytes found there. No meaning is
decoded.

So the name becomes:

```text
COMMODORE  AMIGA  <END>
   $0D      $07     $00
```

The numbers do not contain the meanings of the words. `$0D` means
`COMMODORE` only because our vocabulary table says it does. Renumber every
token consistently and the model can learn the same relationships.

Our model sees two token values and learns to predict the third. One name
therefore becomes three training examples:

```text
# #           > COMMODORE     $00 $00 > $0D
# COMMODORE   > AMIGA         $00 $0D > $07
COMMODORE AMIGA > #           $0D $07 > $00
```

The visible `#` is our compact CoCo-screen representation of `<END>`. At the
beginning it means “nothing came before this name”; at the end it means “the
name is finished.”

Be explicit about the simplification. Modern language models usually tokenize
text into a much larger vocabulary of word pieces, punctuation, and other
fragments. This experiment uses whole words because its domain is deliberately
tiny. The essential handoff is the same: text outside the model becomes token
numbers inside the model.

This also reveals a limitation before discussing intelligence: the CoCo cannot
even represent a word that is absent from these 29 entries. Tokenization is a
human design decision about which distinctions the model is able to see.

### Can a 45-year-old computer learn?

Show the CoCo 1, its processor, clock rate, available memory, and blank model.
Generate from random weights. The machine emits nonsense.

The first reveal: the model contains no words, rules, facts, or vintage-computer
database. It begins as numbers.

The initialization loop makes that literal:

```asm
; model_core.asm — initialize_model
initialize_model
        ldd     #6809           ; deterministic random seed
        std     rng_state
        ldx     #position_embeddings
initialize_random_parameter
        lbsr    xorshift16
        anda    #$03
        subd    #$0200
        std     ,x++            ; store one random parameter
        cmpx    #output_biases
        blo     initialize_random_parameter
        ...                     ; bias initialization follows
```

Ask: where did `COMMODORE` appear in that code? It did not. We initialized
adjustable numbers, not a database.

### What does a language model actually do?

Now give the model two token values:

```text
# COMMODORE → ?
$00 $0D   → ?
```

Ask the audience what might come next: `AMIGA`, `64`, `PET`, perhaps something
unexpected. Their guesses are a probability distribution derived from
experience. The model's job is the same narrow task: assign scores to possible
next tokens.

The forward pass begins by looking up the learned values for those two token
numbers in two positional embedding tables:

```asm
; model_core.asm — forward
        lda     current_context
        ldx     #position_embeddings
        lbsr    add_embedding

        lda     current_context+1
        ldx     #position_embeddings+POS_BYTES
        lbsr    add_embedding
        ...                     ; calculate scores and softmax
```

The same token can influence a prediction differently in the first and second
positions because each position has its own table. The token identifies a row;
training changes the three numbers stored in that row.

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

Show that compromise in the actual softmax loop. It measures the distance from
the winning score, scales it with three right shifts, and looks up an
exponential approximation:

```asm
; model_core.asm — make_exponential
        ldd     maximum_logit
        subd    ,x              ; distance below best score
        lsra
        rorb
        lsra
        rorb
        lsra
        rorb                    ; divide distance by 8
        ...                     ; clamp distance to table range
        ldx     #exp_lut
        abx
        lda     ,x              ; approximate exponential
```

The 6809's hardware multiply then turns that weight into a fixed-point
probability:

```asm
; model_core.asm — make_probability
        lda     ,x+             ; exponential weight
        ldb     reciprocal      ; approximately 256 / total
        mul
        addd    #$0080          ; round
        tfr     a,b
        clra
        std     ,u++            ; rounded probability share
        ...
```

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

Then reveal that the assembly reads in almost exactly that order:

```asm
; training.asm — train_example
train_example
        lbsr    forward
        ...
        subd    #256            ; expected token: probability - 100%
        std     ,x
        lbsr    calculate_context_error
        lbsr    update_output_parameters
        lbsr    update_embeddings
        rts
```

There is no instruction named `BACKPROP`. The idea emerges from ordinary loads,
multiplies, additions, and subtractions arranged to carry the error backward.

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

Even that visual distinction is two tiny 6809 operations:

```asm
; screen.asm — VDG character rendering
        anda    #$3f            ; green character on dark
        sta     ,x+

        ora     #$40            ; black character on green
        sta     ,x+
```

The colour convention is not a slide simulation. The program writes different
VDG character codes so the audience can distinguish supplied context from the
model's prediction.

After the keypress, twelve rows make the same distinction explicit:

```text
# # > COMMODORE 128 #
# # > TANDY COMPUTER #
```

The seed is black-on-green. Every token selected by inference, including the
ending `#`, is green-on-dark. A final-column `+` honestly marks an output that
is wider than the screen rather than allowing it to corrupt the following row.

Now reveal the shared inference loop:

```asm
; inference.asm — generation_token
generation_token
        lbsr    forward
        lbsr    experiment_adjust_probabilities
        lbsr    experiment_choose_token
        lbsr    print_chosen_token
        ...
        lda     current_context+1
        sta     current_context
        lda     chosen_token
        sta     current_context+1
        dec     generation_remaining
        bne     generation_token
```

Training and generation call the same `forward`. What changes is what happens
after the probabilities appear: training sends error backward; inference
chooses a token and feeds it into the next context.

The model does not receive a grammar lesson. It repeatedly discovers which
small numerical changes make the next prediction less wrong.

### What actually changes when we change the lesson?

Put the EXP-004 and EXP-005 assembly drivers beside each other. Both say:
initialize the screen, initialize the same model machinery, train, verify, then
hand control to the demonstration. That is the boring part—and boring is good.

```asm
; Both experiment drivers begin this way
start
        lds     #$7f00
        lbsr    initialize_training_screen
        lbsr    initialize_model
        lbsr    train_model
        lbsr    finish_training
        ...                     ; gallery or prompt workbench
```

The interesting lines name the human choices. EXP-004 uses the narrow multiply
its measured values permit, starts from `# #`, prevents an immediate ending,
and samples a gallery. EXP-005 needs the wider multiply, accepts the audience's
two-word context, permits an immediate ending, and greedily picks the strongest
continuation.

Then put the genuinely different policies beside each other:

```asm
; experiment_004.asm
experiment_multiply_training_context
        lda     1,x
        ldx     probability_pointer
        lbra    multiply_s8_s16

experiment_choose_token
        lbra    choose_sampled_token
```

```asm
; experiment_005.asm
experiment_multiply_training_context
        ldd     ,x
        ldx     probability_pointer
        lbra    multiply_s16_s16

experiment_choose_token
        lbra    choose_greedy_token
```

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

Now show the optimization rather than merely describing it:

```asm
; model_core.asm — multiply_s8_s16
        sta     multiply_factor
        ldb     1,x
        mul                     ; factor * low byte
        std     multiply_product

        lda     multiply_factor
        ldb     ,x
        mul                     ; factor * high byte
        addb    multiply_product
        stb     multiply_product
```

Follow with the signed correction as a second reveal:

```asm
        tst     multiply_factor
        bpl     multiply_ready
        lda     multiply_product
        suba    1,x             ; correct negative factor
        sta     multiply_product
multiply_ready
        ldd     multiply_product
```

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

The assembly contains no fairness concept and no shuffle. It walks the examples
in exactly the order we supplied:

```asm
; training.asm — epoch_loop / example_loop
        ldu     #training_examples
        lda     #EXAMPLE_COUNT
        sta     examples_remaining
example_loop
        lda     ,u+
        sta     current_context
        lda     ,u+
        sta     current_context+1
        lda     ,u+
        sta     current_target
        ...                     ; train this example and repeat
```

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

Then connect that diagram to the lookup code. Each token owns three two-byte
embedding parameters, so multiplying its token value by six selects its row:

```asm
; model_core.asm — add_embedding
add_embedding
        ldb     #6              ; 3 values * 2 bytes
        mul
        leax    d,x             ; X = this token's row
        ldu     #context_vector
        lda     #EMBED_DIMS
        sta     dimensions_remaining
        ...
```

The dimension loop adds those learned values into the shared context vector:

```asm
add_embedding_dimension
        lda     ,x
        tfr     a,b
        sex
        addd    ,u
        std     ,u
        leax    2,x
        leau    2,u
        ...                     ; repeat for all three dimensions
```

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

1. Reveal EXP-004's 29 token values and encode `COMMODORE AMIGA`.
2. Turn that name into its three sliding two-token training examples.
3. Reset deterministic random weights.
4. Generate visible nonsense.
5. Inspect one next-token prediction.
6. Train that example one step at a time.
7. Start the optimized loop.
8. Reveal how two unsigned `MUL` operations replaced the slow signed routine.
9. Walk one training step—scores, softmax, error, backpropagation, update—while
   the epochs run.
10. Reach the predeclared training boundary and pause at `PRESS ANY KEY`.
11. Let the audience choose when to begin inference.
12. Fill the screen with twelve deterministic inference samples.
13. Compare the controlled Apple-, Commodore-, and Tandy-fan models.
14. Reveal the ordering effect in concatenated versus interleaved balanced
    data.
15. Ask which human choices created each observed behaviour.
16. Test the model outside its competence.
17. Reveal the final model size, memory use, and elapsed time.

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

EXP-006 is the planned practical-use branch: “What if we train on a modern
machine, spend 8 KiB on weights, and let the CoCo complete what you type?” It
creates a strong contrast without disguising where the work happened:

1. EXP-004 genuinely trains a 290-parameter model on the CoCo.
2. EXP-005 shows that starting words steer the same kind of model.
3. EXP-006 explicitly loads 8,188 parameters trained on the Mac.
4. The audience types a phrase and Tab asks the old machine to predict its next
   word.
5. Familiar completions demonstrate bounded usefulness; unfamiliar input
   demonstrates the fixed vocabulary and lack of understanding.

The optimized assembly supplies another teachable code reveal:

```asm
        lda     ,x+            ; signed Q4.4 output weight
        ldb     ,u+            ; signed context value
        lbsr    multiply_s8_s8 ; one native MUL plus sign correction
        addd    accumulator
```

Then reveal what is absent: inference ranks logits directly. Softmax is needed
to turn scores into probabilities for training and sampling, but it cannot
change which score is largest.

The first workbench now fits the complete interaction on the CoCo's 32×16
screen. Typed text is black-on-green. Prediction opens a compact green-on-dark
popover at the text cursor, sized to its widest candidate and shifted away from
the right or bottom edge when necessary. Dismissing it restores the covered
screen bytes. Right Arrow serves as the original keyboard's Tab-equivalent: it
predicts, then accepts. Up and Down choose; Enter also accepts; Left erases;
Clear restarts. The last row identifies the 178-word vocabulary and four-word
context. The presenter must state before launching it that the Mac trained the
weights and the CoCo is performing inference; the practical improvement must
not obscure where training happened.

This branch is not yet in `make present`. Its frozen experiment saved 58.8% of
held-out word keystrokes and passed quantization and XRoar interaction parity,
but missed its 70% top-three target at 59.3%. Add it only after physical
keyboard behaviour and stock-rate latency are verified and the quality
decision is explicit. The failed stretch criterion is useful presentation
material in its own right: we declared success before looking, then let
evidence constrain the claim.

## Presentation stance

The emotional movement is:

```text
mystery → mechanism → delight → limitation → agency
```

Do not argue that language models are harmless or that no job will change.
Demonstrate something more durable: the mechanism is understandable, its
limitations are observable, and people can make intentional choices about
where it belongs.
