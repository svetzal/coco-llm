; EXP-015, the faster-clock listening test: the EXP-009 player, unchanged,
; running on a CoCo 3 at its 1.78 MHz clock.
;
; The sample rate is the loop's cycle count, so doubling the clock doubles
; the rate exactly. Nothing in the loop moves; only the increment table is
; built for the doubled rate so every note lands on the same pitch.
;
; CoCo 3 only. On a CoCo 1 the fast clock garbles the display.

MUSIC_FAST_CLOCK    equ 1
TUNE_DATA_EXTERNAL  equ 1

        include "music_player.asm"
        include "../../build/exp015/tune_data_fast.inc"

; Standalone: no screen, so this wrapper supplies the row hook. See
; coco_music.asm for why the player cannot default it itself.
coco_music_entry
        ldd     #row_hook_none
        std     >row_hook
        clr     >ticks_cfg      ; zero asks music_start for the default tempo;
                                ; the RAM it loads into is not zero by right
        jmp     music_start

        end     coco_music_entry
