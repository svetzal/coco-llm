; Four-voice software synthesizer for a stock CoCo 1.
;
; The CoCo 1 has no timer usable at audio rates. Its only periodic interrupt
; fast enough is horizontal sync at 15.7 kHz, and a 6809 IRQ costs 19 cycles
; to enter and 15 to leave against a 57-cycle HSYNC period, so interrupt
; overhead alone would consume the machine. The sample clock therefore has to
; be the instruction stream itself: the sample rate IS this loop's cycle
; count, and every path through it must cost the same.
;
; That constraint drives every decision here.
;
; Voices 0 to 2 take bit 15 of a 16-bit phase accumulator. Voice 3 is a
; dedicated noise channel with no accumulator: an LFSR is clocked once per
; sample and its low bit is the output. A switchable tone/noise voice would
; need a branch, and a branch would modulate the sample period.
;
; There is no mix table. An earlier version precomputed the sixteen possible
; voice sums, which made the sample path cheap but forced a 199-cycle rebuild
; whenever a volume changed. That rebuild froze the DAC for three sample
; periods fifty times a second, and the resulting 50 Hz disturbance of the
; sample clock was clearly audible as warble.
;
; Instead each voice's contribution is masked in branchlessly and summed. With
; A zero, SBCA #0 leaves $FF when carry was set and $00 when it was clear, so
; ANDing that against the voice's amplitude adds either the amplitude or
; nothing without testing anything. Volumes are pre-shifted into PA2-PA7
; position, so four voices at full volume sum to 240 and never leave a byte.
;
; Interrupts stay masked throughout. The 60 Hz IRQ would jitter the loop.

PIA0_CRA        equ     $FF01
PIA0_CRB        equ     $FF03
PIA1_DA         equ     $FF20
PIA1_CRA        equ     $FF21
PIA1_CRB        equ     $FF23

; Writing anywhere in $FFD8 selects the slow clock. On a CoCo 1 that clears
; SAM bit R1, the normal state; on a CoCo 3 it selects 0.89 MHz rather than
; 1.78. The tuning is a cycle count, so the clock cannot be left to whatever
; the host BASIC happened to set.
SLOW_CLOCK      equ     $FFD8

VOICES          equ     4
LOW_NOTE        equ     12
NOTE_HOLD_CODE  equ     0
NOTE_OFF_CODE   equ     1

                setdp   $20
                org     $2000

; ---- direct page state ----
; phases through decays are cleared as one contiguous block on reset.
phases          rmb     8               ; three 16-bit accumulators, one spare
incrs           rmb     8               ; matching phase increments
scaled          rmb     4               ; volume already shifted to PA2-PA7
decays          rmb     4               ; per-tick decrement, in the same units
STATE_BYTES     equ     24

dac_acc         rmb     1               ; sum of the voices high this sample
lfsr            rmb     2               ; 16-bit maximal-length shift register

tick_samples    rmb     1
row_ticks       rmb     1
rows_left       rmb     1
repeats_left    rmb     1
row_ptr         rmb     2
finished        rmb     1
voice_no        rmb     1
cells_left      rmb     1               ; cells of the current row still to apply
row_hook        rmb     2               ; called once per row, in its own sample
ticks_cfg       rmb     1               ; ticks per row, so tempo can change
incr_tmp        rmb     2
scratch         rmb     1
saved_dp        rmb     1

                org     $2100

; ---------------------------------------------------------------- entry ----
music_start
                tfr     dp,a
                sta     <saved_dp       ; DP is still the caller's page here
                orcc    #$50            ; mask IRQ and FIRQ for the whole tune
                lda     #$20
                tfr     a,dp

                tst     <ticks_cfg      ; default the tempo if nobody set one
                bne     ms_tempo_set
                lda     #TICKS_PER_ROW
                sta     <ticks_cfg
ms_tempo_set
                lbsr    audio_enable
                lda     #TUNE_REPEATS
                sta     <repeats_left

music_pass
                lbsr    tune_reset
                lbsr    play_tune
                dec     <repeats_left
                bne     music_pass

                lbsr    audio_disable
                lda     <saved_dp
                tfr     a,dp
                andcc   #$AF            ; restore interrupts
                rts

