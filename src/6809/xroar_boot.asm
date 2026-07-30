; ROM-cartridge bootstrap for running CoCo LLM in XRoar without Tandy ROMs.
;
; The cartridge copies the writable program image from ROM to $2000 and then
; transfers control there. This is an emulator convenience only; physical
; machines will load the DECB binary through CoCo SDC or FujiNet.

        org     $c000

boot
        orcc    #$50
        lds     #$7f00
        ldx     #payload
        ldu     #$2000
        ldy     #payload_end-payload
copy_payload
        lda     ,x+
        sta     ,u+
        leay    -1,y
        bne     copy_payload
        jmp     $2000

        include "../../build/coco-llm-payload.inc"

        rmb     $fff0-*
        fdb     boot
        fdb     boot
        fdb     boot
        fdb     boot
        fdb     boot
        fdb     boot
        fdb     boot
        fdb     boot
