; EXP-013: Rock Paper Scissors Lizard Spock against an opponent that starts
; knowing neither the rules nor you.
;
; INCOMPLETE. It assembles, runs, and draws a recognisable board, but the
; screen does not yet match src/reference/rpsls_screen.py and must not be
; presented as though it does. Known wrong, from the first simulator dump:
;
;   - the title never draws: draw_board loads the row into A, then clobbers A
;     before calling blit_inverse, so the bar is written over row 1.
;   - row_centred's length arithmetic is wrong (a stray sbca).
;   - lay_string does not advance the column, so the score row's pieces
;     overlap: "YOU HAVE WON qq h" instead of "WON 1 OF 1 (100%)".
;   - the history lays short_names as a terminated string, but the table has
;     no terminators, so one entry spills the whole block.
;   - the result and machine rows come out blank.
;
; The next step is a parity test against the reference's cells(), which is
; what should have been written before this file rather than after it.
;
; Two tables, 100 bytes between them, and nothing else:
;
;   rules   25 cells, one per (my move, your move). Unknown until played, then
;           permanently loss, tie or win. The machine is never told these; it
;           fills them in from what happened, exactly as a person would.
;   counts  15 contexts (your last move x the last outcome) of 5 counts. This
;           is the part that never finishes, because you adapt.
;
; It shows what it expects before you throw, which hands you the way to beat
; it. `R` empties both tables mid-game - EXP-008 called that the falsifiability
; demonstration, because without it nobody can tell learning from a difficulty
; ramp.
;
; No part of this shares code with the token model. The arithmetic is a
; compare and an increment; there is no multiplier in the loop and nothing to
; quantize, which is the finding EXP-008 recorded and this experiment inherited.

MOVE_COUNT      equ     5
OUTCOMES        equ     3
CONTEXTS        equ     MOVE_COUNT*OUTCOMES
HISTORY         equ     7
SCREEN          equ     $0400
POLCAT          equ     $A000
COLS            equ     32
BLANK           equ     $60

UNKNOWN         equ     0
K_LOSS          equ     1
K_TIE           equ     2
K_WIN           equ     3

; Semigraphics-4: 1 C C C L L L L. Bit 7 makes the cell a block rather than a
; letter, bits 6-4 pick the colour, bits 3-0 light the quadrants.
MARK_WIN        equ     $8f             ; green
MARK_TIE        equ     $af             ; blue
MARK_LOSS       equ     $bf             ; red

start
        lds     #$7f00
        ldd     #$1a2b
        std     rng_state
        lbsr    forget_everything
rpsls_round
        lbsr    agent_choose
        sta     agent_move
        lbsr    draw_board
        lbsr    wait_for_move
        cmpa    #$ff
        bne     rpsls_play
        lbsr    forget_everything
        bra     rpsls_round
rpsls_play
        sta     player_move
        lbsr    settle_round
        lbsr    draw_board
        ifdef   DIRECT_TEST
        swi
        else
        bra     rpsls_round
        endc

; Empty both tables. The game's own tallies survive, so the screen shows a
; machine that has forgotten inside a session that has not.
forget_everything
        ldx     #rules
        clra
clear_rules
        sta     ,x+
        cmpx    #rules+MOVE_COUNT*MOVE_COUNT
        blo     clear_rules
        ldx     #counts
clear_counts
        sta     ,x+
        cmpx    #counts+CONTEXTS*MOVE_COUNT
        blo     clear_counts
        clr     memory
        clr     have_context
        rts

; A is the outcome of move A against move B: 0 loss, 1 tie, 2 win.
; a beats b exactly when (a - b) mod 5 is 1 or 2, which is why the moves are
; ordered ROCK SPOCK PAPER LIZARD SCISSORS rather than by name.
outcome_of
        pshs    b
        suba    ,s+
        bpl     outcome_positive
        adda    #MOVE_COUNT
outcome_positive
        tsta
        beq     outcome_tie
        cmpa    #2
        bls     outcome_win
        clra
        rts
outcome_tie
        lda     #1
        rts
outcome_win
        lda     #2
        rts

; XorShift16, the same generator the reference uses.
xorshift
        ldd     rng_state
        std     shift_work
        ldb     #7
