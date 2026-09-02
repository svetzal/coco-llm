; The signed multiply, twice, and a loop that times it.
;
; This is a standalone story and it shares no code with the learning engine.
; It does share the engine's arithmetic: bench_kernel_6809 is transcribed from
; multiply_s8_s16 in src/6809/model_forward.asm, and the numbers it multiplies
; are the trained parameters and the real context bytes, exported by
; tools/export_bench_data.py.
;
; Define BENCH_6309 to include the MULD kernel. Without it the file assembles
; for a stock 6809 and only the first kernel exists.

TIMER           equ     $0112           ; Color BASIC's 60 Hz tick counter.

; 200 passes over 290 parameters is 58,000 multiplications. The product has
; to stay under 65,536 because the screen prints it as one 16-bit number.
        ifndef  BENCH_PASSES
BENCH_PASSES    equ     200
        endc

BENCH_EXPECTED  equ     (BENCH_PASS_SUM*BENCH_PASSES)&$ffff

; ---------------------------------------------------------------------------
; Kernel one. A signed 8-bit multiplicand in A, a signed 16-bit weight at X,
; the low word of the product in D.
;
; The 6809 multiplies 8 bits by 8 bits, unsigned. Two MUL instructions build
; the low word. Reading a negative A as an unsigned byte adds 256 times the
; weight, so the last three instructions take it back off again.
bench_kernel_6809
        sta     multiply_factor
        ldb     1,x
        mul
        std     multiply_product
        lda     multiply_factor
        ldb     ,x
        mul
        addb    multiply_product
        stb     multiply_product
        tst     multiply_factor
        bpl     bench_6809_ready
        lda     multiply_product        ; the sign correction
        suba    1,x
        sta     multiply_product
bench_6809_ready
        ldd     multiply_product
        rts

        ifdef   BENCH_6309
; ---------------------------------------------------------------------------
; Kernel two. Same inputs, same output, on a chip that has the instruction.
;
; MULD multiplies 16 bits by 16 bits and it is signed, so the correction above
; is not faster here. It is absent. SEX widens the multiplicand, MULD leaves a
; 32-bit result in Q, and the answer is the low half.
bench_kernel_6309
        tfr     a,b
        sex
        muld    ,x
        tfr     w,d
        rts
        endc

; ---------------------------------------------------------------------------
; BENCH_PASSES passes over the whole parameter block, accumulating products
; into bench_sum with 16-bit wraparound. Y holds the kernel, so both
; measurements run byte-identical loop code and the comparison is about the
; multiply rather than about the harness.
bench_run
        ldd     #0
        std     bench_sum
        ldd     #BENCH_PASSES
        std     bench_passes_left
bench_pass
        ldx     #bench_weights
        ldu     #bench_multiplicands
        ldd     #BENCH_COUNT
        std     bench_items_left
bench_item
        lda     ,u+
        jsr     ,y
        addd    bench_sum
        std     bench_sum
        leax    2,x
        ldd     bench_items_left
        subd    #1
        std     bench_items_left
        bne     bench_item
        ldd     bench_passes_left
        subd    #1
        std     bench_passes_left
        bne     bench_pass
        rts

; Run the kernel in Y and leave the elapsed 60 Hz ticks in D.
;
; TIMER counts video frames, not processor cycles, so it measures the same
; wall-clock second whichever speed the machine is running at. That is the
; point: a faster CPU has to show up as fewer ticks.
bench_timed
        ldd     TIMER
        std     bench_start
        lbsr    bench_run
        ldd     TIMER
        subd    bench_start
        std     bench_elapsed
        rts

; ---------------------------------------------------------------------------
; Unsigned 16-bit divide: D divided by bench_divisor, quotient in D and
; remainder in bench_remainder. Shift and subtract, sixteen times.
bench_divide
        std     bench_dividend
        ldd     #0
        std     bench_remainder
        lda     #16
        sta     bench_bits
bench_divide_step
        lsl     bench_dividend+1
        rol     bench_dividend
        ldd     bench_remainder
        rolb
        rola
        std     bench_remainder
        subd    bench_divisor
        bcs     bench_divide_next
        std     bench_remainder
        inc     bench_dividend+1
bench_divide_next
        dec     bench_bits
        bne     bench_divide_step
        ldd     bench_dividend
        rts

; ticks_a divided by ticks_b to one decimal place: whole part in
; bench_ratio_whole, tenths digit in bench_ratio_tenth.
;
; One decimal rather than two, because the remainder has to be multiplied
; before the second divide and ten times a tick count still fits in sixteen
; bits for any run shorter than a hundred and nine seconds. A hundred times it
; would not, and the answer would be quietly wrong.
bench_ratio
        ldd     bench_ratio_b
        std     bench_divisor
        ldd     bench_ratio_a
        lbsr    bench_divide
        std     bench_ratio_whole
        ldd     bench_remainder
        lbsr    bench_times_ten
        lbsr    bench_divide
        std     bench_ratio_tenth
        rts

; D times ten, as shifts and one add.
bench_times_ten
        std     bench_scaled
        aslb
        rola
        aslb
        rola
        addd    bench_scaled
        aslb
        rola
        rts

bench_sum               rmb     2
bench_elapsed           rmb     2
bench_start             rmb     2
bench_passes_left       rmb     2
bench_items_left        rmb     2
bench_dividend          rmb     2
bench_divisor           rmb     2
bench_remainder         rmb     2
bench_scaled            rmb     2
bench_bits              rmb     1
bench_ratio_a           rmb     2
bench_ratio_b           rmb     2
bench_ratio_whole       rmb     2
bench_ratio_tenth       rmb     2
multiply_product        rmb     2
multiply_factor         rmb     1
