; CoCo 1 executable: compose a tune with the EXP-010 model, then perform it
; on the EXP-009 player.
;
; Layout keeps the three pieces apart. The player owns page $20 for its direct
; page variables and the code that follows; the model and its inference sit
; above it; the composer and the tune buffer above that.

TUNE_DATA_EXTERNAL equ 1

        include "music_player.asm"

        org     $2C00
        include "../../build/exp010/tune_frame.inc"

        org     $3200
        include "../../build/exp010/melody_model.inc"
        include "melody_inference.asm"

        org     $4E00
        include "melody_demo.asm"

        end     demo_main
