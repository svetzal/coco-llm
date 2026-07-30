; Standalone CPU-simulator wrapper for the EXP-005 prompted model.

DIRECT_TEST     equ     1
EXPERIMENT_5    equ     1

        org     $2000

        include "../model_core.asm"

; The simulator evaluates this criterion after the model reaches SWI.
;! parity_result = #$01

        end     start
