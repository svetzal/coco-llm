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
        lbra    exp6_show_workbench
        endc

        include "../../../build/exp006/model_data.inc"
        include "../completion_inference.asm"
        include "../completion_screen.asm"
        include "../completion_workbench.asm"

        ifndef  DIRECT_TEST
        include "../../../build/exp006/model_image.inc"
        endc
