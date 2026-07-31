; Interactive EXP-006 editor and completion controller.
;
; The original CoCo keyboard has no key labelled Tab: its Right Arrow returns
; character code 9, the same control code conventionally used for Tab. The UI
; therefore names both meanings while remaining usable on physical hardware.

EXP6_POLCAT       equ     $A000
EXP6_KEY_LEFT     equ     $08
EXP6_KEY_RIGHT    equ     $09
EXP6_KEY_DOWN     equ     $0a
EXP6_KEY_CLEAR    equ     $0c
EXP6_KEY_ENTER    equ     $0d
EXP6_KEY_UP       equ     $5e
EXP6_INPUT_LIMIT  equ     255

exp6_show_workbench
        clr     exp6_input_length
        clr     exp6_suggestions_visible
        clr     exp6_selected_suggestion
        clr     exp6_prefix_length
        lbsr    exp6_initialize_screen
exp6_input_loop
        jsr     [EXP6_POLCAT]
        beq     exp6_input_loop
        cmpa    #EXP6_KEY_RIGHT
        lbeq    exp6_key_complete
        cmpa    #EXP6_KEY_ENTER
        lbeq    exp6_key_enter
        cmpa    #EXP6_KEY_UP
        lbeq    exp6_key_up
        cmpa    #EXP6_KEY_DOWN
        lbeq    exp6_key_down
        cmpa    #EXP6_KEY_LEFT
        lbeq    exp6_key_left
        cmpa    #EXP6_KEY_CLEAR
        lbeq    exp6_key_clear
        cmpa    #$20
        lbeq    exp6_key_character
        cmpa    #$30
        lblo    exp6_input_loop
        cmpa    #$39
        lbls    exp6_key_character
        cmpa    #$41
        lblo    exp6_input_loop
        cmpa    #$5a
        lbhi    exp6_input_loop

exp6_key_character
        pshs    a
        lbsr    exp6_hide_suggestions
        puls    a
        cmpa    #$20
        bne     exp6_append_typed_character
        ldb     exp6_input_length
        beq     exp6_input_loop
        ldx     #exp6_input_buffer-1
        abx
        cmpa    ,x
        beq     exp6_input_loop
exp6_append_typed_character
        lbsr    exp6_append_character
        lbcs    exp6_input_loop
        lbsr    exp6_draw_input
        lbsr    exp6_clear_status_line
        lbra    exp6_input_loop

exp6_key_left
        lbsr    exp6_hide_suggestions
        ldb     exp6_input_length
        lbeq    exp6_input_loop
        decb
        stb     exp6_input_length
        ldx     #exp6_input_buffer
        abx
        clr     ,x
        lbsr    exp6_draw_input
        lbsr    exp6_clear_status_line
        lbra    exp6_input_loop

exp6_key_clear
        clr     exp6_input_length
        clr     exp6_input_buffer
        lbsr    exp6_hide_suggestions
        lbsr    exp6_draw_input
        lbsr    exp6_clear_status_line
        lbra    exp6_input_loop

exp6_key_complete
        tst     exp6_suggestions_visible
        lbne    exp6_accept_suggestion
        lbsr    exp6_predict_input
        lbra    exp6_input_loop

exp6_key_enter
        tst     exp6_suggestions_visible
        lbne    exp6_accept_suggestion
        lbsr    exp6_predict_input
        lbra    exp6_input_loop

exp6_key_up
        tst     exp6_suggestions_visible
        lbeq    exp6_input_loop
        lda     exp6_selected_suggestion
        bne     exp6_key_up_decrement
        lda     exp6_suggestion_count
exp6_key_up_decrement
        deca
        sta     exp6_selected_suggestion
        lbsr    exp6_draw_suggestions
        lbra    exp6_input_loop

exp6_key_down
        tst     exp6_suggestions_visible
        lbeq    exp6_input_loop
        inc     exp6_selected_suggestion
        lda     exp6_selected_suggestion
        cmpa    exp6_suggestion_count
        blo     exp6_key_down_ready
        clr     exp6_selected_suggestion
exp6_key_down_ready
        lbsr    exp6_draw_suggestions
        lbra    exp6_input_loop

exp6_predict_input
        lbsr    exp6_parse_input
        bcs     exp6_predict_done
        ldd     #EXP6_MODEL_BASE
        std     exp6_position_base
        lbsr    exp6_predict_top_three
        tst     exp6_top_one_token
        beq     exp6_predict_no_match
        lda     #3
        sta     exp6_suggestion_count
        tst     exp6_top_three_token
        bne     exp6_suggestion_count_ready
        dec     exp6_suggestion_count
        tst     exp6_top_two_token
        bne     exp6_suggestion_count_ready
        dec     exp6_suggestion_count
exp6_suggestion_count_ready
        clr     exp6_selected_suggestion
        lbsr    exp6_draw_suggestions
        rts
