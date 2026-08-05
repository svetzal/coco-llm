; EXP-012: fill the screen with episode titles the CoCo made up.
;
; The Mac trained a model over title *frames* - THE <X> OF THE <X> - and
; nothing else. Nouns come from a table. That split is what makes generation
; possible on 79 titles: the frames repeat, the nouns never do.
;
; Three constraints do the work the model is too small to do, and each is a
; table lookup rather than arithmetic:
;
;   frame_successors  a bit per legal next token. Without it the decoder
;                     invents adjacencies the corpus never states, and emits
;                     things like "TRISKELION THE MAN TRAP".
;   slot_tags_*       which grammatical classes may fill a slot, read from the
;                     word before it and the word after it. This is what
;                     refuses "A TRIBBLES" and "THE GOTHOS".
;   real_titles       two bytes of fingerprint per real episode. A generator
;                     advertised as making them up should not emit one.
;
; A title needs exactly two slots. One is not allowed because every noun the
; corpus will build a whole title from rebuilds its own episode; three chains
; into "THE MAN TO GIDEON TO ELAAN", which the bigram mask cannot see.

SCREEN_ROWS     equ     16
SCREEN_COLS     equ     32
MIN_SLOTS       equ     2
MAX_SLOTS       equ     2
TITLE_ATTEMPTS  equ     120
NO_TOKEN        equ     $ff

start
        lds     #$7f00
        lbsr    load_parameters
        ldd     #$1a2b
        std     rng_state

titles_again
        lbsr    fill_screen
        ifdef   DIRECT_TEST
        swi
        else
wait_key
        jsr     [POLCAT]
        beq     wait_key
        bra     titles_again
        endc

; Copy the Mac's Q4.12 masters into the RAM block model_core.asm expects, so
; the shared forward pass runs against them unaltered.
load_parameters
        ldx     #title_parameters
        ldu     #position_embeddings
copy_parameter
        ldd     ,x++
        std     ,u++
        cmpu    #parameters_end
        blo     copy_parameter
        rts

fill_screen
        ldx     #SCREEN
        lda     #$60
clear_cell
        sta     ,x+
        cmpx    #SCREEN+SCREEN_ROWS*SCREEN_COLS
        blo     clear_cell

        clr     seen_count
        ldx     #SCREEN
        stx     row_pointer
        lda     #SCREEN_ROWS
        sta     rows_left
next_row
        lbsr    make_title
        tst     title_length
        beq     row_blank
        lbsr    print_title
        lbsr    remember_title
row_blank
        ldx     row_pointer
        leax    SCREEN_COLS,x
        stx     row_pointer
        dec     rows_left
        bne     next_row
        rts

; Draw a frame, fill its slots, and keep the result only if it fits the row
; and is not a title anyone has seen. title_length is zero on failure.
make_title
        lda     #TITLE_ATTEMPTS
        sta     attempts_left
title_attempt
        lbsr    sample_frame
        lda     slot_count
        cmpa    #MIN_SLOTS
        blo     title_retry
        cmpa    #MAX_SLOTS
        bhi     title_retry
        lbsr    fill_slots
        tsta
        beq     title_retry
        lbsr    render_title
        lda     title_length
        cmpa    #SCREEN_COLS
        bhi     title_retry
        lbsr    hash_title
        lbsr    title_is_known
        tsta
        beq     make_title_done
title_retry
        dec     attempts_left
        bne     title_attempt
        clr     title_length
make_title_done
        rts

; Sample one frame, one token at a time, from the legal successors only.
sample_frame
        clr     current_context
        clr     current_context+1
        clr     frame_length
        clr     slot_count
sample_token
        lbsr    forward
        lda     current_context+1
        lbsr    successor_pointer
        stx     successor_ptr
        lbsr    legal_total
        ldd     weight_total
        beq     sample_frame_done
        std     draw_limit
        lbsr    draw_below
        lbsr    pick_token
        tsta
        beq     sample_frame_done
        ldb     frame_length
        ldx     #frame_tokens
        abx
        sta     ,x
        inc     frame_length
        cmpa    #SLOT_TOKEN
        bne     sample_not_slot
        inc     slot_count
