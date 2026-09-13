; CG6 UI: 128x192, four pixels per byte, 6144 bytes at $0400.
; Public keys: ROCK PAPER SCISSORS LIZARD SPOCK. The engine's cyclic
; numbering stays private. It commits its move BEFORE keyboard polling.
GFX_SCREEN      equ     $0400
GFX_END         equ     $1c00
GFX_LEFT        equ     GFX_SCREEN+16*32+2
GFX_RIGHT       equ     GFX_SCREEN+16*32+18

gfx_start
        lds     #$7f00
        clra
        tfr     a,dp
        lbsr    gfx_init
gfx_next
        lbsr    agent_choose
        sta     agent_move
gfx_ready
        jsr     [POLCAT]
        beq     gfx_ready
        cmpa    #'R
        beq     gfx_restart
        cmpa    #'r
        beq     gfx_restart
        lbsr    gfx_decode_key
        bcs     gfx_ready
        sta     player_move
        lbsr    gfx_player_reveal
        ; 18 video frames, about 0.30 seconds at NTSC stock speed.
        lbsr    gfx_pause
        lbsr    gfx_finish_round
        lbsr    gfx_release
        bra     gfx_next
gfx_restart
        lbsr    gfx_init
        lbsr    gfx_release
        bra     gfx_next

; Invalid input returns carry set and never changes a score or either move.
gfx_decode_key
        suba    #'1
        bcs     gfx_bad_key
        cmpa    #5
        bhs     gfx_bad_key
        ldx     #gfx_key_moves
        lda     a,x
        andcc   #$fe
        rts
gfx_bad_key
        orcc    #1
        rts

; Initialise every state read by the graphical path, including hostile RAM.
gfx_init
        ldd     #$1a2b
        std     rng_state
        lbsr    new_game
        ldx     #gfx_scores
        clra
        ldb     #4
gfx_zero_scores
        sta     ,x+
        decb
        bne     gfx_zero_scores
        ldx     #GFX_SCREEN
        ldd     #0
gfx_clear_screen
        std     ,x++
        cmpx    #GFX_END
        blo     gfx_clear_screen
        ; SAM V=110: 32 bytes/line, one scanline per row. F=2: $0400.
        sta     $ffc0
        sta     $ffc3
        sta     $ffc5
        sta     $ffc6
        sta     $ffc9
        sta     $ffca
        sta     $ffcc
        sta     $ffce
        sta     $ffd0
        sta     $ffd2
        ; AG=1, GM=110, CSS=0; preserve PIA's low I/O bits.
        lda     $ff22
        anda    #7
        ora     #$e0
        sta     $ff22
        ldd     #gfx_font_normal
        std     gfx_font
        ldx     #GFX_SCREEN+2*32
        ldu     #gfx_you
        ldb     #16
        lbsr    gfx_centre
        ldx     #GFX_SCREEN+2*32+16
        ldu     #gfx_coco
        ldb     #16
        lbsr    gfx_centre
        lbsr    gfx_clear_hands
        ldx     #GFX_SCREEN+46*32
        ldu     #gfx_question
        ldb     #16
        lbsr    gfx_centre
        ldx     #GFX_SCREEN+154*32
        ldu     #gfx_keys1
        ldb     #32
        lbsr    gfx_centre
        ldx     #GFX_SCREEN+166*32
        ldu     #gfx_keys2
        ldb     #32
        lbsr    gfx_centre
        ldx     #GFX_SCREEN+178*32
        ldu     #gfx_keys3
        ldb     #32
        lbsr    gfx_centre
        lbsr    gfx_draw_scores
        ldu     #gfx_pick
        lbsr    gfx_status
        rts

; Wipe the hand field and names, then put a question in the computer slot.
gfx_clear_hands
        ldx     #GFX_SCREEN+16*32
        ldd     #0
gfx_clear_hands_loop
        std     ,x++
        cmpx    #GFX_SCREEN+100*32
        blo     gfx_clear_hands_loop
        ldx     #GFX_SCREEN+46*32+16
        ldu     #gfx_question
        ldb     #16
        lbra    gfx_centre

gfx_player_reveal
        lbsr    gfx_clear_hands
        lda     player_move
        ldx     #GFX_LEFT
        lbsr    gfx_sprite
        lda     player_move
        lbsr    move_name
        ldx     #GFX_SCREEN+90*32
        ldb     #16
        lbsr    gfx_centre
        ldu     #gfx_ready_text
        lbra    gfx_status

gfx_finish_round
        ; The opaque sprite replaces the question, including its green pixels.
        lda     agent_move
        ldx     #GFX_RIGHT
        lbsr    gfx_sprite
        lda     agent_move
        lbsr    move_name
        ldx     #GFX_SCREEN+90*32+16
        ldb     #16
        lbsr    gfx_centre
        lbsr    settle_round
        lbsr    gfx_count_result
        lbsr    gfx_draw_scores
        ldu     #gfx_draw
        lda     agent_result
        cmpa    #1
        beq     gfx_verdict
        ldu     #gfx_win
        tsta
        beq     gfx_verdict
        ldu     #gfx_lose
gfx_verdict
        lbra    gfx_status

; Two win counters saturate at 999. A draw awards neither side a point.
gfx_count_result
        lda     agent_result
        cmpa    #1
        beq     gfx_count_done
        ldx     #gfx_wins
        tsta
        beq     gfx_increment
        ldx     #gfx_cpu_wins
gfx_increment
        ldd     ,x
        cmpd    #999
        bhs     gfx_count_done
        addd    #1
        std     ,x
