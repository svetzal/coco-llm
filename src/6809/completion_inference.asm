; EXP-006 inference-only additive language model.
;
; Mac training exports signed Q4.4 bytes at EXP6_MODEL_BASE:
;   four positional embedding tables, output weights, output biases.
;
; The four embeddings add into nine signed bytes. The exporter proves every
; possible token combination remains in signed-byte range. Each output then
; needs nine native 8x8 MUL instructions. Ranking logits directly avoids
; softmax: softmax changes probabilities, but never their order.

exp6_predict_top_three
        ldx     #exp6_context_vector
        ldb     #EXP6_EMBED_DIMS
        clra
exp6_clear_context
        sta     ,x+
        decb
        bne     exp6_clear_context

        ldu     #exp6_current_context
        ldx     #EXP6_MODEL_BASE
        lda     #EXP6_CONTEXT_SIZE
        sta     exp6_positions_remaining
exp6_add_position
        lda     ,u+
        ldb     #EXP6_EMBED_DIMS
        mul
        leax    d,x
        pshs    u
        ldu     #exp6_context_vector
        lda     #EXP6_EMBED_DIMS
        sta     exp6_dimensions_remaining
exp6_add_dimension
        lda     ,x+
        adda    ,u
        sta     ,u+
        dec     exp6_dimensions_remaining
        bne     exp6_add_dimension
        puls    u
        ; Advance from this embedding row to the next positional table:
        ; current X = table + token*9 + 9.
        ; next table = current X + (VOCAB_SIZE-token-1)*9.
        ; Resetting from a stored table pointer is clearer and cheaper here.
        ldx     exp6_position_base
        leax    1602,x
        stx     exp6_position_base
        ldx     exp6_position_base
        dec     exp6_positions_remaining
        bne     exp6_add_position

        ldd     #$8000
        std     exp6_top_one_score
        std     exp6_top_two_score
        std     exp6_top_three_score
        clr     exp6_top_one_token
        clr     exp6_top_two_token
        clr     exp6_top_three_token
        ldx     #EXP6_OUTPUT_WEIGHTS+EXP6_EMBED_DIMS
        stx     exp6_weight_pointer
        ldx     #EXP6_OUTPUT_BIASES+1
        stx     exp6_bias_pointer
        lda     #1
        sta     exp6_output_index
        lda     #EXP6_VOCAB_SIZE-1
        sta     exp6_outputs_remaining
exp6_score_output
        ldx     exp6_bias_pointer
        lda     ,x+
        stx     exp6_bias_pointer
        tfr     a,b
        sex
        aslb
        rola
        aslb
        rola
        aslb
        rola
        aslb
        rola
        std     exp6_accumulator

        ldx     exp6_weight_pointer
        ldu     #exp6_context_vector
        lda     #EXP6_EMBED_DIMS
        sta     exp6_dimensions_remaining
exp6_score_dimension
        lda     ,x+
        ldb     ,u+
        lbsr    exp6_multiply_s8_s8
        addd    exp6_accumulator
        std     exp6_accumulator
        dec     exp6_dimensions_remaining
        bne     exp6_score_dimension
        stx     exp6_weight_pointer
        lbsr    exp6_consider_score
        inc     exp6_output_index
        dec     exp6_outputs_remaining
        bne     exp6_score_output
        rts

; Insert the current signed 16-bit accumulator into a descending top-three.
; Strict comparisons preserve lower token identifiers when scores tie.
exp6_consider_score
        ldd     exp6_accumulator
        cmpd    exp6_top_one_score
        ble     exp6_consider_two
        ldd     exp6_top_two_score
        std     exp6_top_three_score
        lda     exp6_top_two_token
        sta     exp6_top_three_token
        ldd     exp6_top_one_score
        std     exp6_top_two_score
        lda     exp6_top_one_token
        sta     exp6_top_two_token
        ldd     exp6_accumulator
        std     exp6_top_one_score
        lda     exp6_output_index
        sta     exp6_top_one_token
        rts
exp6_consider_two
        ldd     exp6_accumulator
        cmpd    exp6_top_two_score
        ble     exp6_consider_three
        ldd     exp6_top_two_score
        std     exp6_top_three_score
        lda     exp6_top_two_token
        sta     exp6_top_three_token
        ldd     exp6_accumulator
        std     exp6_top_two_score
        lda     exp6_output_index
        sta     exp6_top_two_token
        rts
exp6_consider_three
        ldd     exp6_accumulator
        cmpd    exp6_top_three_score
        ble     exp6_score_not_selected
        std     exp6_top_three_score
        lda     exp6_output_index
        sta     exp6_top_three_token
exp6_score_not_selected
        rts

; Signed A times signed B -> signed 16-bit D, using the 6809's unsigned MUL.
; Each negative operand contributes one high-byte two's-complement correction.
exp6_multiply_s8_s8
        sta     exp6_factor_a
        stb     exp6_factor_b
        mul
        tst     exp6_factor_a
        bpl     exp6_factor_a_positive
        suba    exp6_factor_b
exp6_factor_a_positive
        tst     exp6_factor_b
        bpl     exp6_multiply_done
        suba    exp6_factor_a
exp6_multiply_done
        rts

exp6_current_context       rmb     EXP6_CONTEXT_SIZE
exp6_context_vector        rmb     EXP6_EMBED_DIMS
exp6_position_base         rmb     2
exp6_weight_pointer        rmb     2
exp6_bias_pointer          rmb     2
exp6_accumulator           rmb     2
exp6_top_one_score         rmb     2
exp6_top_two_score         rmb     2
exp6_top_three_score       rmb     2
exp6_top_one_token         rmb     1
exp6_top_two_token         rmb     1
exp6_top_three_token       rmb     1
exp6_positions_remaining   rmb     1
exp6_dimensions_remaining  rmb     1
exp6_outputs_remaining     rmb     1
exp6_output_index          rmb     1
exp6_factor_a              rmb     1
exp6_factor_b              rmb     1
