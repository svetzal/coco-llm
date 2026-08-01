; Measures the real cost of the four-voice sample loop.
;
; The sample rate is not a design choice; it is whatever the inner loop costs.
; This harness plays the whole tune in the direct simulator so that --perf
; reports total cycles, which tools/measure_music_rate.py divides by the known
; sample count to derive the rate the increment table must be built for.

        include "../music_player.asm"

start   lds     #$1FFF          ; stack below the player's page $20 variables
        lbsr    music_start
        clra
        sta     done_flag
        swi

done_flag rmb   1

;! done_flag = #$00
