; EXP-004: prove that a complete token model can train and generate on a 6809.
;
; The lesson-specific choices are visible here:
;   - train the 29-token vintage-computer model;
;   - use the fast 8x16 multiply justified by this corpus's measured range;
;   - begin inference with the boundary context "# #";
;   - sample from the learned distribution to produce a gallery of names.

start
        lds     #$7f00
        lbsr    initialize_training_screen
        lbsr    initialize_model
        lbsr    capture_untrained_sample
        lbsr    initialize_training_screen
        lbsr    train_model
        lbsr    finish_training
        lbra    show_sample_gallery

; Preserve one deterministic generation from the initialized weights. The
; final screen will run seed 6809 again after training, putting the causal
; before/after comparison in the artifact rather than only in the narration.
capture_untrained_sample
        ldd     #6809
        std     rng_state
        ldd     #SCREEN+96
        std     screen_pointer
        lbsr    generate_name
        ldx     #SCREEN+96
        ldu     #untrained_sample_display
        ldb     #32
capture_untrained_cell
        lda     ,x+
        sta     ,u+
        decb
        bne     capture_untrained_cell
        rts

; EXP-004's context values fit signed eight bits, so only their low byte needs
; to be multiplied by the signed 16-bit output error.
experiment_multiply_training_context
        lda     1,x
        ldx     probability_pointer
        lbra    multiply_s8_s16

; Begin every generated sample from the learned boundary context and print that
; seed in black-on-green before generated tokens appear in green-on-dark.
experiment_prepare_generation
        clr     current_context
        clr     current_context+1
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
        rts

; Require at least two visible tokens before allowing the boundary token to
; end a sample. The removed probability is restored after winner correction.
experiment_adjust_probabilities
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
        rts

experiment_choose_token
        lbra    choose_sampled_token

message_training
        fcc     "COCO LLM TRAINING"
        fcb     0
message_epoch
        fcc     "EPOCH 00 / 20"
        fcb     0

        include "sample_gallery.asm"
        include "../model_core.asm"
        include "../../../build/model_data.inc"
        include "../model_storage.asm"

sample_seed_pointer     rmb     2
sample_count            rmb     1
