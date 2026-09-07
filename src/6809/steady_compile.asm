; Compile a row buffer into the steady player's event stream, on the CoCo.
;
; The melody demo composes its rows at run time, so it cannot carry a
; stream the Mac compiled. This is src/reference/steady_synth.py's
; compile_rows in 6809, mirrored line for line: the same writes in the
; same order, the same wait arithmetic, the same fillers where a wait
; would not fit a byte. A parity test compiles the same rows both ways
; and compares the bytes.
;
; Runs before the player, with the caller's direct page, so every
; variable here is addressed in full. The player's own cells are named
; by their labels, which are absolute.
;
; In:  the row buffer at tune_rows, TUNE_ROWS rows of four cells, each
;      note code, volume, decay; compile_ticks, the ticks per row.
; Out: the stream at event_buffer, ending before event_buffer_end;
;      compile_end, the address after the spare byte; compile_overflow,
;      nonzero if the buffer filled and the tune was cut short there.
;
; Optional, defined by the caller:
;   COMPILE_CURSOR   emit a playback cursor: one cell per CURSOR_ROWS rows
;                    along CURSOR_TRACK, CURSOR_MARK drawn, CURSOR_BLANK
;                    behind it.

VOICES          equ     4
LOW_NOTE        equ     12              ; first entry of note_increments
NOTE_HOLD_CODE  equ     0               ; the row data's note codes
NOTE_OFF_CODE   equ     1

CEVENT_BYTES    equ     4
; Room the final event and the spare byte need, plus one filler.
CRESERVE        equ     CEVENT_BYTES*2+1

compile_ticks   rmb     1               ; ticks per row: the tempo
compile_end     rmb     2
compile_overflow rmb    1
cvol            rmb     4               ; each voice's volume, 0..15
cdec            rmb     4               ; and its per-tick decrement
celapsed        rmb     2               ; samples since the last event was due
cwrites         rmb     1               ; events this tick, fillers aside
crow            rmb     1
ctick           rmb     1
cvoice          rmb     1
cprev_cell      rmb     1
cincr           rmb     2
caddr           rmb     2
ctmp            rmb     1

; ------------------------------------------------------------------------
compile_rows
                ldx     #cvol
                ldb     #8
cr_clear        clr     ,x+
                decb
                bne     cr_clear
                clr     >celapsed
                clr     >celapsed+1
                clr     >crow
                clr     >cprev_cell
                clr     >compile_overflow
                ldu     #event_buffer
                ldy     #tune_rows

cr_row
                clr     >ctick
cr_tick
                clr     >cwrites
                tst     >ctick
                lbne    cr_decays

                ifdef   COMPILE_CURSOR
                lda     >crow
                anda    #CURSOR_ROWS-1
                bne     cr_cells
                lda     >crow
                lsra
                lsra                    ; CURSOR_ROWS is four
                sta     >ctmp           ; this row's cell
                ldb     >cprev_cell
                ldx     #CURSOR_TRACK
                abx
                lda     #CURSOR_BLANK
                lbsr    emit_event
                ldb     >ctmp
                stb     >cprev_cell
                ldx     #CURSOR_TRACK
                abx
                lda     #CURSOR_MARK
                lbsr    emit_event
                endc

cr_cells
                clr     >cvoice
cr_cell
                ldb     >cvoice
                lda     #3
                mul
                leax    b,y             ; this voice's cell
                lda     ,x              ; note code
                lbeq    cr_cell_next    ; hold: nothing
                cmpa    #NOTE_OFF_CODE
                lbeq    cr_cell_off

                ldb     >cvoice
                cmpb    #VOICES-1
                beq     cr_cell_volume  ; the noise voice has no pitch

                pshs    x
                suba    #LOW_NOTE
                lsla
                tfr     a,b
                ldx     #note_increments
                abx
                ldd     ,x
                std     >cincr
                ldb     >cvoice
                lslb
                ldx     #incrs
                abx
                stx     >caddr
                lda     >cincr
                lbsr    emit_event      ; increment, high byte
                ldx     >caddr
                leax    1,x
                lda     >cincr+1
                lbsr    emit_event      ; increment, low byte
                ldb     >cvoice
                lslb
                ldx     #phases
                abx
                stx     >caddr
                clra
                lbsr    emit_event      ; phase reset, high
                ldx     >caddr
                leax    1,x
                clra
                lbsr    emit_event      ; phase reset, low
                puls    x