xorshift_l7
        lsl     shift_work+1
        rol     shift_work
        decb
        bne     xorshift_l7
        ldd     rng_state
        eora    shift_work
        eorb    shift_work+1
        std     rng_state
        std     shift_work
        ldb     #9
xorshift_r9
        lsr     shift_work
        ror     shift_work+1
        decb
        bne     xorshift_r9
        ldd     rng_state
        eora    shift_work
        eorb    shift_work+1
        std     rng_state
        tfr     a,b
        clra
        eorb    rng_state+1
        eora    rng_state
        std     rng_state
        rts

; B becomes a number below A, by masking and retrying. No divide on a 6809,
; and a modulo would bias the draw low.
draw_below
        sta     draw_limit
        lda     #1
        sta     draw_mask
widen_mask
        lda     draw_mask
        cmpa    draw_limit
        bhs     mask_ready
        lsla
        inca
        sta     draw_mask
        bra     widen_mask
mask_ready
        ldb     #16
        stb     draw_tries
try_draw
        lbsr    xorshift
        andb    draw_mask
        cmpb    draw_limit
        blo     draw_done
        dec     draw_tries
        bne     try_draw
        ldb     draw_limit
        decb
draw_done
        rts

; What it expects you to throw. A is the move; expects_known is zero when the
; context has never been seen, which the screen states rather than showing a
; default as though it were a guess.
predict_player
        clr     expects_known
        clr     expected
        clr     best_move
        clr     best_count
        tst     have_context
        beq     predict_done
        lbsr    context_row
        clr     scan
predict_next
        lda     ,x+
        cmpa    best_count
        bls     predict_skip
        sta     best_count
        lda     scan
        sta     best_move
        lda     #1
        sta     expects_known
predict_skip
        inc     scan
        lda     scan
        cmpa    #MOVE_COUNT
        blo     predict_next
        lda     best_move
        sta     expected
predict_done
        rts

; X becomes the count row for the current context: your last move and the
; last outcome. That pairing is the whole reason this table beats a bigger
; one keyed on more history.
context_row
        lda     last_move
        ldb     #OUTCOMES
        mul
        addb    last_outcome
        lda     #MOVE_COUNT
        mul
        ldx     #counts
        leax    d,x
        rts

; Pick a move: a known win against the expected throw, else a cell never
; played, else a known tie. Exploration is not a mode - an unseen cell simply
; outranks a tie, so curiosity falls out of the ordering.
agent_choose
        lbsr    predict_player
        lda     #K_WIN
        lbsr    best_against
        tstb
        bpl     choose_found
        lda     #UNKNOWN
        lbsr    best_against
        tstb
        bpl     choose_found
        lda     #K_TIE
        lbsr    best_against
        tstb
        bpl     choose_found
        lda     #MOVE_COUNT
        lbsr    draw_below
choose_found
        tfr     b,a
        rts

; B becomes a move whose rules cell against `expected` equals A, or -1.
; Candidates are collected first and one drawn, so a tie between equally good
; moves does not always resolve the same way and make the machine predictable.
best_against
        sta     want
        clr     found
        clr     scan
best_scan
        lda     scan
        ldb     #MOVE_COUNT
        mul
        addb    expected
        ldx     #rules
        abx
        lda     ,x
        cmpa    want
        bne     best_skip
        ldb     found
        ldx     #candidates
        abx
        lda     scan
        sta     ,x
        inc     found
best_skip
        inc     scan
        lda     scan
        cmpa    #MOVE_COUNT
        blo     best_scan
        lda     found
        beq     best_none
        lbsr    draw_below
        ldx     #candidates
        abx
        ldb     ,x
        rts
best_none
        ldb     #$ff
        rts

; Record the round: the rules cell it just proved, the count for what you
; threw, the tallies, and the history the screen draws from.
settle_round
        lda     agent_move
        ldb     player_move
        lbsr    outcome_of
        sta     agent_result

        lda     agent_move
        ldb     #MOVE_COUNT
        mul
        addb    player_move
        ldx     #rules
        abx
        lda     agent_result
        inca                            ; 0,1,2 -> K_LOSS, K_TIE, K_WIN
        sta     ,x

        tst     have_context
        beq     settle_no_context
        lbsr    context_row
        ldb     player_move
        abx
        lda     ,x
        cmpa    #255
        beq     settle_counted
        inca
        sta     ,x
