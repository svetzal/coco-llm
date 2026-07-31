; Direct-simulator parity test for the pretrained EXP-006 inference core.

        org     $2000

start
        lds     #$5f00
        ldd     #EXP6_MODEL_BASE
        std     exp6_position_base
        ldx     #exp6_test_context
        ldu     #exp6_current_context
        ldd     ,x++
        std     ,u++
        ldd     ,x
        std     ,u
        lbsr    exp6_predict_top_three

        ldx     #exp6_expected_top_three
        lda     exp6_top_one_token
        cmpa    ,x+
        bne     exp6_test_failed
        lda     exp6_top_two_token
        cmpa    ,x+
        bne     exp6_test_failed
        lda     exp6_top_three_token
        cmpa    ,x
        bne     exp6_test_failed
        lda     #1
        sta     exp6_parity_result
        swi
exp6_test_failed
        clr     exp6_parity_result
        swi

        include "../../../build/exp006/model_data.inc"
        include "../completion_inference.asm"

exp6_parity_result rmb     1

;! exp6_parity_result = #$01

        end     start
