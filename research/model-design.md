# Candidate model design

## Status

This is the first candidate to test, not a frozen architecture.

## Learning task

Given the previous three characters, predict the next character. Training
examples come from a short list of real vintage-computer names. Generation
begins with a short seed and repeatedly samples the next character from the
model's output distribution.

The generated result should become visibly less random during a live training
run. It should eventually resemble the corpus without merely replaying it.

## Candidate architecture

| Component | Shape | Parameters |
| --- | ---: | ---: |
| Character embeddings | 40 × 3 | 120 |
| Hidden weights | 9 × 6 | 54 |
| Hidden biases | 6 | 6 |
| Output weights | 6 × 40 | 240 |
| Output biases | 40 | 40 |
| **Total** | — | **460** |

The forward pass is:

```text
three character tokens
        ↓
three learned embeddings
        ↓
nine fixed-point values
        ↓
six hidden activations
        ↓
forty next-character logits
        ↓
softmax and sampling
```

The first nonlinearity candidate is ReLU or a symmetric hard clamp. The output
uses an approximate softmax so that the training objective remains recognizable
as next-token cross-entropy.

## Why this architecture

An even smaller trainable bigram table would demonstrate prediction and gradient
descent, but it would barely exercise the 6809 multiplier and would omit learned
representations and hidden layers.

A transformer would add attention projections, another normalization step, and
a substantially more complex backward pass. That complexity does not initially
buy enough teaching value or output quality to justify the implementation risk.

This model keeps:

- tokenization;
- embeddings;
- matrix multiplication;
- nonlinear layers;
- logits and probabilities;
- a next-token loss;
- backpropagation;
- parameter updates;
- autoregressive generation.

It omits attention and uses a fixed context window. That boundary must remain
visible in the presentation.

## Fixed-point direction

The initial reference implementation should use ordinary floating-point
arithmetic only long enough to establish whether the architecture can learn the
corpus. It should then move to a fully specified integer implementation.

The first fixed-point candidate is:

- signed 8-bit operands for hot multiply-accumulate loops;
- signed 16-bit master parameters so small updates survive quantization;
- signed 16-bit accumulators where range analysis permits;
- explicit saturation rather than accidental wraparound;
- a power-of-two learning rate;
- online stochastic gradient descent with no optimizer state;
- table-driven exponential and logarithm approximations;
- deterministic pseudo-random initialization and sampling.

The 6809 `MUL` instruction is unsigned. Signed multiplication will require an
exact wrapper or a representation that makes sign correction inexpensive.
Cycle counts and overflow bounds must be measured rather than assumed.

## Memory budget

The candidate model requires 920 bytes for 16-bit master parameters. Runtime
memory must also include:

- compact forward operands or cached high bytes;
- activation and error buffers;
- a 500–800 character corpus;
- lookup tables;
- screen memory and platform state;
- code and stack.

The first implementation should target a 32K CoCo 1 unless physical-hardware
inventory establishes a different minimum. A smaller-memory build is a later
optimization, not an initial constraint.

## Open questions

1. Does the 460-parameter model generate recognizably computer-like names?
2. How many examples and epochs are required?
3. Can fixed-point training reach comparable quality without fragile tuning?
4. What is the measured signed multiply-accumulate cost on the 6809?
5. Does a full run complete within three minutes at the CoCo 1 clock rate?
6. Is approximate cross-entropy useful to display, or is correct-token
   probability a clearer live measure?
7. Does the model need a four-character context or eight hidden units?
