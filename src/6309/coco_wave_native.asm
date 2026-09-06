; EXP-017, the wavetable voices: a CoCo 3 with a 6309, native mode, at the
; 1.78 MHz clock. The same instruction stream as the 6809 builds, at the
; cycle counts native mode gives it, so the rate is EXP-015's prediction
; again and the pitch test is the same one. The waveform comes from the
; -I directory, so this one wrapper serves the triangle and sine builds.

MUSIC_6309          equ 1
MUSIC_FAST_CLOCK    equ 1

        include "../6809/wave_player.asm"
        include "tune_data.inc"
        include "wavetable.inc"

coco_wave_entry
        ldd     #row_hook_none
        std     >row_hook
        clr     >ticks_cfg      ; zero asks music_start for the default tempo;
                                ; the RAM it loads into is not zero by right
        jmp     music_start

        end     coco_wave_entry
