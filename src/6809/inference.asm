; Inference driver for the integer token language model.
;
; EXP-004 generates a fixed gallery of sampled names. EXP-005 presents the
; interactive prompt workbench and uses greedy next-token selection. Both call
; the same shared forward pass used during training.

show_samples
        ifdef   EXPERIMENT_5
        lbra    show_prompt_menu
        else
        ldx     #SCREEN+64
        lda     #$60
        ldb     #32
clear_key_prompt
        sta     ,x+
        decb
        bne     clear_key_prompt
        ldx     #SCREEN+96
        ldu     #message_generating
        lbsr    print_black_on_green
        ldd     #sample_seeds
        std     sample_seed_pointer
        ldx     #SCREEN+128
        stx     screen_pointer
        lda     #12
        sta     sample_count
sample_loop
        ldx     sample_seed_pointer
        ldd     ,x++
        stx     sample_seed_pointer
        std     rng_state
        lbsr    generate_name
        ldd     screen_pointer
        addd    #32
        std     screen_pointer
        dec     sample_count
        bne     sample_loop

        ldx     #SCREEN+96
        ldu     #message_generated
        lbsr    print_black_on_green
        ifdef   DIRECT_TEST
        swi
        else
finished
        bra     finished
        endc
        endc

        ifdef   EXPERIMENT_5
; Build a persistent six-prompt workbench. Each prompt occupies one row and
; its completion the row beneath it, so previous inference remains visible.
show_prompt_menu
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
        endc

generate_name
        ifndef  EXPERIMENT_5
        clr     current_context
        clr     current_context+1
        endc
        clr     generated_tokens
        lda     #6
        sta     generation_remaining
        ifndef  EXPERIMENT_5
        ldx     screen_pointer
        lda     #$60
        ldb     #32
clear_sample_line
        sta     ,x+
        decb
        bne     clear_sample_line
        ldx     screen_pointer
        ldu     #message_seed
        lbsr    print_black_on_green
        stx     output_pointer
        ldd     screen_pointer
        addd    #31
        std     output_limit
        clr     generation_display_full
        else
        ldx     screen_pointer
        stx     output_pointer
        leax    31,x
        stx     output_limit
        clr     generation_display_full
        endc
generation_token
        lbsr    forward
        ifndef  EXPERIMENT_5
        lda     generated_tokens
        cmpa    #2
        bhs     generation_can_end
        ldd     probabilities
        std     removed_boundary
        clra
        clrb
        std     probabilities
        lbsr    find_probability_winner
        lda     winner_index
        ldb     #2
        mul
        ldx     #probabilities
        leax    d,x
        ldd     ,x
        addd    removed_boundary
        std     ,x
generation_can_end
        endc
        ifdef   EXPERIMENT_5
        lbsr    find_probability_winner
        lda     winner_index
        sta     chosen_token
        else
        lbsr    xorshift16
        stb     sample_draw
        clr     chosen_token
        clra
        clrb
        std     sample_cumulative
        ldx     #probabilities
        clr     output_index
choose_token
        ldd     ,x++
        addd    sample_cumulative
        std     sample_cumulative
        tsta
        bne     token_chosen
        cmpb    sample_draw
        bhi     token_chosen
        inc     output_index
        lda     output_index
        cmpa    #VOCAB_SIZE
        blo     choose_token
        clr     output_index
token_chosen
        lda     output_index
        sta     chosen_token
        endc
        lbsr    print_chosen_token
        lda     chosen_token
        beq     generation_done
        lda     current_context+1
        sta     current_context
        lda     chosen_token
        sta     current_context+1
        inc     generated_tokens
        dec     generation_remaining
        bne     generation_token
generation_done
        rts

find_probability_winner
        ldx     #probabilities
        ldd     ,x++
        std     maximum_probability
        clr     winner_index
        lda     #1
        sta     output_index
        lda     #VOCAB_SIZE-1
        sta     outputs_remaining
find_probability_loop
        ldd     ,x++
        cmpd    maximum_probability
        bls     find_probability_not_winner
        std     maximum_probability
        lda     output_index
        sta     winner_index
find_probability_not_winner
        inc     output_index
        dec     outputs_remaining
        bne     find_probability_loop
        rts

print_chosen_token
        lda     chosen_token
        ldx     output_pointer
        tsta
        bne     print_chosen_token_text
        ldu     #message_boundary
        bra     print_chosen_token_ready
print_chosen_token_text
        ldb     #2
        mul
        ldu     #token_pointers
        leau    d,u
        ldu     ,u
print_chosen_token_ready
        lbsr    print_generated_string
        tst     generation_display_full
        bne     print_chosen_token_done
        cmpx    output_limit
        bhs     print_chosen_token_done
        lda     #$20
        sta     ,x+
print_chosen_token_done
        stx     output_pointer
        rts

; Print generated text without crossing its 32-column row. Reserve the final
; cell for "+" when a genuine six-token sample is too long to show in full.
print_generated_string
        tst     generation_display_full
        bne     print_generated_string_done
print_generated_character
        lda     ,u+
        beq     print_generated_string_done
        cmpx    output_limit
        bhs     print_generated_string_truncated
        anda    #$3f
        sta     ,x+
        bra     print_generated_character
print_generated_string_truncated
        lda     #$2b
        sta     ,x
        inc     generation_display_full
print_generated_string_done
        rts

sample_seeds
        fdb     6809,6810,6811,6812,6813,6814
        fdb     6815,6816,6817,6818,6819,6820
