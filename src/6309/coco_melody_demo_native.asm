; CoCo 3 with a 6309: the melody demo with its performer in native mode at
; the 1.78 MHz clock, EXP-018's steady clock at 11,188 Hz. The stage
; build. Everything but the player's cycle counts and the tune frame's
; increments is the CoCo 1 demo; the composer and the display run in 6809
; emulation mode, and the player switches to native mode only while it
; plays.

MUSIC_6309      equ     1
MUSIC_FAST_CLOCK equ    1

COMPILE_CURSOR  equ     1
CURSOR_TRACK    equ     $0400+15*32
CURSOR_BLANK    equ     $80
CURSOR_MARK     equ     $FF
CURSOR_ROWS     equ     4

event_buffer    equ     $4800
event_buffer_end equ    $8000
event_stream    equ     event_buffer

        include "../6809/steady_player.asm"
        include "../6809/steady_compile.asm"

        org     $2500
        include "../../build/exp010/tune_frame_6309.inc"

        org     $2C00
        include "../../build/exp010/melody_model.inc"
        include "../6809/melody_inference.asm"

        org     $4000
        include "../6809/melody_demo.asm"
        include "../6809/melody_ui.asm"

        ifdef   ENTRY_RUN
        end     demo_run
        else
        end     demo_main
        endc
