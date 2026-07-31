; EXP-007 sentence-completion policy.
;
; The shared workbench delegates here for the rules introduced by this lesson:
; five-token context, punctuation tokens, punctuation-aware spacing, the
; 32 KiB EXP-007 model layout, and keyboard polling while BASIC ROM is hidden.

EXP7_POLCAT         equ     $a000
EXP7_SAM_ROM_MAP    equ     $ffde
EXP7_SAM_ALL_RAM    equ     $ffdf

completion_policy_initialize
        clr     exp7_prefix_length
        orcc    #$50
        sta     EXP7_SAM_ALL_RAM
        ifndef  EXP7_UI_TEST
        lbsr    exp7_unpack_model
        endc
        rts

; The DECB loader runs while map Type 0 is active, where addresses above
; $7FFF select the current 32 KiB page rather than contiguous high RAM. The
; packed model therefore travels below $8000 with the program. Once Type 1 is
; active, expand two signed Q2.2 nibbles per source byte into contiguous signed
; bytes at EXP7_MODEL_BASE.
exp7_unpack_model
        ldx     #exp7_packed_model
        ldu     #EXP7_MODEL_BASE
exp7_unpack_pair
        lda     ,x+
        sta     exp7_packed_byte
        lsra
        lsra
        lsra
        lsra
        cmpa    #8
        blo     exp7_unpack_high_ready
        ora     #$f0
exp7_unpack_high_ready
        sta     ,u+
        cmpu    #EXP7_MODEL_BASE+EXP7_PARAM_COUNT
        bhs     exp7_unpack_done

        lda     exp7_packed_byte
        anda    #$0f
        cmpa    #8
        blo     exp7_unpack_low_ready
        ora     #$f0
exp7_unpack_low_ready
        sta     ,u+
        cmpu    #EXP7_MODEL_BASE+EXP7_PARAM_COUNT
        blo     exp7_unpack_pair
exp7_unpack_done
        rts

; POLCAT lives in BASIC ROM and expects the normal interrupt-driven ROM
; environment. Restore that map and interrupt state only for the call. Mask
; interrupts again before exposing RAM at the ROM addresses.
completion_policy_read_key
        sta     EXP7_SAM_ROM_MAP
        andcc   #$af
        jsr     [EXP7_POLCAT]
        pshs    a
        orcc    #$50
        sta     EXP7_SAM_ALL_RAM
        puls    a
        rts

; Return non-zero in A for letters, digits, spaces, and the punctuation tokens
; represented in the EXP-007 corpus.
completion_policy_character_allowed
        cmpa    #$20
        beq     exp7_character_allowed
        cmpa    #$21
        beq     exp7_character_allowed
        cmpa    #$2c
        beq     exp7_character_allowed
        cmpa    #$2e
        beq     exp7_character_allowed
        cmpa    #$3a
        beq     exp7_character_allowed
        cmpa    #$3b
        beq     exp7_character_allowed
        cmpa    #$3f
        beq     exp7_character_allowed
        cmpa    #$30
        blo     exp7_character_rejected
        cmpa    #$39
        bls     exp7_character_allowed
        cmpa    #$41
        blo     exp7_character_rejected
        cmpa    #$5a
        bhi     exp7_character_rejected
exp7_character_allowed
        lda     #1
        rts
exp7_character_rejected
        clra
        rts

; Model-accepted words leave a space ready for the next word. If the audience
; types punctuation at that point, remove the pending space so punctuation
; remains attached to the preceding word.
completion_policy_append_typed_character
        cmpa    #$21
        beq     exp7_append_typed_punctuation
        cmpa    #$2c
        beq     exp7_append_typed_punctuation
        cmpa    #$2e
        beq     exp7_append_typed_punctuation
        cmpa    #$3a
        beq     exp7_append_typed_punctuation
        cmpa    #$3b
        beq     exp7_append_typed_punctuation
        cmpa    #$3f
        bne     exp7_append_typed_ready
exp7_append_typed_punctuation
        pshs    a
        lbsr    exp7_remove_trailing_space
        puls    a
exp7_append_typed_ready
        lbra    completion_append_character

completion_policy_predict_input
        lbsr    exp7_parse_input
        bcs     exp7_predict_done
        ldd     #EXP7_MODEL_BASE
        std     exp7_position_base
        lbsr    exp7_predict_top_three
        lda     exp7_top_one_token
        cmpa    #$ff
        beq     exp7_predict_no_match
        lda     #3
        sta     completion_suggestion_count
        lda     exp7_top_three_token
        cmpa    #$ff
        bne     exp7_suggestion_count_ready
        dec     completion_suggestion_count
        lda     exp7_top_two_token
        cmpa    #$ff
        bne     exp7_suggestion_count_ready
        dec     completion_suggestion_count
