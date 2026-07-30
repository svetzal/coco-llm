; Bit-exact integer token language model for the Motorola 6809.
;
; The caller must select an origin, define entry point "start", and provide
; build/model_data.inc. The implementation deliberately favours readable,
; testable arithmetic over final optimization in this first complete port.

SCREEN          equ     $0400
POLCAT          equ     $A000
KEY_UP          equ     $5e
KEY_DOWN        equ     $0a
KEY_ENTER       equ     $0d
EMBED_DIMS      equ     3
CONTEXT_SIZE    equ     2
POS_BYTES       equ     VOCAB_SIZE*EMBED_DIMS*2
WEIGHT_BYTES    equ     VOCAB_SIZE*EMBED_DIMS*2
BIAS_BYTES      equ     VOCAB_SIZE*2
PARAM_BYTES     equ     PARAM_COUNT*2

start
        lds     #$7f00
        lbsr    initialize_training_screen
        lbsr     initialize_model
        lbsr     train_model
        lbsr     verify_parameters
        lbsr    show_training_complete
        tst     parity_result
        beq     verification_failed
        ifndef  DIRECT_TEST
wait_for_key
        jsr     [POLCAT]
        beq     wait_for_key
        endc
        lbra    show_samples
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
xorshift16
        ldd     rng_state
        std     shift_temp
        std     shift_left
        ldb     #7
xorshift_left7
        lsl     shift_left+1
        rol     shift_left
        decb
        bne     xorshift_left7
        ldd     shift_temp
        eora    shift_left
        eorb    shift_left+1
        std     shift_temp
        lsra
        sta     shift_right
        ldd     shift_temp
        eorb    shift_right
        std     shift_temp
        eora    shift_temp+1
        std     rng_state
        rts

; Produce the three-value context vector, all logits, and probabilities.
forward
        clra
        clrb
        std     context_vector
        std     context_vector+2
        std     context_vector+4

        lda     current_context
        ldx     #position_embeddings
        lbsr     add_embedding
        lda     current_context+1
        ldx     #position_embeddings+POS_BYTES
        lbsr     add_embedding

        ldx     #output_weights
        stx     weight_pointer
        ldx     #output_biases
        stx     bias_pointer
        ldx     #logits
        stx     logit_pointer
        lda     #VOCAB_SIZE
        sta     outputs_remaining
forward_output
        ldx     bias_pointer
        lda     ,x
        tfr     a,b
        sex
        aslb
        rola
        aslb
        rola
        aslb
        rola
        aslb
        rola
        std     accumulator

        ldx     weight_pointer
        ldu     #context_vector
        lda     #EMBED_DIMS
        sta     dimensions_remaining
forward_dimension
        lda     ,x
        pshs    x,u
        tfr     u,x
        lbsr     multiply_s8_s16
        puls    x,u
        addd    accumulator
        std     accumulator
        leax    2,x
        leau    2,u
        dec     dimensions_remaining
        bne     forward_dimension

        ldd     accumulator
        ldu     logit_pointer
        std     ,u
        leau    2,u
        stu     logit_pointer
        stx     weight_pointer
        ldx     bias_pointer
        leax    2,x
        stx     bias_pointer
        dec     outputs_remaining
        bne     forward_output

        lbsr     softmax
        rts

; A is a token identifier and X is the relevant positional embedding table.
add_embedding
        ldb     #6
        mul
        leax    d,x
        ldu     #context_vector
        lda     #EMBED_DIMS
        sta     dimensions_remaining
add_embedding_dimension
        lda     ,x
        tfr     a,b
        sex
        addd    ,u
        std     ,u
        leax    2,x
        leau    2,u
        dec     dimensions_remaining
        bne     add_embedding_dimension
        rts

softmax
        ldx     #logits
        ldd     ,x++
        std     maximum_logit
        lda     #VOCAB_SIZE-1
        sta     outputs_remaining
find_maximum_logit
        ldd     ,x++
        cmpd    maximum_logit
        ble     maximum_logit_kept
        std     maximum_logit
maximum_logit_kept
        dec     outputs_remaining
        bne     find_maximum_logit

        ldx     #logits
        stx     logit_pointer
        ldu     #exponentials
        clra
        clrb
        std     exponential_total
        lda     #VOCAB_SIZE
        sta     outputs_remaining
make_exponential
        ldx     logit_pointer
        ldd     maximum_logit
        subd    ,x
        lsra
        rorb
        lsra
        rorb
        lsra
        rorb
        tsta
        beq     exponential_distance_ready
        ldb     #$ff
exponential_distance_ready
        ldx     #exp_lut
        abx
        lda     ,x
        sta     ,u+
        tfr     a,b
        clra
        addd    exponential_total
        std     exponential_total
        ldx     logit_pointer
        leax    2,x
        stx     logit_pointer
        dec     outputs_remaining
        bne     make_exponential

        ; Divide $10000 + total/2 by total. The maximum exponential is 255,
        ; so this model's reciprocal always fits in one byte.
        ldd     exponential_total
        lsra
        rorb
        std     division_numerator+1
        lda     #1
        sta     division_numerator
        clr     reciprocal
reciprocal_loop
        lda     division_numerator
        bne     reciprocal_subtract
        ldd     division_numerator+1
        cmpd    exponential_total
        blo     reciprocal_ready
reciprocal_subtract
        ldd     division_numerator+1
        subd    exponential_total
        std     division_numerator+1
        lda     division_numerator
        sbca    #0
        sta     division_numerator
        inc     reciprocal
        bra     reciprocal_loop
