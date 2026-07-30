; Shared mutable state for the integer token language model.
;
; Experiment drivers include this after their generated read-only model data,
; keeping all uninitialized storage at the end of the DECB program image.

; Trainable Q4.12 master parameters are one contiguous block so the test build
; can compare every byte with the Python reference fixture.
position_embeddings
        rmb     POS_BYTES*CONTEXT_SIZE
output_weights
        rmb     WEIGHT_BYTES
output_biases
        rmb     BIAS_BYTES
parameters_end

context_vector          rmb     6
logits                  rmb     VOCAB_SIZE*2
exponentials            rmb     VOCAB_SIZE
probabilities           rmb     VOCAB_SIZE*2
context_error           rmb     6

rng_state               rmb     2
shift_temp              rmb     2
shift_left              rmb     2
shift_right             rmb     1
accumulator             rmb     2
maximum_logit           rmb     2
exponential_total       rmb     2
division_numerator      rmb     3
reciprocal              rmb     1
probability_total       rmb     2
maximum_probability     rmb     2
correction              rmb     2
removed_boundary        rmb     2
sample_cumulative       rmb     2
arithmetic_update       rmb     2
arithmetic_original     rmb     2
multiply_product        rmb     2
multiply_factor16       rmb     2

weight_pointer          rmb     2
bias_pointer            rmb     2
logit_pointer           rmb     2
probability_pointer     rmb     2
embedding_pointer       rmb     2
screen_pointer          rmb     2
output_pointer          rmb     2
output_limit            rmb     2

current_context         rmb     2
current_target          rmb     1
epochs_remaining        rmb     1
examples_remaining      rmb     1
outputs_remaining       rmb     1
dimensions_remaining    rmb     1
dimension_index         rmb     1
output_index            rmb     1
winner_index            rmb     1
parity_result           rmb     1
mismatch_offset         rmb     2
mismatch_actual         rmb     1
mismatch_expected       rmb     1
multiply_factor         rmb     1
generated_tokens        rmb     1
generation_remaining    rmb     1
chosen_token            rmb     1
sample_draw             rmb     1
last_epoch_displayed    rmb     1
generation_display_full rmb     1
