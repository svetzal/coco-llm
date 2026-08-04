; EXP-011 32x16 VDG interface.
;
; Normal inverse-video text represents context supplied by a person. Dark text
; marks model-selected material. Selection also uses > and attention uses *, so
; the states remain distinct without relying on colour alone.

ATT_UI_SCREEN           equ     $0400
ATT_UI_WIDTH            equ     32
ATT_UI_POLCAT           equ     $a000
ATT_UI_KEY_DOWN         equ     $0a
ATT_UI_KEY_CLEAR        equ     $0c
ATT_UI_KEY_ENTER        equ     $0d
ATT_UI_KEY_UP           equ     $5e
ATT_UI_KEY_VIEW         equ     $56
ATT_UI_KEY_EDIT         equ     $45

attention_ui_start
        lbsr    attention_ui_initialize
attention_ui_main_loop
attention_ui_wait
        jsr     [ATT_UI_POLCAT]
        beq     attention_ui_main_loop
        cmpa    #ATT_UI_KEY_UP
        beq     attention_ui_key_up
        cmpa    #ATT_UI_KEY_DOWN
        beq     attention_ui_key_down
        cmpa    #ATT_UI_KEY_ENTER
        beq     attention_ui_key_ask
        cmpa    #ATT_UI_KEY_VIEW
        beq     attention_ui_key_view
        cmpa    #ATT_UI_KEY_EDIT
        beq     attention_ui_key_edit
        cmpa    #ATT_UI_KEY_CLEAR
        beq     attention_ui_key_clear
        bra     attention_ui_main_loop

attention_ui_key_up
        lda     attention_ui_selected_slot
        bne     attention_ui_up_ready
        lda     #ATT_MEMORY_SIZE
attention_ui_up_ready
        deca
        sta     attention_ui_selected_slot
        lbsr    attention_ui_select_query
        clr     attention_ui_has_answer
        lbsr    attention_ui_draw_main
        bra     attention_ui_main_loop

attention_ui_key_down
        inc     attention_ui_selected_slot
        lda     attention_ui_selected_slot
        cmpa    #ATT_MEMORY_SIZE
        blo     attention_ui_down_ready
        clr     attention_ui_selected_slot
attention_ui_down_ready
        lbsr    attention_ui_select_query
        clr     attention_ui_has_answer
        lbsr    attention_ui_draw_main
        bra     attention_ui_main_loop

attention_ui_key_ask
        lbsr    attention_ui_ask
        bra     attention_ui_main_loop

attention_ui_key_edit
        lbsr    attention_ui_edit_start
        bra     attention_ui_main_loop

attention_ui_key_view
        tst     attention_ui_has_answer
        bne     attention_ui_view_ready
        lbsr    attention_ui_ask
attention_ui_view_ready
        lbsr    attention_ui_slow_start
        lbsr    attention_ui_draw_main
        bra     attention_ui_main_loop

attention_ui_key_clear
        clr     attention_ui_has_answer
        lbsr    attention_ui_draw_main
        bra     attention_ui_main_loop

; Edit one value in context RAM. No address in the exported query/key weight
; tables is touched. The UI makes the write and the locked model explicit.
attention_ui_edit_start
        ldx     #attention_memory_values
        ldb     attention_ui_selected_slot
        abx
        lda     ,x
        sta     attention_ui_edit_old_value
        lbsr    attention_ui_draw_edit
attention_ui_edit_loop
attention_ui_edit_wait
        jsr     [ATT_UI_POLCAT]
        beq     attention_ui_edit_loop
        cmpa    #ATT_UI_KEY_CLEAR
        beq     attention_ui_edit_cancel
        cmpa    #$30
        blo     attention_ui_edit_loop
        cmpa    #$37
        bhi     attention_ui_edit_loop
        suba    #$30
        lbsr    attention_ui_apply_edit
        lbsr    attention_ui_draw_edit_done
attention_ui_edit_done_loop
attention_ui_edit_done_wait
        jsr     [ATT_UI_POLCAT]
        beq     attention_ui_edit_done_loop
        cmpa    #ATT_UI_KEY_ENTER
        beq     attention_ui_edit_ask
        cmpa    #ATT_UI_KEY_CLEAR
        bne     attention_ui_edit_done_loop
