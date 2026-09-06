; CoCo 1/2/3 executable wrapper for the four-voice music player.
;
; The player leaves the row hook to its caller, because the composer's
; screen owns it there. Standalone there is no screen, so this wrapper is
; the caller: it points the hook at the plain return before entering. Left
; unset, the hook is whatever the RAM held and the first row's end jumps
; into it; that is how the standalone player was silently broken between
; 2026-08-02 and 2026-09-06 (found by EXP-015, the faster-clock listening
; test, whose emulator runs never reached the end of the tune).

        include "music_player.asm"

coco_music_entry
        ldd     #row_hook_none
        std     >row_hook
        jmp     music_start

        end     coco_music_entry