settle_counted
settle_no_context
        lda     player_move
        sta     last_move
        lda     agent_result
        ldb     #2
        pshs    b
        suba    ,s+
        nega                            ; your outcome is the mirror of its
        sta     last_outcome
        lda     #1
        sta     have_context

        lda     rounds
        cmpa    #255
        beq     settle_capped
        inc     rounds
        lda     memory
        cmpa    #255
        beq     settle_capped
        inc     memory
settle_capped
        lda     agent_result
        cmpa    #0
        bne     settle_history
        inc     wins                    ; it lost, so you won
        lbsr    name_the_round
settle_history
        ldx     #history_you
        lbsr    push_history
        lda     player_move
        sta     history_you+HISTORY-1
        ldx     #history_cpu
        lbsr    push_history
        lda     agent_move
        sta     history_cpu+HISTORY-1
        lda     history_len
        cmpa    #HISTORY
        bhs     settle_done
        inc     history_len
settle_done
        rts

; Point the two result lines at the round just played. Winner first, then the
; verb the game uses for that pair, then the loser.
name_the_round
        lda     agent_result
        cmpa    #1
        bne     name_decisive
        ldu     #text_both
        stu     reason_a
        lda     agent_move
        lbsr    move_name
        stu     reason_verb
        ldu     #text_empty
        stu     reason_b
        ldu     #text_tie
        stu     verdict_text
        rts
name_decisive
        ldu     #text_lose
        lda     agent_move
        ldb     player_move
        tst     agent_result
        bne     name_store
        ldu     #text_win
        lda     player_move
        ldb     agent_move
name_store
        stu     verdict_text
        sta     name_winner
        stb     name_loser
        lbsr    move_name
        stu     reason_a
        lda     name_loser
        lbsr    move_name
        stu     reason_b
        lda     name_winner
        ldb     #MOVE_COUNT
        mul
        addb    name_loser
        aslb
        rola
        ldu     #verbs
        ldu     d,u
        stu     reason_verb
        rts

; U becomes the name of move A.
move_name
        ldb     #8
        mul
        ldu     #move_names
        leau    d,u
        rts

; Shift a history row left one, newest lands on the right.
push_history
        ldb     #HISTORY-1
push_next
        lda     1,x
        sta     ,x
        leax    1,x
        decb
        bne     push_next
        rts

; Poll until 1-5, or R to forget. A is the move, or $ff for a reset.
wait_for_move
        ifdef   DIRECT_TEST
        lda     scripted_move
        rts
        else
poll_again
        jsr     [POLCAT]
        beq     poll_again
        cmpa    #'R
        beq     poll_reset
        cmpa    #'r
        beq     poll_reset
        suba    #'1
        bcs     poll_again
        cmpa    #MOVE_COUNT
        bhs     poll_again
        rts
poll_reset
        lda     #$ff
        rts
        endc

; ---------------------------------------------------------------- drawing
;
; Every row is built as 32 ASCII bytes in `line` and then blitted, which keeps
; the layout readable here and matches src/reference/rpsls_screen.py row for
; row. The reference is the design; this is meant to agree with it exactly.

draw_board
        lda     #0
        ldu     #level_name
        lbsr    row_centred
        lda     #1
        lbsr    blit_inverse

        lda     #1
        ldu     #text_keys1
        lbsr    row_text
        lda     #2
        ldu     #text_keys2
        lbsr    row_text
        lbsr    row_score
        lbsr    row_marks
        lbsr    row_throws
        lbsr    row_result
        lbsr    row_machine
        rts

; --- row helpers ---------------------------------------------------------

clear_line
        ldx     #line
        lda     #$20
clear_line_next
        sta     ,x+
        cmpx    #line+COLS
        blo     clear_line_next
        rts

; U is a zero-terminated string, laid into `line` from column B.
lay_string
        pshs    b
        ldx     #line
        abx
lay_next
        lda     ,u+
        beq     lay_done
        cmpx    #line+COLS
        bhs     lay_done
        sta     ,x+
        bra     lay_next
lay_done
        puls    b,pc

; A is the row, U the string: cleared, laid at column 1, blitted as text.
row_text
        pshs    a
        lbsr    clear_line
        ldb     #1
        lbsr    lay_string
        puls    a
        lbra    blit_text