; ------------------------------------------------------------ hardware ----
; PA2-PA7 drive the DAC. PA0 is cassette in and PA1 is RS-232 in, so the
; direction register must leave those two as inputs.
audio_enable
                sta     SLOW_CLOCK      ; force 0.89 MHz before anything is timed

                lda     PIA1_CRA
                anda    #$FB            ; select the direction register
                sta     PIA1_CRA
                lda     #$FC
                sta     PIA1_DA         ; PA2-PA7 out, PA0-PA1 in
                lda     PIA1_CRA
                ora     #$04            ; back to the peripheral register
                sta     PIA1_CRA

                lda     PIA1_CRB
                ora     #$38            ; CB2 as output, held high: sound on
                sta     PIA1_CRB

                lda     PIA0_CRA        ; mux select lines low selects the DAC
                anda    #$F7
                ora     #$30
                sta     PIA0_CRA
                lda     PIA0_CRB
                anda    #$F7
                ora     #$30
                sta     PIA0_CRB
                rts

audio_disable
                clra
                sta     PIA1_DA         ; rest the DAC at zero
                lda     PIA1_CRB
                anda    #$F7            ; CB2 low mutes the output
                sta     PIA1_CRB
                rts

; ---------------------------------------------------------------- reset ----
tune_reset
                ldx     #phases
                ldb     #STATE_BYTES
tr_clear        clr     ,x+
                decb
                bne     tr_clear

                ldd     #$ACE1          ; LFSR seed, matching the reference
                std     <lfsr
                clr     <dac_acc
                clr     <cells_left
                clr     <finished

                ldd     #row_hook_none  ; nothing on screen unless installed
                std     <row_hook
                ldd     #tune_rows
                std     <row_ptr
                lda     #TUNE_ROWS
                sta     <rows_left
                lda     #1
                sta     <row_ticks      ; expires immediately, fetching row 0
                sta     <tick_samples
                rts

; ----------------------------------------------------------- sample loop ----
; Constant cost on every path. `make music-cycles` enumerates it.
play_tune
sample_loop
; ---- voice 3: noise ----
                lsr     <lfsr           ; 6
                ror     <lfsr+1         ; 6   carry is the bit shifted out
                lda     #$00            ; 2
                sbca    #$00            ; 2   $FF if the shifted-out bit was 1
                anda    #$B4            ; 2   taps $B400; low byte is untouched
                eora    <lfsr           ; 4
                sta     <lfsr           ; 4
                lda     <lfsr+1         ; 4
                lsra                    ; 2   bit 0 into carry
                lda     #$00            ; 2
                sbca    #$00            ; 2   mask from the voice's output bit
                anda    <scaled+3       ; 4
                sta     <dac_acc        ; 4   first voice seeds the sum

; ---- voice 2 ----
                ldd     <phases+4       ; 5
                addd    <incrs+4        ; 6
                std     <phases+4       ; 5
                rola                    ; 2   bit 15 into carry
                lda     #$00            ; 2
                sbca    #$00            ; 2
                anda    <scaled+2       ; 4
                adda    <dac_acc        ; 4
                sta     <dac_acc        ; 4

; ---- voice 1 ----
                ldd     <phases+2
                addd    <incrs+2
                std     <phases+2
                rola
                lda     #$00
                sbca    #$00
                anda    <scaled+1
                adda    <dac_acc
                sta     <dac_acc

; ---- voice 0 ----
                ldd     <phases
                addd    <incrs
                std     <phases
                rola
                lda     #$00
                sbca    #$00
                anda    <scaled+0
                adda    <dac_acc

; ---- output ----
                sta     PIA1_DA         ; 5

                dec     <tick_samples   ; 6
                bne     sample_loop     ; 3

                lbsr    next_tick
                tst     <finished
                bne     play_done
                bra     sample_loop

play_done
                rts

; ----------------------------------------------------------------- tick ----
; Reached whenever tick_samples reaches zero. Every path through here is kept
; under one sample period, so no pause can stretch the timeline by a whole
; sample. That is the whole design rule: the sample clock is the instruction
; stream, so anything that runs between samples has to fit between samples.
next_tick
                tst     <cells_left     ; still applying a row?
                bne     nt_cell

                lda     #SAMPLES_PER_TICK
                sta     <tick_samples

                dec     <row_ticks
                beq     nt_row

                ldx     #scaled         ; decay: 124 cycles, 0.8 sample periods
                ldy     #decays
                lda     #VOICES
                sta     <voice_no
