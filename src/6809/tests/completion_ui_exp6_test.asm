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

        ; Typed text is black-on-green and the popover begins at its cursor.
        ldd     EXP6_INPUT_SCREEN
        cmpd    #$5052                 ; "PR" | $40
        lbne    exp6_ui_test_failed
        ldx     exp6_popover_origin
        cmpx    exp6_input_cursor
        lbne    exp6_ui_test_failed
        lda     exp6_popover_width
        cmpa    #11                    ; widest candidate plus marker padding
        lbne    exp6_ui_test_failed
        lda     ,x
        cmpa    #$3e                   ; reverse-field first-row marker
        lbne    exp6_ui_test_failed
        ldd     2,x
        cmpd    #$030f                 ; dark "CO" from COMPLETE
        lbne    exp6_ui_test_failed
        lda     exp6_suggestions_visible
        cmpa    #1
        lbne    exp6_ui_test_failed

        ; Redrawing selection leaves exactly one visible marker.
        lda     #1
        sta     exp6_selected_suggestion
        lbsr    exp6_draw_suggestions
        ldx     exp6_popover_origin
        lda     ,x
        cmpa    #$20                   ; old marker cleared to dark background
        lbne    exp6_ui_test_failed
        lda     32,x
        cmpa    #$3e                   ; second row selected
        lbne    exp6_ui_test_failed
        lda     64,x
        cmpa    #$20                   ; third row remains clear
        lbne    exp6_ui_test_failed
        clr     exp6_selected_suggestion
        lbsr    exp6_draw_suggestions
        ldx     exp6_popover_origin
        lda     ,x
        cmpa    #$3e                   ; first row selected again
        lbne    exp6_ui_test_failed
        lda     32,x
        cmpa    #$20                   ; second-row marker cleared
        lbne    exp6_ui_test_failed

        ; Dismissing the overlay restores the cursor and phrase underneath.
        lbsr    exp6_hide_suggestions
        ldx     exp6_input_cursor
        lda     ,x
        cmpa    #$20
        lbne    exp6_ui_test_failed
        ldd     EXP6_INPUT_SCREEN
        cmpd    #$5052
        lbne    exp6_ui_test_failed

        ; At the right edge, the measured box shifts left to fit exactly.
        ldd     #EXP6_SCREEN+158        ; row four, column 30
        std     exp6_input_cursor
        lbsr    exp6_draw_suggestions
        lda     exp6_popover_origin+1
        anda    #$1f
        adda    exp6_popover_width
        cmpa    #32
        lbne    exp6_ui_test_failed
        ldd     exp6_popover_origin
        andb    #$e0
        cmpd    #EXP6_SCREEN+128
        lbne    exp6_ui_test_failed
        lbsr    exp6_hide_suggestions

        ; At the bottom-right corner, the box shifts both left and upward.
        lda     EXP6_SCREEN+511
        sta     exp6_ui_saved_corner
        ldd     #EXP6_SCREEN+510
        std     exp6_input_cursor
        lbsr    exp6_draw_suggestions
        ldd     exp6_popover_origin
        andb    #$e0
        cmpd    #EXP6_SCREEN+416        ; last legal start row for height three
        lbne    exp6_ui_test_failed
        lda     exp6_popover_origin+1
        anda    #$1f
        adda    exp6_popover_width
        cmpa    #32
        lbne    exp6_ui_test_failed
        lbsr    exp6_hide_suggestions
        lda     EXP6_SCREEN+511
        cmpa    exp6_ui_saved_corner
        lbne    exp6_ui_test_failed

        ; C is a typed prefix. Acceptance appends OMPLETE and a space.
        lbsr    exp6_draw_input
        clr     exp6_selected_suggestion
        lbsr    exp6_draw_suggestions
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

        ; A separator after a full row is consumed rather than indented.
        ldx     #exp6_ui_exact_wrap_phrase
        ldu     #exp6_input_buffer
        ldb     #37
        stb     exp6_input_length
exp6_ui_copy_exact_wrap_phrase
        lda     ,x+
        sta     ,u+
        decb
        bne     exp6_ui_copy_exact_wrap_phrase
        clr     ,u
        lbsr    exp6_draw_input
        ldd     EXP6_INPUT_SCREEN+32
        cmpd    #$574f                 ; no blank before "WORD"
        lbne    exp6_ui_test_failed
        lda     EXP6_INPUT_SCREEN+36
        cmpa    #$20                   ; cursor remains immediately after it
        lbne    exp6_ui_test_failed

        ; Ten wrapped rows fill the editor immediately above the instructions.
        ldu     #exp6_input_buffer
        lda     #10
        sta     exp6_ui_fill_rows_remaining
exp6_ui_fill_next_row
        ldb     #16
        lda     #$41
exp6_ui_fill_row_word
        sta     ,u+
        decb
        bne     exp6_ui_fill_row_word
        lda     #$20
        sta     ,u+
        dec     exp6_ui_fill_rows_remaining
        bne     exp6_ui_fill_next_row
        clr     ,u
        lda     #170
        sta     exp6_input_length
        lbsr    exp6_draw_input
        lda     EXP6_INPUT_END-32
        cmpa    #$41                   ; text reaches screen row eleven
        lbne    exp6_ui_test_failed
        lda     EXP6_INPUT_END-15
        cmpa    #$20                   ; cursor remains on the final text row
        lbne    exp6_ui_test_failed
        lda     EXP6_INPUT_END
        cmpa    #$52                   ; instructions begin on the next row
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
exp6_ui_exact_wrap_phrase
        fcc     "12345678901234567890123456789012 WORD"
exp6_ui_saved_corner
        rmb     1
exp6_ui_fill_rows_remaining
        rmb     1

exp6_parity_result
        rmb     1

        end     start
