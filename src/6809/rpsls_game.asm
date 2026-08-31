; EXP-013: Rock Paper Scissors Lizard Spock against an opponent that starts
; knowing neither the rules nor you.
;
; The screen is verified against src/reference/rpsls_screen.py: all three
; cases in tools/make_rpsls_parity_test.py match every one of the 512 cells.
;
; The opponent is verified too: tools/make_rpsls_agent_test.py runs 38
; scripted throws through this loop and compares the move it chose every
; round against src/reference/rpsls.py, along with the rules it ended up
; holding. That is what carries EXP-013's numbers onto the machine - the
; board test only proves the screen.
;
; The drawing itself is text_screen.asm's - the two VDG character sets, the
; blank each one carries, and screen_title_bar. This file had its own copies
; and chose the wrong set, drawing the body reversed and the title bar plain,
; so the whole board came out inverted. A parity test cannot catch that: it
; compares the CoCo against a reference that was equally free to guess.
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

; A whole session fits in RAM easily, so it is kept: every throw, the move the
; machine answered with, and what it expected before either. `Q` ends the
; session and parks the program on a label XRoar can trap, which is how the
; game gets its own moves out to be scored. Playing the real thing and
; measuring a stand-in for it are not the same evidence.
LOG_MAX         equ     200
LOG_RESETS      equ     16
NO_EXPECTATION  equ     $ff

MOVE_COUNT      equ     5
OUTCOMES        equ     3
CONTEXTS        equ     MOVE_COUNT*OUTCOMES
HISTORY         equ     7
POLCAT          equ     $A000
; The screen, its two character sets, and the title bar live in
; text_screen.asm. COLS and BLANK are that module's, so the body cannot be
; drawn in one character set and the title in the other by accident - which is
; exactly how this screen came out inverted.
COLS            equ     SCREEN_COLS
BLANK           equ     BODY_BLANK

UNKNOWN         equ     0
K_LOSS          equ     1
K_TIE           equ     2
K_WIN           equ     3

; Semigraphics-4: 1 C C C L L L L. Bit 7 makes the cell a block rather than a
; letter, bits 6-4 pick the colour, bits 3-0 light the quadrants.
MARK_WIN        equ     $8f             ; green
MARK_TIE        equ     $af             ; blue
MARK_LOSS       equ     $bf             ; red
; An inverse-video space: an all-black cell. The play field rows sit on
; black so the marks' colours land on it rather than on the body green.
BLACK_BLANK     equ     $20

start
        lds     #$7f00
        ldd     #$1a2b
        std     rng_state
        lbsr    new_game
rpsls_round
        lbsr    agent_choose
        sta     agent_move
        lbsr    draw_board
        lbsr    wait_for_move
        cmpa    #$fe
        beq     session_done
        cmpa    #$ff
        bne     rpsls_play
        lbsr    log_reset
        lbsr    forget_everything
        bra     rpsls_round
rpsls_play
        sta     player_move
        lbsr    settle_round
        lbsr    draw_board
        bra     rpsls_round

; `Q`: park on a label a snapshot can be taken at. The loop is deliberate -
; the session has to still be in RAM when the trap fires.
session_done
        ldu     #text_saved
        lbsr    centre_notice
session_halt
        bra     session_halt

; U is a message, written across the continuation row, which is blank unless a
; long rule wrapped into it.
centre_notice
        pshs    u
        lbsr    screen_text_length
        lda     #11
        lbsr    screen_row_address
        lda     #SCREEN_COLS
        suba    screen_length
        lsra
        tfr     a,b
        abx
        puls    u
centre_notice_next
        lda     ,u+
        beq     centre_notice_done
        ora     #$40
        sta     ,x+
        bra     centre_notice_next
centre_notice_done
        rts

