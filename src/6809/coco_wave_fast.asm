; EXP-017, the wavetable voices: the CoCo 3 build at its 1.78 MHz clock.
; Same code as the CoCo 1 build; the tune table is built for twice the
; rate. CoCo 3 only.

MUSIC_FAST_CLOCK    equ 1

        include "wave_player.asm"
        include "tune_data.inc"
        include "wavetable.inc"

coco_wave_entry
        ldd     #row_hook_none
        std     >row_hook
        clr     >ticks_cfg      ; zero asks music_start for the default tempo;
                                ; the RAM it loads into is not zero by right
        jmp     music_start

        end     coco_wave_entry