; A is the row, U the string: cleared and centred, left in `line`.
row_centred
        pshs    a
        lbsr    clear_line
        lbsr    string_length
        lda     #COLS
        sbca    #0
        suba    length
        lsra
        tfr     a,b
        lbsr    lay_string
        puls    a
        rts

string_length
        pshs    u
        clr     length
length_next
        lda     ,u+
        beq     length_done
        inc     length
        bra     length_next
length_done
        puls    u,pc

; A is the row. Text cells are the low six bits of uppercase ASCII.
blit_text
        lbsr    row_address
        ldu     #line
        ldb     #COLS
blit_text_next
        lda     ,u+
        anda    #$3f
        sta     ,x+
        decb
        bne     blit_text_next
        rts

; A is the row. Inverse cells are $40-$7F: black on green, the title bar.
blit_inverse
        lbsr    row_address
        ldu     #line
        ldb     #COLS
blit_inverse_next
        lda     ,u+
        ora     #$40
        sta     ,x+
        decb
        bne     blit_inverse_next
        rts

; X becomes the screen address of row A.
row_address
        ldb     #COLS
        mul
        ldx     #SCREEN
        leax    d,x
        rts

; --- the rows themselves -------------------------------------------------

row_score
        lbsr    clear_line
        tst     rounds
        bne     row_score_played
        ldu     #text_no_rounds
        ldb     #1
        lbsr    lay_string
        lda     #3
        lbra    blit_text
row_score_played
        ldu     #text_won
        ldb     #1
        lbsr    lay_string
        ldb     #14
        lda     wins
        lbsr    lay_number
        ldu     #text_of
        lbsr    lay_string
        lda     rounds
        lbsr    lay_number
        ldu     #text_open
        lbsr    lay_string
        lbsr    win_percent
        lbsr    lay_number
        ldu     #text_close
        lbsr    lay_string
        lda     #3
        lbra    blit_text

; A becomes the percentage of rounds won, by repeated subtraction: the 6809
; has no divide and the quotient is at most 100.
win_percent
        lda     wins
        ldb     #100
        mul
        std     percent_top
        clr     percent_out
percent_next
        ldd     percent_top
        clra
        ldb     rounds
        std     percent_div
        ldd     percent_top
        subd    percent_div
        bcs     percent_done
        std     percent_top
        inc     percent_out
        bra     percent_next
percent_done
        lda     percent_out
        rts

; A is the value, B the column: written without padding, B left past the end.
lay_number
        sta     number_value
        stb     number_column
        clr     number_lead
        lda     number_value
        ldb     #100
        lbsr    lay_digit
        ldb     #10
        lbsr    lay_digit
        adda    #'0
        lbsr    lay_char
        ldb     number_column
        rts

lay_digit
        clr     digit_count
lay_digit_sub
        pshs    b
        cmpa    ,s
        blo     lay_digit_done
        suba    ,s
        inc     digit_count
        puls    b
        bra     lay_digit_sub
lay_digit_done
        puls    b
        tst     digit_count
        bne     lay_digit_emit
        tst     number_lead
        beq     lay_digit_ret
lay_digit_emit
        pshs    a
        lda     digit_count
        adda    #'0
        lbsr    lay_char
        inc     number_lead
        puls    a
lay_digit_ret
        rts

lay_char
        pshs    a,b,x
        ldb     number_column
        ldx     #line
        abx
        cmpx    #line+COLS
        bhs     lay_char_done
        puls    a
        pshs    a
        sta     ,x
        inc     number_column
lay_char_done
        puls    a,b,x,pc

; The result strip: one solid block per round, green won, red lost, blue tied.
; Written straight to the screen because these are graphics cells, not text,
; and passing them through the ASCII path would strip the high bit that makes
; them blocks at all.
row_marks
        lda     #5
        lbsr    row_address
        ldb     #COLS
        lda     #BLANK
row_marks_clear
        sta     ,x+
        decb
        bne     row_marks_clear

        lda     #5
        lbsr    row_address
        leax    6,x
        clr     scan
