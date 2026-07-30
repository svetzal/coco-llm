# EXP-001: Model feasibility

**Status:** planned

## Question

Can a 460-parameter, character-level neural language model learn a short corpus
of vintage-computer names well enough to create a compelling live
demonstration within the CoCo 1 performance envelope?

## Hypothesis

A model with a 40-character vocabulary, three-character context,
three-dimensional embeddings, and six hidden units can train from random
weights to recognizably corpus-shaped output in no more than three minutes on a
stock CoCo 1.

The fixed-point implementation will produce qualitatively similar samples to
the floating-point reference without pretrained weights.

## Variables

Test a deliberately small matrix:

| Variable | Candidates |
| --- | --- |
| Corpus size | 256, 512, and 768 characters |
| Context | 3 and 4 characters |
| Embedding width | 3 and 4 |
| Hidden width | 6 and 8 |
| Arithmetic | Floating point, then candidate fixed point |

Begin with the smallest candidate. Expand only when evidence shows that output
quality is insufficient.

## Procedure

1. Assemble and commit a fixed corpus of vintage-computer names.
2. Implement deterministic tokenization, initialization, training, and
   generation in the reference environment.
3. Record samples before training and after each epoch.
4. Record parameter count, peak memory, examples processed, and
   multiply-accumulates.
5. Define a fixed-point format and repeat with integer-only arithmetic.
6. Create deterministic intermediate test vectors for one forward pass and one
   training step.
7. Implement or model the critical 6809 kernels and estimate cycles from actual
   instruction sequences.
8. Run on physical CoCo 1 hardware and measure wall-clock time.
9. Confirm the CoCo 3 produces the same checksum at the normal clock rate.

## Success evidence

The experiment supports the candidate when:

- loss or correct-token probability improves consistently across the run;
- generated samples visibly progress from noise to name-like output;
- at least half of a fixed sample set is novel rather than copied verbatim;
- generated output repeatedly contains corpus-learned fragments or structure;
- fixed-point and floating-point runs have comparable visible quality;
- repeated runs with the same seed produce identical checksums;
- physical CoCo 1 training reaches the quality threshold within 180 seconds.

The exact qualitative rubric for "name-like" must be written before comparing
models, so it cannot be adjusted to favour a result.

## Failure decisions

- **Too slow:** reduce corpus, hidden width, epochs, or output work before using
  CoCo 3 fast mode.
- **Too incoherent:** increase context or hidden width and measure the cost.
- **Copies corpus:** reduce epochs, improve sampling, or expand corpus.
- **Fixed point diverges:** revise scaling, saturation, update retention, or
  activation functions.
- **Softmax dominates:** measure a lookup-and-reciprocal implementation before
  replacing the learning objective.

## Evidence

Not yet run.

## Conclusion

Pending.
