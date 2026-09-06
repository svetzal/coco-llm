; EXP-017, the wavetable voices: the CoCo 1 build.
;
; The wrapper supplies the two generated includes by name, so the build
; chooses the tune table and the waveform with -I. It also supplies the
; row hook: the player leaves that to its caller, and standalone there is
; no screen, so the hook is the plain return.

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
