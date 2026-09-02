; Direct-simulator check of the 6809 kernel and the benchmark loop.
;
; The simulator is MC6809 only, so this covers kernel one. Kernel two is
; checked in Python over every input pair, and then on the machine itself.
;
; BENCH_PASSES is small here. The point is the sum, not the clock.

BENCH_PASSES    equ     3

        org     $2000
start
        lds     #$7f00
        ldy     #bench_kernel_6809
        lbsr    bench_run
        swi

        include "../../../build/bench6309/bench_data.inc"
        include "../multiply_bench.asm"

        end     start