nt_voice
                lda     ,y+             ; this voice's per-tick decrement
                beq     nt_next
                ldb     ,x              ; current amplitude
                beq     nt_next         ; already silent
                sta     <scratch
                subb    <scratch
                bcc     nt_store
                clrb                    ; clamp at silence
nt_store
                stb     ,x
nt_next
                leax    1,x
                dec     <voice_no
                bne     nt_voice
                rts

; One cell per sample. Applying all four together stalled the DAC for 2.7
; sample periods eight times a second; spread out, each pause is under one,
; and the four notes still land within a millisecond of each other.
; The last borrowed sample of a row calls the display hook rather than a
; cell. It gets a whole sample period to itself, so a screen update cannot
; stretch the timeline any more than applying a cell does. The hook defaults
; to a plain return, leaving the standalone player unchanged.
nt_cell
                lda     <cells_left
                cmpa    #1
                bne     nt_cell_apply
                clr     <cells_left
                lda     #SAMPLES_PER_TICK-VOICES-1
                sta     <tick_samples
                jsr     [row_hook]
                rts

nt_cell_apply
                ldu     <row_ptr
                lbsr    apply_cell
                stu     <row_ptr
                inc     <voice_no
                dec     <cells_left
                lda     #1              ; return on the very next sample
                sta     <tick_samples
                rts

nt_row
                lbsr    next_row
                rts

; ------------------------------------------------------------------ row ----
; Only starts a row. Its cells are applied one per sample by nt_cell.
next_row
                lda     <rows_left
                bne     nr_fetch
                lda     #1
                sta     <finished
                rts

nr_fetch
                deca
                sta     <rows_left
                lda     <ticks_cfg
                sta     <row_ticks
                clr     <voice_no
                lda     #VOICES+1       ; one extra for the display hook
                sta     <cells_left
                lda     #1              ; first cell on the next sample
                sta     <tick_samples
                rts

; The default hook: no display, so the standalone player behaves exactly as
; it did before one existed.
row_hook_none   rts

; Apply one cell. U points at note, volume, decay and is advanced by three.
; Voice 3 has no pitch, but writing its unused increment is cheaper than
; branching around it.
apply_cell
                lda     ,u
                cmpa    #NOTE_HOLD_CODE
                beq     ac_skip
                cmpa    #NOTE_OFF_CODE
                beq     ac_off

                suba    #LOW_NOTE       ; index the increment table
                lsla                    ; two bytes per entry, 0..192
                tfr     a,b
                ldx     #note_increments
                abx                     ; ABX adds B unsigned, so >127 is fine
                ldd     ,x
                std     <incr_tmp

                ldx     #incrs
                ldb     <voice_no
                lslb
                abx
                ldd     <incr_tmp
                std     ,x

                ldx     #phases         ; retrigger from a known phase
                ldb     <voice_no
                lslb
                abx
                clr     ,x
                clr     1,x

                lda     1,u             ; volume, 0..15
                lsla
                lsla                    ; pre-shift onto PA2-PA7
                sta     <scratch
                ldx     #scaled
                ldb     <voice_no
                abx
                lda     <scratch
                sta     ,x

                lda     2,u             ; decay, in the same shifted units
                lsla
                lsla
                sta     <scratch
                ldx     #decays
                ldb     <voice_no
                abx
                lda     <scratch
                sta     ,x
                bra     ac_skip

ac_off
                ldx     #scaled         ; silence this voice, leave the rest
                ldb     <voice_no
                abx
                clr     ,x

ac_skip
                leau    3,u
                rts

; The tune data is a build artifact, not part of the player. The demo supplies
; its own frame with an empty buffer the generator fills, which the player
; cannot distinguish: it only ever reads twelve bytes per row from tune_rows.
                ifndef  TUNE_DATA_EXTERNAL
                include "../../build/exp009/tune_data.inc"
                endc
