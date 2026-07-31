; CoCo VDG presentation for the EXP-006 completion workbench.
;
; Human-typed text is black-on-green. Model suggestions use the dark reverse
; field, preserving the same visual distinction as the earlier experiments.

EXP6_SCREEN             equ     $0400
EXP6_INPUT_SCREEN       equ     EXP6_SCREEN+64
EXP6_SUGGESTION_SCREEN  equ     EXP6_SCREEN+192
EXP6_STATUS_SCREEN      equ     EXP6_SCREEN+320

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
        ldx     #EXP6_SCREEN+160
        ldu     #exp6_message_suggestions
        lbsr    exp6_print_normal
        ldx     #EXP6_SCREEN+480
        ldu     #exp6_message_shape
        lbsr    exp6_print_normal
        lbsr    exp6_draw_input
        rts

exp6_draw_input
        ldx     #EXP6_INPUT_SCREEN
        lda     #$60
        ldb     #64
exp6_clear_input_rows
        sta     ,x+
        decb
        bne     exp6_clear_input_rows
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
        cmpx    #EXP6_INPUT_SCREEN+64
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
        cmpx    #EXP6_INPUT_SCREEN+64
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
        cmpx    #EXP6_INPUT_SCREEN+64
        bhs     exp6_draw_input_done
        lda     #$20
        sta     ,x
exp6_draw_input_done
        rts

exp6_clear_suggestions
        ldx     #EXP6_SUGGESTION_SCREEN
        lda     #$60
        ldb     #96
exp6_clear_suggestion_rows
        sta     ,x+
        decb
        bne     exp6_clear_suggestion_rows
        clr     exp6_suggestions_visible
        rts

exp6_draw_suggestions
        ldx     #EXP6_SUGGESTION_SCREEN
        stx     exp6_suggestion_row
        ldu     #exp6_top_one_token
        lda     #3
        sta     exp6_suggestions_remaining
exp6_draw_suggestion
        ldx     exp6_suggestion_row
        lda     #$60
        sta     ,x                       ; clear any previous selection marker
        leax    2,x
        lda     ,u+
        beq     exp6_suggestion_blank
        pshs    u
        lbsr    exp6_print_token_dark
        puls    u
exp6_suggestion_blank
        ldd     exp6_suggestion_row
        addd    #32
        std     exp6_suggestion_row
        dec     exp6_suggestions_remaining
        bne     exp6_draw_suggestion

        lda     exp6_selected_suggestion
        ldb     #32
        mul
        addd    #EXP6_SUGGESTION_SCREEN
        tfr     d,x
        lda     #$7e
        sta     ,x
        lda     #1
        sta     exp6_suggestions_visible
        rts

exp6_clear_status_line
        ldx     #EXP6_STATUS_SCREEN
        lda     #$60
        ldb     #32
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
exp6_message_suggestions
        fcc     "SUGGESTIONS"
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

exp6_suggestion_row        rmb     2
exp6_suggestions_remaining rmb     1
exp6_draw_remaining        rmb     1
exp6_draw_column           rmb     1
