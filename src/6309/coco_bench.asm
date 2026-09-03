; The multiply benchmark, as a CoCo program.
;
; Assemble twice. Without BENCH_6309 it is a stock 6809 program reporting one
; result, which is what a CoCo 1 runs. With BENCH_6309 it reports three, over
; the same data, on one screen:
;
;   the 6809 kernel in 6809 emulation mode  - what a stock machine does
;   the 6809 kernel in 6309 native mode     - what the mode alone is worth
;   the MULD kernel in 6309 native mode     - what the instruction is worth
;
; Three rows rather than two, because one before-and-after cannot separate a
; generally faster chip from a chip that has the instruction this workload
; wants, and that distinction is the whole point of the block.
;
; A register convention worth stating, because getting it wrong cost an
; afternoon: nothing passes a 16-bit value in D alongside a small number in A
; or B. B is the low half of D and A is the high half, so `ldd value` followed
; by `ldb #column` silently replaces half the value with the column. Values
; travel in X, or the small number is stored before the value is loaded.

; $4000, not $2000. A disk system puts DOS buffers and the start of BASIC's
; program area below roughly $2600, so a program loaded at $2000 lands on top
; of the buffers DSKCON is using to load it and LOADM hangs. This was found by
; loading the disk image in the emulator, which is the only reason it is not
; going to be found on Saturday instead.
        ifndef  BENCH_ORG
BENCH_ORG       equ     $4000
        endc

        org     BENCH_ORG

start
        lds     #$7f00
; rmb reserves the byte but DECB does not load it, so it starts as whatever
; the machine happened to leave there.
        clr     sum_faults
        ldd     #0
        std     ticks_native
        std     ticks_muld
        lbsr    screen_clear
        ldu     #text_title
        lbsr    screen_title_bar

        ldx     #BENCH_COUNT*BENCH_PASSES
        ldu     #text_multiplies
        lda     #2
        lbsr    report_count
        ldx     #BENCH_COUNT
        ldu     #text_parameters
        lda     #3
        lbsr    report_count

        ldu     #text_kernel_6809
        lda     #5
        lbsr    say
        ldy     #bench_kernel_6809
        lbsr    bench_timed
        std     ticks_emulation
        lbsr    check_sum
        lda     #6
        lbsr    report_result

        ifdef   BENCH_6309
        ifdef   BENCH_NATIVE
; Native mode is bit 0 of MD. Interrupts stay enabled because TIMER is the
; clock, and the 6309 stacks and unstacks the extra register itself. That is
; the one thing here that has never run on real silicon, which is why
; BENCH_NATIVE is optional: MULD works in either mode, so the fallback build
; still gets the comparison the block is about.
        ldu     #text_kernel_native
        lda     #8
        lbsr    say
        ldmd    #1
        ldy     #bench_kernel_6809
        lbsr    bench_timed
        std     ticks_native
        lbsr    check_sum
        lda     #9
        lbsr    report_result
        endc

        ldu     #text_kernel_muld
        lda     #11
        lbsr    say
        ldy     #bench_kernel_6309
        lbsr    bench_timed
        std     ticks_muld
        lbsr    check_sum
        lda     #12
        lbsr    report_result
        ifdef   BENCH_NATIVE
        ldmd    #0
        endc

        ldd     ticks_emulation
        std     bench_ratio_a
        ldd     ticks_muld
        std     bench_ratio_b
        lbsr    bench_ratio
        lda     #14
        lbsr    report_ratio
        endc

        lda     #15
        lbsr    report_agreement

; The screen is the result a person reads. This is the result a test reads:
; every number in a register at one known address, so a harness can trap here
; and take them off a single line of XRoar's instruction trace. Reading them
; out of a snapshot was tried first and the snapshot proved unreliable.
bench_done
        ldx     ticks_emulation
        ldy     ticks_native
        ldu     ticks_muld
        ldd     bench_sum
bench_trap
        bra     bench_trap

; Every run has to reach the checksum tools/export_bench_data.py computed in
; Python. A faster kernel with a different sum is a broken kernel, and saying
; so on the screen is cheaper than trusting it.
check_sum
        ldd     bench_sum
        cmpd    #BENCH_EXPECTED
        beq     check_sum_done
        inc     sum_faults
check_sum_done
        rts

; ---------------------------------------------------------------------------
; A is the row, U a zero-terminated string.
say
        sta     pending_row
        lbsr    row_clear
        clrb
        lbsr    row_text
        lda     pending_row
        ldu     #row_buffer
        lbra    screen_blit_body

; A is the row, X a number, U the words that follow it.
report_count
        sta     pending_row
        stu     pending_text
        stx     scratch
        lbsr    row_clear
        clr     number_offset
        ldd     scratch
        lbsr    row_number_left
        ldb     row_cursor
        incb
        ldu     pending_text
        lbsr    row_text
        lda     pending_row
        ldu     #row_buffer
        lbra    screen_blit_body

; A is the row. The ticks and the checksum the run just produced.
report_result
        sta     pending_row
        lbsr    row_clear
        clr     number_offset
        ldd     bench_elapsed
        lbsr    row_number_left
        ldb     row_cursor
        incb
        ldu     #text_ticks
        lbsr    row_text
        ldb     #14
        ldu     #text_sum
        lbsr    row_text
        ldb     #18
        ldx     bench_sum
        lbsr    row_hex
        lda     pending_row
        ldu     #row_buffer
        lbra    screen_blit_body

        ifdef   BENCH_6309
