; CoCo 1 executable: enter an opening figure, watch the model compose from it,
; then hear the result performed.
;
; The three pieces stay apart in memory. The player owns page $20 for its
; direct page variables and the code above it; the model and its inference sit
; higher; the composer, the display and the tune buffer above that.

TUNE_DATA_EXTERNAL equ 1

        include "music_player.asm"

        org     $2C00
        include "../../build/exp010/tune_frame.inc"

        org     $3200
        include "../../build/exp010/melody_model.inc"
        include "melody_inference.asm"

        org     $4E00
        include "melody_demo.asm"
        include "melody_ui.asm"

        end     demo_main
