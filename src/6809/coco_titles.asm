; CoCo 1/2/3 executable wrapper for the EXP-012 fake episode title generator.
;
; Only model_forward.asm is included, not model_core.asm: the model was trained
; on the Mac, so the on-CoCo training driver and its experiment policy hooks are
; not wanted here. The arithmetic is the same code every other experiment runs.

        org     $2000

        include "../../build/exp012/title_model.inc"
        include "title_generator.asm"
        include "model_forward.asm"
        include "model_storage.asm"

        end     start
