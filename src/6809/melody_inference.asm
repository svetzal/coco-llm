; EXP-010 melody model inference for the 6809.
;
; Given sixteen context tokens (mode, metre, chord, beat, then twelve rows of
; melody history) this produces a score for each of the thirty-four melody
; tokens and returns the highest.
;
; The structure follows EXP-007's completion inference, with one difference.
; EXP-007's context positions all held the same vocabulary, so it could step
; from one positional table to the next by a fixed stride. Here they do not:
; mode has two rows, metre nine, chord seven, beat twenty-four, and each
; melody position thirty-five. A table of pointers replaces the stride.
;
; A note on labels. The direct simulator's assembler crashes on any label of
; sixteen characters or more, so the parity test assembles this file with
; lwasm and feeds the simulator the resulting bytes. That is the pattern the
; model experiments already use, and it tests the artifact the CoCo runs
; rather than a second assembly of the same source.
;
; Both hardware bounds were proven unreachable before this was written,
; rather than discovered here. The context vector cannot exceed 124 and the
; score
; cannot exceed 31,283, against limits of 127 and 32,767, because the export
; refuses to emit a model whose worst case would overflow. Nothing in this
; file needs to clamp.

melody_context          rmb     MEL_CONTEXT     ; the tokens to predict from
melody_context_vector   rmb     MEL_EMBED       ; their embeddings, summed
melody_scores           rmb     MEL_TOKENS*2    ; signed 16-bit per token

melody_positions_left   rmb     1
melody_dims_left        rmb     1
melody_outputs_left     rmb     1
melody_accumulator      rmb     2
melody_best_score       rmb     2
melody_best_token       rmb     1
melody_token_index      rmb     1
melody_factor_a         rmb     1
melody_factor_b         rmb     1

; ------------------------------------------------------------------------
; Sum one embedding row per context position into the context vector.
melody_build_context
                ldx     #melody_context_vector
                ldb     #MEL_EMBED
                clra
mbc_clear       sta     ,x+
                decb
                bne     mbc_clear

                ldu     #melody_context
                ldy     #mel_position_table
                lda     #MEL_CONTEXT
                sta     melody_positions_left

mbc_position
                ldx     ,y++            ; this position's embedding table
                lda     ,u+             ; the token sitting in this position
                ldb     #MEL_EMBED
                mul                     ; token * MEL_EMBED is its row offset
                leax    d,x

                pshs    u,y
                ldu     #melody_context_vector
                ldb     #MEL_EMBED
mbc_dimension
                lda     ,x+
                adda    ,u
                sta     ,u+
                decb
                bne     mbc_dimension
                puls    u,y

                dec     melody_positions_left
                bne     mbc_position
                rts

; ------------------------------------------------------------------------
; Score every melody token: bias plus the dot product of the context vector
; with that token's weight row.
melody_score_all
                ldx     #mel_weights
                ldy     #mel_biases
                ldu     #melody_scores
                lda     #MEL_TOKENS
                sta     melody_outputs_left

msa_output
                ldd     ,y++            ; the bias is already at score scale
                std     melody_accumulator

                pshs    u,y
                ldu     #melody_context_vector
                ldb     #MEL_EMBED
                stb     melody_dims_left
msa_dimension
                lda     ,x+             ; weight
                ldb     ,u+             ; context
                lbsr    melody_multiply_s8_s8
                addd    melody_accumulator
                std     melody_accumulator
                dec     melody_dims_left
                bne     msa_dimension
                puls    u,y

                ldd     melody_accumulator
                std     ,u++
                dec     melody_outputs_left
                bne     msa_output
                rts

; ------------------------------------------------------------------------
; Highest-scoring token. Softmax cannot change which score is largest, so
; generation that only wants the best token never needs one.
melody_argmax
                ldu     #melody_scores
                ldd     ,u++
                std     melody_best_score
                clr     melody_best_token
                lda     #1
                sta     melody_token_index
                lda     #MEL_TOKENS-1
                sta     melody_outputs_left

ma_next
                ldd     ,u++
                cmpd    melody_best_score
                ble     ma_skip
                std     melody_best_score
                lda     melody_token_index
                sta     melody_best_token
ma_skip
                inc     melody_token_index
                dec     melody_outputs_left
                bne     ma_next
                rts

; ------------------------------------------------------------------------
melody_predict
                lbsr    melody_build_context
                lbsr    melody_score_all
                lbsr    melody_argmax
                rts

; ------------------------------------------------------------------------
; Signed 8-bit A times signed 8-bit B, product in D.
;
; MUL is unsigned. Reading a negative operand as its unsigned byte adds 256
; times the other operand, so each negative operand is corrected by one
; subtraction from the high byte.
melody_multiply_s8_s8
                sta     melody_factor_a
                stb     melody_factor_b
                mul
                tst     melody_factor_a
                bpl     mms_a_positive
                suba    melody_factor_b
