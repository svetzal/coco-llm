; EXP-005: expand the vocabulary and let the audience prompt the trained model.
;
; The lesson-specific choices are visible here:
;   - train the 38-token marketing-language model for 80 epochs;
;   - retain the full 16-bit context values required by the expanded corpus;
;   - begin inference with an audience-selected two-token context;
;   - greedily choose the most probable continuation for easy comparison.

start
        lds     #$7f00
        lbsr    initialize_training_screen
        lbsr    initialize_model
        lbsr    train_model
        lbsr    finish_training
        lbra    show_prompt_workbench

; EXP-005's context values exceed signed eight-bit range, so this lesson uses
; the complete 16x16 product instead of EXP-004's narrower optimization.
experiment_multiply_training_context
        ldd     ,x
        ldx     probability_pointer
        lbra    multiply_s16_s16

; The prompt workbench has already placed the audience's two seed tokens in
; current_context and selected the completion row.
experiment_prepare_generation
        ldx     screen_pointer
        stx     output_pointer
        leax    31,x
        stx     output_limit
        clr     generation_display_full
        rts

; EXP-005 imposes no minimum-length constraint: an immediate boundary token is
; an honest possible completion for a selected prompt.
experiment_adjust_probabilities
        rts

experiment_choose_token
        lbra    choose_greedy_token

message_training
        fcc     "COCO LLM EXP-005 TRAINING"
        fcb     0
message_epoch
        fcc     "EPOCH 00 / 80"
        fcb     0

        include "prompt_workbench.asm"
        include "../model_core.asm"
        include "../../../build/model_data_exp5.inc"
        include "../model_storage.asm"

selected_prompt         rmb     1
prompts_remaining       rmb     1
prompt_context_pointer  rmb     2
prompt_row_pointer      rmb     2
