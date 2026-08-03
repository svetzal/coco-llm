; Screen and controls for the EXP-010 composer.
;
; The CoCo's semigraphics-4 mode is selected per character cell: a byte with
; bit 7 set draws four coloured blocks, a byte with bit 7 clear draws a
; character. One screen therefore carries text and graphics at once, which is
; what lets a control panel and a piano roll share 512 bytes.
;
; The roll is the point of the display. Watching notes appear left to right as
; the model composes shows the generation happening rather than asserting that
; it happened, and the same grid carries a cursor during playback.

UI_SCREEN       equ     $0400
UI_WIDTH        equ     32
UI_ROLL_TOP     equ     6               ; first character row of the roll
UI_ROLL_ROWS    equ     10
UI_PITCHES      equ     UI_ROLL_ROWS*2  ; one pixel row per semitone
UI_COLUMNS      equ     UI_WIDTH*2
UI_BLANK        equ     $80             ; semigraphic cell, nothing lit
UI_COLOUR       equ     $8F             ; green; the low nibble adds blocks
UI_SPACE        equ     $60

POLCAT          equ     $A000
UI_SEED_MAX     equ     8

ui_x            rmb     1
ui_y            rmb     1
ui_addr         rmb     2
ui_last         rmb     1               ; last pitch drawn, plus one
ui_cursor       rmb     1               ; column the playback cursor is on
ui_seed_len     rmb     1
ui_seed         rmb     UI_SEED_MAX
ui_mode         rmb     1
ui_tempo        rmb     1
ui_entropy      rmb     2

; ------------------------------------------------------------------------
ui_clear
                ldx     #UI_SCREEN
                lda     #UI_SPACE
uc_text         sta     ,x+
                cmpx    #UI_SCREEN+UI_ROLL_TOP*UI_WIDTH
                blo     uc_text
                lda     #UI_BLANK
uc_roll         sta     ,x+
                cmpx    #UI_SCREEN+512
                blo     uc_roll
                rts

ui_clear_roll
                ldx     #UI_SCREEN+UI_ROLL_TOP*UI_WIDTH
                lda     #UI_BLANK
ucr_next        sta     ,x+
                cmpx    #UI_SCREEN+512
                blo     ucr_next
                clr     ui_last
                rts

; X is a screen address, U a zero-terminated string. VDG text codes are the
; low six bits of uppercase ASCII, as in screen.asm.
ui_print
                lda     ,u+
                beq     uip_done
                anda    #$3F
                sta     ,x+
                bra     ui_print
uip_done        rts

; ------------------------------------------------------------------------
; Light one pixel. B is the column, A the pixel row.
;
; A cell covers two columns and two rows, so both are halved and the quadrant
; comes from the low bits. Quadrant bits are 3,2,1,0 for top-left, top-right,
; bottom-left, bottom-right.
ui_plot
                cmpb    #UI_COLUMNS
                bhs     up_done
                cmpa    #UI_PITCHES
                bhs     up_done
                sta     ui_y
                stb     ui_x

                lsra
                ldb     #UI_WIDTH
                mul
                addd    #UI_SCREEN+UI_ROLL_TOP*UI_WIDTH
                std     ui_addr
                ldb     ui_x
                lsrb
                ldx     ui_addr
                abx

                lda     #$08            ; top-left block
                ldb     ui_y
                bitb    #1
                beq     up_top
                lsra
                lsra                    ; drop to the lower pair
up_top
                ldb     ui_x
                bitb    #1
                beq     up_left
                lsra                    ; and to the right of the pair
up_left
                ora     ,x
                ora     #UI_COLOUR-$0F
                sta     ,x
up_done
                rts

; ------------------------------------------------------------------------
; Draw one composed row. A is the melody token; demo_row supplies the column,
; two tune rows to a column so all 128 fit across the screen.
ui_show_token
                cmpa    #MEL_REST
                beq     ust_rest
                cmpa    #MEL_HOLD
                bne     ust_pitch
                lda     ui_last         ; a hold continues the line
                beq     ust_done
                deca
                bra     ust_draw
ust_rest
                clr     ui_last
                rts
ust_pitch
                inca
                sta     ui_last
                deca
ust_draw
                ; Pitches run to 28 semitones above the tonic but the roll is
                ; twenty rows tall. Clamping put a sixth of every tune on the
                ; top row, which reads as a melody that keeps hitting a
                ; ceiling. Scaling by five eighths fits the whole range and
                ; keeps the contour, which is what the display is for.
                ldb     #5
                mul
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                tfr     b,a
                cmpa    #UI_PITCHES
                blo     ust_inrange
                lda     #UI_PITCHES-1
