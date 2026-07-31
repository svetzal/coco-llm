; Direct-simulator interaction test for the EXP-006 completion workbench.

DIRECT_TEST  equ     1
EXP6_UI_TEST equ     1

        org     $2000

        include "../experiments/experiment_006.asm"

exp6_ui_test_start
        lbsr    exp6_initialize_screen
        ldx     #exp6_ui_test_phrase
        ldu     #exp6_input_buffer
        ldb     #14
        stb     exp6_input_length
exp6_ui_copy_phrase
        lda     ,x+
        sta     ,u+
        decb
        bne     exp6_ui_copy_phrase
        clr     ,u
        lbsr    exp6_draw_input
        lbsr    exp6_predict_input

        lda     #33                    ; COMPLETE must match prefix C
        sta     exp6_output_index
        lbsr    exp6_candidate_matches_prefix
        cmpa    #1
        bne     exp6_ui_test_failed

        ; Typed text is black-on-green and the first suggestion is dark.
        ldd     EXP6_INPUT_SCREEN+2
        cmpd    #$5052                 ; "PR" | $40
        bne     exp6_ui_test_failed
        ldd     EXP6_SUGGESTION_SCREEN+2
        cmpd    #$030f                 ; dark "CO" from COMPLETE
        bne     exp6_ui_test_failed
        lda     exp6_suggestions_visible
        cmpa    #1
        bne     exp6_ui_test_failed

        ; C is a typed prefix. Acceptance appends OMPLETE and a space.
        lbsr    exp6_apply_suggestion
        lda     exp6_input_length
        cmpa    #22
        bne     exp6_ui_test_failed
        ldd     exp6_input_buffer+13
        cmpd    #$434f                 ; "CO"
        bne     exp6_ui_test_failed
        lda     exp6_input_buffer+21
        cmpa    #$20
        bne     exp6_ui_test_failed
        tst     exp6_suggestions_visible
        bne     exp6_ui_test_failed

        ; Restore the unmasked fixed vector for the shared runner criteria.
        clr     exp6_prefix_length
        ldd     #EXP6_MODEL_BASE
        std     exp6_position_base
        lbsr    exp6_predict_top_three

        lda     #1
        sta     exp6_parity_result
        swi
exp6_ui_test_failed
        clr     exp6_parity_result
        swi

exp6_ui_test_phrase
        fcc     "PRESS TAB TO C"

exp6_parity_result
        rmb     1

        end     start