row_marks_next
        lda     scan
        cmpa    history_len
        bhs     row_marks_done
        ldb     #HISTORY
        subb    history_len
        addb    scan
        pshs    x
        ldx     #history_you
        abx
        lda     ,x
        puls    x
        pshs    a
        ldb     #HISTORY
        subb    history_len
        addb    scan
        pshs    x
        ldx     #history_cpu
        abx
        ldb     ,x
        puls    x
        puls    a
        lbsr    outcome_of
        ldb     #MARK_LOSS
        tsta
        beq     row_marks_put
        ldb     #MARK_TIE
        cmpa    #1
        beq     row_marks_put
        ldb     #MARK_WIN
row_marks_put
        stb     ,x
        leax    4,x
        inc     scan
        bra     row_marks_next
row_marks_done
        rts

row_throws
        ldu     #text_you
        lda     #6
        ldy     #history_you
        lbsr    row_trail
        ldu     #text_cpu
        lda     #7
        ldy     #history_cpu
        lbra    row_trail

; U is the label, A the row, Y the history array.
row_trail
        pshs    a
        lbsr    clear_line
        ldb     #1
        lbsr    lay_string
        clr     scan
row_trail_next
        lda     scan
        cmpa    history_len
        bhs     row_trail_done
        ldb     #HISTORY
        subb    history_len
        addb    scan
        leax    b,y
        lda     ,x
        ldb     #3
        mul
        ldu     #short_names
        leau    d,u
        lda     scan
        ldb     #4
        mul
        addb    #5
        lbsr    lay_string
        inc     scan
        bra     row_trail_next
row_trail_done
        puls    a
        lbra    blit_text

; "PAPER COVERS ROCK" is built from three pointers rather than stored as ten
; sentences. The verbs are the game's knowledge, never the agent's: it is told
; only win, tie or loss, and the narration exists for the person.
row_result
        lbsr    clear_line
        tst     rounds
        beq     row_result_blank
        ldb     #1
        ldu     reason_a
        lbsr    lay_string
        lbsr    lay_space
        ldu     reason_verb
        lbsr    lay_string
        lbsr    lay_space
        ldu     reason_b
        lbsr    lay_string
row_result_blank
        lda     #9
        lbsr    blit_text
        lbsr    clear_line
        tst     rounds
        beq     row_result_none
        ldb     #1
        ldu     verdict_text
        lbsr    lay_string
row_result_none
        lda     #10
        lbra    blit_text

; Advance past the string just laid, leaving one space. lay_string leaves B
; where it started, so the caller tracks the column itself.
lay_space
        pshs    a,x,u
        pshs    b
        ldx     #line
        abx
lay_space_next
        lda     ,u+
        beq     lay_space_done
        leax    1,x
        incb
        bra     lay_space_next
lay_space_done
        incb
        leas    1,s
        puls    a,x,u,pc

row_machine
        lbsr    clear_line
        ldb     #1
        tst     expects_known
        bne     row_machine_expects
        ldu     #text_no_idea
        lbsr    lay_string
        bra     row_machine_blit
row_machine_expects
        ldu     #text_expects
        lbsr    lay_string
        lda     expected
        ldb     #8
        mul
        ldu     #move_names
        leau    d,u
        ldb     #12
        lbsr    lay_string
row_machine_blit
        lda     #13
        lbsr    blit_text

        lbsr    clear_line
        ldu     #text_rules
        ldb     #1
        lbsr    lay_string
        lbsr    count_rules
        ldb     #8
        lbsr    lay_number
        ldu     #text_of_25
        lbsr    lay_string
        lda     #14
        lbsr    blit_text

        lbsr    clear_line
        ldu     #text_memory
        ldb     #1
        lbsr    lay_string
        lda     memory
        ldb     #9
        lbsr    lay_number
        ldu     #text_slash
        lbsr    lay_string
        lda     rounds
        lbsr    lay_number
        lda     #15
        lbra    blit_text

; How many of the 25 cells it has proved. Counted rather than tracked, because
; a counter and a table can disagree and the table is the truth.
count_rules
        clrb
        ldx     #rules
count_rules_next
        lda     ,x+
        beq     count_rules_skip
        incb
count_rules_skip
        cmpx    #rules+MOVE_COUNT*MOVE_COUNT
        blo     count_rules_next
        tfr     b,a
        rts

; ---------------------------------------------------------------- strings

text_keys1      fcc     "1 ROCK    2 SPOCK   3 PAPER"
                fcb     0
