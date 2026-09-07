; CoCo 1 executable: enter an opening figure, watch the model compose from it,
; then hear the result performed.
;
; The performer is EXP-018's steady-clock player. The composer writes rows
; into the tune buffer as it always did; steady_compile.asm then turns the
; rows, and the playback cursor, into the event stream the player replays
; with every sample costing the same. The screen is driven by the stream:
; a cursor cell is an event like a note.
;
; Memory, low to high: the player's page and code, the compiler, the tune
; frame (increments and the row buffer), the model and its inference, the
; composer and the display, and above everything the compiled stream.
; The row buffer used to sit at $2C00 and its last 194 bytes lay on top
; of the model at $3200, so a second performance composed from a corrupted
; model. Everything is packed lower now, with room between regions, and
; the stream gets the 14 KiB from $4800 to the top of a 32 KiB machine:
; a dense 128-row tune at seven ticks a row compiles to about 12 KiB.
;
; ENTRY_RUN, defined on the command line, makes the entry point demo_run,
; which composes from the built-in figure and plays without a keyboard,
; for the emulator test.

COMPILE_CURSOR  equ     1
CURSOR_TRACK    equ     $0400+15*32     ; UI_TRACK: the cursor's own row
CURSOR_BLANK    equ     $80             ; UI_BLANK
CURSOR_MARK     equ     $FF             ; UI_ORANGE+$0F
CURSOR_ROWS     equ     4               ; tune rows per cursor cell

event_buffer    equ     $4800
event_buffer_end equ    $8000
event_stream    equ     event_buffer    ; what the player plays

        include "steady_player.asm"
        include "steady_compile.asm"

        org     $2500
        include "../../build/exp010/tune_frame.inc"

        org     $2C00
        include "../../build/exp010/melody_model.inc"
        include "melody_inference.asm"

        org     $4000
        include "melody_demo.asm"
        include "melody_ui.asm"

        ifdef   ENTRY_RUN
        end     demo_run
        else
        end     demo_main
        endc