sample_not_slot
        ldb     current_context+1
        stb     current_context
        sta     current_context+1
        lda     frame_length
        cmpa    #MAX_FRAME
        blo     sample_token
sample_frame_done
        rts

; X becomes the three-byte successor mask for the token in A.
successor_pointer
        ldb     #3
        mul
        ldx     #frame_successors
        leax    d,x
        rts

; Sum the probabilities of every token this one may be followed by.
legal_total
        clra
        clrb
        std     weight_total
        clr     scan_index
        ldu     #probabilities
legal_next
        lbsr    token_is_legal
        beq     legal_skip
        ldd     ,u
        addd    weight_total
        std     weight_total
legal_skip
        leau    2,u
        inc     scan_index
        lda     scan_index
        cmpa    #VOCAB_SIZE
        blo     legal_next
        rts

; Z clear when the token in scan_index may follow the current one.
token_is_legal
        lda     scan_index
        lsra
        lsra
        lsra
        ldx     successor_ptr
        lda     a,x
        ldb     scan_index
        andb    #7
        ldx     #bit_masks
        anda    b,x
        rts

; Walk the legal tokens until the running total passes draw_value.
pick_token
        clra
        clrb
        std     running_total
        clr     scan_index
        ldu     #probabilities
pick_next
        lbsr    token_is_legal
        beq     pick_skip
        ldd     ,u
        addd    running_total
        std     running_total
        cmpd    draw_value
        bhi     pick_found
pick_skip
        leau    2,u
        inc     scan_index
        lda     scan_index
        cmpa    #VOCAB_SIZE
        blo     pick_next
        clra
        rts
pick_found
        lda     scan_index
        rts

; A number below draw_limit, by masking and retrying. The 6809 cannot divide,
; and a modulo would bias the draw toward the low end of the range.
draw_below
        ldd     #1
        std     draw_mask
draw_widen
        ldd     draw_mask
        cmpd    draw_limit
        bhs     draw_ready
        aslb
        rola
        addd    #1
        std     draw_mask
        bra     draw_widen
draw_ready
        lda     #16
        sta     draw_tries
draw_try
        lbsr    xorshift16
        anda    draw_mask
        andb    draw_mask+1
        std     draw_value
        cmpd    draw_limit
        blo     draw_done
        dec     draw_tries
        bne     draw_try
        ldd     draw_limit
        subd    #1
        std     draw_value
draw_done
        rts

; Choose a noun for each slot. A is zero when a slot cannot be filled.
fill_slots
        clr     slot_index
fill_next_slot
        lbsr    slot_mask
        lbsr    count_candidates
        lda     cand_count
        beq     fill_failed
        clra
        ldb     cand_count
        std     draw_limit
        lbsr    draw_below
        lbsr    take_candidate
        ldb     slot_index
        ldx     #noun_choice
        abx
        sta     ,x
        inc     slot_index
        lda     slot_index
        cmpa    slot_count
        blo     fill_next_slot
        lda     #1
        rts
fill_failed
        clra
        rts

; The admissible tag mask for slot_index, from the words either side of it.
; slot_before holds NO_TOKEN when the slot opens the title, which is the one
; case a bare singular may not fill unless the corpus opened a title with it.
slot_mask
        lbsr    locate_slot
        lda     #TAG_ALL
        ldb     slot_before
        cmpb    #NO_TOKEN
        beq     slot_mask_after
        ldx     #slot_tags_after
        abx
        lda     ,x
slot_mask_after
        ldb     slot_after
        cmpb    #NO_TOKEN
        beq     slot_mask_done
        ldx     #slot_tags_before
        abx
        anda    ,x
slot_mask_done
        sta     tag_mask
        rts

; Find the frame position of slot_index and record its two neighbours.
locate_slot
        clr     scan_index
        clr     slot_seen
        ldx     #frame_tokens
locate_next
        lda     ,x
        cmpa    #SLOT_TOKEN
        bne     locate_step
        lda     slot_seen
        cmpa    slot_index
        beq     locate_found
        inc     slot_seen
