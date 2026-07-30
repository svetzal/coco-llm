; Signed 8-bit by 8-bit multiplication proof.
;
; Inputs:
;   A = signed multiplicand
;   B = signed multiplier
;
; Output:
;   D = signed 16-bit product
;
; The MC6809 MUL instruction treats A and B as unsigned. A signed product can
; be recovered from that result by subtracting B*256 when A was negative and
; A*256 when B was negative. Since those corrections affect only the high byte,
; each correction is a single SUBA.

        org     $1000

start   lds     #$7fff
        lda     #7
        ldb     #9
        bsr     smul8
        std     result1

        lda     #-7
        ldb     #9
        bsr     smul8
        std     result2

        lda     #7
        ldb     #-9
        bsr     smul8
        std     result3

        lda     #-7
        ldb     #-9
        bsr     smul8
        std     result4

        lda     #$80
        ldb     #$80
        bsr     smul8
        std     result5

        lda     #$80
        ldb     #$7f
        bsr     smul8
        std     result6

        swi

smul8  sta     smul8_a
        stb     smul8_b
        mul
        tst     smul8_a
        bpl     smul8_apos
        suba    smul8_b
smul8_apos
        tst     smul8_b
        bpl     smul8_bpos
        suba    smul8_a
smul8_bpos
        rts

smul8_a rmb     1
smul8_b rmb     1
result1 rmb     2
result2 rmb     2
result3 rmb     2
result4 rmb     2
result5 rmb     2
result6 rmb     2

; The standalone CPU simulator evaluates these criteria after SWI.
;! result1 = #$003f
;! result2 = #$ffc1
;! result3 = #$ffc1
;! result4 = #$003f
;! result5 = #$4000
;! result6 = #$c080