attention_ui_edit_cancel
        clr     attention_ui_has_answer
        lbsr    attention_ui_draw_main
        rts
attention_ui_edit_ask
        lbsr    attention_ui_ask
        rts

; A is the new value. This routine is also the direct-simulator evidence seam.
attention_ui_apply_edit
        sta     attention_ui_edit_new_value
        ldx     #attention_memory_values
        ldb     attention_ui_selected_slot
        abx
        sta     ,x
        clr     attention_ui_has_answer
        rts

attention_ui_initialize
        clr     attention_ui_context_index
        clr     attention_ui_has_answer
        lda     #1
        sta     attention_ui_selected_slot
        lbsr    attention_ui_load_context
        lbsr    attention_ui_select_query
        lbsr    attention_ui_draw_main
        rts

attention_ui_select_query
        ldx     #attention_memory_keys
        ldb     attention_ui_selected_slot
        abx
        lda     ,x
        sta     attention_query
        rts

attention_ui_ask
        lbsr    attention_predict
        lda     #1
        sta     attention_ui_has_answer
        lbsr    attention_ui_draw_main
        rts

attention_ui_load_context
        lda     attention_ui_context_index
        ldb     #ATT_MEMORY_SIZE*2
        mul
        ldu     #attention_demo_contexts
        leau    d,u
        ldx     #attention_memory_keys
        ldy     #attention_memory_values
        ldb     #ATT_MEMORY_SIZE
attention_ui_copy_record
        lda     ,u+
        sta     ,x+
        lda     ,u+
        sta     ,y+
        decb
        bne     attention_ui_copy_record
        rts

attention_ui_draw_main
        lbsr    attention_ui_clear
        ldx     #ATT_UI_SCREEN
        lbsr    attention_ui_fill_dark_row
        ldx     #ATT_UI_SCREEN
        tst     attention_ui_has_answer
        lbne    attention_ui_draw_answer
        ldu     #attention_ui_facts_title
        lbsr    attention_ui_print_dark

        lda     #1
        lbsr    attention_ui_row_address
        ldu     #attention_ui_model
        lbsr    attention_ui_print_normal
        ldd     #ATT_MODEL_ID
        lbsr    attention_ui_print_hex16
        lda     #1
        lbsr    attention_ui_row_address
        leax    17,x
        ldu     #attention_ui_weights_locked
        lbsr    attention_ui_print_normal

        clr     attention_ui_draw_slot
attention_ui_draw_record
        lda     attention_ui_draw_slot
        adda    #2
        lbsr    attention_ui_row_address
        lda     #$60
        sta     ,x
        lda     attention_ui_draw_slot
        cmpa    attention_ui_selected_slot
        bne     attention_ui_draw_record_text
        lda     #$7e                    ; inverse-field > marks selection
        sta     ,x
attention_ui_draw_record_text
        leax    2,x
        ldy     #attention_memory_keys
        ldb     attention_ui_draw_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_key_normal
attention_ui_draw_code
        lda     attention_ui_draw_slot
        adda    #2
        lbsr    attention_ui_row_address
        leax    18,x
        ldu     #attention_ui_equals_code
        lbsr    attention_ui_print_normal
        ldy     #attention_memory_values
        ldb     attention_ui_draw_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_digit
        inc     attention_ui_draw_slot
        lda     attention_ui_draw_slot
        cmpa    #ATT_MEMORY_SIZE
        blo     attention_ui_draw_record

        lda     #11
        lbsr    attention_ui_row_address
        ldu     #attention_ui_query_label
        lbsr    attention_ui_print_normal
        lda     attention_query
        lbsr    attention_ui_print_key_dark

        lda     #13
        lbsr    attention_ui_row_address
        ldu     #attention_ui_edit_selected
        lbsr    attention_ui_print_normal
        lda     #14
        lbsr    attention_ui_row_address
        ldu     #attention_ui_enter_ask
        lbsr    attention_ui_print_normal
        lda     #15
        lbsr    attention_ui_row_address
        ldu     #attention_ui_choose
        lbsr    attention_ui_print_normal
        rts

