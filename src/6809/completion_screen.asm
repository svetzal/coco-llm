; CoCo VDG presentation for the EXP-006 completion workbench.
;
; Human-typed text is black-on-green. Model suggestions use the dark reverse
; field, preserving the same visual distinction as the earlier experiments.

EXP6_SCREEN             equ     $0400
EXP6_INPUT_SCREEN       equ     EXP6_SCREEN+64
EXP6_INPUT_END          equ     EXP6_SCREEN+384
EXP6_STATUS_SCREEN      equ     EXP6_SCREEN+48

exp6_initialize_screen
        ldx     #EXP6_SCREEN
        lda     #$60
exp6_clear_screen
        sta     ,x+
        cmpx    #EXP6_SCREEN+512
        blo     exp6_clear_screen

        ldx     #EXP6_SCREEN
        lda     #$20
        ldb     #32
exp6_fill_title
        sta     ,x+
        decb
        bne     exp6_fill_title
        ldx     #EXP6_SCREEN
        ldu     #exp6_message_title
        lbsr    exp6_print_dark

        ldx     #EXP6_SCREEN+32
        ldu     #exp6_message_type
        lbsr    exp6_print_normal
        ldx     #EXP6_SCREEN+384
        ldu     #exp6_message_predict
        lbsr    exp6_print_normal
        ldx     #EXP6_SCREEN+416
        ldu     #exp6_message_choose
        lbsr    exp6_print_normal
        ldx     #EXP6_SCREEN+480
        ldu     #exp6_message_shape
        lbsr    exp6_print_normal
        lbsr    exp6_draw_input
        rts

exp6_draw_input
        ldx     #EXP6_INPUT_SCREEN
        lda     #$60
exp6_clear_input_rows
        sta     ,x+
        cmpx    #EXP6_INPUT_END
        blo     exp6_clear_input_rows
        ldx     #EXP6_INPUT_SCREEN
        ldu     #exp6_input_buffer
        lda     exp6_input_length
        sta     exp6_draw_remaining
        clr     exp6_draw_column
exp6_draw_next
        tst     exp6_draw_remaining
        beq     exp6_draw_cursor
        lda     ,u
        cmpa    #$20
        beq     exp6_draw_separator

        ; Measure the next word before drawing it. If it cannot fit in the
        ; current row, leave the remaining cells blank and start on row two.
        pshs    u
        clrb
exp6_measure_word
        lda     ,u+
        beq     exp6_word_measured
        cmpa    #$20
        beq     exp6_word_measured
        incb
        bra     exp6_measure_word
exp6_word_measured
        puls    u
        lda     exp6_draw_column
        beq     exp6_draw_word_character
        pshs    b
        adda    ,s
        puls    b
        cmpa    #32
        bls     exp6_draw_word_character
        ldb     #32
        subb    exp6_draw_column
        abx
        clr     exp6_draw_column

exp6_draw_word_character
        cmpx    #EXP6_INPUT_END
        bhs     exp6_draw_input_done
        lda     ,u+
        ora     #$40
        sta     ,x+
        dec     exp6_draw_remaining
        inc     exp6_draw_column
        lda     exp6_draw_column
        cmpa    #32
        blo     exp6_draw_next
        clr     exp6_draw_column
        bra     exp6_draw_next

exp6_draw_separator
        cmpx    #EXP6_INPUT_END
        bhs     exp6_draw_input_done
        leau    1,u
        leax    1,x
        dec     exp6_draw_remaining
        inc     exp6_draw_column
        lda     exp6_draw_column
        cmpa    #32
        blo     exp6_draw_next
        clr     exp6_draw_column
        bra     exp6_draw_next

exp6_draw_cursor
        cmpx    #EXP6_INPUT_END
        bhs     exp6_draw_input_done
        stx     exp6_input_cursor
        lda     #$20
        sta     ,x
exp6_draw_input_done
        rts

exp6_clear_suggestions
        tst     exp6_suggestions_visible
        beq     exp6_clear_suggestions_done
        ldx     exp6_popover_origin
        ldy     #exp6_popover_backup
        lda     exp6_popover_height
        sta     exp6_popover_rows_remaining
exp6_restore_popover_row
        ldb     exp6_popover_width
exp6_restore_popover_cell
        lda     ,y+
        sta     ,x+
        decb
        bne     exp6_restore_popover_cell
        ldb     #32
        subb    exp6_popover_width
        abx
        dec     exp6_popover_rows_remaining
        bne     exp6_restore_popover_row
        clr     exp6_suggestions_visible
exp6_clear_suggestions_done
        rts

exp6_draw_suggestions
        tst     exp6_suggestions_visible
        bne     exp6_paint_popover
        lbsr    exp6_prepare_popover
        lbsr    exp6_save_popover_background

exp6_paint_popover
        ldy     exp6_popover_origin
        ldu     #exp6_top_one_token
        clr     exp6_popover_row_index
        lda     exp6_popover_height
        sta     exp6_popover_rows_remaining
exp6_draw_suggestion
        tfr     y,x
        lda     #$20
        ldb     exp6_popover_width
exp6_fill_popover_row
        sta     ,x+
        decb
        bne     exp6_fill_popover_row

        tfr     y,x
        lda     exp6_popover_row_index
        cmpa    exp6_selected_suggestion
        bne     exp6_draw_popover_word
        lda     #$7e
        sta     ,x