locate_step
        leax    1,x
        inc     scan_index
        lda     scan_index
        cmpa    frame_length
        blo     locate_next
locate_found
        lda     #NO_TOKEN
        sta     slot_before
        sta     slot_after
        tst     scan_index
        beq     locate_no_before
        lda     -1,x
        sta     slot_before
locate_no_before
        lda     scan_index
        inca
        cmpa    frame_length
        bhs     locate_done
        lda     1,x
        sta     slot_after
locate_done
        rts

; How many nouns satisfy tag_mask, are allowed to open a title when that is
; what the slot is, and have not already been used in this title.
count_candidates
        clr     cand_count
        clr     scan_index
        ldx     #noun_tags
count_next
        lda     ,x+
        lbsr    noun_admissible
        beq     count_skip
        inc     cand_count
count_skip
        inc     scan_index
        lda     scan_index
        cmpa    #NOUN_COUNT
        blo     count_next
        rts

; The cand_count'th admissible noun, by index, returned in A.
take_candidate
        clr     cand_index
        clr     scan_index
        ldx     #noun_tags
take_next
        lda     ,x+
        lbsr    noun_admissible
        beq     take_skip
        clra
        ldb     cand_index
        cmpd    draw_value
        beq     take_found
        inc     cand_index
take_skip
        inc     scan_index
        lda     scan_index
        cmpa    #NOUN_COUNT
        blo     take_next
        clr     scan_index
take_found
        lda     scan_index
        rts

; Z clear when the noun whose tag byte is in A may fill the current slot.
noun_admissible
        pshs    b
        bita    tag_mask
        beq     noun_rejected
        tst     slot_before
        bpl     noun_check_used         ; NO_TOKEN is $ff, so negative
        bita    #TAG_NS
        beq     noun_check_used
        bita    #TAG_OPENS
        beq     noun_rejected
noun_check_used
        tst     slot_index
        beq     noun_accepted
        ldb     noun_choice
        cmpb    scan_index
        beq     noun_rejected
noun_accepted
        lda     #1
        puls    b,pc
noun_rejected
        clra
        puls    b,pc

; Assemble the title into title_buffer, with title_length set.
render_title
        ldx     #title_buffer
        stx     render_cursor
        clr     scan_index
        clr     slot_seen
render_next
        lda     scan_index
        cmpa    frame_length
        bhs     render_done
        tst     scan_index
        beq     render_no_space
        ldx     render_cursor
        lda     #$20
        sta     ,x+
        stx     render_cursor
render_no_space
        lbsr    render_item
        ldx     render_cursor
render_character
        lda     ,u+
        beq     render_step
        sta     ,x+
        bra     render_character
render_step
        stx     render_cursor
        inc     scan_index
        bra     render_next
render_done
        ldx     render_cursor
        clr     ,x
        tfr     x,d
        subd    #title_buffer
        stb     title_length
        rts

; U becomes the text for the frame position in scan_index.
render_item
        ldb     scan_index
        ldx     #frame_tokens
        lda     b,x
        cmpa    #SLOT_TOKEN
        beq     render_item_slot
        cmpa    #ARTICLE_A
        beq     render_item_article
        cmpa    #ARTICLE_AN
        beq     render_item_article
        lbra    frame_word_pointer
render_item_slot
        ldb     slot_seen
        inc     slot_seen
        ldx     #noun_choice
        abx
        lda     ,x
        lbra    noun_pointer

; "A" or "AN", decided by the first letter of whatever follows it. The frame
; carries whichever article its source title happened to use, so choosing here
; is what keeps "A EYE" and "AN GUN" off the screen.
render_item_article
        lbsr    next_initial
        lbsr    is_vowel
        ldu     #article_a
        tsta
        beq     render_item_done
        ldu     #article_an
render_item_done
        rts

