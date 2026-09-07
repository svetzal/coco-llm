; EXP-010 demonstration: the CoCo composes a tune, then performs it.
;
; Composing and playing cannot overlap. EXP-009 established that the sample
; loop consumes the whole machine, so the tune is generated into RAM first and
; the player is handed the finished rows.
;
; The generator produces one melody token per row. The arrangement around it
; is rules, not model: bass follows the chord root, the arpeggio walks the
; triad, and percussion follows the beat. Nothing about pacing or energy comes
; from the corpus, which is what lets material learned from 1883 fiddle tunes
; be performed at whatever tempo suits.

DEMO_BAR_ROWS   equ     8               ; 2/4 at a row to the sixteenth
DEMO_TONIC      equ     60              ; where the generated tonic sits
DEMO_BASS       equ     DEMO_TONIC-24
DEMO_ARP        equ     DEMO_TONIC-12
DEMO_METRE      equ     3               ; 2/4

MEL_HOLD        equ     32              ; melody token meanings
MEL_REST        equ     33
MEL_PAD         equ     34              ; history before a tune starts

demo_row        rmb     2
demo_chord      rmb     1
demo_beat       rmb     1
demo_last_chord rmb     1
demo_tmp        rmb     1
demo_mode       rmb     1               ; 0 major, 1 minor
demo_seed_rows  rmb     1               ; rows given rather than composed
demo_write      rmb     2
demo_tokens     rmb     TUNE_ROWS

; Four bars of I I IV V, repeating.
demo_prog       fcb     0,0,3,4

; Scale steps, semitones above the tonic.
demo_steps      fcb     0,2,4,5,7,9,11
demo_steps_min  fcb     0,2,3,5,7,8,10

; The opening figure, as melody tokens: 1 2 3 5 4 2 5 1, two rows each,
; an octave above the tonic so it starts where the corpus lives.
demo_seed       fcb     12,MEL_HOLD,14,MEL_HOLD,16,MEL_HOLD,19,MEL_HOLD
                fcb     17,MEL_HOLD,14,MEL_HOLD,19,MEL_HOLD,12,MEL_HOLD

; ------------------------------------------------------------------------
demo_compose
                ldd     #$1A2B          ; a fixed seed keeps runs repeatable
                std     mel_rng

                ldx     #melody_context ; history starts as it did in training
                ldb     #MEL_CONTEXT
                lda     #MEL_PAD
dc_clear        sta     ,x+
                decb
                bne     dc_clear

                ldd     #0
                std     demo_row

dc_row
                lbsr    demo_set_frame

                lda     demo_row+1      ; the opening bars are given, not composed
                cmpa    demo_seed_rows
                bhs     dc_generate
                ldb     demo_row
                bne     dc_generate
                ldx     #demo_seed
                ldb     demo_row+1
                abx
                lda     ,x
                bra     dc_store

dc_generate
                lda     #UI_GREEN       ; from here on the model is inventing
                sta     ui_ink
                lbsr    melody_predict
                lbsr    melody_sample
                lda     melody_best_token

dc_store
                ldx     #demo_tokens
                ldb     demo_row+1
                abx
                sta     ,x
                pshs    a               ; the display must not eat the token
                lbsr    ui_show_token   ; watch the line appear as it composes
                puls    a
                lbsr    demo_push

                ldd     demo_row
                addd    #1
                std     demo_row
                cmpd    #TUNE_ROWS
                blo     dc_row
                rts

; Situational context for this row: mode, metre, chord, beat.
demo_set_frame
                lda     demo_mode
                sta     melody_context
                lda     #DEMO_METRE
                sta     melody_context+1

                ldb     demo_row+1      ; beat = row within the bar
                andb    #DEMO_BAR_ROWS-1
                stb     demo_beat
                stb     melody_context+3

                lda     demo_row+1      ; chord = progression[bar]
                lsra
                lsra
                lsra                    ; row / DEMO_BAR_ROWS
                anda    #3
                ldx     #demo_prog
                ldb     a,x
                stb     demo_chord
                stb     melody_context+2
                rts

