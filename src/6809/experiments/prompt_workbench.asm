; EXP-005 presentation: let the audience select a two-token context, run
; inference, and preserve every completion so different prompts can be
; compared on one screen.

show_prompt_workbench
        ldx     #SCREEN
        lda     #$60
clear_prompt_screen
        sta     ,x+
        cmpx    #SCREEN+512
        blo     clear_prompt_screen
        ldx     #SCREEN
        lda     #$20
        ldb     #32
fill_prompt_title_bar
        sta     ,x+
        decb
        bne     fill_prompt_title_bar
        ldx     #SCREEN
        ldu     #message_prompting
        lbsr    print_string
        ldx     #SCREEN+32
        ldu     #message_prompt_help
        lbsr    print_black_on_green
        ldd     #prompt_contexts
        std     prompt_context_pointer
        ldd     #SCREEN+96
        std     prompt_row_pointer
        lda     #PROMPT_COUNT
        sta     prompts_remaining
draw_prompt_rows
        ldd     prompt_row_pointer
        addd    #2
        tfr     d,x
        ldu     prompt_context_pointer
        lda     ,u+
        stu     prompt_context_pointer
        lbsr    print_token_id
        ldu     #message_space
        lbsr    print_black_on_green
        ldu     prompt_context_pointer
        lda     ,u+
        stu     prompt_context_pointer
        lbsr    print_token_id
        ldd     prompt_row_pointer
        addd    #64
        std     prompt_row_pointer
        dec     prompts_remaining
        bne     draw_prompt_rows
        clr     selected_prompt
        lbsr    draw_prompt_cursor
        ifdef   DIRECT_TEST
        lbsr    run_selected_prompt
        lbsr    select_next_prompt
        swi
        else
prompt_menu_loop
        jsr     [POLCAT]
        beq     prompt_menu_loop
        cmpa    #KEY_UP
        beq     prompt_key_up
        cmpa    #KEY_DOWN
        beq     prompt_key_down
        cmpa    #KEY_ENTER
        bne     prompt_menu_loop
        lbsr    run_selected_prompt
        lbsr    select_next_prompt
        bra     prompt_menu_loop
prompt_key_up
        lbsr    erase_prompt_cursor
        lda     selected_prompt
        bne     prompt_key_up_decrement
        lda     #PROMPT_COUNT
prompt_key_up_decrement
        deca
        sta     selected_prompt
        lbsr    draw_prompt_cursor
        bra     prompt_menu_loop
prompt_key_down
        lbsr    select_next_prompt
        bra     prompt_menu_loop
        endc

select_next_prompt
        lbsr    erase_prompt_cursor
        inc     selected_prompt
        lda     selected_prompt
        cmpa    #PROMPT_COUNT
        blo     select_next_ready
        clr     selected_prompt
select_next_ready
        lbsr    draw_prompt_cursor
        rts

prompt_cursor_address
        lda     selected_prompt
        ldb     #64
        mul
        addd    #SCREEN+96
        tfr     d,x
        rts

erase_prompt_cursor
        lbsr    prompt_cursor_address
        lda     #$60
        sta     ,x
        rts

draw_prompt_cursor
        lbsr    prompt_cursor_address
        lda     #$7e
        sta     ,x
        rts

run_selected_prompt
        lda     selected_prompt
        ldb     #2
        mul
        ldu     #prompt_contexts
        leau    d,u
        ldd     ,u
        std     current_context
        lbsr    prompt_cursor_address
        leax    32,x
        stx     screen_pointer
        pshs    x
        lda     #$60
        ldb     #32
clear_prompt_completion
        sta     ,x+
        decb
        bne     clear_prompt_completion
        puls    x
        lbsr    generate_name
        rts

message_prompting
        fcc     "COCO LLM PROMPTING"
        fcb     0
message_prompt_help
        fcc     "UP/DOWN SELECT  ENTER GENERATE"
        fcb     0
