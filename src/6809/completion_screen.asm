; Shared CoCo VDG presentation for completion experiments.
;
; Human-typed text is black-on-green. Model suggestions use the dark reverse
; field, preserving the same visual distinction as the earlier experiments.

COMPLETION_SCREEN             equ     $0400
COMPLETION_INPUT_SCREEN       equ     COMPLETION_SCREEN+64
COMPLETION_INPUT_END          equ     COMPLETION_SCREEN+384
COMPLETION_STATUS_SCREEN      equ     COMPLETION_SCREEN+48

completion_initialize_screen
        ldx     #COMPLETION_SCREEN
        lda     #$60
completion_clear_screen
        sta     ,x+
        cmpx    #COMPLETION_SCREEN+512
        blo     completion_clear_screen

        ldx     #COMPLETION_SCREEN
        lda     #$20
        ldb     #32
completion_fill_title
        sta     ,x+
        decb
        bne     completion_fill_title
        ldx     #COMPLETION_SCREEN
        ldu     #completion_message_title
        lbsr    completion_print_dark

        ldx     #COMPLETION_SCREEN+32
        ldu     #completion_message_type
        lbsr    completion_print_normal
        ldx     #COMPLETION_SCREEN+384
        ldu     #completion_message_predict
        lbsr    completion_print_normal
        ldx     #COMPLETION_SCREEN+416
        ldu     #completion_message_choose
        lbsr    completion_print_normal
        ldx     #COMPLETION_SCREEN+480
        ldu     #COMPLETION_MESSAGE_SHAPE
        lbsr    completion_print_normal
        lbsr    completion_draw_input
        rts

completion_draw_input
        ldx     #COMPLETION_INPUT_SCREEN
        lda     #$60
completion_clear_input_rows
        sta     ,x+
        cmpx    #COMPLETION_INPUT_END
        blo     completion_clear_input_rows
        ldx     #COMPLETION_INPUT_SCREEN
        ldu     #completion_input_buffer
        lda     completion_input_length
        sta     completion_draw_remaining
        clr     completion_draw_column
completion_draw_next
        tst     completion_draw_remaining
        beq     completion_draw_cursor
        lda     ,u
        cmpa    #$20
        beq     completion_draw_separator

        ; Measure the next word before drawing it. If it cannot fit in the
        ; current row, leave the remaining cells blank and start on row two.
        pshs    u
        clrb
completion_measure_word
        lda     ,u+
        beq     completion_word_measured
        cmpa    #$20
        beq     completion_word_measured
        incb
        bra     completion_measure_word
completion_word_measured
        puls    u
        lda     completion_draw_column
        beq     completion_draw_word_character
        pshs    b
        adda    ,s
        puls    b
        cmpa    #32
        bls     completion_draw_word_character
        ldb     #32
        subb    completion_draw_column
        abx
        clr     completion_draw_column

completion_draw_word_character
        cmpx    #COMPLETION_INPUT_END
        bhs     completion_draw_input_done
        lda     ,u+
        ora     #$40
        sta     ,x+
        dec     completion_draw_remaining
        inc     completion_draw_column
        lda     completion_draw_column
        cmpa    #32
        blo     completion_draw_next
        clr     completion_draw_column
        bra     completion_draw_next

completion_draw_separator
        leau    1,u
        dec     completion_draw_remaining
        tst     completion_draw_column
        beq     completion_draw_next            ; wrapped rows need no leading space
        cmpx    #COMPLETION_INPUT_END
        bhs     completion_draw_input_done
        leax    1,x
        inc     completion_draw_column
        lda     completion_draw_column
        cmpa    #32
        blo     completion_draw_next
        clr     completion_draw_column
        bra     completion_draw_next

completion_draw_cursor
        cmpx    #COMPLETION_INPUT_END
        bhs     completion_draw_input_done
        stx     completion_input_cursor
        lda     #$20
        sta     ,x
completion_draw_input_done
        rts

completion_clear_suggestions
        tst     completion_suggestions_visible
        beq     completion_clear_suggestions_done
        ldx     completion_popover_origin
        ldy     #completion_popover_backup
        lda     completion_popover_height
        sta     completion_popover_rows_remaining
completion_restore_popover_row
        ldb     completion_popover_width
completion_restore_popover_cell
        lda     ,y+
        sta     ,x+
        decb
        bne     completion_restore_popover_cell
        ldb     #32
        subb    completion_popover_width
        abx
        dec     completion_popover_rows_remaining
        bne     completion_restore_popover_row
        clr     completion_suggestions_visible
completion_clear_suggestions_done
        rts

completion_draw_suggestions
        tst     completion_suggestions_visible
        bne     completion_paint_popover
        lbsr    completion_prepare_popover
        lbsr    completion_save_popover_background

completion_paint_popover
        ldy     completion_popover_origin
        ldu     #COMPLETION_SUGGESTION_TOKENS
        clr     completion_popover_row_index
        lda     completion_popover_height
        sta     completion_popover_rows_remaining
completion_draw_suggestion
        tfr     y,x
        lda     #$20
        ldb     completion_popover_width
completion_fill_popover_row
        sta     ,x+
        decb
        bne     completion_fill_popover_row

        tfr     y,x
        lda     completion_popover_row_index
        cmpa    completion_selected_suggestion
        bne     completion_draw_popover_word
        lda     #$3e                       ; reverse-field ">"
        sta     ,x