cr_cell_volume
                lda     1,x             ; volume, 0..15
                ldb     2,x             ; decay
                pshs    x
                ldx     #cvol
                stx     >caddr
                ldx     >caddr
                pshs    b
                ldb     >cvoice
                abx
                sta     ,x              ; cvol[voice] = volume
                puls    b
                ldx     #cdec
                sta     >ctmp
                lda     >cvoice
                pshs    a
                exg     a,b             ; A decay, B voice
                abx
                sta     ,x              ; cdec[voice] = decay
                puls    a
                lda     >ctmp           ; the volume again
                lsla
                lsla                    ; onto PA2-PA7
                ldx     #scaled
                ldb     >cvoice
                abx
                lbsr    emit_event
                puls    x
                bra     cr_cell_next

cr_cell_off
                ldx     #cvol
                ldb     >cvoice
                abx
                clr     ,x
                ldx     #scaled
                ldb     >cvoice
                abx
                clra
                lbsr    emit_event

cr_cell_next
                inc     >cvoice
                lda     >cvoice
                cmpa    #VOICES
                lblo    cr_cell
                bra     cr_tick_end

cr_decays
                clr     >cvoice
cr_decay
                ldx     #cdec
                ldb     >cvoice
                abx
                lda     ,x              ; the decrement
                beq     cr_decay_next
                sta     >ctmp
                ldx     #cvol
                abx                     ; B is still the voice
                ldb     ,x              ; the volume
                beq     cr_decay_next   ; already silent
                subb    >ctmp
                bcc     cr_decay_store
                clrb                    ; clamp at silence
cr_decay_store
                stb     ,x
                tfr     b,a
                lsla
                lsla
                ldx     #scaled
                ldb     >cvoice
                abx
                lbsr    emit_event
cr_decay_next
                inc     >cvoice
                lda     >cvoice
                cmpa    #VOICES
                blo     cr_decay

cr_tick_end
; elapsed += samples per tick - writes this tick; split if past a byte
                ldd     >celapsed
                addd    #SAMPLES_PER_TICK
                subb    >cwrites
                sbca    #0
                std     >celapsed
                cmpd    #255
                bls     cr_tick_next
                lbsr    emit_filler
                ldd     >celapsed
                subd    #255
                std     >celapsed
cr_tick_next
                inc     >ctick
                lda     >ctick
                cmpa    >compile_ticks
                lblo    cr_tick

                leay    12,y            ; the next row
                inc     >crow
                lda     >crow
                cmpa    #TUNE_ROWS
                lblo    cr_row

; the end: finished = 1 after the last tick's samples
                ldb     >celapsed+1     ; at most 255 by construction
                lda     #1
                ldx     #finished
                lbsr    emit_raw
                clr     ,u+             ; the spare byte the player reads past
                stu     >compile_end
                rts

; ------------------------------------------------------------------------
; Emit an event due one sample after the last one, plus whatever has
; elapsed since. A = value, X = address. Splits a wait that would not fit.
emit_event
                pshs    a,x
                ldd     >celapsed
                addd    #1
                cmpd    #255
                bls     ee_fits
                pshs    b               ; keep the low byte of the wait
                lbsr    emit_filler
                puls    b
                subb    #255            ; the remainder, which is 1
ee_fits
                puls    a,x
                lbsr    emit_raw
                clr     >celapsed
                clr     >celapsed+1
                inc     >cwrites
                rts

; A filler: a wait of 255 that writes nothing anyone reads.
emit_filler
                ldb     #255
                clra
                ldx     #scratch
                lbsr    emit_raw
                rts

; Write one event: B = wait, X = address, A = value. Past the reserve line
; the event is dropped and the overflow flag set; the final event still
; has its room.
emit_raw
                cmpu    #event_buffer_end-CRESERVE
                bhs     er_full
                stb     ,u+
                stx     ,u++
                sta     ,u+
                rts
er_full
                inc     >compile_overflow
                rts
