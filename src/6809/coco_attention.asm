; EXP-011 CoCo 1 contextual-attention workbench.

        org     $2000

start
        lds     #$7f00
        lbsr    attention_ui_start
attention_halt
        bra     attention_halt

        include "../../build/exp011/attention_data.inc"
        include "attention_inference.asm"
        include "attention_ui.asm"

        end     start