attention_ui_draw_answer
        ldu     #attention_ui_answer_title
        lbsr    attention_ui_print_dark

        lda     #2
        lbsr    attention_ui_row_address
        ldu     #attention_ui_query_label
        lbsr    attention_ui_print_normal
        lda     attention_query
        lbsr    attention_ui_print_key_dark

        lda     #4
        lbsr    attention_ui_row_address
        ldu     #attention_ui_searched
        lbsr    attention_ui_print_normal

        lda     #6
        lbsr    attention_ui_row_address
        ldu     #attention_ui_best_match
        lbsr    attention_ui_print_normal
        lda     #7
        lbsr    attention_ui_row_address
        leax    2,x
        lda     #$2a
        sta     ,x+
        lda     #$60
        sta     ,x+
        ldy     #attention_memory_keys
        ldb     attention_best_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_key_dark
        ldu     #attention_ui_equals_code
        lbsr    attention_ui_print_normal
        lda     attention_result
        lbsr    attention_ui_print_digit_dark

        lda     #9
        lbsr    attention_ui_row_address
        ldu     #attention_ui_answer_label
        lbsr    attention_ui_print_normal
        ldu     #attention_ui_code
        lbsr    attention_ui_print_dark
        lda     attention_result
        lbsr    attention_ui_print_digit_dark

        lda     #11
        lbsr    attention_ui_row_address
        ldu     #attention_ui_unchanged
        lbsr    attention_ui_print_normal
        lda     #13
        lbsr    attention_ui_row_address
        ldu     #attention_ui_edit_context
        lbsr    attention_ui_print_normal
        lda     #14
        lbsr    attention_ui_row_address
        ldu     #attention_ui_show_lookup
        lbsr    attention_ui_print_normal
        lda     #15
        lbsr    attention_ui_row_address
        ldu     #attention_ui_back_facts
        lbsr    attention_ui_print_normal
        rts

attention_ui_draw_edit
        lbsr    attention_ui_clear
        ldx     #ATT_UI_SCREEN
        lbsr    attention_ui_fill_dark_row
        ldx     #ATT_UI_SCREEN
        ldu     #attention_ui_edit_title
        lbsr    attention_ui_print_dark
        lda     #2
        lbsr    attention_ui_row_address
        ldu     #attention_ui_selected_record
        lbsr    attention_ui_print_normal
        lda     #4
        lbsr    attention_ui_row_address
        ldu     #attention_ui_before
        lbsr    attention_ui_print_normal
        ldy     #attention_memory_keys
        ldb     attention_ui_selected_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_key_dark
        ldu     #attention_ui_equals_code
        lbsr    attention_ui_print_normal
        lda     attention_ui_edit_old_value
        lbsr    attention_ui_print_digit_dark
        lda     #6
        lbsr    attention_ui_row_address
        ldu     #attention_ui_type_new
        lbsr    attention_ui_print_normal
        lda     #8
        lbsr    attention_ui_row_address
        ldu     #attention_ui_new_code
        lbsr    attention_ui_print_normal
        lda     #$7f
        sta     ,x
        lda     #10
        lbsr    attention_ui_row_address
        ldu     #attention_ui_model_locked
        lbsr    attention_ui_print_normal
        lda     #14
        lbsr    attention_ui_row_address
        ldu     #attention_ui_number_apply
        lbsr    attention_ui_print_normal
        lda     #15
        lbsr    attention_ui_row_address
        ldu     #attention_ui_clear_cancel
        lbsr    attention_ui_print_normal
        rts