ust_inrange
                pshs    a
                lda     #UI_PITCHES-1   ; high notes sit near the top
                suba    ,s+
                ldb     demo_row+1
                lsrb
                lbsr    ui_plot
ust_done
                rts

; ------------------------------------------------------------------------
; The playback cursor: a lit column that sweeps the roll. Called once per
; tune row from the player, in a sample borrowed for the purpose, so it has a
; whole sample period to itself and cannot stretch the timeline.
ui_row_cursor
                lda     ui_cursor       ; erase the previous column
                lbsr    ui_cursor_col
                lda     demo_row+1
                lsra
                sta     ui_cursor
                lbsr    ui_cursor_col
                rts

; Flip the top and bottom pixels of column A, so the cursor reads as a tick
; above and below the note line rather than covering it.
ui_cursor_col
                cmpa    #UI_COLUMNS
                bhs     ucc_done
                pshs    a
                lsra
                tfr     a,b
                ldx     #UI_SCREEN+UI_ROLL_TOP*UI_WIDTH
                abx
                lda     ,s
                anda    #1
                beq     ucc_left
                lda     #$04
                bra     ucc_flip
ucc_left        lda     #$08
ucc_flip        eora    ,x
                ora     #UI_BLANK
                sta     ,x
                leas    1,s
ucc_done        rts

; ------------------------------------------------------------------------
ui_panel
                ldx     #UI_SCREEN
                ldu     #ui_title
                lbsr    ui_print
                ldx     #UI_SCREEN+UI_WIDTH*3
                ldu     #ui_help1
                lbsr    ui_print
                ldx     #UI_SCREEN+UI_WIDTH*4
                ldu     #ui_help2
                lbsr    ui_print
                rts

ui_show_seed
                ldx     #UI_SCREEN+UI_WIDTH
                ldu     #ui_label_seed
                lbsr    ui_print
                ldx     #UI_SCREEN+UI_WIDTH+6
                ldb     ui_seed_len
                beq     uss_pad
                ldu     #ui_seed
uss_next        lda     ,u+
                adda    #$30            ; a digit
                anda    #$3F
                sta     ,x+
                lda     #UI_SPACE
                sta     ,x+
                decb
                bne     uss_next
uss_pad         lda     #UI_SPACE
uss_fill        sta     ,x+
                cmpx    #UI_SCREEN+UI_WIDTH*2
                blo     uss_fill
                rts

ui_show_state
                ldx     #UI_SCREEN+UI_WIDTH*2
                ldu     #ui_label_key
                lbsr    ui_print
                ldu     #ui_word_major
                tst     ui_mode
                beq     uso_mode
                ldu     #ui_word_minor
uso_mode        ldx     #UI_SCREEN+UI_WIDTH*2+5
                lbsr    ui_print
                ldx     #UI_SCREEN+UI_WIDTH*2+12
                ldu     #ui_label_speed
                lbsr    ui_print
                lda     ui_tempo        ; smaller ticks per row is faster
                adda    #$30
                anda    #$3F
                sta     UI_SCREEN+UI_WIDTH*2+19
                rts

; A status word in the panel's right-hand end.
ui_status
                ldx     #UI_SCREEN+UI_WIDTH*5
                lbsr    ui_print
                rts

; ------------------------------------------------------------------------
; POLCAT lives in BASIC ROM and wants the normal interrupt environment.
ui_read_key
                andcc   #$AF
                jsr     [POLCAT]
                rts

ui_wait_key
uwk_spin        lbsr    ui_read_key
                tsta
                beq     uwk_spin
                rts

; ------------------------------------------------------------------------
ui_title        fcb     'C,'O,'C,'O,' ,'L,'L,'M,' ,'M,'E,'L,'O,'D,'Y,0
ui_label_seed   fcb     'S,'E,'E,'D,' ,0
ui_label_key    fcb     'K,'E,'Y,' ,0
ui_label_speed  fcb     'S,'P,'D,' ,0
ui_word_major   fcb     'M,'A,'J,'O,'R,0
ui_word_minor   fcb     'M,'I,'N,'O,'R,0
ui_help1        fcb     '1,'-,'7,' ,'N,'O,'T,'E,' ,' ,'0,' ,'D,'E,'L,0
ui_help2        fcb     'M,'O,'D,'E,' ,'S,'P,'D,' ,'E,'N,'T,'E,'R,0
ui_msg_ready    fcb     'R,'E,'A,'D,'Y,' ,' ,' ,' ,' ,' ,0
ui_msg_think    fcb     'C,'O,'M,'P,'O,'S,'I,'N,'G,' ,' ,0
ui_msg_play     fcb     'P,'L,'A,'Y,'I,'N,'G,' ,' ,' ,' ,0

