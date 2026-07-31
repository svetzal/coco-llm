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
        lda     #$7e
        sta     ,x
        leax    2,x
        ldu     #exp6_input_buffer
        ldb     exp6_input_length
        beq     exp6_draw_cursor
exp6_draw_input_character
        lda     ,u+
        ora     #$40
        sta     ,x+
        decb
        bne     exp6_draw_input_character
exp6_draw_cursor
        lda     #$20
        sta     ,x
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