gfx_count_done
        rts

gfx_draw_scores
        ldx     #GFX_SCREEN+110*32+6
        ldd     gfx_wins
        lbsr    gfx_number
        ldx     #GFX_SCREEN+110*32+22
        ldd     gfx_cpu_wins
        lbra    gfx_number

; D=0..999, X=destination. Format three digits without division.
gfx_number
        ldy     #gfx_number_buffer
        clr     gfx_digit
gfx_hundreds
        cmpd    #100
        blo     gfx_hundreds_done
        subd    #100
        inc     gfx_digit
        bra     gfx_hundreds
gfx_hundreds_done
        pshs    d
        lda     gfx_digit
        adda    #'0
        sta     ,y+
        puls    d
        clr     gfx_digit
gfx_tens
        cmpd    #10
        blo     gfx_tens_done
        subd    #10
        inc     gfx_digit
        bra     gfx_tens
gfx_tens_done
        lda     gfx_digit
        adda    #'0
        sta     ,y+
        addb    #'0
        stb     ,y+
        clr     ,y
        ldu     #gfx_number_buffer
        lbra    gfx_text

; U=message. Yellow on a blue strip, then restore the body font.
gfx_status
        ldx     #GFX_SCREEN+136*32
        ldd     #$aaaa
gfx_status_fill
        std     ,x++
        cmpx    #GFX_SCREEN+150*32
        blo     gfx_status_fill
        ldd     #gfx_font_bright
        std     gfx_font
        ldx     #GFX_SCREEN+138*32
        ldb     #32
        lbsr    gfx_centre
        ldd     #gfx_font_normal
        std     gfx_font
        rts

; X=region start; B=width in character cells; U=zero-terminated text.
gfx_centre
        pshs    u
        clr     gfx_length
gfx_length_loop
        lda     ,u+
        beq     gfx_length_done
        inc     gfx_length
        bra     gfx_length_loop
gfx_length_done
        subb    gfx_length
        lsrb
        abx
        puls    u
        ; fall through to text

; One 3x5 character plus blank column per CG6 byte, doubled vertically.
gfx_text
        lda     ,u+
        beq     gfx_text_done
        suba    #32
        ldb     #5
        mul
        ldy     gfx_font
        leay    d,y
        pshs    x
        ldb     #5
gfx_text_rows
        lda     ,y+
        sta     ,x
        sta     32,x
        leax    64,x
        decb
        bne     gfx_text_rows
        puls    x
        leax    1,x
        bra     gfx_text
gfx_text_done
        rts

; A=engine move, X=top-left byte. Each sprite is exactly 864 bytes.
gfx_sprite
        ldu     #gfx_hands
        tsta
        beq     gfx_sprite_address
gfx_sprite_seek
        leau    864,u
        deca
        bne     gfx_sprite_seek
gfx_sprite_address
        lda     #72
        sta     gfx_rows
gfx_sprite_row
        ldd     ,u++
        std     ,x++
        ldd     ,u++
        std     ,x++
        ldd     ,u++
        std     ,x++
        ldd     ,u++
        std     ,x++
        ldd     ,u++
        std     ,x++
        ldd     ,u++
        std     ,x++
        leax    20,x
        dec     gfx_rows
        bne     gfx_sprite_row
        rts

; BASIC's frame counter is maintained by the normal vertical-sync IRQ.
; No speed poke, busy-loop calibration, or modern-host timing dependency.
gfx_pause
        ldd     $0112
        addd    #18
        std     gfx_deadline
gfx_pause_loop
        ldd     $0112
        subd    gfx_deadline
        bmi     gfx_pause_loop
        rts

; Require release of the physical keyboard to prevent held-key repeat rounds.
; Preserve the column strobe for ROM keyboard scanning.
gfx_release
        lda     $ff02
        pshs    a
        clr     $ff02
gfx_release_loop
        lda     $ff00
        anda    #$7f
        cmpa    #$7f
        bne     gfx_release_loop
        puls    a
        sta     $ff02
        rts

gfx_key_moves   fcb     0,2,4,3,1
gfx_you         fcc     "YOU"
                fcb     0
gfx_coco        fcc     "COCO"
                fcb     0
gfx_question    fcc     "?"
                fcb     0
gfx_keys1       fcc     "1 ROCK   2 PAPER"
                fcb     0
gfx_keys2       fcc     "3 SCISSORS  4 LIZARD"
                fcb     0
gfx_keys3       fcc     "5 SPOCK  R NEW GAME"
                fcb     0
gfx_pick        fcc     "PICK A HAND"
                fcb     0
gfx_ready_text  fcc     "HERE WE GO"
                fcb     0
gfx_win         fcc     "YOU WIN"
                fcb     0
gfx_lose        fcc     "COCO WINS"
                fcb     0
gfx_draw        fcc     "DRAW"
                fcb     0
gfx_scores
gfx_wins        rmb     2
gfx_cpu_wins    rmb     2
gfx_font        rmb     2
gfx_length      rmb     1
gfx_digit       rmb     1
gfx_number_buffer rmb   4
gfx_rows        rmb     1
gfx_deadline    rmb     2

gfx_font_normal includebin  "../../build/exp019/font.bin"
gfx_font_bright includebin  "../../build/exp019/font-bright.bin"
gfx_hands       includebin  "../../build/exp019/hands.bin"
gfx_program_end
        ifgt    gfx_program_end-$7e00
        error   "Graphical game overlaps the stack reserve"
        endc
