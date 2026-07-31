; Direct-simulator parity test for the pretrained EXP-007 inference core.

        org     $2000

start
        lds     #$3e00
        ldd     #EXP7_MODEL_BASE
        std     exp7_position_base
        clr     exp7_prefix_length
        ldx     #exp7_test_context
        ldu     #exp7_current_context
        ldd     ,x++
        std     ,u++
        ldd     ,x++
        std     ,u++
        lda     ,x
        sta     ,u
        lbsr    exp7_predict_top_three

        ldx     #exp7_expected_top_three
        lda     exp7_top_one_token
        cmpa    ,x+
        bne     exp7_test_failed
        lda     exp7_top_two_token
        cmpa    ,x+
        bne     exp7_test_failed
        lda     exp7_top_three_token
        cmpa    ,x
        bne     exp7_test_failed
        lda     #1
        sta     exp7_parity_result
        swi
exp7_test_failed
        clr     exp7_parity_result
        swi

        include "../../../build/exp007/model_data.inc"
        include "../completion_inference_exp7.asm"

exp7_parity_result rmb     1

;! exp7_parity_result = #$01

        end     start
