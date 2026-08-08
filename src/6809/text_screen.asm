; Shared CoCo text-screen routines.
;
; The VDG has two character sets, and telling them apart is most of this
; module's reason to exist:
;
;   $40-$7F   black on green. A space is $60, a green cell. This is the
;             CoCo's own look and the body of every screen in this series.
;   $00-$3F   green on black. A space is $20, a black cell. Reversed, and
;             what a title bar is drawn in.
;
; Each set carries its own blank, which falls out of the same arithmetic as
; its letters: `$20 | $40` is $60 and `$20 & $3F` is $20. A row is blitted
; with one mask and its gaps come out right without a special case.
;
; This exists because it was written three times instead of once. EXP-012 and
; EXP-013 each grew a private blitter, each picked a character set by
; reasoning about it rather than looking, and EXP-013 picked the wrong one -
; drawing the body reversed and the title bar plain, so the whole screen came
; out inverted. The convention now lives in one place with one comment.

; Guarded because model_forward.asm and title_generator.asm still declare
; these for themselves. Anything new should take them from here.
        ifndef  SCREEN
SCREEN          equ     $0400
        endc
        ifndef  SCREEN_COLS
SCREEN_COLS     equ     32
        endc
        ifndef  SCREEN_ROWS
SCREEN_ROWS     equ     16
        endc
SCREEN_CELLS    equ     SCREEN_COLS*SCREEN_ROWS

BODY_BLANK      equ     $60             ; a space, black on green
TITLE_BLANK     equ     $20             ; a space, green on black
TITLE_ROW       equ     0

; Fill the screen with the body's blank. Rows nobody writes are part of the
; layout, so they have to be blank rather than whatever was there.
screen_clear
        ldx     #SCREEN
        lda     #BODY_BLANK
screen_clear_next
        sta     ,x+
        cmpx    #SCREEN+SCREEN_CELLS
        blo     screen_clear_next
        rts

; X becomes the screen address of row A.
screen_row_address
        ldb     #SCREEN_COLS
        mul
        ldx     #SCREEN
        leax    d,x
        rts

; screen_length becomes the width of the zero-terminated string in U, which
; is preserved.
screen_text_length
        pshs    u
        clr     screen_length
screen_length_next
        lda     ,u+
        beq     screen_length_done
        inc     screen_length
        bra     screen_length_next
screen_length_done
        puls    u,pc

; Draw the title bar: U is the title, centred on row 0 and reversed. This is
; the one call an app makes to put a name at the top of the screen.
screen_title_bar
        pshs    u
        lda     #TITLE_ROW
        lbsr    screen_row_address
        lda     #TITLE_BLANK
        ldb     #SCREEN_COLS
screen_title_clear
        sta     ,x+
        decb
        bne     screen_title_clear

        puls    u
        lbsr    screen_text_length
        lda     #TITLE_ROW
        lbsr    screen_row_address
        lda     #SCREEN_COLS
        suba    screen_length
        lsra
        tfr     a,b
        abx
screen_title_next
        lda     ,u+
        beq     screen_title_done
        anda    #$3f
        sta     ,x+
        bra     screen_title_next
screen_title_done
        rts

; A is the row, U a SCREEN_COLS buffer of ASCII: drawn black on green.
screen_blit_body
        lbsr    screen_row_address
        ldb     #SCREEN_COLS
screen_blit_next
        lda     ,u+
        ora     #$40
        sta     ,x+
        decb
        bne     screen_blit_next
        rts

screen_length   rmb     1
