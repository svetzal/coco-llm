# Reference implementation

The reference implementations establish model quality and create exact test
vectors before optimization begins.

- `coco_lm.py` preserves the rejected character-level MLP from EXP-001.
- `token_lm.py` is the current 290-parameter token model from EXP-002.
- `fixed_token_lm.py` specifies its integer-only training arithmetic.

The implementation sequence is:

1. Small readable floating-point model.
2. Frozen corpus, vocabulary, seed, and quality rubric.
3. Integer-only, bit-exact model with explicit overflow behaviour.
4. Intermediate test vectors for forward pass, loss, backward pass, update, and
   generation.
5. Operation counts and timing inputs for 6809 feasibility work.

The floating-point implementation is disposable scaffolding. The bit-exact
integer behaviour becomes the portable specification.
