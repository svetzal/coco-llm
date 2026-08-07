; CoCo 1/2/3 executable wrapper for the EXP-013 RPSLS game.
;
; Nothing from the token model is included: this experiment shares no code
; with it, which is worth seeing in the build rather than only in prose.

        org     $2000

        include "rpsls_game.asm"

        end     start