reciprocal_ready

        ldx     #exponentials
        ldu     #probabilities
        clra
        clrb
        std     probability_total
        std     maximum_probability
        clr     winner_index
        clr     output_index
        lda     #VOCAB_SIZE
        sta     outputs_remaining
make_probability
        lda     ,x+
        ldb     reciprocal
        mul
        addd    #$0080
        tfr     a,b
        clra
        std     ,u++
        addd    probability_total
        std     probability_total
        ldd     -2,u
        cmpd    maximum_probability
        bls     probability_not_winner
        std     maximum_probability
        lda     output_index
        sta     winner_index
probability_not_winner
        inc     output_index
        dec     outputs_remaining
        bne     make_probability

        ldd     #256
        subd    probability_total
        std     correction
        lda     winner_index
        ldb     #2
        mul
        ldx     #probabilities
        leax    d,x
        ldd     ,x
        addd    correction
        std     ,x
        rts

; X points to a signed 16-bit master parameter; D is the signed update.
saturating_subtract
        std     arithmetic_update
        ldd     ,x
        std     arithmetic_original
        subd    arithmetic_update
        bvc     subtraction_in_range
        tst     arithmetic_original
        bmi     subtraction_negative_overflow
        ldd     #$7fff
        bra     subtraction_in_range
subtraction_negative_overflow
        ldd     #$8000
subtraction_in_range
        std     ,x
        rts

; Signed 8-bit A times signed 16-bit [X], returning the low 16-bit product in D.
;
; Two unsigned MUL instructions form the low word. Interpreting a negative A
; as its unsigned byte adds 256*[X], so subtract the multiplier's low byte from
; the result's high byte to correct it. All measured products for the fixed
; corpus fit signed 16 bits, making the low word the complete signed result.
multiply_s8_s16
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
        bpl     multiply_ready
        lda     multiply_product
        suba    1,x
        sta     multiply_product
multiply_ready
        ldd     multiply_product
        rts

        ifdef   EXPERIMENT_5
; Signed 16-bit D times signed 16-bit [X], returning the low 16-bit product.
; Three unsigned MUL instructions form that low word. Two's-complement signed
; and unsigned multiplication have the same low word; measured EXP-005
; products fit signed 16 bits, so the low word is the complete result.
multiply_s16_s16
        std     multiply_factor16
        lda     multiply_factor16+1
        ldb     1,x
        mul
        std     multiply_product
        lda     multiply_factor16
        ldb     1,x
        mul
        addb    multiply_product
        stb     multiply_product
        lda     multiply_factor16+1
        ldb     ,x
        mul
        addb    multiply_product
        stb     multiply_product
        ldd     multiply_product
        rts
        endc

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

; Phase-specific orchestration and platform rendering stay out of the shared
; model machinery above. Forward references let these modules call one another
; while this file remains the single composition root for both experiments.
        include "training.asm"
        include "inference.asm"
        include "screen.asm"

        ifdef   EXPERIMENT_5
        include "../../build/model_data_exp5.inc"
        else
        include "../../build/model_data.inc"
        endc

; Trainable Q4.12 master parameters are one contiguous block so the test build
; can compare every byte with the Python reference fixture.
position_embeddings
        rmb     POS_BYTES*CONTEXT_SIZE
output_weights
        rmb     WEIGHT_BYTES
output_biases
        rmb     BIAS_BYTES
parameters_end

context_vector          rmb     6
logits                  rmb     VOCAB_SIZE*2
exponentials            rmb     VOCAB_SIZE
probabilities           rmb     VOCAB_SIZE*2
context_error           rmb     6

rng_state               rmb     2
sample_seed_pointer     rmb     2
shift_temp              rmb     2
shift_left              rmb     2
shift_right             rmb     1
accumulator             rmb     2
maximum_logit           rmb     2
exponential_total       rmb     2
division_numerator      rmb     3
reciprocal              rmb     1
probability_total       rmb     2
maximum_probability     rmb     2
correction              rmb     2
removed_boundary        rmb     2
sample_cumulative       rmb     2
arithmetic_update       rmb     2
arithmetic_original     rmb     2
multiply_product        rmb     2
        ifdef   EXPERIMENT_5
multiply_factor16       rmb     2
        endc

weight_pointer          rmb     2
bias_pointer            rmb     2
logit_pointer           rmb     2
probability_pointer     rmb     2
embedding_pointer       rmb     2
screen_pointer          rmb     2
output_pointer          rmb     2
output_limit            rmb     2

current_context         rmb     2
current_target          rmb     1
epochs_remaining        rmb     1
examples_remaining      rmb     1
outputs_remaining       rmb     1
dimensions_remaining    rmb     1
dimension_index         rmb     1
output_index            rmb     1
winner_index            rmb     1
parity_result           rmb     1
mismatch_offset         rmb     2
mismatch_actual         rmb     1
mismatch_expected       rmb     1
multiply_factor         rmb     1
generated_tokens        rmb     1
        ifdef   EXPERIMENT_5
selected_prompt         rmb     1
prompts_remaining       rmb     1
prompt_context_pointer  rmb     2
prompt_row_pointer      rmb     2
        endc
generation_remaining    rmb     1
chosen_token            rmb     1
sample_draw             rmb     1
sample_count            rmb     1
last_epoch_displayed    rmb     1
generation_display_full rmb     1