exp7_suggestion_count_ready
        clr     completion_selected_suggestion
        lbsr    completion_draw_suggestions
        rts
exp7_predict_no_match
        lbsr    completion_clear_suggestions
        ldu     #exp7_message_no_match
        lbsr    completion_show_status
exp7_predict_done
        rts

; Rebuild the five-token context. Spaces terminate words; punctuation
; terminates any pending word and is then pushed as its own token. Only a final
; unfinished word becomes the prefix used to mask output candidates.
exp7_parse_input
        clr     exp7_current_context
        clr     exp7_current_context+1
        clr     exp7_current_context+2
        clr     exp7_current_context+3
        clr     exp7_current_context+4
        clr     exp7_prefix_length
        ldx     #completion_input_buffer
        stx     exp7_word_pointer
        clr     exp7_word_length
        ldb     completion_input_length
        beq     exp7_parse_finished
exp7_parse_character
        lda     ,x+
        cmpa    #$20
        beq     exp7_parse_space
        lbsr    exp7_is_punctuation
        bne     exp7_parse_punctuation
        inc     exp7_word_length
        bra     exp7_parse_next

exp7_parse_space
        tst     exp7_word_length
        beq     exp7_parse_set_next_word
        pshs    x,b
        lbsr    exp7_finish_word
        puls    x,b
        bcs     exp7_parse_unknown
exp7_parse_set_next_word
        stx     exp7_word_pointer
        clr     exp7_word_length
        bra     exp7_parse_next

exp7_parse_punctuation
        tst     exp7_word_length
        beq     exp7_parse_punctuation_token
        pshs    x,b
        lbsr    exp7_finish_word
        puls    x,b
        bcs     exp7_parse_unknown
exp7_parse_punctuation_token
        pshs    x,b
        leax    -1,x
        ldb     #1
        lbsr    exp7_find_exact_token
        tsta
        beq     exp7_parse_bad_punctuation
        lbsr    exp7_push_token
        puls    x,b
        stx     exp7_word_pointer
        clr     exp7_word_length
        bra     exp7_parse_next
exp7_parse_bad_punctuation
        puls    x,b
        bra     exp7_parse_unknown

exp7_parse_next
        decb
        bne     exp7_parse_character
exp7_parse_finished
        ldd     exp7_word_pointer
        std     exp7_prefix_pointer
        lda     exp7_word_length
        sta     exp7_prefix_length
        andcc   #$fe
        rts
exp7_parse_unknown
        ldu     #exp7_message_unknown
        lbsr    completion_show_status
        orcc    #$01
        rts

; Finish the pending word and push its identifier. Carry reports an unknown
; word. X and B are owned by the caller around this helper.
exp7_finish_word
        ldx     exp7_word_pointer
        ldb     exp7_word_length
        lbsr    exp7_find_exact_token
        tsta
        beq     exp7_finish_word_unknown
        lbsr    exp7_push_token
        andcc   #$fe
        rts
exp7_finish_word_unknown
        orcc    #$01
        rts

; A is the token to append to the rolling five-token context.
exp7_push_token
        pshs    a
        lda     exp7_current_context+1
        sta     exp7_current_context
        lda     exp7_current_context+2
        sta     exp7_current_context+1
        lda     exp7_current_context+3
        sta     exp7_current_context+2
        lda     exp7_current_context+4
        sta     exp7_current_context+3
        puls    a
        sta     exp7_current_context+4
        rts

; Return non-zero in A when A is one of the six punctuation characters.
exp7_is_punctuation
        cmpa    #$21
        beq     exp7_is_punctuation_yes
        cmpa    #$2c
        beq     exp7_is_punctuation_yes
        cmpa    #$2e
        beq     exp7_is_punctuation_yes
        cmpa    #$3a
        beq     exp7_is_punctuation_yes
        cmpa    #$3b
        beq     exp7_is_punctuation_yes
        cmpa    #$3f
        beq     exp7_is_punctuation_yes
        clra
        rts
exp7_is_punctuation_yes
        lda     #1
        rts

; Compare a token at X, length B, with every lexical vocabulary entry.
; Return its token identifier in A, or zero when no exact match exists.
exp7_find_exact_token
        stx     exp7_lookup_word
        stb     exp7_lookup_length
        lda     #1
        sta     exp7_lookup_token
