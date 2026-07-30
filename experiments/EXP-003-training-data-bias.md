# EXP-003: Training-data bias

**Status:** integer reference supported; 6809 implementation pending

## Question

Can an audience see training-data bias emerge when identical models learn from
Apple-fan, Commodore-fan, Tandy-fan, and combined datasets?

What happens when balanced examples are present but ordered poorly?

## Hypothesis

With model architecture, initialization, vocabulary, update count, and
generation seeds held constant:

- each fan corpus will cause its manufacturer to dominate generated names;
- concatenating all three corpora will retain a recency bias toward the
  manufacturer trained last;
- interleaving the same examples will produce a more diverse mixture.

## Controls

Every run uses:

- the same 31-token vocabulary;
- the same 310-parameter integer model;
- seed 6809;
- 1,620 training updates;
- the same twenty generation seeds;
- the same fixed-point arithmetic and sampling procedure.

Only the training examples and their ordering change.

Each fan set contributes 18 two-token names, producing 54 next-token examples
per epoch. A fan model trains for 30 epochs. The combined models contain 162
examples and train for 10 epochs. Every model therefore receives exactly 1,620
updates and performs 451,980 matrix multiplications.

The repeated examples are deliberate weighting, not a claim to be a complete
historical inventory.

## Procedure

1. Initialize every model from seed 6809.
2. Train the Apple, Commodore, and Tandy models separately.
3. Train one combined model with the fan datasets concatenated in that order.
4. Train another combined model with examples interleaved Apple, Commodore,
   Tandy.
5. Generate twenty samples from the same seeds.
6. Count the first token of each generated name.

Run:

```sh
uv run python src/reference/run_bias_demo.py
```

## Evidence

| Training run | Apple | Commodore | Tandy | Other | Final loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| Apple fan | 16 | 0 | 0 | 4 | 1.0876 |
| Commodore fan | 0 | 15 | 0 | 5 | 0.4975 |
| Tandy fan | 0 | 1 | 14 | 5 | 0.5030 |
| All, concatenated | 0 | 1 | 14 | 5 | 2.1802 |
| All, interleaved | 10 | 6 | 3 | 1 | 0.8752 |

Representative fan outputs:

```text
APPLE MACINTOSH
COMMODORE AMIGA
TANDY COCO
```

The concatenated corpus contains equal numbers of two-token Apple, Commodore,
and Tandy names. It still behaves like the Tandy model because online SGD sees
the complete Tandy block last in every epoch.

Interleaving the exact same examples removes that repeated last-block effect.
The resulting twenty-sample set contains all three manufacturers. It is not
perfectly uniform: finite sampling, initialization, token relationships, and
the small model still matter.

## Conclusion

The hypothesis is supported in the integer reference.

The model has no brand loyalty. Apparent preference is learned from which
examples are repeated and when they are presented. Merely saying that all
groups are represented does not establish balanced training.

This is an unusually compact demonstration of several practical lessons:

- data selection expresses human choices;
- repetition changes what the model treats as likely;
- ordering matters in online learning;
- equal source counts do not guarantee equal output;
- sampling exposes a distribution, not a deterministic opinion;
- inspecting outputs is necessary but does not explain every learned weight.

The experiment remains open until these five runs produce matching checksums and
first-token counts in the 6809 implementation.