attention_ui_draw_edit_done
        lbsr    attention_ui_clear
        ldx     #ATT_UI_SCREEN
        lbsr    attention_ui_fill_dark_row
        ldx     #ATT_UI_SCREEN
        ldu     #attention_ui_changed_title
        lbsr    attention_ui_print_dark
        lda     #2
        lbsr    attention_ui_row_address
        ldu     #attention_ui_you_changed
        lbsr    attention_ui_print_normal
        lda     #4
        lbsr    attention_ui_row_address
        ldu     #attention_ui_before
        lbsr    attention_ui_print_normal
        ldy     #attention_memory_keys
        ldb     attention_ui_selected_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_key_normal
        ldu     #attention_ui_equals_code
        lbsr    attention_ui_print_normal
        lda     attention_ui_edit_old_value
        lbsr    attention_ui_print_digit
        lda     #6
        lbsr    attention_ui_row_address
        ldu     #attention_ui_after
        lbsr    attention_ui_print_normal
        ldy     #attention_memory_keys
        ldb     attention_ui_selected_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_key_dark
        ldu     #attention_ui_equals_code
        lbsr    attention_ui_print_normal
        lda     attention_ui_edit_new_value
        lbsr    attention_ui_print_digit_dark
        lda     #9
        lbsr    attention_ui_row_address
        ldu     #attention_ui_context_edited
        lbsr    attention_ui_print_normal
        lda     #11
        lbsr    attention_ui_row_address
        ldu     #attention_ui_unchanged
        lbsr    attention_ui_print_normal
        lda     #14
        lbsr    attention_ui_row_address
        ldu     #attention_ui_enter_again
        lbsr    attention_ui_print_normal
        lda     #15
        lbsr    attention_ui_row_address
        ldu     #attention_ui_back_facts
        lbsr    attention_ui_print_normal
        rts

; Explicitly paced replay of the scores already calculated by attention_predict.
; The actual inference is not slowed; this view reveals one stored score per
; Enter press and labels itself accordingly.
attention_ui_slow_start
        lbsr    attention_ui_clear
        ldx     #ATT_UI_SCREEN
        lbsr    attention_ui_fill_dark_row
        ldx     #ATT_UI_SCREEN
        ldu     #attention_ui_slow_title
        lbsr    attention_ui_print_dark
        lda     #1
        lbsr    attention_ui_row_address
        ldu     #attention_ui_query_label
        lbsr    attention_ui_print_normal
        lda     attention_query
        lbsr    attention_ui_print_key_dark
        lda     #2
        lbsr    attention_ui_row_address
        ldu     #attention_ui_one_per_enter
        lbsr    attention_ui_print_normal

        clr     attention_ui_draw_slot
attention_ui_slow_draw_record
        lda     attention_ui_draw_slot
        adda    #3
        lbsr    attention_ui_row_address
        leax    2,x
        ldy     #attention_memory_keys
        ldb     attention_ui_draw_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_key_normal
        inc     attention_ui_draw_slot
        lda     attention_ui_draw_slot
        cmpa    #ATT_MEMORY_SIZE
        blo     attention_ui_slow_draw_record

        clr     attention_ui_slow_index
        clr     attention_ui_slow_best_valid
        lda     #12
        lbsr    attention_ui_row_address
        ldu     #attention_ui_best_none
        lbsr    attention_ui_print_normal
        lda     #14
        lbsr    attention_ui_row_address
        ldu     #attention_ui_enter_step
        lbsr    attention_ui_print_normal
        lda     #15
        lbsr    attention_ui_row_address
        ldu     #attention_ui_clear_back
        lbsr    attention_ui_print_normal

attention_ui_slow_loop
attention_ui_slow_wait
        jsr     [ATT_UI_POLCAT]
        beq     attention_ui_slow_loop
        cmpa    #ATT_UI_KEY_CLEAR
        beq     attention_ui_slow_done
        cmpa    #ATT_UI_KEY_VIEW
        beq     attention_ui_slow_done
        cmpa    #ATT_UI_KEY_ENTER
        bne     attention_ui_slow_loop
        lbsr    attention_ui_slow_step
        bra     attention_ui_slow_loop
attention_ui_slow_done
        rts

attention_ui_slow_step
        lda     attention_ui_slow_index
        cmpa    #ATT_MEMORY_SIZE
        bhs     attention_ui_slow_step_done
        ldb     #2
        mul
        ldy     #attention_scores
        leay    d,y
        ldd     ,y
        tst     attention_ui_slow_best_valid
        beq     attention_ui_slow_new_best
        cmpd    attention_ui_slow_best_score
        ble     attention_ui_slow_keep_best
attention_ui_slow_new_best
        std     attention_ui_slow_best_score
        lda     attention_ui_slow_index
        sta     attention_ui_slow_best_slot
        lda     #1
        sta     attention_ui_slow_best_valid