completion_draw_popover_word
        leax    2,x
        lda     ,u+
        pshs    u
        lbsr    completion_print_token_dark
        puls    u
        leay    32,y
        inc     completion_popover_row_index
        dec     completion_popover_rows_remaining
        bne     completion_draw_suggestion

        lda     #1
        sta     completion_suggestions_visible
        rts

; Measure the widest candidate, place the popover at the editor cursor, and
; shift it left or upward when its measured rectangle would cross an edge.
completion_prepare_popover
        clr     completion_popover_width
        ldu     #COMPLETION_SUGGESTION_TOKENS
        lda     completion_suggestion_count
        sta     completion_popover_rows_remaining
completion_measure_candidate
        lda     ,u+
        pshs    u
        ldb     #2
        mul
        ldu     #COMPLETION_TOKEN_POINTERS
        leau    d,u
        ldu     ,u
        clrb
completion_measure_candidate_character
        lda     ,u+
        beq     completion_candidate_measured
        incb
        bra     completion_measure_candidate_character
completion_candidate_measured
        cmpb    completion_popover_width
        bls     completion_candidate_width_ready
        stb     completion_popover_width
completion_candidate_width_ready
        puls    u
        dec     completion_popover_rows_remaining
        bne     completion_measure_candidate

        ldb     completion_popover_width
        addb    #2
        cmpb    #32
        bls     completion_popover_width_ready
        ldb     #32
completion_popover_width_ready
        stb     completion_popover_width
        lda     completion_suggestion_count
        sta     completion_popover_height

        ldd     completion_input_cursor
        std     completion_popover_origin
        tfr     b,a
        anda    #$1f
        adda    completion_popover_width
        cmpa    #32
        bls     completion_popover_horizontal_ready
        suba    #32
        tfr     a,b
        clra
        std     completion_popover_scratch
        ldd     completion_popover_origin
        subd    completion_popover_scratch
        std     completion_popover_origin
completion_popover_horizontal_ready
        ldd     completion_popover_origin
        andb    #$1f
        stb     completion_popover_column
        ldd     completion_popover_origin
        andb    #$e0
        std     completion_popover_row_base

        lda     completion_popover_height
        ldb     #32
        mul
        std     completion_popover_scratch
        ldd     #COMPLETION_SCREEN+512
        subd    completion_popover_scratch
        std     completion_popover_last_row
        cmpd    completion_popover_row_base
        bhs     completion_popover_vertical_ready
        ldb     completion_popover_column
        addb    completion_popover_last_row+1
        lda     completion_popover_last_row
        std     completion_popover_origin
completion_popover_vertical_ready
        rts

completion_save_popover_background
        ldx     completion_popover_origin
        ldy     #completion_popover_backup
        lda     completion_popover_height
        sta     completion_popover_rows_remaining
completion_save_popover_row
        ldb     completion_popover_width
completion_save_popover_cell
        lda     ,x+
        sta     ,y+
        decb
        bne     completion_save_popover_cell
        ldb     #32
        subb    completion_popover_width
        abx
        dec     completion_popover_rows_remaining
        bne     completion_save_popover_row
        rts

completion_clear_status_line
        ldx     #COMPLETION_STATUS_SCREEN
        lda     #$60
        ldb     #16
completion_clear_status
        sta     ,x+
        decb
        bne     completion_clear_status
        rts

completion_show_status
        pshs    u
        lbsr    completion_clear_status_line
        ldx     #COMPLETION_STATUS_SCREEN
        puls    u
        lbsr    completion_print_normal
        rts

; A is a token identifier. Print its zero-terminated text at X.
completion_print_token_dark
        ldb     #2
        mul
        ldu     #COMPLETION_TOKEN_POINTERS
        leau    d,u
        ldu     ,u
        lbra    completion_print_dark

; X is a screen address and U is zero-terminated ASCII.
completion_print_normal
        lda     ,u+
        beq     completion_print_normal_done
        ora     #$40
        sta     ,x+
        bra     completion_print_normal
completion_print_normal_done
        rts

completion_print_dark
        lda     ,u+
        beq     completion_print_dark_done
        anda    #$3f
        sta     ,x+
        bra     completion_print_dark
completion_print_dark_done
        rts

completion_message_title
        fcc     "COCO LLM COMPLETION"
        fcb     0
completion_message_type
        fcc     "TYPE A PHRASE"
        fcb     0
completion_message_predict
        fcc     "RIGHT/TAB PREDICTS/ACCEPTS"
        fcb     0
completion_message_choose
        fcc     "UP/DOWN CHOOSE LEFT ERASE CLEAR"
        fcb     0
completion_message_full
        fcc     "INPUT FULL"
        fcb     0

completion_draw_remaining        rmb     1
completion_draw_column           rmb     1
completion_input_cursor          rmb     2
completion_popover_origin        rmb     2
completion_popover_width         rmb     1
completion_popover_height        rmb     1
completion_popover_column        rmb     1
completion_popover_row_base      rmb     2
completion_popover_last_row      rmb     2
completion_popover_scratch       rmb     2
completion_popover_rows_remaining rmb    1
completion_popover_row_index     rmb     1
completion_popover_backup        rmb     96