; Shift the newest token into the melody history.
demo_push
                pshs    a
                ldx     #melody_context+4
                ldb     #MEL_HISTORY-1
dp_shift        lda     1,x
                sta     ,x+
                decb
                bne     dp_shift
                puls    a
                sta     ,x
                rts

; ------------------------------------------------------------------------
; Lay the composed tokens onto the player's four voices.
demo_arrange
                ldd     #tune_rows
                std     demo_write
                ldd     #0
                std     demo_row
                lda     #$FF
                sta     demo_last_chord

da_row
                lbsr    demo_set_frame
                ldu     demo_write

                ; --- voice 0: bass, only when the chord changes ---
                lda     demo_chord
                cmpa    demo_last_chord
                beq     da_bass_hold
                sta     demo_last_chord
                lbsr    demo_scale
                ldb     demo_chord
                abx
                lda     ,x
                adda    #DEMO_BASS
                sta     ,u+
                lda     #12
                sta     ,u+
                clr     ,u+
                lbra    da_lead
da_bass_hold
                clr     ,u+             ; note 0 means hold
                clr     ,u+
                clr     ,u+

                ; --- voice 1: the composed melody ---
da_lead
                ldx     #demo_tokens
                ldb     demo_row+1
                abx
                lda     ,x
                cmpa    #MEL_HOLD
                bne     da_lead_rest
                clr     ,u+
                clr     ,u+
                clr     ,u+
                lbra    da_harmony
da_lead_rest
                cmpa    #MEL_REST
                bne     da_lead_note
                lda     #1              ; note 1 means off
                sta     ,u+
                clr     ,u+
                clr     ,u+
                lbra    da_harmony
da_lead_note
                adda    #DEMO_TONIC
                sta     ,u+
                lda     #13
                sta     ,u+
                clr     ,u+

                ; --- voice 2: arpeggio over the chord ---
da_harmony
                lda     demo_row+1
                anda    #3
                beq     da_arp_root
                cmpa    #2
                beq     da_arp_fifth
                lda     #2              ; the third
                bra     da_arp_tone
da_arp_root
                clra
                bra     da_arp_tone
da_arp_fifth
                lda     #4
da_arp_tone
                adda    demo_chord
                cmpa    #7
                blo     da_arp_wrap
                suba    #7
da_arp_wrap
                pshs    a
                lbsr    demo_scale
                puls    a
                tfr     a,b
                abx
                lda     ,x
                adda    #DEMO_ARP
                sta     ,u+
                lda     #5
                sta     ,u+
                lda     #1
                sta     ,u+

                ; --- voice 3: percussion on the beat ---
                lda     demo_beat
                bne     da_drum_back
                lda     #60             ; kick on the downbeat
                sta     ,u+
                lda     #13
                sta     ,u+
                lda     #4
                sta     ,u+
                bra     da_next
da_drum_back
                cmpa    #DEMO_BAR_ROWS/2
                bne     da_drum_hat
                lda     #60             ; snare on the backbeat
                sta     ,u+
                lda     #10
                sta     ,u+
                lda     #3
                sta     ,u+
                bra     da_next
da_drum_hat
                bita    #1
                bne     da_drum_none
                lda     #60             ; hats between
                sta     ,u+
                lda     #3
                sta     ,u+
                lda     #5
                sta     ,u+
                bra     da_next
da_drum_none
                clr     ,u+
                clr     ,u+
                clr     ,u+

da_next
                stu     demo_write
                ldd     demo_row
                addd    #1
                std     demo_row
                cmpd    #TUNE_ROWS
                lblo    da_row
                rts

; The step table for the current mode.
demo_scale
                ldx     #demo_steps
                tst     demo_mode
                beq     ds_done
                ldx     #demo_steps_min
ds_done         rts

; ------------------------------------------------------------------------
demo_main
                lbsr    ui_main
                rts

demo_run
                lbsr    demo_compose
                lbsr    demo_arrange
                lda     #7              ; the tempo the display defaults to
                sta     >compile_ticks
                lbsr    compile_rows
                lbsr    music_start
                rts