; A new session: the tables and everything the screen reads. `rmb` reserves
; RAM without clearing it, so the first board reported 255 rounds played, a
; history eight throws long, and a rule with no verb in it - all of it read
; out of whatever the machine happened to be holding.
new_game
        ifdef   DIRECT_TEST
        clr     script_index
        endc
        lbsr    forget_everything
        clr     rounds
        clr     wins
        clr     history_len
        clr     last_move
        clr     last_outcome
        clr     expected
        clr     expects_known
        clr     wrap_needed
        clr     agent_move
        clr     player_move
        clr     agent_result
        clr     log_count
        clr     log_reset_count
        ldx     #history_you
        clra
new_game_history
        sta     ,x+
        cmpx    #history_cpu+HISTORY
        blo     new_game_history
        rts

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
        ; value ^= value << 8. Shifting a 16-bit value left eight puts its low
        ; byte in the high half and zero in the low, so only the high byte
        ; changes. The first version built the shifted word with the halves
        ; the wrong way round and diverged from the reference on its very
        ; first draw.
        ldd     rng_state
        pshs    b
        eora    ,s+
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
        ; Logged first, and unconditionally. Nothing it records changes during
        ; the rest of this routine, and placed further down it sat inside the
        ; branch taken only when the player won - so the log held one entry per
        ; win rather than one per round.
        lbsr    log_round
        lda     agent_move
        ldb     player_move
        lbsr    outcome_of
        sta     agent_result
        ; Both of these belong to every round. Sitting below, they were inside
        ; the branch taken only when the player won, so a losing round kept the
        ; previous winning round's verdict on screen and never reached the log.
        lbsr    name_the_round

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
        pshs    x
        ldb     player_move
        abx
        lda     ,x
        inca
        sta     ,x
        puls    x
        cmpa    #255
        blo     settle_counted
        lbsr    halve_context
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

; U becomes the name of move A. B is the caller's column and survives: the
; multiply needs B, and taking it silently laid every move name at the offset
; it had just computed instead of where the row was up to.
move_name
        pshs    b
        ldb     #8
        mul
        ldu     #move_names
        leau    d,u
        puls    b,pc

; Halve every count in the row X addresses. A byte counter cannot hold more,
; and halving is what makes the table forget: a player who changes tactics
; sees their old habit fade rather than stay on the books forever. The first
; version capped at 255 instead, which never forgets and disagrees with the
; reference the moment any count saturates.
halve_context
        ldb     #MOVE_COUNT
halve_next
        lda     ,x
        lsra
        sta     ,x+
        decb
        bne     halve_next
        rts

; Append the round to the session log. Kept separate from the tables because
; it is evidence rather than state: nothing reads it back, and forgetting must
; not erase it.
log_round
        lda     log_count
        cmpa    #LOG_MAX
        bhs     log_round_done
        ldb     log_count
        ldx     #log_player
        abx
        lda     player_move
        sta     ,x
        ldb     log_count
        ldx     #log_agent
        abx
        lda     agent_move
        sta     ,x
        ldb     log_count
        ldx     #log_expected
        abx
        lda     #NO_EXPECTATION
        tst     expects_known
        beq     log_round_store
        lda     expected
log_round_store
        sta     ,x
        inc     log_count
log_round_done
        rts

; Note where the tables were emptied, so a replay knows the machine's memory
; restarted while the session did not.
log_reset
        lda     log_reset_count
        cmpa    #LOG_RESETS
        bhs     log_reset_done
        ldb     log_reset_count
        ldx     #log_resets
        abx
        lda     log_count
        sta     ,x
        inc     log_reset_count
log_reset_done
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
;
; Under DIRECT_TEST the throws come from a table instead of the keyboard, and
; the move the agent chose is recorded before each one. That is what a parity
; test compares: the screen was proved separately, and what remains is whether
; the 100 bytes of table behave like the reference they were measured on.
wait_for_move
        ifdef   DIRECT_TEST
        ldb     script_index
        ldx     #script
        abx
        lda     ,x
        cmpa    #$fe
        beq     script_exhausted
        ldx     #trace_agent
        abx
        pshs    a
        lda     agent_move
        sta     ,x
        puls    a
        inc     script_index
        rts
script_exhausted
        swi
        else