exp7_lookup_candidate
        lda     exp7_lookup_token
        ldb     #2
        mul
        ldu     #exp7_token_pointers
        leau    d,u
        ldu     ,u
        ldx     exp7_lookup_word
        ldb     exp7_lookup_length
exp7_lookup_character
        lda     ,x+
        cmpa    ,u+
        bne     exp7_lookup_next
        decb
        bne     exp7_lookup_character
        tst     ,u
        bne     exp7_lookup_next
        lda     exp7_lookup_token
        rts
exp7_lookup_next
        inc     exp7_lookup_token
        lda     exp7_lookup_token
        cmpa    #EXP7_VOCAB_SIZE
        blo     exp7_lookup_candidate
        clra
        rts

completion_policy_apply_suggestion
        ldx     #exp7_top_one_token
        ldb     completion_selected_suggestion
        abx
        lda     ,x
        sta     exp7_accepted_token
        beq     exp7_accept_end
        ldb     #2
        mul
        ldu     #exp7_token_pointers
        leau    d,u
        ldu     ,u

        lda     exp7_accepted_token
        lbsr    exp7_token_is_punctuation
        bne     exp7_accept_punctuation

        ldb     exp7_prefix_length
        beq     exp7_accept_word_suffix
exp7_skip_accepted_prefix
        leau    1,u
        decb
        bne     exp7_skip_accepted_prefix
exp7_accept_word_suffix
        lda     ,u+
        beq     exp7_accept_word_space
        lbsr    completion_append_character
        bcs     exp7_accept_done
        bra     exp7_accept_word_suffix
exp7_accept_word_space
        lda     #$20
        lbsr    completion_append_character
        bra     exp7_accept_done

exp7_accept_punctuation
        lbsr    exp7_remove_trailing_space
        lda     exp7_accepted_token
        ldb     #2
        mul
        ldu     #exp7_token_pointers
        leau    d,u
        ldu     ,u
        lda     ,u
        lbsr    completion_append_character
        bcs     exp7_accept_done
        lda     #$20
        lbsr    completion_append_character
        bra     exp7_accept_done

; Token zero is the model's visible stop decision. It changes no text, removes
; any pending model-supplied separator, and explains the action in the status
; area instead of silently substituting the second-ranked token.
exp7_accept_end
        lbsr    exp7_remove_trailing_space
        lbsr    completion_hide_suggestions
        lbsr    completion_draw_input
        ldu     #exp7_message_end
        lbsr    completion_show_status
        rts

exp7_accept_done
        lbsr    completion_hide_suggestions
        lbsr    completion_draw_input
        lbsr    completion_clear_status_line
        rts

; Remove one pending separator from the editable buffer, if present.
exp7_remove_trailing_space
        ldb     completion_input_length
        beq     exp7_remove_space_done
        ldx     #completion_input_buffer-1
        abx
        lda     ,x
        cmpa    #$20
        bne     exp7_remove_space_done
        clr     ,x
        dec     completion_input_length
exp7_remove_space_done
        rts

; A is a token identifier. Return non-zero for punctuation tokens.
exp7_token_is_punctuation
        cmpa    #EXP7_TOKEN_PERIOD
        beq     exp7_token_is_punctuation_yes
        cmpa    #EXP7_TOKEN_COMMA
        beq     exp7_token_is_punctuation_yes
        cmpa    #EXP7_TOKEN_QUESTION
        beq     exp7_token_is_punctuation_yes
        cmpa    #EXP7_TOKEN_EXCLAMATION
        beq     exp7_token_is_punctuation_yes
        cmpa    #EXP7_TOKEN_COLON
        beq     exp7_token_is_punctuation_yes
        cmpa    #EXP7_TOKEN_SEMICOLON
        beq     exp7_token_is_punctuation_yes
        clra
        rts
exp7_token_is_punctuation_yes
        lda     #1
        rts

exp7_message_shape
        fcc     "255 TOKENS / 5 TOKEN CONTEXT"
        fcb     0
exp7_message_unknown
        fcc     "UNKNOWN WORD"
        fcb     0
exp7_message_no_match
        fcc     "NO MATCHING TOKEN"
        fcb     0
exp7_message_end
        fcc     "END OF PHRASE"
        fcb     0

exp7_word_pointer       rmb     2
exp7_word_length        rmb     1
exp7_lookup_word        rmb     2
exp7_lookup_length      rmb     1
exp7_lookup_token       rmb     1
exp7_accepted_token     rmb     1
exp7_packed_byte        rmb     1