; A becomes the first character of the frame position after scan_index.
next_initial
        lda     scan_index
        inca
        cmpa    frame_length
        bhs     next_initial_none
        sta     next_index
        ldb     next_index
        ldx     #frame_tokens
        lda     b,x
        cmpa    #SLOT_TOKEN
        beq     next_initial_slot
        lbsr    frame_word_pointer
        bra     next_initial_char
next_initial_slot
        ldb     slot_seen
        ldx     #noun_choice
        abx
        lda     ,x
        lbsr    noun_pointer
next_initial_char
        lda     ,u
        rts
next_initial_none
        clra
        rts

is_vowel
        cmpa    #'A
        beq     is_vowel_yes
        cmpa    #'E
        beq     is_vowel_yes
        cmpa    #'I
        beq     is_vowel_yes
        cmpa    #'O
        beq     is_vowel_yes
        cmpa    #'U
        beq     is_vowel_yes
        clra
        rts
is_vowel_yes
        lda     #1
        rts

; A is a token index, U becomes its text.
frame_word_pointer
        ldb     #2
        mul
        ldu     #frame_word_table
        ldu     d,u
        rts

; A is a noun index, U becomes its text.
noun_pointer
        ldb     #2
        mul
        ldu     #noun_table
        ldu     d,u
        rts

; work_hash = value*31 + character, over the rendered title. Two bytes is
; enough to refuse the 79 real episodes and the fifteen rows already on
; screen; a false match only discards a title nobody would have missed.
hash_title
        clra
        clrb
        std     work_hash
        ldx     #title_buffer
hash_next
        lda     ,x+
        beq     hash_done
        pshs    a
        ldd     work_hash
        pshs    d
        aslb
        rola
        aslb
        rola
        aslb
        rola
        aslb
        rola
        aslb
        rola
        subd    ,s++
        addb    ,s+
        adca    #0
        std     work_hash
        bra     hash_next
hash_done
        rts

; A is one when this title is a real episode or is already on the screen.
title_is_known
        ldx     #real_titles
        ldb     #REAL_COUNT
        lbsr    scan_hashes
        tsta
        bne     title_is_known_done
        ldb     seen_count
        beq     title_is_known_done
        ldx     #seen_hashes
        lbsr    scan_hashes
title_is_known_done
        rts

scan_hashes
        tstb
        beq     scan_hashes_none
scan_hashes_next
        pshs    b
        ldd     ,x++
        cmpd    work_hash
        puls    b
        beq     scan_hashes_found
        decb
        bne     scan_hashes_next
scan_hashes_none
        clra
        rts
scan_hashes_found
        lda     #1
        rts

remember_title
        ldb     seen_count
        aslb
        ldx     #seen_hashes
        abx
        ldd     work_hash
        std     ,x
        inc     seen_count
        rts

; VDG text codes are the low six bits of uppercase ASCII.
print_title
        ldx     row_pointer
        ldu     #title_buffer
print_title_character
        lda     ,u+
        beq     print_title_done
        anda    #$3f
        sta     ,x+
        bra     print_title_character
print_title_done
        rts

bit_masks       fcb     $01,$02,$04,$08,$10,$20,$40,$80
article_a       fcb     $41,0
article_an      fcb     $41,$4e,0

; Working storage. The model's own state lives in model_storage.asm.
frame_tokens    rmb     MAX_FRAME
frame_length    rmb     1
slot_count      rmb     1
slot_index      rmb     1
slot_seen       rmb     1
slot_before     rmb     1
slot_after      rmb     1
tag_mask        rmb     1
noun_choice     rmb     MAX_SLOTS
cand_count      rmb     1
cand_index      rmb     1
scan_index      rmb     1
next_index      rmb     1
successor_ptr   rmb     2
weight_total    rmb     2
running_total   rmb     2
draw_mask       rmb     2
draw_value      rmb     2
draw_limit      rmb     2
draw_tries      rmb     1
title_buffer    rmb     SCREEN_COLS+2
title_length    rmb     1
render_cursor   rmb     2
work_hash       rmb     2
seen_hashes     rmb     SCREEN_ROWS*2
seen_count      rmb     1
attempts_left   rmb     1
row_pointer     rmb     2
rows_left       rmb     1
