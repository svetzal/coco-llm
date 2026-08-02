; Assembles the melody model and its inference core for the direct simulator
; and for the CoCo.
;
; The model data comes first because its equ definitions size the inference
; core's storage.

        org     $2000

        include "../../build/exp010/melody_model.inc"
        include "melody_inference.asm"

        end
