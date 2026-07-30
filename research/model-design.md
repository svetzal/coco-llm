# Model design

## Status

The current token-level candidate is supported by a floating-point reference
run. Fixed-point training and physical CoCo 1 timing remain unproven.

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

The first implementation should target a 32K CoCo 1 unless physical-hardware
inventory establishes a different minimum. A smaller-memory build is a later
optimization, not an initial constraint.

## Open questions

1. Can fixed-point training reach comparable quality without fragile tuning?
2. What is the measured signed multiply-accumulate cost on the 6809?
3. Does a full run complete within three minutes at the CoCo 1 clock rate?
4. Is approximate cross-entropy useful to display, or is correct-token
   probability a clearer live measure?
5. Does a three-value context retain enough resolution after quantization?
6. Can the vocabulary and corpus be made more inclusive without losing the
   performance budget?