attention_ui_slow_keep_best
        lda     attention_ui_slow_index
        adda    #3
        lbsr    attention_ui_row_address
        leax    18,x
        lda     attention_ui_slow_index
        ldb     #2
        mul
        ldy     #attention_scores
        leay    d,y
        ldd     ,y
        lbsr    attention_ui_print_score
        lbsr    attention_ui_slow_markers
        lbsr    attention_ui_slow_best_line
        inc     attention_ui_slow_index
        lda     attention_ui_slow_index
        cmpa    #ATT_MEMORY_SIZE
        blo     attention_ui_slow_step_done
        lda     #13
        lbsr    attention_ui_row_address
        ldu     #attention_ui_selects
        lbsr    attention_ui_print_normal
        lda     attention_result
        lbsr    attention_ui_print_digit_dark
        lda     #14
        lbsr    attention_ui_clear_row
        ldu     #attention_ui_complete
        lbsr    attention_ui_print_normal
attention_ui_slow_step_done
        rts

attention_ui_slow_markers
        clr     attention_ui_draw_slot
attention_ui_slow_clear_marker
        lda     attention_ui_draw_slot
        adda    #3
        lbsr    attention_ui_row_address
        lda     #$60
        sta     ,x
        inc     attention_ui_draw_slot
        lda     attention_ui_draw_slot
        cmpa    #ATT_MEMORY_SIZE
        blo     attention_ui_slow_clear_marker

        lda     attention_ui_slow_index
        adda    #3
        lbsr    attention_ui_row_address
        lda     #$7e
        sta     ,x
        lda     attention_ui_slow_best_slot
        adda    #3
        lbsr    attention_ui_row_address
        lda     #$2a
        sta     ,x
        rts

attention_ui_slow_best_line
        lda     #12
        lbsr    attention_ui_clear_row
        ldu     #attention_ui_best_so_far
        lbsr    attention_ui_print_normal
        ldy     #attention_memory_keys
        ldb     attention_ui_slow_best_slot
        leay    b,y
        lda     ,y
        lbsr    attention_ui_print_key_dark
        rts

attention_ui_clear
        ldx     #ATT_UI_SCREEN
        lda     #$60
attention_ui_clear_cell
        sta     ,x+
        cmpx    #ATT_UI_SCREEN+512
        blo     attention_ui_clear_cell
        rts

; A is a row number; X returns its screen address.
attention_ui_row_address
        ldb     #ATT_UI_WIDTH
        mul
        ldx     #ATT_UI_SCREEN
        leax    d,x
        rts

; A is a row number; X returns its cleared screen address.
attention_ui_clear_row
        lbsr    attention_ui_row_address
        tfr     x,y
        lda     #$60
        ldb     #ATT_UI_WIDTH
attention_ui_clear_row_cell
        sta     ,y+
        decb
        bne     attention_ui_clear_row_cell
        rts

attention_ui_fill_dark_row
        lda     #$20
        ldb     #ATT_UI_WIDTH
attention_ui_fill_dark_cell
        sta     ,x+
        decb
        bne     attention_ui_fill_dark_cell
        rts

; X is a screen address and U a zero-terminated ASCII string.
attention_ui_print_normal
        lda     ,u+
        beq     attention_ui_print_normal_done
        ora     #$40
        sta     ,x+
        bra     attention_ui_print_normal
attention_ui_print_normal_done
        rts

attention_ui_print_dark
        lda     ,u+
        beq     attention_ui_print_dark_done
        anda    #$3f
        sta     ,x+
        bra     attention_ui_print_dark
attention_ui_print_dark_done
        rts

attention_ui_print_key_normal
        ldb     #2
        mul
        ldu     #attention_ui_key_pointers
        leau    d,u
        ldu     ,u
        lbra    attention_ui_print_normal

attention_ui_print_key_dark
        ldb     #2
        mul
        ldu     #attention_ui_key_pointers
        leau    d,u
        ldu     ,u
        lbra    attention_ui_print_dark

attention_ui_print_digit
        adda    #$30
        ora     #$40
        sta     ,x+
        rts

attention_ui_print_digit_dark
        adda    #$30
        anda    #$3f
        sta     ,x+
        rts

