; Four-voice wavetable synthesizer: EXP-017, the wavetable voices.
;
; This is EXP-009's player with one change to each tone voice. Where that
; player took bit 15 of the phase accumulator and masked a volume against
; it, this one uses the accumulator's high byte to index a 256-byte page of
; a waveform, and the voice's volume to choose which of sixteen pages. The
; page number sits in memory immediately before the phase, so a single LDX
; on it loads page:phase_hi, which is the address of the next sample. The
; lookup is then one instruction, and the voice costs the same 33 cycles on
; a 6809 as the masked bit did, one fewer in fact. The sample rate does not
; move; the shape of the wave does.
;
; Everything else the frozen player established still holds: the sample
; clock is the instruction stream, every path through the loop costs the
; same, and anything between samples fits between samples. That last rule
; is why the decay pass, which now also has to update a page number, is
; spread one voice per sample the way the row's cells already were.
;
; Voice 3 is the noise channel, unchanged. Interrupts stay masked.
;
; Build-time switches, off unless a wrapper defines them:
;   MUSIC_FAST_CLOCK  the CoCo 3's 1.78 MHz clock (table built for it)
;   MUSIC_6309        a 6309 in native mode, tick countdown in W
; The wrapper supplies tune_data.inc, wavetable.inc and the entry that
; sets row_hook.

PIA0_CRA        equ     $FF01
PIA0_CRB        equ     $FF03
PIA1_DA         equ     $FF20
PIA1_CRA        equ     $FF21
PIA1_CRB        equ     $FF23

SLOW_CLOCK      equ     $FFD8
FAST_CLOCK      equ     $FFD9

VOICES          equ     4
LOW_NOTE        equ     12
NOTE_HOLD_CODE  equ     0
NOTE_OFF_CODE   equ     1
VSTATE_STRIDE   equ     3               ; page, phase high, phase low

; The wavetable's first page. Volume v's page is WAVE_PAGE+v, and page 0,
; volume zero, is all silence, which is what a cleared voice must read.
WAVE_PAGE       equ     wave_table/256

set_tick        macro
                ifdef   MUSIC_6309
                ldd     #\1
                std     <tick_samples
                else
                lda     #\1
                sta     <tick_samples
                endc
                endm

                setdp   $20
                org     $2000

; ---- direct page state ----
; vstate through decays are cleared as one contiguous block on reset.
vstate          rmb     VOICES*VSTATE_STRIDE ; per voice: page, phase_hi, phase_lo
incrs           rmb     8               ; matching phase increments
scaled          rmb     4               ; volume already shifted to PA2-PA7
decays          rmb     4               ; per-tick decrement, in the same units
STATE_BYTES     equ     28

dac_acc         rmb     1
lfsr            rmb     2

                ifdef   MUSIC_6309
tick_samples    rmb     2
                else
tick_samples    rmb     1
                endc
row_ticks       rmb     1
rows_left       rmb     1
repeats_left    rmb     1
row_ptr         rmb     2
finished        rmb     1
voice_no        rmb     1
cells_left      rmb     1
decay_left      rmb     1               ; voices of this tick's decay still to run
row_hook        rmb     2               ; set by the wrapper; see coco_wave.asm
ticks_cfg       rmb     1
incr_tmp        rmb     2
scratch         rmb     1
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

                tst     <ticks_cfg
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
                ldx     #vstate
                ldb     #STATE_BYTES
tr_clear        clr     ,x+
                decb
                bne     tr_clear

; A cleared voice must read the silent page, not page zero of memory.
                lda     #WAVE_PAGE
                sta     <vstate
                sta     <vstate+VSTATE_STRIDE
                sta     <vstate+VSTATE_STRIDE*2
                sta     <vstate+VSTATE_STRIDE*3

                ldd     #$ACE1          ; LFSR seed, matching the reference
                std     <lfsr
                clr     <dac_acc
                clr     <cells_left
                clr     <decay_left
                clr     <finished

                ldd     #tune_rows
                std     <row_ptr
                lda     #TUNE_ROWS
                sta     <rows_left
                lda     #1
                sta     <row_ticks      ; expires immediately, fetching row 0
                ifdef   MUSIC_6309
                ldd     #1
                std     <tick_samples
                else
                sta     <tick_samples
                endc
                rts

; ----------------------------------------------------------- sample loop ----
; Constant cost on every path. `make music-cycles PLAYER=wave` enumerates it.
play_tune
                ifdef   MUSIC_6309
                ldw     <tick_samples
                endc
