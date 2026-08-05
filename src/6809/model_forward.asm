; Integer forward pass, softmax and fixed-point arithmetic for the token model.
;
; Split out of model_core.asm so a Mac-trained experiment can run inference
; without assembling the on-CoCo training driver, whose policy hooks and data
; symbols it has no use for. model_core.asm includes this and adds training,
; verification and the experiment interface on top; EXP-012 includes only this.
;
; The include sits exactly where this code used to be, so the five existing
; experiment binaries assemble byte for byte identically. That equality is the
; check that the split changed nothing.

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