; A is the row. "MULD IS n.n TIMES FASTER".
report_ratio
        sta     pending_row
        lbsr    row_clear
        clrb
        ldu     #text_muld_is
        lbsr    row_text
        ldb     #8
        stb     number_offset
        ldd     bench_ratio_whole
        lbsr    row_number_left
        lda     #'.
        lbsr    row_char
        ldb     row_cursor
        stb     number_offset
        ldd     bench_ratio_tenth
        lbsr    row_number_left
        ldb     row_cursor
        incb
        ldu     #text_times_faster
        lbsr    row_text
        lda     pending_row
        ldu     #row_buffer
        lbra    screen_blit_body
        endc

; A is the row. Did every run reach the reference checksum?
report_agreement
        sta     pending_row
        lbsr    row_clear
        ldu     #text_sum_right
        tst     sum_faults
        beq     report_agreement_say
        ldu     #text_sum_wrong
report_agreement_say
        clrb
        lbsr    row_text
        lda     pending_row
        ldu     #row_buffer
        lbra    screen_blit_body

; ---------------------------------------------------------------------------
row_clear
        ldx     #row_buffer
        lda     #$20
row_clear_next
        sta     ,x+
        cmpx    #row_buffer+32
        blo     row_clear_next
        clr     row_cursor
        rts

; B is the offset, U a zero-terminated string. row_cursor ends past the text.
row_text
        ldx     #row_buffer
        abx
row_text_next
        lda     ,u+
        beq     row_text_done
        sta     ,x+
        bra     row_text_next
row_text_done
        tfr     x,d
        subd    #row_buffer
        stb     row_cursor
        rts

; A is the character, written at row_cursor.
row_char
        ldx     #row_buffer
        ldb     row_cursor
        abx
        sta     ,x
        inc     row_cursor
        rts

; D is the value, number_offset the column. Left to right, no leading zeros.
row_number_left
        std     number_value
        clr     number_started
        ldx     #number_powers
row_number_digit
        ldd     ,x++
        cmpd    #0
        beq     row_number_done
        std     number_power
        clr     number_digit
row_number_subtract
        ldd     number_value
        subd    number_power
        blo     row_number_emit
        std     number_value
        inc     number_digit
        bra     row_number_subtract
row_number_emit
        lda     number_digit
        bne     row_number_write
        tst     number_started
        bne     row_number_write
        cmpx    #number_powers+10
        bne     row_number_digit
row_number_write
        lda     #1
        sta     number_started
        lda     number_digit
        adda    #'0
        pshs    x
        ldx     #row_buffer
        ldb     number_offset
        abx
        sta     ,x
        puls    x
        inc     number_offset
        bra     row_number_digit
row_number_done
        ldb     number_offset
        stb     row_cursor
        rts

; X is the value, B the offset. Four hexadecimal digits after a dollar sign.
row_hex
        stx     number_value
        stb     number_offset
        ldx     #row_buffer
        abx
        lda     #'$
        sta     ,x+
        ldb     number_value
        lsrb
        lsrb
        lsrb
        lsrb
        lbsr    hex_digit
        sta     ,x+
        ldb     number_value
        lbsr    hex_digit
        sta     ,x+
        ldb     number_value+1
        lsrb
        lsrb
        lsrb
        lsrb
        lbsr    hex_digit
        sta     ,x+
        ldb     number_value+1
        lbsr    hex_digit
        sta     ,x+
        rts

hex_digit
        andb    #$0f
        cmpb    #10
        blo     hex_digit_numeral
        addb    #'A-10
        tfr     b,a
        rts
hex_digit_numeral
        addb    #'0
        tfr     b,a
        rts

number_powers   fdb     10000,1000,100,10,1,0

text_title              fcn     "MULTIPLY BENCHMARK"
text_multiplies         fcn     "MULTIPLICATIONS"
text_parameters         fcn     "TRAINED PARAMETERS"
text_kernel_6809        fcn     "6809 KERNEL, 6809 MODE"
text_kernel_native      fcn     "6809 KERNEL, NATIVE MODE"
        ifdef   BENCH_NATIVE
text_kernel_muld        fcn     "MULD KERNEL, NATIVE MODE"
        else
text_kernel_muld        fcn     "MULD KERNEL, 6809 MODE"
        endc
text_ticks              fcn     "TICKS"
text_sum                fcn     "SUM"
text_muld_is            fcn     "MULD IS"
text_times_faster       fcn     "TIMES FASTER"
text_sum_right          fcn     "SUM MATCHES THE REFERENCE"
text_sum_wrong          fcn     "SUM IS WRONG"

row_buffer      rmb     32
row_cursor      rmb     1
pending_row     rmb     1
pending_text    rmb     2
scratch         rmb     2
number_value    rmb     2
number_power    rmb     2
number_offset   rmb     1
number_digit    rmb     1
number_started  rmb     1
ticks_emulation rmb     2
ticks_native    rmb     2
ticks_muld      rmb     2
sum_faults      rmb     1

        include "../../build/bench6309/bench_data.inc"
        include "multiply_bench.asm"
        include "../6809/text_screen.asm"

        end     start