exp6_draw_popover_word
        leax    2,x
        lda     ,u+
        pshs    u
        lbsr    exp6_print_token_dark
        puls    u
        leay    32,y
        inc     exp6_popover_row_index
        dec     exp6_popover_rows_remaining
        bne     exp6_draw_suggestion

        lda     #1
        sta     exp6_suggestions_visible
        rts

; Measure the widest candidate, place the popover at the editor cursor, and
; shift it left or upward when its measured rectangle would cross an edge.
exp6_prepare_popover
        clr     exp6_popover_width
        ldu     #exp6_top_one_token
        lda     exp6_suggestion_count
        sta     exp6_popover_rows_remaining
exp6_measure_candidate
        lda     ,u+
        pshs    u
        ldb     #2
        mul
        ldu     #exp6_token_pointers
        leau    d,u
        ldu     ,u
        clrb
exp6_measure_candidate_character
        lda     ,u+
        beq     exp6_candidate_measured
        incb
        bra     exp6_measure_candidate_character
exp6_candidate_measured
        cmpb    exp6_popover_width
        bls     exp6_candidate_width_ready
        stb     exp6_popover_width
exp6_candidate_width_ready
        puls    u
        dec     exp6_popover_rows_remaining
        bne     exp6_measure_candidate

        ldb     exp6_popover_width
        addb    #2
        cmpb    #32
        bls     exp6_popover_width_ready
        ldb     #32
exp6_popover_width_ready
        stb     exp6_popover_width
        lda     exp6_suggestion_count
        sta     exp6_popover_height

        ldd     exp6_input_cursor
        std     exp6_popover_origin
        tfr     b,a
        anda    #$1f
        adda    exp6_popover_width
        cmpa    #32
        bls     exp6_popover_horizontal_ready
        suba    #32
        tfr     a,b
        clra
        std     exp6_popover_scratch
        ldd     exp6_popover_origin
        subd    exp6_popover_scratch
        std     exp6_popover_origin
exp6_popover_horizontal_ready
        ldd     exp6_popover_origin
        andb    #$1f
        stb     exp6_popover_column
        ldd     exp6_popover_origin
        andb    #$e0
        std     exp6_popover_row_base

        lda     exp6_popover_height
        ldb     #32
        mul
        std     exp6_popover_scratch
        ldd     #EXP6_SCREEN+512
        subd    exp6_popover_scratch
        std     exp6_popover_last_row
        cmpd    exp6_popover_row_base
        bhs     exp6_popover_vertical_ready
        ldb     exp6_popover_column
        addb    exp6_popover_last_row+1
        lda     exp6_popover_last_row
        std     exp6_popover_origin
exp6_popover_vertical_ready
        rts

exp6_save_popover_background
        ldx     exp6_popover_origin
        ldy     #exp6_popover_backup
        lda     exp6_popover_height
        sta     exp6_popover_rows_remaining
exp6_save_popover_row
        ldb     exp6_popover_width
exp6_save_popover_cell
        lda     ,x+
        sta     ,y+
        decb
        bne     exp6_save_popover_cell
        ldb     #32
        subb    exp6_popover_width
        abx
        dec     exp6_popover_rows_remaining
        bne     exp6_save_popover_row
        rts

exp6_clear_status_line
        ldx     #EXP6_STATUS_SCREEN
        lda     #$60
        ldb     #16
exp6_clear_status
        sta     ,x+
        decb
        bne     exp6_clear_status
        rts

exp6_show_status
        pshs    u
        lbsr    exp6_clear_status_line
        ldx     #EXP6_STATUS_SCREEN
        puls    u
        lbsr    exp6_print_normal
        rts

; A is a token identifier. Print its zero-terminated text at X.
exp6_print_token_dark
        ldb     #2
        mul
        ldu     #exp6_token_pointers
        leau    d,u
        ldu     ,u
        lbra    exp6_print_dark

; X is a screen address and U is zero-terminated ASCII.
exp6_print_normal
        lda     ,u+
        beq     exp6_print_normal_done
        ora     #$40
        sta     ,x+
        bra     exp6_print_normal
exp6_print_normal_done
        rts

exp6_print_dark
        lda     ,u+
        beq     exp6_print_dark_done
        anda    #$3f
        sta     ,x+
        bra     exp6_print_dark
exp6_print_dark_done
        rts

exp6_message_title
        fcc     "COCO LLM COMPLETION"
        fcb     0
exp6_message_type
        fcc     "TYPE A PHRASE"
        fcb     0
exp6_message_predict
        fcc     "RIGHT/TAB PREDICTS/ACCEPTS"
        fcb     0
exp6_message_choose
        fcc     "UP/DOWN CHOOSE LEFT ERASE CLEAR"
        fcb     0
exp6_message_shape
        fcc     "178 WORDS / 4 WORD CONTEXT"
        fcb     0
exp6_message_unknown
        fcc     "UNKNOWN WORD"
        fcb     0
exp6_message_no_match
        fcc     "NO MATCHING WORD"
        fcb     0
exp6_message_full
        fcc     "INPUT FULL"
        fcb     0

exp6_draw_remaining        rmb     1
exp6_draw_column           rmb     1
exp6_input_cursor          rmb     2
exp6_popover_origin        rmb     2
exp6_popover_width         rmb     1
exp6_popover_height        rmb     1
exp6_popover_column        rmb     1
exp6_popover_row_base      rmb     2
exp6_popover_last_row      rmb     2
exp6_popover_scratch       rmb     2
exp6_popover_rows_remaining rmb    1
exp6_popover_row_index     rmb     1
exp6_popover_backup        rmb     96
