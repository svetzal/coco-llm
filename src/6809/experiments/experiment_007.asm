; EXP-007: use a Mac-trained 32 KiB sentence model in the CoCo's all-RAM map.
;
; The driver remains a composition root. The shared screen/editor provide the
; familiar EXP-006 workbench; this experiment supplies five-token inference,
; punctuation policy, and the ROM-switching keyboard adapter.

start
        lds     #$3e00
        ifdef   EXP7_UI_TEST
        lbra    exp7_ui_test_start
        else
        lbra    completion_show_workbench
        endc

        include "../../../build/exp007/model_data.inc"

COMPLETION_TOKEN_POINTERS    equ     exp7_token_pointers
COMPLETION_SUGGESTION_TOKENS equ     exp7_top_one_token
COMPLETION_MESSAGE_SHAPE     equ     exp7_message_shape

        include "../completion_inference_exp7.asm"
        include "../completion_screen.asm"
        include "../completion_editor.asm"
        include "../completion_policy_exp7.asm"

exp7_resident_end
        ifgt    exp7_resident_end-$3f00
        fail    "EXP-007 resident image crosses the $3F00 ceiling"
        endc

        ifndef  DIRECT_TEST
        include "../../../build/exp007/model_image.inc"
        endc