; ------------------------------------------------------------------------
; The control loop. Degrees are entered, not pitches, so the keyboard cannot
; produce a note outside the scale - the audience cannot play a wrong one.
ui_main
                lbsr    ui_clear
                lbsr    ui_panel
                clr     ui_seed_len
                clr     ui_mode
                lda     #7
                sta     ui_tempo
                ldd     #$1A2B
                std     ui_entropy

um_idle
                lbsr    ui_show_seed
                lbsr    ui_show_state
                ldu     #ui_msg_ready
                lbsr    ui_status

um_key
                lbsr    ui_read_key
                tsta
                beq     um_stir         ; idle time feeds the generator
                cmpa    #'1
                blo     um_other
                cmpa    #'7
                bhi     um_other
                suba    #'0
                lbsr    ui_add_degree
                bra     um_idle

um_stir
                ldx     ui_entropy      ; how long the user thought is entropy
                leax    1,x
                stx     ui_entropy
                bra     um_key

um_other
                cmpa    #'0             ; delete the last degree
                bne     um_mode
                tst     ui_seed_len
                beq     um_idle
                dec     ui_seed_len
                bra     um_idle
um_mode
                cmpa    #'M
                bne     um_speed
                lda     ui_mode
                eora    #1
                sta     ui_mode
                bra     um_idle
um_speed
                cmpa    #'S
                bne     um_go
                lda     ui_tempo
                deca
                cmpa    #5
                bhs     um_speed_set
                lda     #9
um_speed_set    sta     ui_tempo
                bra     um_idle
um_go
                cmpa    #$0D            ; ENTER composes and performs
                lbne    um_key
                tst     ui_seed_len
                lbeq    um_key
                lbsr    ui_perform
                lbra    um_idle

; Append a degree, replacing the oldest once the figure is full.
ui_add_degree
                ldb     ui_seed_len
                cmpb    #UI_SEED_MAX
                blo     uad_room
                ldx     #ui_seed        ; slide the figure along
                ldb     #UI_SEED_MAX-1
uad_slide       ldu     1,x
                stu     ,x+
                decb
                bne     uad_slide
                ldb     #UI_SEED_MAX-1
                bra     uad_store
uad_room        inc     ui_seed_len
uad_store       ldx     #ui_seed
                abx
                sta     ,x
                rts

; ------------------------------------------------------------------------
ui_perform
                lbsr    ui_clear_roll
                ldu     #ui_msg_think
                lbsr    ui_status

                ldd     ui_entropy      ; a different draw each time
                std     mel_rng
                lda     ui_mode
                sta     demo_mode
                lda     ui_tempo
                sta     demo_ticks
                lbsr    ui_build_seed

                lbsr    demo_compose
                lbsr    demo_arrange

                ldu     #ui_msg_play
                lbsr    ui_status
                clr     ui_cursor
                ldd     #ui_row_cursor  ; sweep the roll while it plays
                std     row_hook
                lbsr    music_start
                ldd     #row_hook_none
                std     row_hook
                rts

; Turn the entered degrees into melody tokens, two rows each.
ui_build_seed
                ldx     #demo_seed
                ldu     #ui_seed
                ldb     ui_seed_len
                stb     demo_seed_rows
ubs_next        lda     ,u+
                deca                    ; degrees are one-based
                pshs    b
                ldb     ui_mode
                lbsr    ui_step_of
                puls    b
                sta     ,x+
                lda     #MEL_HOLD
                sta     ,x+
                decb
                bne     ubs_next

                lda     demo_seed_rows  ; two rows per entered degree
                lsla
                sta     demo_seed_rows
                rts

; Semitones above the tonic for scale degree A in mode B.
ui_step_of
                tstb
                bne     uso_minor
                ldx     #demo_steps
                bra     uso_pick
uso_minor       ldx     #demo_steps_min
uso_pick        tfr     a,b
                abx
                lda     ,x
                rts