exp6_predict_no_match
        lbsr    exp6_clear_suggestions
        ldu     #exp6_message_no_match
        lbsr    exp6_show_status
exp6_predict_done
        rts

; Rebuild the four-token context from complete, space-terminated words. The
; final unterminated word becomes a prefix used to mask output candidates.
exp6_parse_input
        clr     exp6_current_context
        clr     exp6_current_context+1
        clr     exp6_current_context+2
        clr     exp6_current_context+3
        clr     exp6_prefix_length
        ldx     #exp6_input_buffer
        stx     exp6_word_pointer
        clr     exp6_word_length
        ldb     exp6_input_length
        beq     exp6_parse_finished
exp6_parse_character
        lda     ,x+
        cmpa    #$20
        bne     exp6_parse_word_character
        tst     exp6_word_length
        beq     exp6_parse_next
        pshs    x,b
        ldx     exp6_word_pointer
        ldb     exp6_word_length
        lbsr    exp6_find_exact_token
        puls    x,b
        tsta
        beq     exp6_parse_unknown
        pshs    a
        lda     exp6_current_context+1
        sta     exp6_current_context
        lda     exp6_current_context+2
        sta     exp6_current_context+1
        lda     exp6_current_context+3
        sta     exp6_current_context+2
        puls    a
        sta     exp6_current_context+3
        stx     exp6_word_pointer
        clr     exp6_word_length
        bra     exp6_parse_next
exp6_parse_word_character
        inc     exp6_word_length
exp6_parse_next
        decb
        bne     exp6_parse_character
exp6_parse_finished
        ldd     exp6_word_pointer
        std     exp6_prefix_pointer
        lda     exp6_word_length
        sta     exp6_prefix_length
        andcc   #$fe
        rts
exp6_parse_unknown
        ldu     #exp6_message_unknown
        lbsr    exp6_show_status
        orcc    #$01
        rts

; Compare a word at X, length B, with every lexical vocabulary entry.
; Return its token identifier in A, or zero when no exact match exists.
exp6_find_exact_token
        stx     exp6_lookup_word
        stb     exp6_lookup_length
        lda     #1
        sta     exp6_lookup_token
exp6_lookup_candidate
        lda     exp6_lookup_token
        ldb     #2
        mul
        ldu     #exp6_token_pointers
        leau    d,u
        ldu     ,u
        ldx     exp6_lookup_word
        ldb     exp6_lookup_length
exp6_lookup_character
        lda     ,x+
        cmpa    ,u+
        bne     exp6_lookup_next
        decb
        bne     exp6_lookup_character
        tst     ,u
        bne     exp6_lookup_next
        lda     exp6_lookup_token
        rts
exp6_lookup_next
        inc     exp6_lookup_token
        lda     exp6_lookup_token
        cmpa    #EXP6_VOCAB_SIZE
        blo     exp6_lookup_candidate
        clra
        rts

exp6_accept_suggestion
        lbsr    exp6_apply_suggestion
        lbra    exp6_input_loop

exp6_apply_suggestion
        ldx     #exp6_top_one_token
        ldb     exp6_selected_suggestion
        abx
        lda     ,x
        ldb     #2
        mul
        ldu     #exp6_token_pointers
        leau    d,u
        ldu     ,u
        ldb     exp6_prefix_length
        beq     exp6_accept_suffix
exp6_skip_accepted_prefix
        leau    1,u
        decb
        bne     exp6_skip_accepted_prefix
exp6_accept_suffix
        lda     ,u+
        beq     exp6_accept_space
        lbsr    exp6_append_character
        bcs     exp6_accept_done
        bra     exp6_accept_suffix
exp6_accept_space
        lda     #$20
        lbsr    exp6_append_character
exp6_accept_done
        lbsr    exp6_hide_suggestions
        lbsr    exp6_draw_input
        lbsr    exp6_clear_status_line
        rts

; Append A to the editor buffer. Carry reports a full buffer.
exp6_append_character
        ldb     exp6_input_length
        cmpb    #EXP6_INPUT_LIMIT
        bhs     exp6_append_full
        ldx     #exp6_input_buffer
        abx
        sta     ,x+
        clr     ,x
        inc     exp6_input_length
        andcc   #$fe
        rts
exp6_append_full
        ldu     #exp6_message_full
        lbsr    exp6_show_status
        orcc    #$01
        rts

exp6_hide_suggestions
        tst     exp6_suggestions_visible
        beq     exp6_hide_done
        lbsr    exp6_clear_suggestions
exp6_hide_done
        rts

exp6_input_buffer          rmb     EXP6_INPUT_LIMIT+1
exp6_input_length          rmb     1
exp6_word_pointer          rmb     2
exp6_word_length           rmb     1
exp6_lookup_word           rmb     2
exp6_lookup_length         rmb     1
exp6_lookup_token          rmb     1
exp6_selected_suggestion   rmb     1
exp6_suggestion_count      rmb     1
exp6_suggestions_visible   rmb     1