sample_loop
; ---- voice 3: noise, exactly as EXP-009 ----
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

; ---- voice 2: advance the phase, then read the wave at page:phase_hi ----
                ldd     <vstate+7       ; 5   phase
                addd    <incrs+4        ; 6
                std     <vstate+7       ; 5
                ldx     <vstate+6       ; 5   page:phase_hi is the sample's address
                lda     ,x              ; 4
                adda    <dac_acc        ; 4
                sta     <dac_acc        ; 4

; ---- voice 1 ----
                ldd     <vstate+4
                addd    <incrs+2
                std     <vstate+4
                ldx     <vstate+3
                lda     ,x
                adda    <dac_acc
                sta     <dac_acc

; ---- voice 0 ----
                ldd     <vstate+1
                addd    <incrs
                std     <vstate+1
                ldx     <vstate
                lda     ,x
                adda    <dac_acc

; ---- output ----
                sta     PIA1_DA

                ifdef   MUSIC_6309
                decw
                bne     sample_loop

                lbsr    next_tick
                tst     <finished
                bne     play_done
                ldw     <tick_samples
                bra     sample_loop
                else
                dec     <tick_samples
                bne     sample_loop

                lbsr    next_tick
                tst     <finished
                bne     play_done
                bra     sample_loop
                endc

play_done
                rts

; ----------------------------------------------------------------- tick ----
; Every path through here fits in one sample period. A row's cells are
; applied one per sample, as in EXP-009; a tick's decays are now applied
; one per sample as well, because each one also rewrites a table page.
next_tick
                tst     <cells_left
                bne     nt_cell
                tst     <decay_left
                bne     nt_decay

                dec     <row_ticks
                beq     nt_row

                lda     #VOICES         ; a plain tick: decay, one voice per sample
                sta     <decay_left
                clr     <voice_no
                set_tick 1
                rts

nt_decay
                ldx     #vstate         ; this voice's page byte: X = vstate + 3*voice
                ldb     <voice_no
                abx
                abx
                abx
                ldy     #decays
                ldb     <voice_no
                lda     b,y             ; per-tick decrement
                beq     nd_next
                ldy     #scaled
                leay    b,y
                ldb     ,y              ; current amplitude
                beq     nd_next         ; already silent
                sta     <scratch
                subb    <scratch
                bcc     nd_store
                clrb                    ; clamp at silence
nd_store
                stb     ,y
                lsrb                    ; amplitude is volume*4; the page is
                lsrb                    ; WAVE_PAGE + volume
                addb    #WAVE_PAGE
                stb     ,x
nd_next
                inc     <voice_no
                dec     <decay_left
                bne     nd_more
                set_tick SAMPLES_PER_TICK-VOICES ; the rest of the tick
                rts
nd_more
                set_tick 1
                rts

nt_cell
                lda     <cells_left
                cmpa    #1
                bne     nt_cell_apply
                clr     <cells_left
                set_tick SAMPLES_PER_TICK-VOICES-1
                jsr     [row_hook]
                rts

nt_cell_apply
                ldu     <row_ptr
                lbsr    apply_cell
                stu     <row_ptr
                inc     <voice_no
                dec     <cells_left
                set_tick 1
                rts

nt_row
                lbsr    next_row
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
                lda     <ticks_cfg
                sta     <row_ticks
                clr     <voice_no
                lda     #VOICES+1       ; one extra for the display hook
                sta     <cells_left
                set_tick 1
                rts

row_hook_none   rts

; Apply one cell. U points at note, volume, decay and is advanced by three.
apply_cell
                lda     ,u
                cmpa    #NOTE_HOLD_CODE
                beq     ac_skip
                cmpa    #NOTE_OFF_CODE
                beq     ac_off

                suba    #LOW_NOTE       ; index the increment table
                lsla
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

                ldx     #vstate         ; retrigger the phase and point the
                ldb     <voice_no       ; voice at its volume's page
                abx
                abx
                abx
                clr     1,x
                clr     2,x
                lda     1,u
                adda    #WAVE_PAGE
                sta     ,x
                bra     ac_skip

ac_off
                ldx     #scaled         ; silence this voice, leave the rest
                ldb     <voice_no
                abx
                clr     ,x
                ldx     #vstate
                ldb     <voice_no
                abx
                abx
                abx
                lda     #WAVE_PAGE      ; the silent page
                sta     ,x

ac_skip
                leau    3,u
                rts