poll_again
        jsr     [POLCAT]
        beq     poll_again
        cmpa    #'R
        beq     poll_reset
        cmpa    #'r
        beq     poll_reset
        cmpa    #'Q
        beq     poll_quit
        cmpa    #'q
        beq     poll_quit
        suba    #'1
        bcs     poll_again
        cmpa    #MOVE_COUNT
        bhs     poll_again
        rts
poll_reset
        lda     #$ff
        rts
poll_quit
        lda     #$fe
        rts
        endc

; ---------------------------------------------------------------- drawing
;
; Every row is built as 32 ASCII bytes in `line` and then blitted, which keeps
; the layout readable here and matches src/reference/rpsls_screen.py row for
; row. The reference is the design; this is meant to agree with it exactly.

draw_board
        lbsr    screen_clear
        ldu     #level_name
        lbsr    screen_title_bar

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

; --- laying text into one row ---------------------------------------------
;
; Every row is built as 32 ASCII bytes in `line` and then blitted. B is the
; column throughout and every lay advances it, so a row reads as the sentence
; it draws. The first version left B where it started and each row wrote its
; pieces on top of the last.

clear_line
        ldx     #line
        lda     #$20
clear_line_next
        sta     ,x+
        cmpx    #line+COLS
        blo     clear_line_next
        rts

; U is a zero-terminated string, B the column. B ends past the last character.
lay_string
        pshs    x
        ldx     #line
        abx
lay_next
        lda     ,u+
        beq     lay_done
        cmpx    #line+COLS
        bhs     lay_done
        sta     ,x+
        incb
        bra     lay_next
lay_done
        puls    x,pc

; U is a source, A a count, B the column: exactly A characters, no terminator
; wanted. The three-letter history names are packed end to end, so laying one
; as a string spills the whole table.
lay_fixed
        pshs    x,a
        ldx     #line
        abx
lay_fixed_next
        lda     ,u+
        cmpx    #line+COLS
        bhs     lay_fixed_skip
        sta     ,x+
        incb
lay_fixed_skip
        dec     ,s
        bne     lay_fixed_next
        puls    a,x,pc

; One space, by stepping over a cell `line` already holds blank.
lay_gap
        incb
        rts

; A is the character, laid at number_column, which advances.
lay_char
        pshs    a,b,x
        ldb     number_column
        cmpb    #COLS
        bhs     lay_char_done
        ldx     #line
        abx
        lda     ,s
        sta     ,x
        inc     number_column
lay_char_done
        puls    a,b,x,pc

; A is the value, B the column: laid unpadded, B ends past it.
lay_number
        stb     number_column
lay_number_here
        sta     number_value
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

; A is the value, B the column, number_width the field: right-aligned. No
; padding is written, because `line` already holds spaces.
lay_number_right
        sta     number_value
        stb     number_column
        lbsr    count_digits
        pshs    a
        lda     number_width
        suba    ,s+
        adda    number_column
        sta     number_column
        lda     number_value
        lbra    lay_number_here

count_digits
        lda     number_value
        cmpa    #100
        bhs     count_three
        cmpa    #10
        bhs     count_two
        lda     #1
        rts
count_two
        lda     #2
        rts
count_three
        lda     #3
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

; A is the row, U the string: cleared, laid at column 1, blitted as text.
row_text
        pshs    a
        pshs    u
        lbsr    clear_line
        puls    u
        ldb     #0
        lbsr    lay_string
        puls    a
        lbra    blit_line

; The board builds each row in `line`; the shared blitter takes its buffer in
; U, so this is where the two meet.
blit_line
        ldu     #line
        lbra    screen_blit_body

; The play-field rows are green on black, so the score marks' colours sit
; on black. Same buffer, inverse blit.
blit_line_inverse
        ldu     #line
        lbra    screen_blit_body_inverse

; --- the rows themselves -------------------------------------------------

row_score
        lbsr    clear_line
        tst     rounds
        bne     row_score_played
        ldu     #text_no_rounds
        ldb     #0
        lbsr    lay_string
        lda     #3
        lbra    blit_line