; D is printed as four uppercase hexadecimal digits at X.
attention_ui_print_hex16
        std     attention_ui_hex_value
        lda     attention_ui_hex_value
        lbsr    attention_ui_print_hex8
        lda     attention_ui_hex_value+1
attention_ui_print_hex8
        sta     attention_ui_hex_byte
        lsra
        lsra
        lsra
        lsra
        lbsr    attention_ui_print_nibble
        lda     attention_ui_hex_byte
        anda    #$0f
attention_ui_print_nibble
        cmpa    #10
        blo     attention_ui_hex_digit
        adda    #7
attention_ui_hex_digit
        adda    #$30
        ora     #$40
        sta     ,x+
        rts

; D is a signed score. Print sign plus four fixed decimal digits at X.
attention_ui_print_score
        std     attention_ui_number
        tsta
        bpl     attention_ui_score_positive
        lda     #$6d                    ; inverse-field -
        sta     ,x+
        ldd     attention_ui_number
        coma
        comb
        addd    #1
        std     attention_ui_number
        bra     attention_ui_score_digits
attention_ui_score_positive
        lda     #$6b                    ; inverse-field +
        sta     ,x+
attention_ui_score_digits
        ldu     #attention_ui_decimal_places
        lda     #4
        sta     attention_ui_digits_left
attention_ui_score_next_digit
        clr     attention_ui_digit
        ldd     attention_ui_number
attention_ui_score_subtract
        cmpd    ,u
        blo     attention_ui_score_digit_ready
        subd    ,u
        inc     attention_ui_digit
        bra     attention_ui_score_subtract
attention_ui_score_digit_ready
        std     attention_ui_number
        lda     attention_ui_digit
        lbsr    attention_ui_print_digit
        leau    2,u
        dec     attention_ui_digits_left
        bne     attention_ui_score_next_digit
        rts

attention_ui_decimal_places
        fdb     1000,100,10,1

attention_ui_key_pointers
        fdb     attention_ui_key_amiga
        fdb     attention_ui_key_lisa
        fdb     attention_ui_key_trs80
        fdb     attention_ui_key_archimedes
        fdb     attention_ui_key_pet
        fdb     attention_ui_key_macintosh
        fdb     attention_ui_key_spectrum
        fdb     attention_ui_key_atari_st
        fdb     attention_ui_key_commodore64
        fdb     attention_ui_key_apple_ii
        fdb     attention_ui_key_tandy100
        fdb     attention_ui_key_bbc_micro
        fdb     attention_ui_key_zx81
        fdb     attention_ui_key_acorn
        fdb     attention_ui_key_color_computer
        fdb     attention_ui_key_sinclair

attention_ui_key_amiga          fcc     "AMIGA"
                                fcb     0
attention_ui_key_lisa           fcc     "LISA"
                                fcb     0
attention_ui_key_trs80          fcc     "TRS-80"
                                fcb     0
attention_ui_key_archimedes     fcc     "ARCHIMEDES"
                                fcb     0
attention_ui_key_pet            fcc     "PET"
                                fcb     0
attention_ui_key_macintosh      fcc     "MACINTOSH"
                                fcb     0
attention_ui_key_spectrum       fcc     "SPECTRUM"
                                fcb     0
attention_ui_key_atari_st       fcc     "ATARI ST"
                                fcb     0
attention_ui_key_commodore64    fcc     "COMMODORE 64"
                                fcb     0
attention_ui_key_apple_ii       fcc     "APPLE II"
                                fcb     0
attention_ui_key_tandy100       fcc     "TANDY 100"
                                fcb     0
attention_ui_key_bbc_micro      fcc     "BBC MICRO"
                                fcb     0
attention_ui_key_zx81           fcc     "ZX81"
                                fcb     0
attention_ui_key_acorn          fcc     "ACORN"
                                fcb     0
attention_ui_key_color_computer fcc     "COLOR COMPUTER"
                                fcb     0
attention_ui_key_sinclair       fcc     "SINCLAIR"
                                fcb     0

attention_ui_facts_title        fcc     "1. TEMPORARY CONTEXT IN RAM"
                                fcb     0
