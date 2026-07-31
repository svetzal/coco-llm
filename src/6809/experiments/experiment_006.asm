; EXP-006: load a Mac-trained 8 KiB model and use it for practical completion.
;
; This driver is intentionally small. The lesson-specific policy is visible:
; the CoCo does no training, ranks pretrained integer logits, and gives the
; audience an editor instead of a fixed prompt menu.

start
        lds     #$5f00
        ifdef   EXP6_UI_TEST
        lbra    exp6_ui_test_start
        else
        lbra    completion_show_workbench
        endc

        include "../../../build/exp006/model_data.inc"

; Bind the experiment-neutral VDG UI to EXP-006's exported vocabulary and
; ranked output slots. EXP-007 will provide the same three bindings.
COMPLETION_TOKEN_POINTERS    equ     exp6_token_pointers
COMPLETION_SUGGESTION_TOKENS equ     exp6_top_one_token
COMPLETION_MESSAGE_SHAPE     equ     exp6_message_shape

        include "../completion_inference.asm"
        include "../completion_screen.asm"
        include "../completion_editor.asm"
        include "../completion_policy_exp6.asm"

        ifndef  DIRECT_TEST
        include "../../../build/exp006/model_image.inc"
        endc
