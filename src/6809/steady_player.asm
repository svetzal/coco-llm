; Four-voice synthesizer with a steady sample clock: EXP-018.
;
; EXP-009's sample loop, with its row and tick machinery removed. The tune
; arrives compiled into a stream of events: a wait in samples, then one
; byte and the address to store it at. When the wait runs out the loop
; applies the event and reads the next wait; when it has not, the loop
; runs a padding path that costs exactly the same. So every sample costs
; the same number of cycles whatever the tune is doing, and the sample
; clock never stretches. That stretch, five nearly-doubled samples at
; every row change, is the warble EXP-015 heard on the melody voice.
;
; What the CoCo does per sample: four voices, one DAC write, one countdown,
; and one event or its padding. What it never does: fetch a row, apply a
; cell, decay a volume. The compiler did all of that first, on the Mac
; (tools/export_events.py) or on the CoCo (steady_compile.asm). The
; address is absolute, so an event can as easily draw a cursor on the
; screen as change a voice.
;
; X holds the stream pointer for the whole tune. Interrupts stay masked.
;
; Build-time switches, off unless a wrapper defines them:
;   MUSIC_FAST_CLOCK  the CoCo 3's 1.78 MHz clock (stream built for it)
;   MUSIC_6309        a 6309 in native mode: same instructions, its own
;                     padding, because its cycle counts differ

PIA0_CRA        equ     $FF01
PIA0_CRB        equ     $FF03
PIA1_DA         equ     $FF20
PIA1_CRA        equ     $FF21
PIA1_CRB        equ     $FF23

SLOW_CLOCK      equ     $FFD8
FAST_CLOCK      equ     $FFD9

                setdp   $20
                org     $2000

; ---- direct page state ----
; The offsets are the contract with src/reference/steady_synth.py, which
; compiles the stream against them. The parity test checks they agree.
phases          rmb     8               ; $00  three 16-bit accumulators, one spare
incrs           rmb     8               ; $08  matching phase increments
scaled          rmb     4               ; $10  volume already shifted to PA2-PA7
STATE_BYTES     equ     20
dac_acc         rmb     1               ; $14
lfsr            rmb     2               ; $15
tick_samples    rmb     1               ; $17  samples until the next event
finished        rmb     1               ; $18  the last event writes 1 here
scratch         rmb     1               ; $19  where a filler event writes
ev_ptr          rmb     2               ; $1A  the stream, for play_tune
repeats_left    rmb     1
saved_dp        rmb     1

                org     $2100

; ---------------------------------------------------------------- entry ----
music_start
                tfr     dp,a
                sta     >saved_dp
                orcc    #$50            ; mask IRQ and FIRQ for the whole tune
                ifdef   MUSIC_6309
                ldmd    #1
                endc
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
                lda     >saved_dp
                tfr     a,dp
                ifdef   MUSIC_6309
                ldmd    #0
                endc
                andcc   #$AF
                rts

; ------------------------------------------------------------ hardware ----
audio_enable
                ifdef   MUSIC_FAST_CLOCK
                sta     FAST_CLOCK
                else
                sta     SLOW_CLOCK
                endc

                lda     PIA1_CRA
                anda    #$FB
                sta     PIA1_CRA
                lda     #$FC
                sta     PIA1_DA         ; PA2-PA7 out, PA0-PA1 in
                lda     PIA1_CRA
                ora     #$04
                sta     PIA1_CRA

                lda     PIA1_CRB
                ora     #$38            ; CB2 high: sound on
                sta     PIA1_CRB

                lda     PIA0_CRA        ; mux select lines low: the DAC
                anda    #$F7
                ora     #$30
                sta     PIA0_CRA
                lda     PIA0_CRB
                anda    #$F7
                ora     #$30
                sta     PIA0_CRB
                rts

audio_disable
                ifdef   MUSIC_FAST_CLOCK
                sta     SLOW_CLOCK
                endc
                clra
                sta     PIA1_DA
                lda     PIA1_CRB
                anda    #$F7
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
                clr     <finished
                ldd     #event_stream
                std     <ev_ptr
                rts

; ----------------------------------------------------------- sample loop ----
; Constant cost on every path, including the two ways out of the countdown.
; `make music-cycles PLAYER=steady` enumerates it and states the padding.
play_tune
                ldx     <ev_ptr         ; the stream
                lda     ,x+             ; the first wait
                sta     <tick_samples
sample_loop
; ---- voice 3: noise ----
                lsr     <lfsr
                ror     <lfsr+1
                lda     #$00
                sbca    #$00
                anda    #$B4
                eora    <lfsr
                sta     <lfsr
                lda     <lfsr+1
                lsra
                lda     #$00
                sbca    #$00
                anda    <scaled+3
                sta     <dac_acc

; ---- voice 2 ----
                ldd     <phases+4
                addd    <incrs+4
                std     <phases+4
                rola
                lda     #$00
                sbca    #$00
                anda    <scaled+2
                adda    <dac_acc
                sta     <dac_acc

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
                sta     PIA1_DA

; ---- the event, or exactly its cost in padding ----
                dec     <tick_samples   ; 6809 6   6309 5
                bne     idle            ;      3        3
                ldu     ,x++            ;      8        6   the address,
                lda     ,x+             ;      6        5   the byte,
                sta     ,u              ;      4        4   stored there,
                lda     ,x+             ;      6        5   and the next wait
                sta     <tick_samples   ;      4        3
                tst     <finished       ;      6        5
                bne     play_done       ;      3        3
                bra     sample_loop     ;      3        3   = 40 / 34 after bne

idle
                ifdef   MUSIC_6309
; 31 cycles: ten BRN at 3 and one NOP at 1, then the branch back.
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                nop
                else
; 37 cycles: eleven BRN at 3 and two NOP at 2, then the branch back.
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                brn     *
                nop
                nop
                endc
                bra     sample_loop     ;      3        3   = 40 / 34 after bne

play_done
                rts