row_score_played
        ldb     #0
        ldu     #text_won
        lbsr    lay_string
        lda     wins
        lbsr    lay_number
        ldu     #text_of
        lbsr    lay_string
        lda     rounds
        lbsr    lay_number
        ldu     #text_open
        lbsr    lay_string
        pshs    b
        lbsr    win_percent
        puls    b
        lbsr    lay_number
        ldu     #text_close
        lbsr    lay_string
        lda     #3
        lbra    blit_line

; A becomes the share of rounds won: wins * 100 / rounds by repeated
; subtraction. There is no divide, and the quotient is at most 100.
win_percent
        lda     wins
        ldb     #100
        mul
        std     percent_top
        clra                            ; half a round, so the share rounds
        ldb     rounds                  ; up rather than truncating: 2 of 7
        lsrb                            ; is 29%, not 28%
        addd    percent_top
        std     percent_top
        clr     percent_out
        clra
        ldb     rounds
        std     percent_div
percent_next
        ldd     percent_top
        subd    percent_div
        bcs     percent_done
        std     percent_top
        inc     percent_out
        bra     percent_next
percent_done
        lda     percent_out
        rts

; The result strip: one solid block per round, green won, red lost, blue
; tied. Written straight to the screen because these are graphics cells, and
; the text path would strip the high bit that makes them blocks at all.
row_marks
        lda     #5
        lbsr    screen_row_address
        ldb     #COLS
        lda     #BLACK_BLANK
row_marks_clear
        sta     ,x+
        decb
        bne     row_marks_clear

        lda     #5
        lbsr    screen_row_address
        leax    5,x
        clr     scan
row_marks_next
        lda     scan
        cmpa    history_len
        bhs     row_marks_done
        lbsr    history_index
        pshs    x
        ldx     #history_you
        abx
        lda     ,x
        puls    x
        pshs    a
        lbsr    history_index
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

; B becomes the array index of displayed entry `scan`. The rows hold the
; newest throw at the end, so a short history is drawn from the right.
history_index
        ldb     #HISTORY
        subb    history_len
        addb    scan
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
        pshs    u
        lbsr    clear_line
        puls    u
        ldb     #0
        lbsr    lay_string
        clr     scan
row_trail_next
        lda     scan
        cmpa    history_len
        bhs     row_trail_done
        lbsr    history_index
        leax    b,y
        lda     ,x
        ldb     #3
        mul
        ldu     #short_names
        leau    d,u
        lda     scan
        ldb     #4
        mul
        addb    #4
        lda     #3
        lbsr    lay_fixed
        inc     scan
        bra     row_trail_next
row_trail_done
        puls    a
        lbra    blit_line_inverse

; Row 9 names both throws facing each other, row 10 the verdict and the rule
; that decided it. The three longest rules will not fit beside a verdict, so
; the last word hangs on row 11 under the rule rather than under the verdict.
row_result
        lbsr    clear_line
        tst     rounds
        beq     row_result_faced
        ldb     #0
        ldu     #text_you_colon
        lbsr    lay_string
        lda     player_move
        lbsr    move_name
        lbsr    lay_string
        lda     agent_move
        lbsr    move_name
        lbsr    screen_text_length
        lda     #COLS-5
        suba    screen_length
        tfr     a,b
        pshs    u
        ldu     #text_cpu_colon
        lbsr    lay_string
        puls    u
        lbsr    lay_string
row_result_faced
        lda     #9
        lbsr    blit_line

        lbsr    clear_line
        tst     rounds
        beq     row_result_none
        lbsr    lay_verdict
row_result_none
        lda     #10
        lbsr    blit_line

        lbsr    clear_line
        tst     rounds
        beq     row_result_no_wrap
        tst     wrap_needed
        beq     row_result_no_wrap
        ldb     rule_column
        ldu     reason_b
        lbsr    lay_string
row_result_no_wrap
        lda     #11
        lbra    blit_line

; The verdict, a comma, then the rule. wrap_needed is set when the loser's
; name will not fit and belongs on the row below.
lay_verdict
        clr     wrap_needed
        ldb     #0
        ldu     verdict_text
        lbsr    lay_string
        ldu     #text_comma
        lbsr    lay_string
        stb     rule_column

        lbsr    measure_rule
        lda     rule_column
        adda    rule_len
        cmpa    #COLS
        bls     lay_verdict_one
        inc     wrap_needed
