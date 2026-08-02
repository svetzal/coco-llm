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
