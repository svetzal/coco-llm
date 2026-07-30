; Bit-exact integer token language model for the Motorola 6809.
;
; The caller must select an origin, define entry point "start", and provide
; build/model_data.inc. The implementation deliberately favours readable,
; testable arithmetic over final optimization in this first complete port.

SCREEN          equ     $0400
EMBED_DIMS      equ     3
CONTEXT_SIZE    equ     2
POS_BYTES       equ     VOCAB_SIZE*EMBED_DIMS*2
WEIGHT_BYTES    equ     VOCAB_SIZE*EMBED_DIMS*2
BIAS_BYTES      equ     VOCAB_SIZE*2
PARAM_BYTES     equ     PARAM_COUNT*2

start
        lds     #$7f00
        ldx     #SCREEN
        lda     #$60
clear_screen
        sta     ,x+
        cmpx    #SCREEN+512
        blo     clear_screen

        ldx     #SCREEN
        ldu     #message_training
        lbsr     print_string

        lbsr     initialize_model
        lbsr     train_model
        lbsr     verify_parameters

        ldx     #SCREEN+32
        ldu     #message_complete
        lbsr     print_string
        tst     parity_result
        beq     parity_failed
        ldx     #SCREEN+64
        ldu     #message_parity_ok
        lbsr     print_string
        bra     show_samples
parity_failed
        ldx     #SCREEN+64
        ldu     #message_parity_bad
        lbsr     print_string

show_samples
        ldd     #6809
        std     sample_seed
        ldx     #SCREEN+128
        stx     screen_pointer
        lda     #5
        sta     sample_count
sample_loop
        ldd     sample_seed
        std     rng_state
        addd    #1
        std     sample_seed
        lbsr     generate_name
        ldd     screen_pointer
        addd    #32
        std     screen_pointer
        dec     sample_count
        bne     sample_loop

        ifdef   DIRECT_TEST
        swi
        else
finished
        bra     finished
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

train_model
        lda     #TRAIN_EPOCHS
        sta     epochs_remaining
epoch_loop
        ldu     #training_examples
        lda     #EXAMPLE_COUNT
        sta     examples_remaining
example_loop
        lda     ,u+
        sta     current_context
        lda     ,u+
        sta     current_context+1
        lda     ,u+
        sta     current_target
        pshs    u
        lbsr     train_example
        puls    u
        dec     examples_remaining
        bne     example_loop
        dec     epochs_remaining
        bne     epoch_loop
        rts

train_example
        lbsr     forward

        ; output_error aliases probabilities. Subtract 256 at the target.
        lda     current_target
        ldb     #2
        mul
        ldx     #probabilities
        leax    d,x
        ldd     ,x
        subd    #256
        std     ,x

        lbsr     calculate_context_error
        lbsr     update_output_parameters
        lbsr     update_embeddings
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

calculate_context_error
        clr     dimension_index
context_error_dimension
        lda     dimension_index
        ldb     #2
        mul
        ldx     #output_weights
        leax    d,x
        stx     weight_pointer
        ldx     #probabilities
        stx     probability_pointer
        clra
        clrb
        std     accumulator
        lda     #VOCAB_SIZE
        sta     outputs_remaining
context_error_output
        ldx     weight_pointer
        lda     ,x
        ldx     probability_pointer
        lbsr     multiply_s8_s16
        asra
        rorb
        asra
        rorb
        asra
        rorb
        asra
        rorb
        addd    accumulator
        std     accumulator
        ldx     weight_pointer
        leax    6,x
        stx     weight_pointer
        ldx     probability_pointer
        leax    2,x
        stx     probability_pointer
        dec     outputs_remaining
        bne     context_error_output

        lda     dimension_index
        ldb     #2
        mul
        ldx     #context_error
        leax    d,x
        ldd     accumulator
        std     ,x
        inc     dimension_index
        lda     dimension_index
        cmpa    #EMBED_DIMS
        blo     context_error_dimension
        rts

update_output_parameters
        ldx     #output_weights
        stx     weight_pointer
        ldx     #output_biases
        stx     bias_pointer
        ldx     #probabilities
        stx     probability_pointer
        lda     #VOCAB_SIZE
        sta     outputs_remaining
update_output
        ldx     probability_pointer
        ldd     ,x
        ldx     bias_pointer
        lbsr     saturating_subtract

        clr     dimension_index
