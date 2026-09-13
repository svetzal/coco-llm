; EXP-019, the graphical hand game. 32 KiB CoCo 1, normal 6809 clock.
; The established opponent is linked unchanged. Its text UI is never called.
        org     $2000
        include "text_screen.asm"
        include "rpsls_game.asm"
        include "rpsls_graphics.asm"
        end     gfx_start
