; Four-voice software synthesizer for a stock CoCo 1.
;
; Every voice is a one-bit source, so the sum of four voices takes only
; sixteen values. Those are precomputed into a table whenever a volume
; changes, which happens on tick boundaries. The per-sample path is then four
; 16-bit adds, four bit extractions, one indexed load, and one store to the
; DAC. There is no multiply, no divide, and no per-sample addition.
;
; Voices 0 to 2 take bit 15 of a 16-bit phase accumulator. Voice 3 is a
; dedicated noise channel with no accumulator: an LFSR is clocked once per
; sample and its low bit is the output.
;
; Voices are processed 3,2,1,0 so that successive ROLs leave voice v in bit v
; of the mix index, matching the reference implementation's bit order.
;
; Interrupts stay masked for the whole tune. The 60 Hz IRQ would otherwise
; jitter the sample loop audibly.

PIA0_CRA        equ     $FF01
PIA0_CRB        equ     $FF03
PIA1_DA         equ     $FF20
PIA1_CRA        equ     $FF21
PIA1_CRB        equ     $FF23

; Writing anywhere in $FFD8 selects the slow clock. On a CoCo 1 that clears
; SAM bit R1, the normal state; on a CoCo 3 it selects 0.89 MHz rather than
; 1.78. The tuning is derived from a cycle count, so the clock cannot be left
; to whatever the host BASIC happened to leave set.
SLOW_CLOCK      equ     $FFD8

VOICES          equ     4
NOISE_VOICE     equ     3
LOW_NOTE        equ     12
MIX_ENTRIES     equ     16

NOTE_HOLD_CODE  equ     0
NOTE_OFF_CODE   equ     1

                setdp   $20
                org     $2000

; ---- direct page state, all within page $20 ----
; phases through noises are cleared as one contiguous block on reset.
phases          rmb     8               ; four 16-bit phase accumulators
incrs           rmb     8               ; four 16-bit phase increments
vols            rmb     4               ; 0..15 per voice
decays          rmb     4               ; subtracted from vol each tick
noises          rmb     4               ; retained so the reset block stays contiguous
STATE_BYTES     equ     28

mixindex        rmb     1               ; low four bits rebuilt every sample
lfsr            rmb     2               ; 16-bit maximal-length shift register
mixtable        rmb     MIX_ENTRIES     ; DAC values, already shifted to PA2-PA7

tick_samples    rmb     1               ; samples remaining in this tick
row_ticks       rmb     1               ; ticks remaining in this row
rows_left       rmb     1               ; rows remaining in this pass
repeats_left    rmb     1
row_ptr         rmb     2
finished        rmb     1
voice_no        rmb     1               ; row cursor, also the tick countdown
changed         rmb     1               ; a volume moved, so rebuild the table
scratch         rmb     1
scaled          rmb     4               ; volumes pre-shifted for the mix table
saved_dp        rmb     1

                org     $2100

; ---------------------------------------------------------------- entry ----
music_start
                tfr     dp,a
                sta     <saved_dp       ; DP is still the caller's page here
                orcc    #$50            ; mask IRQ and FIRQ for the whole tune
                lda     #$20
                tfr     a,dp

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
                clr     <mixindex
                clr     <finished

                ldd     #tune_rows
                std     <row_ptr
                lda     #TUNE_ROWS
                sta     <rows_left
                lda     #1
                sta     <row_ticks      ; expires immediately, fetching row 0
                sta     <tick_samples
                lbsr    build_mix
                rts

; ----------------------------------------------------------- sample loop ----
; The hot path. `make music-cycles` measures its real cost; the sample rate in
; the exported tune data is derived from that measurement.
play_tune
                ldx     #mixtable

sample_loop
; ---- voice 3: dedicated noise, branch-free, fixed cost ----
; A software DAC has no timer, so the sample rate IS this loop's cycle count.
; Any branch here modulates the sample period and is audible as distortion.
; The tap is applied with SBCA rather than a conditional branch: with A zero,
; SBCA #0 leaves $FF when carry was set and $00 when it was clear. LDA does
; not disturb carry, so it can sit between the shift and the subtract.
                lsr     <lfsr           ; 6
                ror     <lfsr+1         ; 6   carry is the bit shifted out
                lda     #$00            ; 2
                sbca    #$00            ; 2   $FF if the shifted-out bit was 1
                anda    #$B4            ; 2   taps $B400; low byte is untouched
                eora    <lfsr           ; 4
                sta     <lfsr           ; 4
                lda     <lfsr+1         ; 4
                lsra                    ; 2   bit 0 of the register into carry
                rol     <mixindex       ; 6

; ---- voices 2, 1, 0: always square ----
                ldd     <phases+4
                addd    <incrs+4
                std     <phases+4
                rola
                rol     <mixindex

                ldd     <phases+2
                addd    <incrs+2
                std     <phases+2
                rola
                rol     <mixindex

                ldd     <phases
                addd    <incrs
                std     <phases
                rola
                rol     <mixindex