update_weight
        lda     dimension_index
        ldb     #2
        mul
        ldx     #context_vector
        leax    d,x
        lda     1,x
        ldx     probability_pointer
        lbsr     multiply_s8_s16
        asra
        rorb
        asra
        rorb
        asra
        rorb
        asra
        rorb
        ldx     weight_pointer
        lbsr     saturating_subtract
        ldx     weight_pointer
        leax    2,x
        stx     weight_pointer
        inc     dimension_index
        lda     dimension_index
        cmpa    #EMBED_DIMS
        blo     update_weight

        ldx     bias_pointer
        leax    2,x
        stx     bias_pointer
        ldx     probability_pointer
        leax    2,x
        stx     probability_pointer
        dec     outputs_remaining
        bne     update_output
        rts

update_embeddings
        lda     current_context
        ldx     #position_embeddings
        lbsr     update_one_embedding
        lda     current_context+1
        ldx     #position_embeddings+POS_BYTES
        lbsr     update_one_embedding
        rts

update_one_embedding
        ldb     #6
        mul
        leax    d,x
        stx     embedding_pointer
        ldu     #context_error
        lda     #EMBED_DIMS
        sta     dimensions_remaining
update_embedding_dimension
        ldd     ,u++
        ldx     embedding_pointer
        lbsr     saturating_subtract
        leax    2,x
        stx     embedding_pointer
        dec     dimensions_remaining
        bne     update_embedding_dimension
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

generate_name
        clr     current_context
        clr     current_context+1
        clr     generated_tokens
        lda     #6
        sta     generation_remaining
        ldx     screen_pointer
        lda     #$60
        ldb     #32
clear_sample_line
        sta     ,x+
        decb
        bne     clear_sample_line
        ldx     screen_pointer
        stx     output_pointer
generation_token
        lbsr     forward
        lda     generated_tokens
        cmpa    #2
        bhs     generation_can_end
        ldd     probabilities
        std     removed_boundary
        clra
        clrb
        std     probabilities
        lbsr     find_probability_winner
        lda     winner_index
        ldb     #2
        mul
        ldx     #probabilities
        leax    d,x
        ldd     ,x
        addd    removed_boundary
        std     ,x
generation_can_end
        lbsr     xorshift16
        stb     sample_draw
        clr     chosen_token
        clra
        clrb
        std     sample_cumulative
        ldx     #probabilities
        clr     output_index
choose_token
        ldd     ,x++
        addd    sample_cumulative
        std     sample_cumulative
        tsta
        bne     token_chosen
        cmpb    sample_draw
        bhi     token_chosen
        inc     output_index
        lda     output_index
        cmpa    #VOCAB_SIZE
        blo     choose_token
        clr     output_index
token_chosen
        lda     output_index
        sta     chosen_token
        beq     generation_done
        lbsr     print_chosen_token
        lda     current_context+1
        sta     current_context
        lda     chosen_token
        sta     current_context+1
        inc     generated_tokens
        dec     generation_remaining
        bne     generation_token
generation_done
        rts

find_probability_winner
        ldx     #probabilities
        ldd     ,x++
        std     maximum_probability
        clr     winner_index
        lda     #1
        sta     output_index
        lda     #VOCAB_SIZE-1
        sta     outputs_remaining
find_probability_loop
        ldd     ,x++
        cmpd    maximum_probability
        bls     find_probability_not_winner
        std     maximum_probability
        lda     output_index
        sta     winner_index
find_probability_not_winner
        inc     output_index
        dec     outputs_remaining
        bne     find_probability_loop
        rts

print_chosen_token
        lda     chosen_token
        ldb     #2
        mul
        ldu     #token_pointers
        leau    d,u
        ldu     ,u
        ldx     output_pointer
        lbsr     print_string
        lda     #$20
        sta     ,x+
        stx     output_pointer
        rts

; X is a screen destination, U is a zero-terminated ASCII string. CoCo VDG
; text codes are the low six bits of uppercase ASCII.
print_string
        lda     ,u+
        beq     print_string_done
        anda    #$3f
        sta     ,x+
        bra     print_string
print_string_done
        rts

message_training
        fcc     "COCO LLM TRAINING"
        fcb     0
message_complete
        fcc     "TRAINING COMPLETE"
        fcb     0
message_parity_ok
        fcc     "BIT EXACT: YES"
        fcb     0
message_parity_bad
        fcc     "BIT EXACT: NO"
        fcb     0

        include "../../build/model_data.inc"

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
sample_seed             rmb     2
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

weight_pointer          rmb     2
bias_pointer            rmb     2
logit_pointer           rmb     2
probability_pointer     rmb     2
embedding_pointer       rmb     2
screen_pointer          rmb     2
output_pointer          rmb     2

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
generation_remaining    rmb     1
chosen_token            rmb     1
sample_draw             rmb     1
sample_count            rmb     1
