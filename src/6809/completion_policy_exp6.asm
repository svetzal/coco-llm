; EXP-006 completion policy.
;
; This is the lesson-specific part of the workbench: four space-delimited
; context words, an optional lexical prefix, the EXP-006 model layout, and a
; trailing space after an accepted word. The shared editor and VDG screen know
; none of these rules.

EXP6_POLCAT     equ     $a000

completion_policy_initialize
        clr     exp6_prefix_length
        rts

; EXP-006 runs with BASIC ROM visible, so its keyboard adapter is just POLCAT.
completion_policy_read_key
        jsr     [EXP6_POLCAT]
        rts

; Return non-zero in A for the characters accepted by the EXP-006 vocabulary.
; The caller preserves the original character while consulting this hook.
completion_policy_character_allowed
        cmpa    #$20
        beq     exp6_character_allowed
        cmpa    #$30
        blo     exp6_character_rejected
        cmpa    #$39
        bls     exp6_character_allowed
        cmpa    #$41
        blo     exp6_character_rejected
        cmpa    #$5a
        bhi     exp6_character_rejected
exp6_character_allowed
        lda     #1
        rts
exp6_character_rejected
        clra
        rts

completion_policy_append_typed_character
        lbra    completion_append_character

completion_policy_predict_input
        lbsr    exp6_parse_input
        bcs     exp6_predict_done
        ldd     #EXP6_MODEL_BASE
        std     exp6_position_base
        lbsr    exp6_predict_top_three
        tst     exp6_top_one_token
        beq     exp6_predict_no_match
        lda     #3
        sta     completion_suggestion_count
        tst     exp6_top_three_token
        bne     exp6_suggestion_count_ready
        dec     completion_suggestion_count
        tst     exp6_top_two_token
        bne     exp6_suggestion_count_ready
        dec     completion_suggestion_count
exp6_suggestion_count_ready
        clr     completion_selected_suggestion
        lbsr    completion_draw_suggestions
        rts
exp6_predict_no_match
        lbsr    completion_clear_suggestions
        ldu     #exp6_message_no_match
        lbsr    completion_show_status
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
        ldx     #completion_input_buffer
        stx     exp6_word_pointer
        clr     exp6_word_length
        ldb     completion_input_length
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
        lbsr    completion_show_status
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

completion_policy_apply_suggestion
        ldx     #exp6_top_one_token
        ldb     completion_selected_suggestion
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
        lbsr    completion_append_character
        bcs     exp6_accept_done
        bra     exp6_accept_suffix
exp6_accept_space
        lda     #$20
        lbsr    completion_append_character
exp6_accept_done
        lbsr    completion_hide_suggestions
        lbsr    completion_draw_input
        lbsr    completion_clear_status_line
        rts

exp6_message_shape
        fcc     "178 WORDS / 4 WORD CONTEXT"
        fcb     0
exp6_message_unknown
        fcc     "UNKNOWN WORD"
        fcb     0
exp6_message_no_match
        fcc     "NO MATCHING WORD"
        fcb     0

exp6_word_pointer       rmb     2
exp6_word_length        rmb     1
exp6_lookup_word        rmb     2
exp6_lookup_length      rmb     1
exp6_lookup_token       rmb     1