lay_verdict_one
        ldb     rule_column
        ldu     reason_a
        lbsr    lay_string
        lbsr    lay_gap
        ldu     reason_verb
        lbsr    lay_string
        tst     wrap_needed
        bne     lay_verdict_done
        ldu     reason_b
        lbsr    screen_text_length
        tst     screen_length
        beq     lay_verdict_done
        lbsr    lay_gap
        ldu     reason_b
        lbsr    lay_string
lay_verdict_done
        rts

; rule_len becomes the width of "<A> <VERB> <B>", with no trailing space when
; B is empty, which is how a tie is stated.
measure_rule
        ldu     reason_a
        lbsr    screen_text_length
        lda     screen_length
        sta     rule_len
        ldu     reason_verb
        lbsr    screen_text_length
        lda     screen_length
        inca
        adda    rule_len
        sta     rule_len
        ldu     reason_b
        lbsr    screen_text_length
        tst     screen_length
        beq     measure_done
        lda     screen_length
        inca
        adda    rule_len
        sta     rule_len
measure_done
        rts

row_machine
        lbsr    clear_line
        ldb     #0
        tst     expects_known
        bne     row_machine_expects
        ldu     #text_no_idea
        lbsr    lay_string
        bra     row_machine_blit
row_machine_expects
        ldu     #text_expects
        lbsr    lay_string
        lda     expected
        lbsr    move_name
        lbsr    lay_string
row_machine_blit
        lda     #13
        lbsr    blit_line

        lbsr    clear_line
        ldu     #text_rules
        ldb     #0
        lbsr    lay_string
        lda     #2
        sta     number_width
        lbsr    count_rules
        ldb     #7
        lbsr    lay_number_right
        ldu     #text_of_25
        lbsr    lay_string
        lda     #14
        lbsr    blit_line

        lbsr    clear_line
        ldu     #text_memory
        ldb     #0
        lbsr    lay_string
        lda     #3
        sta     number_width
        lda     memory
        ldb     #7
        lbsr    lay_number_right
        ldu     #text_slash
        lbsr    lay_string
        lda     rounds
        lbsr    lay_number
        lda     #15
        lbra    blit_line

; A becomes how many of the 25 cells it has proved. Counted rather than
; tracked, because a counter and a table can disagree and the table is the
; truth.
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
text_won        fcc     "YOU HAVE WON "
                fcb     0
text_of         fcc     " OF "
                fcb     0
text_open       fcc     " ("
                fcb     0
text_you_colon  fcc     "YOU: "
                fcb     0
text_cpu_colon  fcc     "CPU: "
                fcb     0
text_comma      fcc     ", "
                fcb     0
text_close      fcc     "%)"
                fcb     0
text_you        fcc     "YOU"
                fcb     0
text_cpu        fcc     "CPU"
                fcb     0
text_no_idea    fcc     "IT HAS NO IDEA YET"
                fcb     0
text_expects    fcc     "IT EXPECTS "
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
text_saved      fcc     "SESSION SAVED"
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
                fcb     0

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
number_value    rmb     1
number_column   rmb     1
number_lead     rmb     1
number_width    rmb     1
rule_column     rmb     1
rule_len        rmb     1
wrap_needed     rmb     1
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

; The session log. The magic string sits immediately in front of it so a
; snapshot can be searched for the log without this file, or the tool reading
; it, having to know XRoar's format.
log_magic       fcc     "RPSLSLOG"
log_count       rmb     1
log_reset_count rmb     1
log_resets      rmb     LOG_RESETS
log_player      rmb     LOG_MAX
log_agent       rmb     LOG_MAX
log_expected    rmb     LOG_MAX
        ifdef   DIRECT_TEST
SCRIPT_MAX      equ     64
script          rmb     SCRIPT_MAX
trace_agent     rmb     SCRIPT_MAX
script_index    rmb     1
        endc
