; EXP-011 fixed-point key-value attention.
;
; The query and each memory key select signed Q4.4 vectors. Their dot product
; is a raw signed 16-bit score; the common Q8.8 scale does not affect ranking.
; The highest-scoring record supplies the copied value. No softmax is needed at
; inference because it cannot change which score is highest.

attention_predict
        lda     attention_query
        ldb     #ATT_WIDTH
        mul
        ldx     #attention_query_weights
        leax    d,x
        stx     attention_query_pointer
        clr     attention_slot

attention_score_next
        ldx     #attention_memory_keys
        ldb     attention_slot
        abx
        lda     ,x
        ldb     #ATT_WIDTH
        mul
        ldu     #attention_key_weights
        leau    d,u
        ldx     attention_query_pointer
        clr     attention_score
        clr     attention_score+1
        lda     #ATT_WIDTH
        sta     attention_dimensions_left

attention_score_dimension
        lda     ,x+
        ldb     ,u+
        lbsr    attention_smul8
        addd    attention_score
        std     attention_score
        dec     attention_dimensions_left
        bne     attention_score_dimension

        lda     attention_slot
        ldb     #2
        mul
        ldy     #attention_scores
        leay    d,y
        ldd     attention_score
        std     ,y
        tst     attention_slot
        beq     attention_new_best
        cmpd    attention_best_score
        ble     attention_keep_best
attention_new_best
        std     attention_best_score
        lda     attention_slot
        sta     attention_best_slot
attention_keep_best
        inc     attention_slot
        lda     attention_slot
        cmpa    #ATT_MEMORY_SIZE
        blo     attention_score_next

        ldx     #attention_memory_values
        ldb     attention_best_slot
        abx
        lda     ,x
        sta     attention_result
        rts

; A and B are signed bytes; D returns their signed 16-bit product. MUL is
; unsigned, so each negative operand contributes one high-byte correction.
attention_smul8
        sta     attention_multiply_a
        stb     attention_multiply_b
        mul
        tst     attention_multiply_a
        bpl     attention_multiply_a_ready
        suba    attention_multiply_b
attention_multiply_a_ready
        tst     attention_multiply_b
        bpl     attention_multiply_done
        suba    attention_multiply_a
attention_multiply_done
        rts

attention_memory_keys           rmb     ATT_MEMORY_SIZE
attention_memory_values         rmb     ATT_MEMORY_SIZE
attention_query                 rmb     1
attention_scores                rmb     ATT_MEMORY_SIZE*2
attention_best_score            rmb     2
attention_best_slot             rmb     1
attention_result                rmb     1
attention_query_pointer         rmb     2
attention_slot                  rmb     1
attention_score                 rmb     2
attention_dimensions_left       rmb     1
attention_multiply_a            rmb     1
attention_multiply_b            rmb     1