text_keys2      fcc     "4 LIZARD  5 SCISSORS"
                fcb     0
text_no_rounds  fcc     "NO ROUNDS PLAYED YET"
                fcb     0
text_won        fcc     "YOU HAVE WON"
                fcb     0
text_of         fcc     " OF "
                fcb     0
text_open       fcc     " ("
                fcb     0
text_close      fcc     "%)"
                fcb     0
text_you        fcc     "YOU"
                fcb     0
text_cpu        fcc     "CPU"
                fcb     0
text_no_idea    fcc     "IT HAS NO IDEA YET"
                fcb     0
text_expects    fcc     "IT EXPECTS"
                fcb     0
text_rules      fcc     "RULES"
                fcb     0
text_of_25      fcc     "/25"
                fcb     0
text_memory     fcc     "MEMORY"
                fcb     0
text_slash      fcc     "/"
                fcb     0
text_win        fcc     "YOU WIN"
                fcb     0
text_lose       fcc     "YOU LOSE"
                fcb     0
text_tie        fcc     "A TIE"
                fcb     0
text_both       fcc     "BOTH THREW"
                fcb     0
text_empty      fcb     0

; The title bar. EXP-012 generates these; wiring its generator in place of a
; fixed string is the next step, not a different one.
level_name      fcc     "THE MARK OF GIDEON"
                fcb     0

; Eight bytes each so a move name is found by shifting, not multiplying.
move_names      fcc     "ROCK"
                fcb     0,0,0,0
                fcc     "SPOCK"
                fcb     0,0,0
                fcc     "PAPER"
                fcb     0,0,0
                fcc     "LIZARD"
                fcb     0,0
                fcc     "SCISSORS"

short_names     fcc     "ROCSPOPAPLIZSCI"

; The ten decisive pairs, indexed winner*5+loser. Zero where the pair cannot
; happen, which is every cell a tie or a loss would land in.
verbs           fdb     0,verb_vaporize,0,0,verb_crush          ; ROCK
                fdb     verb_vaporize,0,0,0,verb_smash          ; SPOCK
                fdb     verb_cover,verb_disprove,0,0,0          ; PAPER
                fdb     0,verb_poison,verb_eat,0,0              ; LIZARD
                fdb     0,0,verb_cut,verb_decapitate,0          ; SCISSORS

verb_crush      fcc     "CRUSHES"
                fcb     0
verb_vaporize   fcc     "VAPORIZES"
                fcb     0
verb_smash      fcc     "SMASHES"
                fcb     0
verb_cover      fcc     "COVERS"
                fcb     0
verb_disprove   fcc     "DISPROVES"
                fcb     0
verb_poison     fcc     "POISONS"
                fcb     0
verb_eat        fcc     "EATS"
                fcb     0
verb_cut        fcc     "CUTS"
                fcb     0
verb_decapitate fcc     "DECAPITATES"
                fcb     0

; ---------------------------------------------------------------- storage

rng_state       rmb     2
shift_work      rmb     2
rules           rmb     MOVE_COUNT*MOVE_COUNT
counts          rmb     CONTEXTS*MOVE_COUNT
history_you     rmb     HISTORY
history_cpu     rmb     HISTORY
history_len     rmb     1
agent_move      rmb     1
player_move     rmb     1
agent_result    rmb     1
last_move       rmb     1
last_outcome    rmb     1
have_context    rmb     1
rounds          rmb     1
wins            rmb     1
memory          rmb     1
expected        rmb     1
expects_known   rmb     1
best_move       rmb     1
best_count      rmb     1
scan            rmb     1
want            rmb     1
found           rmb     1
candidates      rmb     MOVE_COUNT
draw_limit      rmb     1
draw_mask       rmb     1
draw_tries      rmb     1
line            rmb     COLS
length          rmb     1
number_value    rmb     1
number_column   rmb     1
number_lead     rmb     1
digit_count     rmb     1
percent_top     rmb     2
percent_div     rmb     2
percent_out     rmb     1
reason_a        rmb     2
reason_verb     rmb     2
reason_b        rmb     2
verdict_text    rmb     2
name_winner     rmb     1
name_loser      rmb     1
        ifdef   DIRECT_TEST
scripted_move   rmb     1
        endc
