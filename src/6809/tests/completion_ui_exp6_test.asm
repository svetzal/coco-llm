; Direct-simulator interaction test for the EXP-006 completion workbench.

DIRECT_TEST  equ     1
EXP6_UI_TEST equ     1

        org     $2000

        include "../experiments/experiment_006.asm"

exp6_ui_test_start
        lbsr    exp6_initialize_screen
        lda     EXP6_INPUT_SCREEN
        cmpa    #$20                   ; cursor, with no prompt marker
        lbne    exp6_ui_test_failed

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
        lbne    exp6_ui_test_failed

        ; Typed text is black-on-green and the first suggestion is dark.
        ldd     EXP6_INPUT_SCREEN
        cmpd    #$5052                 ; "PR" | $40
        lbne    exp6_ui_test_failed
        ldd     EXP6_SUGGESTION_SCREEN+2
        cmpd    #$030f                 ; dark "CO" from COMPLETE
        lbne    exp6_ui_test_failed
        lda     exp6_suggestions_visible
        cmpa    #1
        lbne    exp6_ui_test_failed

        ; Redrawing selection leaves exactly one visible marker.
        lda     #1
        sta     exp6_selected_suggestion
        lbsr    exp6_draw_suggestions
        lda     EXP6_SUGGESTION_SCREEN
        cmpa    #$60                   ; old marker cleared
        lbne    exp6_ui_test_failed
        lda     EXP6_SUGGESTION_SCREEN+32
        cmpa    #$7e                   ; second row selected
        lbne    exp6_ui_test_failed
        lda     EXP6_SUGGESTION_SCREEN+64
        cmpa    #$60                   ; third row remains clear
        lbne    exp6_ui_test_failed
        clr     exp6_selected_suggestion
        lbsr    exp6_draw_suggestions
        lda     EXP6_SUGGESTION_SCREEN
        cmpa    #$7e                   ; first row selected again
        lbne    exp6_ui_test_failed
        lda     EXP6_SUGGESTION_SCREEN+32
        cmpa    #$60                   ; second-row marker cleared
        lbne    exp6_ui_test_failed

        ; C is a typed prefix. Acceptance appends OMPLETE and a space.
        lbsr    exp6_apply_suggestion
        lda     exp6_input_length
        cmpa    #22
        lbne    exp6_ui_test_failed
        ldd     exp6_input_buffer+13
        cmpd    #$434f                 ; "CO"
        lbne    exp6_ui_test_failed
        lda     exp6_input_buffer+21
        cmpa    #$20
        lbne    exp6_ui_test_failed
        tst     exp6_suggestions_visible
        lbne    exp6_ui_test_failed

        ; A word that will not fit moves intact to the following row.
        ldx     #exp6_ui_wrap_phrase
        ldu     #exp6_input_buffer
        ldb     #34
        stb     exp6_input_length
exp6_ui_copy_wrap_phrase
        lda     ,x+
        sta     ,u+
        decb
        bne     exp6_ui_copy_wrap_phrase
        clr     ,u
        lbsr    exp6_draw_input
        lda     EXP6_INPUT_SCREEN+30
        cmpa    #$60                   ; unused tail of the first row
        lbne    exp6_ui_test_failed
        ldd     EXP6_INPUT_SCREEN+32
        cmpd    #$574f                 ; "WO" begins the second row
        lbne    exp6_ui_test_failed
        ldd     EXP6_INPUT_SCREEN+34
        cmpd    #$5244                 ; the complete word remains intact
        lbne    exp6_ui_test_failed
        lda     EXP6_INPUT_SCREEN+36
        cmpa    #$20                   ; cursor follows the wrapped word
        lbne    exp6_ui_test_failed

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
exp6_ui_wrap_phrase
        fcc     "12345678901234567890123456789 WORD"

exp6_parity_result
        rmb     1

        end     start
