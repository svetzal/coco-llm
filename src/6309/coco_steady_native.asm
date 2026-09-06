; EXP-018, the steady sample clock: a CoCo 3 with a 6309, native mode, at
; the 1.78 MHz clock. Same instructions as the CoCo 1 build with the
; padding that matches native-mode cycle counts; the stream is compiled
; for the rate that loop implies.

MUSIC_6309          equ 1
MUSIC_FAST_CLOCK    equ 1

        include "../6809/steady_player.asm"
        include "tune_events.inc"

        end     music_start
