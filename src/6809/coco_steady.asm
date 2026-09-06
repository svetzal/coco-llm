; EXP-018, the steady sample clock: the CoCo 1 build. The wrapper supplies
; the compiled event stream by name, so the build chooses it with -I.
; Nothing else to set: this player has no hook and no tempo cell.

        include "steady_player.asm"
        include "tune_events.inc"

        end     music_start