; ---- mix and output ----
                ldb     <mixindex
                andb    #$0F            ; discard bits rolled out earlier
                lda     b,x
                sta     PIA1_DA

                dec     <tick_samples
                bne     sample_loop

                lbsr    next_tick
                tst     <finished
                bne     play_done
                ldx     #mixtable
                bra     sample_loop

play_done
                rts

; ----------------------------------------------------------------- tick ----
next_tick
                lda     #SAMPLES_PER_TICK
                sta     <tick_samples

                dec     <row_ticks
                beq     nt_row

                clr     <changed
                ldx     #vols
                ldy     #decays
                lda     #VOICES
                sta     <voice_no
nt_voice
                lda     ,y+             ; decay amount for this voice
                beq     nt_next
                ldb     ,x              ; current volume
                beq     nt_next         ; already silent
                sta     <scratch
                subb    <scratch
                bcc     nt_store
                clrb                    ; clamp at silence
nt_store
                stb     ,x
                inc     <changed
nt_next
                leax    1,x
                dec     <voice_no
                bne     nt_voice

                tst     <changed
                beq     nt_done
                lbsr    build_mix
nt_done
                rts

nt_row
                lbsr    next_row        ; a new row rebuilds the table itself
                rts

; ------------------------------------------------------------------ row ----
next_row
                lda     <rows_left
                bne     nr_fetch
                lda     #1
                sta     <finished
                rts

nr_fetch
                deca
                sta     <rows_left
                lda     #TICKS_PER_ROW
                sta     <row_ticks

                ldu     <row_ptr
                clr     <voice_no
nr_voice
                lbsr    apply_cell
                inc     <voice_no
                lda     <voice_no
                cmpa    #VOICES
                bne     nr_voice

                stu     <row_ptr
                lbsr    build_mix
                rts

; Apply one cell. U points at note, volume+flags, decay; it is advanced by
; three. The voice index lives in <voice_no so every register stays free.
apply_cell
                lda     ,u
                cmpa    #NOTE_HOLD_CODE
                beq     ac_skip
                cmpa    #NOTE_OFF_CODE
                beq     ac_off

                ldb     <voice_no       ; voice 3 has no pitch; only retrigger
                cmpb    #NOISE_VOICE
                beq     ac_volume

                suba    #LOW_NOTE       ; index the increment table
                lsla                    ; two bytes per entry, 0..192
                tfr     a,b
                ldx     #note_increments
                abx                     ; ABX adds B unsigned, so >127 is fine
                ldd     ,x              ; D is this note's phase increment

                ldx     #incrs
                pshs    d
                ldb     <voice_no
                lslb                    ; two bytes per voice
                abx
                puls    d
                std     ,x

                ldx     #phases         ; retrigger from a known phase
                ldb     <voice_no
                lslb
                abx
                clr     ,x
                clr     1,x

ac_volume
                lda     1,u             ; volume, already masked by the exporter
                ldx     #vols
                pshs    a
                ldb     <voice_no
                abx
                puls    a
                sta     ,x

                lda     2,u
                ldx     #decays
                pshs    a
                ldb     <voice_no
                abx
                puls    a
                sta     ,x
                bra     ac_skip

ac_off
                ldx     #vols           ; silence this voice, leave the rest
                ldb     <voice_no
                abx
                clr     ,x

ac_skip
                leau    3,u
                rts

; ------------------------------------------------------------ mix table ----
; table[i] = sum of the volumes of the voices whose bit is set in i, shifted
; left twice so the value already sits on PA2-PA7.
;
; Subset sums, fully unrolled: fifteen adds rather than sixty-four bit tests.
; This runs between samples, so a variable cost would show up as a periodic
; artefact at the tick rate. Unrolled, it is constant.
;
; Volumes are pre-shifted so every entry is a plain add. Four voices at full
; volume reach 60, and 60 << 2 is 240, still inside a byte.
build_mix
                lda     <vols+0
                lsla
                lsla
                sta     <scaled+0
                lda     <vols+1
                lsla
                lsla
                sta     <scaled+1
                lda     <vols+2
                lsla
                lsla
                sta     <scaled+2
                lda     <vols+3
                lsla
                lsla
                sta     <scaled+3

                clr     <mixtable+0
                lda     <scaled+0
                sta     <mixtable+1
                lda     <scaled+1
                sta     <mixtable+2
                adda    <scaled+0
                sta     <mixtable+3
                lda     <scaled+2
                sta     <mixtable+4
                adda    <scaled+0
                sta     <mixtable+5
                lda     <scaled+2
                adda    <scaled+1
                sta     <mixtable+6
                adda    <scaled+0
                sta     <mixtable+7
                lda     <scaled+3
                sta     <mixtable+8
                adda    <scaled+0
                sta     <mixtable+9
                lda     <scaled+3
                adda    <scaled+1
                sta     <mixtable+10
                adda    <scaled+0
                sta     <mixtable+11
                lda     <scaled+3
                adda    <scaled+2
                sta     <mixtable+12
                adda    <scaled+0
                sta     <mixtable+13
                lda     <scaled+3
                adda    <scaled+2
                adda    <scaled+1
                sta     <mixtable+14
                adda    <scaled+0
                sta     <mixtable+15
                rts

                include "../../build/exp009/tune_data.inc"
