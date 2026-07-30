; Standalone CPU-simulator wrapper for the complete training engine.

DIRECT_TEST     equ     1

        org     $2000

        include "../experiments/experiment_004.asm"

; The simulator evaluates these criteria after the model reaches SWI.
;! parity_result = #$01

        end     start
