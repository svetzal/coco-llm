; EXP-007 inference-only additive language model.
;
; Mac training exports signed Q2.2 values expanded to bytes at EXP7_MODEL_BASE:
;   five positional embedding tables, output weights, output biases.
;
; The five embeddings add into 22 signed bytes. The exporter proves every
; possible token combination remains in signed-byte range. Each output then
; needs 22 native 8x8 MUL instructions. Ranking logits directly avoids
; softmax: softmax changes probabilities, but never their order.

exp7_predict_top_three
        ldx     #exp7_context_vector
        ldb     #EXP7_EMBED_DIMS
        clra
exp7_clear_context
        sta     ,x+
        decb
        bne     exp7_clear_context

        ldu     #exp7_current_context
        ldx     #EXP7_MODEL_BASE
        lda     #EXP7_CONTEXT_SIZE
        sta     exp7_positions_remaining
exp7_add_position
        lda     ,u+
        ldb     #EXP7_EMBED_DIMS
        mul
        leax    d,x
        pshs    u
        ldu     #exp7_context_vector
        lda     #EXP7_EMBED_DIMS
        sta     exp7_dimensions_remaining
exp7_add_dimension
        lda     ,x+
        adda    ,u
        sta     ,u+
        dec     exp7_dimensions_remaining
        bne     exp7_add_dimension
        puls    u
        ; Advance from this embedding row to the next positional table:
        ; current X = table + token*22 + 22.
        ; next table = current X + (VOCAB_SIZE-token-1)*22.
        ; Resetting from a stored table pointer is clearer and cheaper here.
        ldx     exp7_position_base
        leax    EXP7_POSITION_STRIDE,x
        stx     exp7_position_base
        ldx     exp7_position_base
        dec     exp7_positions_remaining
        bne     exp7_add_position

        ldd     #$8000
        std     exp7_top_one_score
        std     exp7_top_two_score
        std     exp7_top_three_score
        clr     exp7_top_one_token
        clr     exp7_top_two_token
        clr     exp7_top_three_token
        ldx     #EXP7_OUTPUT_WEIGHTS+EXP7_EMBED_DIMS
        stx     exp7_weight_pointer
        ldx     #EXP7_OUTPUT_BIASES+1
        stx     exp7_bias_pointer
        lda     #1
        sta     exp7_output_index
        lda     #EXP7_VOCAB_SIZE-1
        sta     exp7_outputs_remaining
exp7_score_output
        ldx     exp7_bias_pointer
        lda     ,x+
        stx     exp7_bias_pointer
        tfr     a,b
        sex
        aslb
        rola
        aslb
        rola
        std     exp7_accumulator

        ldx     exp7_weight_pointer
        ldu     #exp7_context_vector
        lda     #EXP7_EMBED_DIMS
        sta     exp7_dimensions_remaining
exp7_score_dimension
        lda     ,x+
        ldb     ,u+
        lbsr    exp7_multiply_s8_s8
        addd    exp7_accumulator
        std     exp7_accumulator
        dec     exp7_dimensions_remaining
        bne     exp7_score_dimension
        stx     exp7_weight_pointer
        lbsr    exp7_candidate_matches_prefix
        beq     exp7_score_skipped
        lbsr    exp7_consider_score
exp7_score_skipped
        inc     exp7_output_index
        dec     exp7_outputs_remaining
        bne     exp7_score_output
        rts

; Return non-zero when the current output token begins with the typed prefix.
; An empty prefix permits every lexical token.
exp7_candidate_matches_prefix
        ldb     exp7_prefix_length
        beq     exp7_prefix_matches
        lda     exp7_output_index
        pshs    b
        ldb     #2
        mul
        ldx     #exp7_token_pointers
        leax    d,x
        ldx     ,x
        puls    b
        ldu     exp7_prefix_pointer
exp7_compare_prefix
        lda     ,u+
        cmpa    ,x+
        bne     exp7_prefix_mismatch
        decb
        bne     exp7_compare_prefix
exp7_prefix_matches
        lda     #1
        rts
exp7_prefix_mismatch
        clra
        rts

; Insert the current signed 16-bit accumulator into a descending top-three.
; Strict comparisons preserve lower token identifiers when scores tie.
exp7_consider_score
        ldd     exp7_accumulator
        cmpd    exp7_top_one_score
        ble     exp7_consider_two
        ldd     exp7_top_two_score
        std     exp7_top_three_score
        lda     exp7_top_two_token
        sta     exp7_top_three_token
        ldd     exp7_top_one_score
        std     exp7_top_two_score
        lda     exp7_top_one_token
        sta     exp7_top_two_token
        ldd     exp7_accumulator
        std     exp7_top_one_score
        lda     exp7_output_index
        sta     exp7_top_one_token
        rts
exp7_consider_two
        ldd     exp7_accumulator
        cmpd    exp7_top_two_score
        ble     exp7_consider_three
        ldd     exp7_top_two_score
        std     exp7_top_three_score
        lda     exp7_top_two_token
        sta     exp7_top_three_token
        ldd     exp7_accumulator
        std     exp7_top_two_score
        lda     exp7_output_index
        sta     exp7_top_two_token
        rts
exp7_consider_three
        ldd     exp7_accumulator
        cmpd    exp7_top_three_score
        ble     exp7_score_not_selected
        std     exp7_top_three_score
        lda     exp7_output_index
        sta     exp7_top_three_token
exp7_score_not_selected
        rts

; Signed A times signed B -> signed 16-bit D, using the 6809's unsigned MUL.
; Each negative operand contributes one high-byte two's-complement correction.
exp7_multiply_s8_s8
        sta     exp7_factor_a
        stb     exp7_factor_b
        mul
        tst     exp7_factor_a
        bpl     exp7_factor_a_positive
        suba    exp7_factor_b
exp7_factor_a_positive
        tst     exp7_factor_b
        bpl     exp7_multiply_done
        suba    exp7_factor_a
exp7_multiply_done
        rts

exp7_current_context       rmb     EXP7_CONTEXT_SIZE
exp7_context_vector        rmb     EXP7_EMBED_DIMS
exp7_position_base         rmb     2
exp7_weight_pointer        rmb     2
exp7_bias_pointer          rmb     2
exp7_accumulator           rmb     2
exp7_top_one_score         rmb     2
exp7_top_two_score         rmb     2
exp7_top_three_score       rmb     2
exp7_top_one_token         rmb     1
exp7_top_two_token         rmb     1
exp7_top_three_token       rmb     1
exp7_positions_remaining   rmb     1
exp7_dimensions_remaining  rmb     1
exp7_outputs_remaining     rmb     1
exp7_output_index          rmb     1
exp7_factor_a              rmb     1
exp7_factor_b              rmb     1
exp7_prefix_pointer        rmb     2
exp7_prefix_length         rmb     1
