; Shared interactive editor and completion controller.
;
; The original CoCo keyboard has no key labelled Tab: its Right Arrow returns
; character code 9, the same control code conventionally used for Tab. The UI
; therefore names both meanings while remaining usable on physical hardware.
;
; An experiment supplies five narrow policy hooks:
;   completion_policy_initialize
;   completion_policy_read_key
;   completion_policy_character_allowed
;   completion_policy_predict_input
;   completion_policy_apply_suggestion
;
; Keeping those hooks outside this file lets EXP-006 remain a simple
; space-delimited word lesson while EXP-007 adds punctuation, five-token
; context, and an all-RAM keyboard wrapper without duplicating the editor.

COMPLETION_KEY_LEFT     equ     $08
COMPLETION_KEY_RIGHT    equ     $09
COMPLETION_KEY_DOWN     equ     $0a
COMPLETION_KEY_CLEAR    equ     $0c
COMPLETION_KEY_ENTER    equ     $0d
COMPLETION_KEY_UP       equ     $5e
COMPLETION_INPUT_LIMIT  equ     255

completion_show_workbench
        clr     completion_input_length
        clr     completion_suggestions_visible
        clr     completion_selected_suggestion
        lbsr    completion_policy_initialize
        lbsr    completion_initialize_screen
completion_input_loop
        lbsr    completion_policy_read_key
        beq     completion_input_loop
        cmpa    #COMPLETION_KEY_RIGHT
        lbeq    completion_key_complete
        cmpa    #COMPLETION_KEY_ENTER
        lbeq    completion_key_enter
        cmpa    #COMPLETION_KEY_UP
        lbeq    completion_key_up
        cmpa    #COMPLETION_KEY_DOWN
        lbeq    completion_key_down
        cmpa    #COMPLETION_KEY_LEFT
        lbeq    completion_key_left
        cmpa    #COMPLETION_KEY_CLEAR
        lbeq    completion_key_clear
        pshs    a
        lbsr    completion_policy_character_allowed
        tsta
        puls    a
        lbeq    completion_input_loop

completion_key_character
        pshs    a
        lbsr    completion_hide_suggestions
        puls    a
        cmpa    #$20
        bne     completion_append_typed_character
        ldb     completion_input_length
        beq     completion_input_loop
        ldx     #completion_input_buffer-1
        abx
        cmpa    ,x
        beq     completion_input_loop
completion_append_typed_character
        lbsr    completion_append_character
        lbcs    completion_input_loop
        lbsr    completion_draw_input
        lbsr    completion_clear_status_line
        lbra    completion_input_loop

completion_key_left
        lbsr    completion_hide_suggestions
        ldb     completion_input_length
        lbeq    completion_input_loop
        decb
        stb     completion_input_length
        ldx     #completion_input_buffer
        abx
        clr     ,x
        lbsr    completion_draw_input
        lbsr    completion_clear_status_line
        lbra    completion_input_loop

completion_key_clear
        clr     completion_input_length
        clr     completion_input_buffer
        lbsr    completion_hide_suggestions
        lbsr    completion_draw_input
        lbsr    completion_clear_status_line
        lbra    completion_input_loop

completion_key_complete
        tst     completion_suggestions_visible
        lbne    completion_accept_suggestion
        lbsr    completion_policy_predict_input
        lbra    completion_input_loop

completion_key_enter
        tst     completion_suggestions_visible
        lbne    completion_accept_suggestion
        lbsr    completion_policy_predict_input
        lbra    completion_input_loop

completion_key_up
        tst     completion_suggestions_visible
        lbeq    completion_input_loop
        lda     completion_selected_suggestion
        bne     completion_key_up_decrement
        lda     completion_suggestion_count
completion_key_up_decrement
        deca
        sta     completion_selected_suggestion
        lbsr    completion_draw_suggestions
        lbra    completion_input_loop

completion_key_down
        tst     completion_suggestions_visible
        lbeq    completion_input_loop
        inc     completion_selected_suggestion
        lda     completion_selected_suggestion
        cmpa    completion_suggestion_count
        blo     completion_key_down_ready
        clr     completion_selected_suggestion
completion_key_down_ready
        lbsr    completion_draw_suggestions
        lbra    completion_input_loop

completion_accept_suggestion
        lbsr    completion_policy_apply_suggestion
        lbra    completion_input_loop

; Append A to the editor buffer. Carry reports a full buffer.
completion_append_character
        ldb     completion_input_length
        cmpb    #COMPLETION_INPUT_LIMIT
        bhs     completion_append_full
        ldx     #completion_input_buffer
        abx
        sta     ,x+
        clr     ,x
        inc     completion_input_length
        andcc   #$fe
        rts
completion_append_full
        ldu     #completion_message_full
        lbsr    completion_show_status
        orcc    #$01
        rts

completion_hide_suggestions
        tst     completion_suggestions_visible
        beq     completion_hide_done
        lbsr    completion_clear_suggestions
completion_hide_done
        rts

completion_input_buffer          rmb     COMPLETION_INPUT_LIMIT+1
completion_input_length          rmb     1
completion_selected_suggestion   rmb     1
completion_suggestion_count      rmb     1
completion_suggestions_visible   rmb     1