attention_ui_changed_title      fcc     "CONTEXT CHANGED - NO TRAINING"
                                fcb     0
attention_ui_answer_title       fcc     "2. ANSWER FROM CONTEXT"
                                fcb     0
attention_ui_model              fcc     "MODEL "
                                fcb     0
attention_ui_weights_locked     fcc     "WEIGHTS LOCKED"
                                fcb     0
attention_ui_code               fcc     "CODE "
                                fcb     0
attention_ui_equals_code        fcc     "= CODE "
                                fcb     0
attention_ui_query_label        fcc     "QUESTION: "
                                fcb     0
attention_ui_answer_label       fcc     "ANSWER: "
                                fcb     0
attention_ui_searched           fcc     "SEARCHED 8 CONTEXT RECORDS"
                                fcb     0
attention_ui_best_match         fcc     "BEST MATCH:"
                                fcb     0
attention_ui_unchanged          fcc     "MODEL 751B DID NOT CHANGE"
                                fcb     0
attention_ui_enter_ask          fcc     "ENTER: ASK THIS QUESTION"
                                fcb     0
attention_ui_choose             fcc     "UP/DOWN: CHOOSE ANOTHER"
                                fcb     0
attention_ui_edit_selected      fcc     "E: EDIT SELECTED RECORD"
                                fcb     0
attention_ui_edit_context       fcc     "E: CHANGE THE CONTEXT"
                                fcb     0
attention_ui_show_lookup        fcc     "V: SHOW HOW IT LOOKED"
                                fcb     0
attention_ui_back_facts         fcc     "CLEAR: BACK TO CONTEXT"
                                fcb     0
attention_ui_edit_title         fcc     "EDIT CONTEXT - NOT TRAINING"
                                fcb     0
attention_ui_selected_record    fcc     "SELECTED CONTEXT RECORD"
                                fcb     0
attention_ui_before             fcc     "BEFORE: "
                                fcb     0
attention_ui_after              fcc     "AFTER:  "
                                fcb     0
attention_ui_type_new           fcc     "TYPE A NEW CODE (0-7)"
                                fcb     0
attention_ui_new_code           fcc     "NEW CODE: "
                                fcb     0
attention_ui_model_locked       fcc     "MODEL 751B IS LOCKED"
                                fcb     0
attention_ui_number_apply       fcc     "NUMBER: EDIT CONTEXT"
                                fcb     0
attention_ui_clear_cancel       fcc     "CLEAR: CANCEL"
                                fcb     0
attention_ui_you_changed        fcc     "YOU CHANGED THIS RECORD"
                                fcb     0
attention_ui_context_edited     fcc     "CONTEXT MEMORY WAS EDITED"
                                fcb     0
attention_ui_enter_again        fcc     "ENTER: ASK AGAIN"
                                fcb     0
attention_ui_slow_title         fcc     "HOW ATTENTION SEARCHED"
                                fcb     0
attention_ui_one_per_enter      fcc     "ONE RECORD PER ENTER"
                                fcb     0
attention_ui_best_none          fcc     "BEST SO FAR -"
                                fcb     0
attention_ui_best_so_far        fcc     "BEST SO FAR "
                                fcb     0
attention_ui_enter_step         fcc     "ENTER STEP"
                                fcb     0
attention_ui_clear_back         fcc     "CLEAR BACK"
                                fcb     0
attention_ui_selects            fcc     "SELECTS CODE "
                                fcb     0
attention_ui_complete           fcc     "ATTENTION COMPLETE"
                                fcb     0

attention_ui_context_index      rmb     1
attention_ui_selected_slot      rmb     1
attention_ui_has_answer         rmb     1
attention_ui_draw_slot          rmb     1
attention_ui_slow_index         rmb     1
attention_ui_slow_best_valid    rmb     1
attention_ui_slow_best_slot     rmb     1
attention_ui_slow_best_score    rmb     2
attention_ui_hex_value          rmb     2
attention_ui_hex_byte           rmb     1
attention_ui_number             rmb     2
attention_ui_digit              rmb     1
attention_ui_digits_left        rmb     1
attention_ui_edit_old_value     rmb     1
attention_ui_edit_new_value     rmb     1
