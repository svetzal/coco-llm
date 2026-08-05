; Bit-exact integer token language model for the Motorola 6809.
;
; An experiment driver selects an origin and data fixture, calls the reusable
; training phases, and chooses the presentation used after training. The
; implementation deliberately favours readable, testable arithmetic.

PARAM_BYTES     equ     PARAM_COUNT*2

; Verify the completed training run, report its status, and wait for the
; audience before returning to the experiment driver's inference lesson.
finish_training
        lbsr     verify_parameters
        lbsr    show_training_complete
        tst     parity_result
        beq     verification_failed
        ifndef  DIRECT_TEST
wait_for_key
        jsr     [POLCAT]
        beq     wait_for_key
        endc
        rts
verification_failed
        lbsr    show_verification_failed
        ifdef   DIRECT_TEST
        swi
        else
verification_halt
        bra     verification_halt
        endc

; Initialize all embedding and output-weight masters from XorShift16. Each
; Q4.12 value is (state & $03ff) - $0200. Bias masters begin at zero.
initialize_model
        ldd     #6809
        std     rng_state
        ldx     #position_embeddings
initialize_random_parameter
        lbsr     xorshift16
        anda    #$03
        subd    #$0200
        std     ,x++
        cmpx    #output_biases
        blo     initialize_random_parameter
        clra
        clrb
clear_bias
        std     ,x++
        cmpx    #parameters_end
        blo     clear_bias
        rts

; XorShift16: x ^= x << 7; x ^= x >> 9; x ^= x << 8.
        include "model_forward.asm"

verify_parameters
        ldx     #position_embeddings
        ldu     #expected_parameters
        ldy     #PARAM_BYTES
        clra
        clrb
        std     mismatch_offset
verify_parameter
        lda     ,x+
        cmpa    ,u+
        bne     verify_failed
        ldd     mismatch_offset
        addd    #1
        std     mismatch_offset
        leay    -1,y
        bne     verify_parameter
        lda     #1
        sta     parity_result
        ldd     #$ffff
        std     mismatch_offset
        rts
verify_failed
        sta     mismatch_actual
        lda     -1,u
        sta     mismatch_expected
        clr     parity_result
        rts

; Phase-specific orchestration stays in the experiment drivers. These modules
; supply the common training, inference, and platform-rendering functions.
        include "training.asm"
        include "inference.asm"
        include "screen.asm"
