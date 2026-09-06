; EXP-015, the faster-clock listening test: the EXP-009 player on a CoCo 3
; fitted with a 6309, in native mode, at the 1.78 MHz clock.
;
; The instruction stream is the 6809 player's, so the sound is produced by
; the same arithmetic. What changes is what each instruction costs: native
; mode trims a cycle from most of the loop, so the sample rate rises again
; beyond the fast-clock build's. The only code that differs is the tick
; countdown, which moves from a byte in memory to the 6309's W register
; because a tick at this rate no longer fits in a byte.
;
; The rate this build is tuned for is a data-sheet prediction, not a
; measurement. If the prediction is wrong the tune plays out of tune against
; the other two builds, which is the test.
;
; CoCo 3 with a 6309 only. LDMD on a 6809 is not an instruction.

MUSIC_6309          equ 1
MUSIC_FAST_CLOCK    equ 1
TUNE_DATA_EXTERNAL  equ 1

        include "../6809/music_player.asm"
        include "../../build/exp015/tune_data_6309.inc"

; Standalone: no screen, so this wrapper supplies the row hook. See
; ../6809/coco_music.asm for why the player cannot default it itself.
coco_music_entry
        ldd     #row_hook_none
        std     >row_hook
        jmp     music_start

        end     coco_music_entry
