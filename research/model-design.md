# Model design

## Status

The original token-level model is implemented in both an integer reference and
a bit-exact 6809 assembly training engine. All 580 final parameter bytes match
after 20 epochs. Two larger pretrained inference models are also implemented:
EXP-006 uses 8 KiB of weights, and EXP-007 uses the CoCo's all-RAM map for a
32 KiB working model. Emulator execution is proven across all three paths;
physical CoCo 1 timing remains unproven.

## Learning task

Given the previous two tokens, predict the next token. Tokens are complete
components from a deliberately small vocabulary of vintage-computer names:

```text
COMMODORE AMIGA → COMMODORE | AMIGA | <END>
TANDY MODEL 100 → TANDY | MODEL | 100 | <END>
```

This tokenizer is simpler than the subword tokenizers used by contemporary
language models, but it teaches the same essential distinction: the model
operates on token identifiers, not directly upon concepts or written prose.

## Candidate architecture

| Component | Shape | Parameters |
| --- | ---: | ---: |
| Position-dependent token embeddings | 2 × 29 × 3 | 174 |
| Output weights | 29 × 3 | 87 |
| Output biases | 29 | 29 |
| **Total** | — | **290** |

The forward pass is:

```text
two token identifiers
        ↓
two position-dependent embeddings
        ↓
add into a three-value context vector
        ↓
twenty-nine next-token logits
        ↓
softmax and sampling
```

The output uses an approximate softmax so the training objective remains
recognizable as next-token cross-entropy. The additive context representation
has no hidden activation function; the softmax supplies the model's
nonlinearity.

## Why this architecture

The original character-level MLP required 12,859,560 multiplications for twenty
epochs over its corpus. At eleven cycles for the bare 6809 `MUL` instruction,
those multiplies alone require roughly 159 seconds at 0.89 MHz. That leaves no
credible route to a complete three-minute training demonstration.

Tokenizing name components reduces the corpus from 729 character predictions to
58 token predictions. The new model performs 261 matrix multiplications per
example, or 302,760 across twenty epochs.

This model keeps:

- tokenization;
- position-dependent embeddings;
- matrix multiplication;
- logits and probabilities;
- a next-token loss;
- backpropagation;
- parameter updates;
- autoregressive generation.

It omits attention, hidden layers, and interaction terms between context
positions. Those boundaries must remain visible in the presentation.

A trainable token-to-token table would be even smaller, but would barely
exercise the multiplier and would omit learned representations. A transformer
would add attention projections, normalization, and a substantially more
complex backward pass without initially buying enough teaching value.

## Fixed-point direction

The initial reference implementation should use ordinary floating-point
arithmetic only long enough to establish whether the architecture can learn the
corpus. It should then move to a fully specified integer implementation.

The first fixed-point candidate is:

- signed 8-bit operands for hot multiply-accumulate loops;
- signed 16-bit master parameters so small updates survive quantization;
- signed 16-bit accumulators where range analysis permits;
- explicit saturation rather than accidental wraparound;
- a learning rate of 1/16 so parameter updates become shifts;
- online stochastic gradient descent with no optimizer state;
- table-driven exponential and logarithm approximations;
- deterministic pseudo-random initialization and sampling.

The 6809 `MUL` instruction is unsigned. Signed multiplication will require an
exact wrapper or a representation that makes sign correction inexpensive.
Cycle counts and overflow bounds must be measured rather than assumed.

## Memory budget

The candidate model requires 580 bytes for 16-bit master parameters. Runtime
memory must also include:

- compact forward operands or cached high bytes;
- activation and error buffers;
- 58 compact training examples;
- lookup tables;
- screen memory and platform state;
- code and stack.

The current writable image is 3,850 bytes at `$2000`, including code,
parameters, generated lookup data, verification data, and work buffers. It
comfortably targets a 32K CoCo 1. A smaller-memory build is a later
optimization, not an initial constraint.

## Pretrained inference direction

EXP-006 asks a different question from the live-training centerpiece: what
becomes practical if the CoCo spends 8 KiB on pretrained inference weights?

The first supported engineering candidate retains the additive architecture
but expands it to four tokens of context, 178 vocabulary entries, and nine
embedding dimensions. Mac training exports 8,188 signed Q4.4 parameters:

```text
four token identifiers
        ↓
four position-dependent embeddings
        ↓
add into a nine-byte context vector
        ↓
1,602 signed 8×8 products
        ↓
rank 178 next-word logits
```

No softmax is required for tab completion because it cannot change logit
ordering. This is a useful distinction for the presentation: softmax is
essential to normalized training probabilities and sampling, but not to
choosing the single largest score.

The complete image loads at `$6000` through `$7FFF`. The parameter bytes end at
`$7FFB`; four zero bytes pad the transport image. Vocabulary strings, editor
state, code, and stack remain below `$6000`.

On the frozen holdout, the Q4.4 model saves 58.8% of word-entry keystrokes but
reaches only 59.3% top-three accuracy, below the experiment's predeclared 70%
threshold. Its original quality hypothesis therefore failed. The direct 6809
simulator nevertheless proves the Mac and assembly rankings match, and the
complete UI is available as an explicitly labelled emulator demonstration.
Presenting the failed stretch target is part of the evidence rather than a
revised claim.

## All-RAM sentence-completion direction

EXP-007 fills the one-byte token identifier space and uses the CoCo 1's 64 KiB
all-RAM map. Its current architecture has five context positions, 255 tokens,
21 embedding dimensions, and 32,385 signed Q2.2 parameters:

```text
five token identifiers
        ↓
five position-dependent embeddings
        ↓
add into a twenty-one-byte context vector
        ↓
5,355 signed 8×8 products
        ↓
rank 255 next-token logits
```

The packed transport contains two signed nibbles per byte and occupies 16,193
bytes below `$8000`. Startup masks interrupts, selects the contiguous all-RAM
map, and expands 32,385 working bytes at `$8000-$FE80`. The keyboard adapter
briefly restores the ROM map around `POLCAT` without exposing the model to ROM
interrupt vectors.

The expanded corpus contains 423 training sentences and 61 disjoint holdout
sentences. At five epochs the deployed Q2.2 model reaches 39.5% top-one and
60.0% top-three accuracy, with 51.7% measured keystroke savings. It supports
word-prefix completion, punctuation tokens, and a visible `<END>` choice. The
Mac trains and exports; the 6809 performs fixed-point ranking and interaction.

## Contextual attention direction

EXP-011 adds the first mechanism whose answer can depend on a binding supplied
only in the current context. Eight key-value records change on every example,
so the answer cannot be memorized in the parameters. A learned query vector
scores the learned key vector in every record, and the value belonging to the
highest-scoring record is copied.

The selected head uses sixteen key tokens, five dimensions, and separate query
and key tables: 160 parameters in total. Across two data batches and ten seeds
it recalls 100% of 4,096 novel test bindings after signed Q4.4 quantization.
Inference needs 40 signed byte multiplications and a signed 16-bit score
accumulator.

The 6809 core now matches 96 reference scores across twelve novel contexts,
including every winning slot and copied value. Its 32-by-16 workbench keeps the
model identifier visible while cycling four temporary contexts and provides an
explicitly paced score replay. Real-ROM XRoar reaches the keyboard loop;
physical timing and keyboard behaviour remain unmeasured.

This is key-value attention, not a transformer. It deliberately omits causal
self-attention over a token stream, learned value projections, positional
encoding, residual connections, normalization, and a feed-forward layer. The
minimal form isolates content-addressed selection before any of those costs are
considered.

## Open questions

1. Does the approximately 72-second cycle-model projection hold on a physical
   CoCo 1?
2. Is approximate cross-entropy useful to display, or is correct-token
   probability a clearer live measure?
3. Is held-out top-three accuracy or measured keystroke savings the more honest
   success criterion for an interactive completion tool?
4. What are the loaded EXP-006 and EXP-007 models' suggestion latencies on a
   stock CoCo 1?
5. Does the CoCo 3 HDMI presentation path preserve keyboard and display
   behaviour?
6. What is EXP-011's measured query latency on a physical stock-rate CoCo 1?
7. After associative recall, which additional transformer mechanism would add
   enough learning value to justify its memory and arithmetic cost?
