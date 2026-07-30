; Training driver for the integer token language model.
;
; This module owns the epoch/example loops and all gradient-driven parameter
; updates. It calls the shared forward pass and fixed-point arithmetic in
; model_core.asm, and the training-progress renderer in screen.asm.

train_model
        lda     #TRAIN_EPOCHS
        sta     epochs_remaining
epoch_loop
        lda     #TRAIN_EPOCHS
        suba    epochs_remaining
        inca
        sta     last_epoch_displayed
        ldx     #SCREEN+38
        lbsr    write_decimal_2
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
        pshs    u
        lbsr    display_training_example
        lbsr    train_example
        puls    u
        dec     examples_remaining
        bne     example_loop
        dec     epochs_remaining
        bne     epoch_loop
        rts

train_example
        lbsr    forward

        ; output_error aliases probabilities. Subtract 256 at the target.
        lda     current_target
        ldb     #2
        mul
        ldx     #probabilities
        leax    d,x
        ldd     ,x
        subd    #256
        std     ,x

        lbsr    calculate_context_error
        lbsr    update_output_parameters
        lbsr    update_embeddings
        rts

calculate_context_error
        clr     dimension_index
context_error_dimension
        lda     dimension_index
        ldb     #2
        mul
        ldx     #output_weights
        leax    d,x
        stx     weight_pointer
        ldx     #probabilities
        stx     probability_pointer
        clra
        clrb
        std     accumulator
        lda     #VOCAB_SIZE
        sta     outputs_remaining
context_error_output
        ldx     weight_pointer
        lda     ,x
        ldx     probability_pointer
        lbsr    multiply_s8_s16
        asra
        rorb
        asra
        rorb
        asra
        rorb
        asra
        rorb
        addd    accumulator
        std     accumulator
        ldx     weight_pointer
        leax    6,x
        stx     weight_pointer
        ldx     probability_pointer
        leax    2,x
        stx     probability_pointer
        dec     outputs_remaining
        bne     context_error_output

        lda     dimension_index
        ldb     #2
        mul
        ldx     #context_error
        leax    d,x
        ldd     accumulator
        std     ,x
        inc     dimension_index
        lda     dimension_index
        cmpa    #EMBED_DIMS
        blo     context_error_dimension
        rts

update_output_parameters
        ldx     #output_weights
        stx     weight_pointer
        ldx     #output_biases
        stx     bias_pointer
        ldx     #probabilities
        stx     probability_pointer
        lda     #VOCAB_SIZE
        sta     outputs_remaining
update_output
        ldx     probability_pointer
        ldd     ,x
        ldx     bias_pointer
        lbsr    saturating_subtract

        clr     dimension_index
update_weight
        lda     dimension_index
        ldb     #2
        mul
        ldx     #context_vector
        leax    d,x
        ifdef   EXPERIMENT_5
        ldd     ,x
        ldx     probability_pointer
        lbsr    multiply_s16_s16
        else
        lda     1,x
        ldx     probability_pointer
        lbsr    multiply_s8_s16
        endc
        asra
        rorb
        asra
        rorb
        asra
        rorb
        asra
        rorb
        ldx     weight_pointer
        lbsr    saturating_subtract
        ldx     weight_pointer
        leax    2,x
        stx     weight_pointer
        inc     dimension_index
        lda     dimension_index
        cmpa    #EMBED_DIMS
        blo     update_weight

        ldx     bias_pointer
        leax    2,x
        stx     bias_pointer
        ldx     probability_pointer
        leax    2,x
        stx     probability_pointer
        dec     outputs_remaining
        bne     update_output
        rts

update_embeddings
        lda     current_context
        ldx     #position_embeddings
        lbsr    update_one_embedding
        lda     current_context+1
        ldx     #position_embeddings+POS_BYTES
        lbsr    update_one_embedding
        rts

update_one_embedding
        ldb     #6
        mul
        leax    d,x
        stx     embedding_pointer
        ldu     #context_error
        lda     #EMBED_DIMS
        sta     dimensions_remaining
update_embedding_dimension
        ldd     ,u++
        ldx     embedding_pointer
        lbsr    saturating_subtract
        leax    2,x
        stx     embedding_pointer
        dec     dimensions_remaining
        bne     update_embedding_dimension
        rts