mms_a_positive
                tst     melody_factor_b
                bpl     mms_b_positive
                suba    melody_factor_a
mms_b_positive
                rts

; ------------------------------------------------------------------------
; Weighted draw over the scores.
;
; Argmax alone circles a few notes and dies: the most probable row is often a
; HOLD, and always taking it produces a held drone. Drawing in proportion to
; score is what makes a generated line move.
;
; No division and no 32-bit multiply. The draw is masked to the smallest power
; of two above the running total and retried when it lands past the end, which
; is a handful of instructions where a divide is not.

mel_probs       rmb     MEL_TOKENS      ; unnormalised weight per token
mel_total       rmb     2
mel_mask        rmb     2
mel_draw        rmb     2
mel_rng         rmb     2
mel_tmp         rmb     2
mel_tries       rmb     1
mel_top         rmb     2

melody_sample
                lbsr    mel_find_top
                lbsr    mel_weigh
                lbsr    mel_pick_mask
                lbsr    mel_roll
                lbsr    mel_walk
                rts

; The largest score, so every weight is a drop from the best.
mel_find_top
                ldu     #melody_scores
                ldd     ,u++
                std     mel_top
                lda     #MEL_TOKENS-1
                sta     melody_outputs_left
mft_next        ldd     ,u++
                cmpd    mel_top
                ble     mft_skip
                std     mel_top
mft_skip        dec     melody_outputs_left
                bne     mft_next
                rts

; weight[i] = EXP_LUT[min(255, (top - score[i]) >> MEL_SHIFT)]
mel_weigh
                ldu     #melody_scores
                ldy     #mel_probs
                ldd     #0
                std     mel_total
                lda     #MEL_TOKENS
                sta     melody_outputs_left
mw_next
                ldd     mel_top
                subd    ,u++            ; the drop is never negative
                std     mel_tmp
                ldb     #MEL_SHIFT
mw_shift        lsr     mel_tmp
                ror     mel_tmp+1
                decb
                bne     mw_shift
                ldd     mel_tmp
                tsta                    ; anything past 255 saturates
                beq     mw_inrange
                ldb     #255
mw_inrange
                ldx     #mel_exp_lut
                abx
                lda     ,x
                sta     ,y+
                tfr     a,b
                clra
                addd    mel_total
                std     mel_total
                dec     melody_outputs_left
                bne     mw_next
                rts

; Smallest power of two above the total, minus one.
mel_pick_mask
                ldd     #1
                std     mel_mask
mpm_grow        ldd     mel_mask
                cmpd    mel_total
                bhs     mpm_done
                lslb
                rola
                addd    #1
                std     mel_mask
                bra     mpm_grow
mpm_done        rts

; Uniform in [0, total), by masking and retrying.
mel_roll
                lda     #16
                sta     mel_tries
mr_try          lbsr    mel_rand
                anda    mel_mask
                andb    mel_mask+1
                std     mel_draw
                cmpd    mel_total
                blo     mr_done
                dec     mel_tries
                bne     mr_try
                ldd     mel_total       ; give up and take the last slot
                subd    #1
                std     mel_draw
mr_done         rts

; First token whose running total passes the draw.
mel_walk
                ldu     #mel_probs
                ldd     #0
                std     mel_tmp
                clr     melody_token_index
                lda     #MEL_TOKENS
                sta     melody_outputs_left
mwk_next        ldb     ,u+
                clra
                addd    mel_tmp
                std     mel_tmp
                cmpd    mel_draw
                bhi     mwk_found
                inc     melody_token_index
                dec     melody_outputs_left
                bne     mwk_next
                lda     #MEL_TOKENS-1
                sta     melody_token_index
mwk_found       lda     melody_token_index
                sta     melody_best_token
                rts

; XorShift16, the same generator the Python reference uses, so a given seed
; produces the same sequence on both.
mel_rand
                ldd     mel_rng
                std     mel_tmp
                lslb
                rola
                lslb
                rola
                lslb
                rola
                lslb
                rola
                lslb
                rola
                lslb
                rola
                lslb
                rola                    ; value << 7
                eora    mel_tmp
                eorb    mel_tmp+1
                std     mel_rng
                std     mel_tmp

                tfr     a,b             ; value >> 9
                lsrb
                clra
                eora    mel_tmp
                eorb    mel_tmp+1
                std     mel_rng
                std     mel_tmp

                tfr     b,a             ; value << 8
                clrb
                eora    mel_tmp
                eorb    mel_tmp+1
                std     mel_rng
                rts
