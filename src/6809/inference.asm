; Shared inference engine for the integer token language model.
;
; The experiment driver supplies three small, named policies:
;   experiment_prepare_generation    seed context and screen output
;   experiment_adjust_probabilities  impose any lesson-specific constraints
;   experiment_choose_token          sample or select the next token
;
; Everything else is the same next-token loop for every experiment.

generate_name
        clr     generated_tokens
        lda     #6
        sta     generation_remaining
        lbsr    experiment_prepare_generation
generation_token
        lbsr    forward
        lbsr    experiment_adjust_probabilities
        lbsr    experiment_choose_token
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

; Greedy decoding: choose the single highest-probability token.
choose_greedy_token
        lbsr    find_probability_winner
        lda     winner_index
        sta     chosen_token
        rts

; Seeded sampling: draw from the complete next-token distribution.
choose_sampled_token
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
