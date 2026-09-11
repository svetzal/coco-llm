# Tools. Every one of these can be overridden on the command line, e.g.
# `make xroar-test XROAR=/usr/bin/xroar COCO_ROM_ARCHIVE=~/roms/cocoe.zip`.
# See README.md, "Getting started", for what to install.
UV ?= uv
LWASM ?= lwasm
SIM6809 := .tools/6809/bin/6809
SIM6809_REV := 546c8d2efc7d30cecb5afe9bc05e683a4bfbd672
# XRoar: whatever is on PATH, else Homebrew's keg on Apple silicon.
XROAR ?= $(or $(shell command -v xroar 2>/dev/null),/opt/homebrew/opt/xroar/bin/xroar)
# The Tandy ROM images are copyrighted and not in this repository. Point
# these at your own MAME-style archives (cocoe.zip holds bas11.rom and
# extbas10.rom; coco3.zip holds coco3.rom). The defaults are the author's.
COCO_ROM_ARCHIVE ?= $(HOME)/OneDrive/CoCo/MAME/roms/cocoe.zip
COCO_BASIC_ROM := build/roms/bas11.rom
COCO_EXTBASIC_ROM := build/roms/extbas10.rom

.PHONY: test reference-test asm-test model-test model-test-exp6 model-test-exp7 \
	workbench-test-exp6 workbench-test-exp7 coco-bin \
	xroar-test xroar \
	model-test-exp5 coco-bin-exp5 xroar-test-exp5 xroar-exp5 exp006-model \
	coco-bin-exp6 xroar-test-exp6 xroar-exp6 \
	exp007-model coco-bin-exp7 xroar-test-exp7 xroar-exp7 \
	exp007-sweep exp007-epoch-sweep exp008-sweep exp008-capture \
	exp008-replay music-tune music-cycles music-bin music-test \
	xroar-music music-dsk exp010-corpus exp010-dance exp010-model \
	exp010-core exp010-test exp010-demo exp010-demo-test \
	xroar-melody xroar-melody-6309 melody-dsk block9-6309 exp010-compile-test exp010-xroar-test exp011-sweep exp011-replicate exp011-model \
	attention-bin attention-test attention-ui-test xroar-test-attention \
	xroar-attention exp012-corpus exp012-vocabulary exp012-tokenizations \
	exp012-titles exp012-model titles-bin titles-test xroar-titles \
	exp013-sweep exp013-play exp013-record rpsls-bin rpsls-test xroar-rpsls \
	present stage xroar-test-music block1 block2 block3 block4 block5 block6 block7 block8 \
	block9 block10 sdcard sdcard-install tools deck-figures

PRESENTER := $(UV) run python tools/present_experiment.py
6809_COMMON_SOURCES := \
	src/6809/model_core.asm \
	src/6809/model_storage.asm \
	src/6809/training.asm \
	src/6809/inference.asm \
	src/6809/screen.asm
6809_EXP004_SOURCES := \
	src/6809/experiments/experiment_004.asm \
	src/6809/experiments/sample_gallery.asm
6809_EXP005_SOURCES := \
	src/6809/experiments/experiment_005.asm \
	src/6809/experiments/prompt_workbench.asm

present:
	@$(PRESENTER) $(if $(EXP),run $(EXP),list)

# Pre-flight for the talk: launch the five parkable XRoar instances in the
# background, one per demo block. EXP-004 is deliberately absent - it starts
# training the moment it loads, so block 3 launches it live with
# `make present EXP=4`. Arrange the four windows in block order once they
# are up; XRoar windows are otherwise indistinguishable.
STAGE_BINARIES := build/coco-llm-exp5.bin \
	build/coco-titles.bin build/coco-rpsls.bin build/coco-melody-demo.bin

stage: $(STAGE_BINARIES) build/coco-llm-exp7.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@for binary in $(STAGE_BINARIES); do \
		nohup $(XROAR) -machine cocous -ram 32 \
			-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
			-ratelimit -run $$binary >/dev/null 2>&1 & \
	done
	@nohup $(XROAR) -machine cocous -ram 64 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm-exp7.bin >/dev/null 2>&1 &
	@echo "Parked: EXP-005 (block 4), EXP-007 (block 5)," \
		"EXP-012 (block 6), EXP-013 (block 8), EXP-010 (block 9)."
	@echo "The windows detach from this terminal; quit them from XRoar itself."
	@echo "Block 3 launches live: make block3"

# One command per runsheet block, so the stage thinks in blocks rather than
# experiment numbers. Blocks 4, 5, 6, 8 and 9 are normally parked in advance by
# `make stage`; their targets are the rehearsal path and the relaunch for a
# dead window. Block 3 is the one launched live during the talk.
# The deck opens first, then the emulator launches: the most recent launch
# takes focus, so XRoar fronts the training screen with the deck ready
# underneath for the switch to block 2's slides.
block1: build/coco-llm.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@open presentation/deck/index.html
	@echo "BLOCK 1 - WATCH IT WORK - deck opened, launching EXP-004 in"
	@echo "front of the room. It starts training from random weights the"
	@echo "moment it loads; block 2's slides explain it while it runs."
	@echo "Call the shot out loud, then press S on the deck for notes."
	@nohup $(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

block2:
	@echo "BLOCK 2 - HOW IT WORKS - eight figures. EXP-004 is training in"
	@echo "the window block 1 opened; it parks at PRESS ANY KEY."

block3: build/coco-llm.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@echo "BLOCK 3 - A LITTLE 6809 ASSEMBLY - normally a window switch:"
	@echo "EXP-004 has been training since block 1. This launches a"
	@echo "FRESH run (launch = reset) - the recovery if that window died."
	@nohup $(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

block4: build/coco-llm-exp5.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@echo "BLOCK 4 - THE PROMPT - EXP-005 trains itself, parks at"
	@echo "PRESS ANY KEY. Up/Down chooses a prompt, Enter generates."
	@nohup $(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm-exp5.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

block5: build/coco-llm-exp7.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@echo "BLOCK 5 - THE SIZE - EXP-007 parks at the completion editor."
	@echo "Right Arrow predicts and accepts, Up/Down choose, Clear resets."
	@nohup $(XROAR) -machine cocous -ram 64 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm-exp7.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

block6: build/coco-titles.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@echo "BLOCK 6 - NEVER EXISTED - EXP-012 parks showing titles."
	@echo "Any key deals sixteen fresh ones."
	@nohup $(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-titles.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

block7:
	@echo "BLOCK 7 - THE UPBRINGING - slides only, the five bias bars."

block8: build/coco-rpsls.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@echo "BLOCK 8 - YOU PLAY IT - EXP-013 parks at the RPSLS keys."
	@echo "1-5 throw, R forgets everything. Press R before the talk."
	@nohup $(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-rpsls.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

block9: build/coco-melody-demo.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@echo "BLOCK 9 - A TOKEN IS A NOTE - EXP-010 parks at YOU SEED -"
	@echo "MODEL CONTINUES. 1-7 enter notes, - holds, . rests, 0 erases,"
	@echo "Enter composes, then performs. Let a phrase play before talking."
	@nohup $(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-melody-demo.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

block10:
	@echo "BLOCK 10 - WRAP UP - slides only: the recap, the coordinates, then the table."

# Everything the hardware loads, staged for an SD card: one disk image per
# purpose plus the same files loose, and a manifest derived from the
# binaries. tools/make_sdcard.py owns the list. DEST is the mounted card.
SDCARD_BINARIES := build/coco-llm.bin build/coco-llm-exp5.bin \
	build/coco-llm-exp6.bin build/coco-llm-exp7.bin \
	build/coco-titles.bin build/coco-rpsls.bin \
	build/coco-melody-demo.bin build/coco-melody-demo-6309.bin \
	build/coco-music.bin build/coco-attention.bin \
	build/bench6309/BENCH309.DSK build/exp015/MUSIC015.DSK \
	build/exp017/WAVE017.DSK build/exp018/STEADY18.DSK

sdcard: $(SDCARD_BINARIES) tools/make_sdcard.py tools/make_rsdos_dsk.py
	$(UV) run python tools/make_sdcard.py

DEST ?= /Volumes/COCO
sdcard-install: $(SDCARD_BINARIES) tools/make_sdcard.py tools/make_rsdos_dsk.py
	$(UV) run python tools/make_sdcard.py --install $(DEST)

exp006-model:
	$(UV) run python tools/export_exp_006.py

exp007-sweep:
	$(UV) run python tools/run_exp_007.py --punctuation \
		--training experiments/data/EXP-007-sentence-training.txt \
		--holdout experiments/data/EXP-007-sentence-holdout.txt \
		--contexts 5

exp007-epoch-sweep:
	$(UV) run python tools/run_exp_007_epoch_sweep.py

exp007-model:
	$(UV) run python tools/export_exp_007.py

exp008-sweep:
	$(UV) run python tools/run_exp_008.py

exp008-capture:
ifndef LABEL
	$(error set LABEL, for example: make exp008-capture LABEL=stacey-01)
endif
	$(UV) run python tools/capture_exp_008.py --label $(LABEL)

exp008-replay:
	$(UV) run python tools/replay_exp_008.py

exp011-sweep:
	$(UV) run python tools/run_exp_011.py --sweep

exp011-replicate:
	$(UV) run python tools/run_exp_011.py --training-seed 1111 \
		--test-seed 1112 --seed 6814 --sweep-seed-start 6814 --sweep

exp011-model:
	$(UV) run python tools/export_exp_011.py

attention-bin: build/coco-attention.bin

attention-test: build/attention-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

attention-ui-test: build/attention-ui-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

xroar-test-attention: build/coco-attention.bin build/coco-attention.sym \
		build/roms/.coco1-roms
	$(UV) run python tools/test_xroar.py \
		--xroar $(XROAR) --binary build/coco-attention.bin \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--symbols build/coco-attention.sym \
		--trap-symbol attention_ui_wait

xroar-attention: build/coco-attention.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-attention.bin

MUSIC_RATE ?= 5679
# Toolshed's decb is the reference DECB disk tool; override if it moves.
DECB ?= $(HOME)/OneDrive/CoCo/dev/toolshed/build/unix/decb/decb

# PLAYER=wave enumerates EXP-017's wavetable loop instead of EXP-009's.
PLAYER ?= square
music-cycles:
	$(UV) run python tools/music_cycle_budget.py --player $(PLAYER)

build/exp009/tune_data.inc: tools/export_tune.py src/reference/coco_synth.py
	$(UV) run python tools/export_tune.py --sample-rate $(MUSIC_RATE)

music-tune: build/exp009/tune_data.inc
	$(UV) run python tools/render_tune.py --sample-rate $(MUSIC_RATE)

build/coco-music.bin: src/6809/coco_music.asm src/6809/music_player.asm \
		build/exp009/tune_data.inc
	$(LWASM) --6809 --format=decb --symbol-dump=build/coco-music.sym \
		--output=$@ $<

music-bin: build/coco-music.bin

build/coco-music.dsk: build/coco-music.bin
	@test -x "$(DECB)" || \
		(echo "Build toolshed's decb first, or set DECB=" && exit 1)
	rm -f $@
	$(DECB) dskini $@
	$(DECB) copy -2 -b $< $@,MUSIC.BIN
	$(DECB) dir $@

music-dsk: build/coco-music.dsk

# ---- EXP-015, the faster-clock listening test ----------------------------
# The EXP-009 player three ways on the CoCo 3: as built for the CoCo 1, at
# the CoCo 3's fast clock, and in 6309 native mode at the fast clock. The
# sample loop is untouched. Each build gets an increment table for the rate
# its cycle count implies, so all three should play at one pitch; if one
# does not, its rate is wrong and that is the finding.
#
# MUSIC_RATE doubles exactly at the fast clock: same instructions, same
# cycles, twice the clock. The 6309 rate is `make music-cycles-6309`, a
# data-sheet prediction that the pitch comparison on the hardware tests.
MUSIC_RATE_FAST ?= 11358
MUSIC_RATE_6309 ?= 14405
COCO3_ROM_ARCHIVE ?= $(HOME)/OneDrive/CoCo/MAME/roms/coco3.zip
COCO3_ROM := build/roms/coco3.rom

music-cycles-6309:
	$(UV) run python tools/music_cycle_budget.py --cpu 6309 --player $(PLAYER)

build/exp015/tune_data_fast.inc: tools/export_tune.py src/reference/coco_synth.py
	$(UV) run python tools/export_tune.py --sample-rate $(MUSIC_RATE_FAST) \
		--output $@

build/exp015/tune_data_6309.inc: tools/export_tune.py src/reference/coco_synth.py
	$(UV) run python tools/export_tune.py --sample-rate $(MUSIC_RATE_6309) \
		--wide-ticks --output $@

build/exp015/music-fast.bin: src/6809/coco_music_fast.asm \
		src/6809/music_player.asm build/exp015/tune_data_fast.inc
	$(LWASM) --6809 --format=decb --symbol-dump=build/exp015/music-fast.sym \
		--output=$@ $<

build/exp015/music-6309.bin: src/6309/coco_music_native.asm \
		src/6809/music_player.asm build/exp015/tune_data_6309.inc
	$(LWASM) --6309 --format=decb --symbol-dump=build/exp015/music-6309.sym \
		--output=$@ $<

# The three files under the names the session sheet uses, loose and on a
# disk image, the way EXP-014's benchmark travelled to the machine.
build/exp015/MUSIC015.DSK: build/coco-music.bin build/exp015/music-fast.bin \
		build/exp015/music-6309.bin tools/make_rsdos_dsk.py
	cp build/coco-music.bin build/exp015/MUSIC09.BIN
	cp build/exp015/music-fast.bin build/exp015/MUSIC2X.BIN
	cp build/exp015/music-6309.bin build/exp015/MUSIC39.BIN
	$(UV) run python tools/make_rsdos_dsk.py --output $@ \
		--file MUSIC09.BIN=build/exp015/MUSIC09.BIN \
		--file MUSIC2X.BIN=build/exp015/MUSIC2X.BIN \
		--file MUSIC39.BIN=build/exp015/MUSIC39.BIN

exp015-bin: build/exp015/MUSIC015.DSK

# The reference rendered at each build's rate: what the machine should
# sound like, to hear on the Mac before carrying the card over.
exp015-wav:
	$(UV) run python tools/render_tune.py --sample-rate $(MUSIC_RATE) \
		--output build/exp015/music-$(MUSIC_RATE).wav
	$(UV) run python tools/render_tune.py --sample-rate $(MUSIC_RATE_FAST) \
		--output build/exp015/music-$(MUSIC_RATE_FAST).wav
	$(UV) run python tools/render_tune.py --sample-rate $(MUSIC_RATE_6309) \
		--output build/exp015/music-$(MUSIC_RATE_6309).wav

build/roms/.coco3-rom: $(COCO3_ROM_ARCHIVE)
	mkdir -p build/roms
	unzip -jo $(COCO3_ROM_ARCHIVE) coco3.rom -d build/roms
	touch $@

$(COCO3_ROM_ARCHIVE):
	@echo "CoCo 3 ROM archive not found: $@"
	@echo "The CoCo 3 targets need Super Extended Color BASIC (coco3.rom), which is"
	@echo "copyrighted and not shipped here. Put your own MAME-style coco3.zip"
	@echo "somewhere and run:"
	@echo "    make $(MAKECMDGOALS) COCO3_ROM_ARCHIVE=/path/to/coco3.zip"
	@echo "See README.md, \"ROM images\"."
	@exit 1

# Each build runs to the end of its tune under XRoar's CoCo 3, trapping at
# audio_disable. That proves the tick machinery works at the new rates; it
# says nothing about pitch, which only the hardware can, and XRoar calls its
# own 6309 emulation unverified.
exp015-test: build/exp015/music-fast.bin build/exp015/music-6309.bin \
		build/roms/.coco3-rom
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--machine coco3 --coco3-rom $(COCO3_ROM) \
		--binary build/exp015/music-fast.bin \
		--symbols build/exp015/music-fast.sym --trap-symbol audio_disable \
		--ram-init set
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--machine coco3h --coco3-rom $(COCO3_ROM) \
		--binary build/exp015/music-6309.bin \
		--symbols build/exp015/music-6309.sym --trap-symbol audio_disable \
		--ram-init set

xroar-exp015-fast: build/exp015/music-fast.bin build/roms/.coco3-rom
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine coco3 -extbas $(COCO3_ROM) -ratelimit -run $<

xroar-exp015-6309: build/exp015/music-6309.bin build/roms/.coco3-rom
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine coco3h -extbas $(COCO3_ROM) -ratelimit -run $<

exp015: exp015-bin exp015-wav exp015-test

.PHONY: music-cycles-6309 exp015-bin exp015-wav exp015-test exp015 \
	xroar-exp015-fast xroar-exp015-6309

# ---- EXP-017, the wavetable voices ---------------------------------------
# EXP-009's player with each tone voice's masked bit replaced by a table
# lookup: a triangle or a sine instead of a square, at the same cost per
# sample. Rates are pinned from `make music-cycles PLAYER=wave` and its
# 6309 twin; the 6309 rate is the same prediction EXP-015 is testing.
#
# Each build assembles in its own directory holding the two generated
# includes it needs, tune_data.inc for its rate and wavetable.inc for its
# shape, found through -I. One wrapper per processor and clock serves
# every shape.
EXP017 := build/exp017
WAVE_RATE ?= 5789
WAVE_RATE_FAST ?= 11578
WAVE_RATE_6309 ?= 14402

$(EXP017)/table-%.inc: tools/export_wavetable.py src/reference/wave_synth.py
	$(UV) run python tools/export_wavetable.py --shape $* --output $@

$(EXP017)/tune-$(WAVE_RATE).inc: tools/export_tune.py src/reference/coco_synth.py
	$(UV) run python tools/export_tune.py --sample-rate $(WAVE_RATE) --output $@

$(EXP017)/tune-$(WAVE_RATE_FAST).inc: tools/export_tune.py src/reference/coco_synth.py
	$(UV) run python tools/export_tune.py --sample-rate $(WAVE_RATE_FAST) \
		--output $@

$(EXP017)/tune-$(WAVE_RATE_6309).inc: tools/export_tune.py src/reference/coco_synth.py
	$(UV) run python tools/export_tune.py --sample-rate $(WAVE_RATE_6309) \
		--wide-ticks --output $@

# $(1) build name, $(2) wrapper, $(3) processor, $(4) shape, $(5) rate
define wave_build
$(EXP017)/$(1)/wave.bin: $(2) src/6809/wave_player.asm \
		$(EXP017)/table-$(4).inc $(EXP017)/tune-$(5).inc
	mkdir -p $(EXP017)/$(1)
	cp $(EXP017)/table-$(4).inc $(EXP017)/$(1)/wavetable.inc
	cp $(EXP017)/tune-$(5).inc $(EXP017)/$(1)/tune_data.inc
	$(LWASM) --$(3) -I $(EXP017)/$(1) --format=decb \
		--symbol-dump=$(EXP017)/$(1)/wave.sym --output=$$@ $(2)
endef

$(eval $(call wave_build,wave09,src/6809/coco_wave.asm,6809,triangle,$(WAVE_RATE)))
$(eval $(call wave_build,square09,src/6809/coco_wave.asm,6809,square,$(WAVE_RATE)))
$(eval $(call wave_build,wave2x,src/6809/coco_wave_fast.asm,6809,triangle,$(WAVE_RATE_FAST)))
$(eval $(call wave_build,wave39,src/6309/coco_wave_native.asm,6309,triangle,$(WAVE_RATE_6309)))
$(eval $(call wave_build,sine39,src/6309/coco_wave_native.asm,6309,sine,$(WAVE_RATE_6309)))

WAVE_BINS := $(EXP017)/wave09/wave.bin $(EXP017)/wave2x/wave.bin \
	$(EXP017)/wave39/wave.bin $(EXP017)/sine39/wave.bin

$(EXP017)/WAVE017.DSK: $(WAVE_BINS) tools/make_rsdos_dsk.py
	cp $(EXP017)/wave09/wave.bin $(EXP017)/WAVE09.BIN
	cp $(EXP017)/wave2x/wave.bin $(EXP017)/WAVE2X.BIN
	cp $(EXP017)/wave39/wave.bin $(EXP017)/WAVE39.BIN
	cp $(EXP017)/sine39/wave.bin $(EXP017)/SINE39.BIN
	$(UV) run python tools/make_rsdos_dsk.py --output $@ \
		--file WAVE09.BIN=$(EXP017)/WAVE09.BIN \
		--file WAVE2X.BIN=$(EXP017)/WAVE2X.BIN \
		--file WAVE39.BIN=$(EXP017)/WAVE39.BIN \
		--file SINE39.BIN=$(EXP017)/SINE39.BIN

exp017-bin: $(EXP017)/WAVE017.DSK

# Loop-level parity in the direct simulator, for the triangle build and for
# a square-table build that must reproduce EXP-009's masked bit exactly.
$(EXP017)/wave-parity-test.asm: $(EXP017)/wave09/wave.bin tools/make_wave_parity_test.py
	$(UV) run python tools/make_wave_parity_test.py --shape triangle \
		--binary $(EXP017)/wave09/wave.bin --symbols $(EXP017)/wave09/wave.sym \
		--output $@

$(EXP017)/square-parity-test.asm: $(EXP017)/square09/wave.bin tools/make_wave_parity_test.py
	$(UV) run python tools/make_wave_parity_test.py --shape square \
		--binary $(EXP017)/square09/wave.bin --symbols $(EXP017)/square09/wave.sym \
		--output $@

wave-test: $(EXP017)/wave-parity-test.asm $(EXP017)/square-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $(EXP017)/wave-parity-test.asm
	$(SIM6809) --ram-top 65535 --run $(EXP017)/square-parity-test.asm

# The reference at each build's rate and shape, to hear on the Mac.
exp017-wav:
	$(UV) run python tools/render_wave_tune.py --shape triangle \
		--sample-rate $(WAVE_RATE) --output $(EXP017)/wave-triangle-$(WAVE_RATE).wav
	$(UV) run python tools/render_wave_tune.py --shape triangle \
		--sample-rate $(WAVE_RATE_6309) --output $(EXP017)/wave-triangle-$(WAVE_RATE_6309).wav
	$(UV) run python tools/render_wave_tune.py --shape sine \
		--sample-rate $(WAVE_RATE_6309) --output $(EXP017)/wave-sine-$(WAVE_RATE_6309).wav
	$(UV) run python tools/render_wave_tune.py --shape square \
		--sample-rate $(WAVE_RATE_6309) --output $(EXP017)/wave-square-$(WAVE_RATE_6309).wav

# Every build to the end of its tune under XRoar.
exp017-test: $(WAVE_BINS) build/roms/.coco1-roms build/roms/.coco3-rom
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--basic-rom $(COCO_BASIC_ROM) --extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--binary $(EXP017)/wave09/wave.bin --symbols $(EXP017)/wave09/wave.sym \
		--trap-symbol audio_disable --ram-init set
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--machine coco3 --coco3-rom $(COCO3_ROM) \
		--binary $(EXP017)/wave2x/wave.bin --symbols $(EXP017)/wave2x/wave.sym \
		--trap-symbol audio_disable --ram-init set
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--machine coco3h --coco3-rom $(COCO3_ROM) \
		--binary $(EXP017)/wave39/wave.bin --symbols $(EXP017)/wave39/wave.sym \
		--trap-symbol audio_disable --ram-init set
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--machine coco3h --coco3-rom $(COCO3_ROM) \
		--binary $(EXP017)/sine39/wave.bin --symbols $(EXP017)/sine39/wave.sym \
		--trap-symbol audio_disable --ram-init set

xroar-wave09: $(EXP017)/wave09/wave.bin build/roms/.coco1-roms
	$(XROAR) -machine cocous -ram 32 -bas $(COCO_BASIC_ROM) \
		-extbas $(COCO_EXTBASIC_ROM) -ratelimit -run $<

xroar-wave2x: $(EXP017)/wave2x/wave.bin build/roms/.coco3-rom
	$(XROAR) -machine coco3 -extbas $(COCO3_ROM) -ratelimit -run $<

xroar-wave39: $(EXP017)/wave39/wave.bin build/roms/.coco3-rom
	$(XROAR) -machine coco3h -extbas $(COCO3_ROM) -ratelimit -run $<

xroar-sine39: $(EXP017)/sine39/wave.bin build/roms/.coco3-rom
	$(XROAR) -machine coco3h -extbas $(COCO3_ROM) -ratelimit -run $<

exp017: exp017-bin wave-test exp017-wav exp017-test

.PHONY: exp017-bin wave-test exp017-wav exp017-test exp017 \
	xroar-wave09 xroar-wave2x xroar-wave39 xroar-sine39

# ---- EXP-018, the steady sample clock ------------------------------------
# EXP-009's loop with its row and tick work compiled away into an event
# stream, applied one byte per sample through a path padded to cost what
# the idle path costs. Every sample costs the same, so the rate is the
# loop's exact cycle count with nothing amortised: `make music-cycles
# PLAYER=steady` and its 6309 twin, pinned here.
EXP018 := build/exp018
STEADY_RATE ?= 4566
STEADY_RATE_6309 ?= 11188

$(EXP018)/events-%.inc: tools/export_events.py src/reference/steady_synth.py \
		src/reference/coco_synth.py
	$(UV) run python tools/export_events.py --sample-rate $* --output $@

# $(1) build name, $(2) wrapper, $(3) processor, $(4) rate
define steady_build
$(EXP018)/$(1)/steady.bin: $(2) src/6809/steady_player.asm $(EXP018)/events-$(4).inc
	mkdir -p $(EXP018)/$(1)
	cp $(EXP018)/events-$(4).inc $(EXP018)/$(1)/tune_events.inc
	$(LWASM) --$(3) -I $(EXP018)/$(1) --format=decb \
		--symbol-dump=$(EXP018)/$(1)/steady.sym --output=$$@ $(2)
endef

$(eval $(call steady_build,steady09,src/6809/coco_steady.asm,6809,$(STEADY_RATE)))
$(eval $(call steady_build,steady39,src/6309/coco_steady_native.asm,6309,$(STEADY_RATE_6309)))

$(EXP018)/STEADY18.DSK: $(EXP018)/steady09/steady.bin $(EXP018)/steady39/steady.bin \
		tools/make_rsdos_dsk.py
	cp $(EXP018)/steady09/steady.bin $(EXP018)/STEADY09.BIN
	cp $(EXP018)/steady39/steady.bin $(EXP018)/STEADY39.BIN
	$(UV) run python tools/make_rsdos_dsk.py --output $@ \
		--file STEADY09.BIN=$(EXP018)/STEADY09.BIN \
		--file STEADY39.BIN=$(EXP018)/STEADY39.BIN

exp018-bin: $(EXP018)/STEADY18.DSK

$(EXP018)/steady-parity-test.asm: $(EXP018)/steady09/steady.bin \
		tools/make_steady_parity_test.py
	$(UV) run python tools/make_steady_parity_test.py \
		--binary $(EXP018)/steady09/steady.bin \
		--symbols $(EXP018)/steady09/steady.sym --output $@

steady-test: $(EXP018)/steady-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

exp018-wav:
	$(UV) run python tools/render_steady_tune.py --sample-rate $(STEADY_RATE) \
		--output $(EXP018)/steady-$(STEADY_RATE).wav
	$(UV) run python tools/render_steady_tune.py --sample-rate $(STEADY_RATE_6309) \
		--output $(EXP018)/steady-$(STEADY_RATE_6309).wav

exp018-test: $(EXP018)/steady09/steady.bin $(EXP018)/steady39/steady.bin \
		build/roms/.coco1-roms build/roms/.coco3-rom
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--basic-rom $(COCO_BASIC_ROM) --extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--binary $(EXP018)/steady09/steady.bin \
		--symbols $(EXP018)/steady09/steady.sym \
		--trap-symbol audio_disable --ram-init set
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--machine coco3h --coco3-rom $(COCO3_ROM) \
		--binary $(EXP018)/steady39/steady.bin \
		--symbols $(EXP018)/steady39/steady.sym \
		--trap-symbol audio_disable --ram-init set

xroar-steady09: $(EXP018)/steady09/steady.bin build/roms/.coco1-roms
	$(XROAR) -machine cocous -ram 32 -bas $(COCO_BASIC_ROM) \
		-extbas $(COCO_EXTBASIC_ROM) -ratelimit -run $<

xroar-steady39: $(EXP018)/steady39/steady.bin build/roms/.coco3-rom
	$(XROAR) -machine coco3h -extbas $(COCO3_ROM) -ratelimit -run $<

exp018: exp018-bin steady-test exp018-wav exp018-test

.PHONY: exp018-bin steady-test exp018-wav exp018-test exp018 \
	xroar-steady09 xroar-steady39

exp010-corpus:
	$(UV) run python tools/extract_chorales.py

exp010-dance:
	$(UV) run python tools/extract_dance.py

exp012-corpus:
	$(UV) run python tools/extract_tos_titles.py

exp012-vocabulary:
	$(UV) run python tools/measure_tos_vocabulary.py

exp012-tokenizations:
	$(UV) run python tools/measure_tos_tokenizations.py

exp012-titles:
	$(UV) run python tools/run_exp_012.py

build/coco-rpsls.bin: src/6809/coco_rpsls.asm src/6809/rpsls_game.asm
	$(LWASM) --6809 -I src/6809 --format=decb \
		--symbol-dump=build/coco-rpsls.sym --output=$@ $<

rpsls-bin: build/coco-rpsls.bin

build/rpsls-agent.asm: src/6809/coco_rpsls.asm src/6809/rpsls_game.asm \
		src/6809/text_screen.asm
	printf 'DIRECT_TEST equ 1\n' > $@
	cat $< >> $@

build/rpsls-agent.bin: build/rpsls-agent.asm
	$(LWASM) --6809 -I src/6809 --format=decb \
		--symbol-dump=build/rpsls-agent.sym --output=$@ $<

build/rpsls-agent-test.asm: build/rpsls-agent.bin \
		tools/make_rpsls_agent_test.py src/reference/rpsls.py
	$(UV) run python tools/make_rpsls_agent_test.py --output $@

build/rpsls-fresh-test.asm: build/coco-rpsls.bin \
		tools/make_rpsls_parity_test.py src/reference/rpsls_screen.py
	$(UV) run python tools/make_rpsls_parity_test.py --case fresh --output $@

build/rpsls-parity-test.asm: build/coco-rpsls.bin \
		tools/make_rpsls_parity_test.py src/reference/rpsls_screen.py
	$(UV) run python tools/make_rpsls_parity_test.py --case played --output $@

build/rpsls-wrap-test.asm: build/coco-rpsls.bin \
		tools/make_rpsls_parity_test.py src/reference/rpsls_screen.py
	$(UV) run python tools/make_rpsls_parity_test.py --case wrapped --output $@

rpsls-test: build/rpsls-fresh-test.asm build/rpsls-parity-test.asm \
		build/rpsls-wrap-test.asm build/rpsls-agent-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run build/rpsls-fresh-test.asm
	$(SIM6809) --ram-top 65535 --run build/rpsls-parity-test.asm
	$(SIM6809) --ram-top 65535 --run build/rpsls-wrap-test.asm
	$(SIM6809) --ram-top 65535 --run build/rpsls-agent-test.asm

xroar-rpsls: build/coco-rpsls.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-rpsls.bin

exp013-sweep:
	$(UV) run python tools/run_exp_013.py

exp013-record: build/coco-rpsls.bin build/roms/.coco1-roms
ifndef LABEL
	$(error set LABEL, for example: make exp013-record LABEL=stacey-coco-01)
endif
	$(UV) run python tools/capture_rpsls_coco.py --label $(LABEL) \
		--xroar $(XROAR)

exp013-play:
ifndef LABEL
	$(error set LABEL, for example: make exp013-play LABEL=stacey-01)
endif
	$(UV) run python tools/capture_exp_013.py --label $(LABEL) $(ARGS)

build/exp012/title_model.inc: tools/export_exp_012.py tools/run_exp_012.py \
		src/reference/title_generator.py \
		experiments/data/EXP-012-tos-titles.txt \
		experiments/data/EXP-012-tos-lexicon.txt
	$(UV) run python tools/export_exp_012.py

exp012-model: build/exp012/title_model.inc

build/coco-titles.bin: src/6809/coco_titles.asm src/6809/title_generator.asm \
		src/6809/model_forward.asm src/6809/model_storage.asm \
		build/exp012/title_model.inc
	$(LWASM) --6809 --format=decb --symbol-dump=build/coco-titles.sym \
		--output=$@ $<

titles-bin: build/coco-titles.bin

build/titles-parity-test.asm: build/coco-titles.bin \
		tools/make_titles_parity_test.py
	$(UV) run python tools/make_titles_parity_test.py --output $@

titles-test: build/titles-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

xroar-titles: build/coco-titles.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-titles.bin

build/exp010/melody_model.inc: tools/export_melody_model.py \
		src/reference/melody_fixed.py src/reference/melody_lm.py \
		experiments/data/EXP-010-dance.jsonl
	$(UV) run python tools/export_melody_model.py

exp010-model: build/exp010/melody_model.inc

build/melody-core.bin: src/6809/coco_melody.asm \
		src/6809/melody_inference.asm build/exp010/melody_model.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/melody-core.sym \
		--output=$@ $<

exp010-core: build/melody-core.bin

build/melody-parity-test.asm: build/melody-core.bin \
		tools/make_melody_parity_test.py src/reference/melody_fixed.py
	$(UV) run python tools/make_melody_parity_test.py --output $@

exp010-test: build/melody-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

# The demo's performer is EXP-018's steady clock, so the frame's increments
# are built for that player's rate: STEADY_RATE for the CoCo 1 build and
# STEADY_RATE_6309 for the stage build on the CoCo 3.
build/exp010/tune_frame.inc: tools/export_tune.py Makefile
	$(UV) run python tools/export_tune.py --sample-rate $(STEADY_RATE) \
		--ram-rows 128 --output $@

build/exp010/tune_frame_6309.inc: tools/export_tune.py Makefile
	$(UV) run python tools/export_tune.py --sample-rate $(STEADY_RATE_6309) \
		--ram-rows 128 --output $@

MELODY_DEMO_SOURCES := src/6809/melody_demo.asm src/6809/melody_ui.asm \
	src/6809/melody_inference.asm src/6809/steady_player.asm \
	src/6809/steady_compile.asm build/exp010/melody_model.inc

build/coco-melody-demo.bin: src/6809/coco_melody_demo.asm \
		$(MELODY_DEMO_SOURCES) build/exp010/tune_frame.inc
	$(LWASM) --6809 --format=decb \
		--symbol-dump=build/coco-melody-demo.sym --output=$@ $<

# The same demo entered at demo_run: composes from the built-in figure and
# plays with no keyboard, so the emulator can run it to the end.
build/coco-melody-run.bin: src/6809/coco_melody_demo.asm \
		$(MELODY_DEMO_SOURCES) build/exp010/tune_frame.inc
	$(LWASM) --6809 --format=decb --define=ENTRY_RUN=1 \
		--symbol-dump=build/coco-melody-run.sym --output=$@ $<

build/coco-melody-demo-6309.bin: src/6309/coco_melody_demo_native.asm \
		$(MELODY_DEMO_SOURCES) build/exp010/tune_frame_6309.inc
	$(LWASM) --6309 --format=decb \
		--symbol-dump=build/coco-melody-demo-6309.sym --output=$@ $<

build/coco-melody-run-6309.bin: src/6309/coco_melody_demo_native.asm \
		$(MELODY_DEMO_SOURCES) build/exp010/tune_frame_6309.inc
	$(LWASM) --6309 --format=decb --define=ENTRY_RUN=1 \
		--symbol-dump=build/coco-melody-run-6309.sym --output=$@ $<

exp010-demo: build/coco-melody-demo.bin build/coco-melody-run.bin \
	build/coco-melody-demo-6309.bin build/coco-melody-run-6309.bin

# The CoCo's compiler against the reference's, on the same 128 rows.
build/compile-parity-test.asm: build/coco-melody-demo.bin \
		tools/make_compile_parity_test.py src/reference/steady_synth.py
	$(UV) run python tools/make_compile_parity_test.py \
		--binary build/coco-melody-demo.bin --symbols build/coco-melody-demo.sym \
		--sample-rate $(STEADY_RATE) --output $@

exp010-compile-test: build/compile-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

# Compose, compile and play to the end under XRoar, both machines.
exp010-xroar-test: build/coco-melody-run.bin build/coco-melody-run-6309.bin \
		build/roms/.coco1-roms build/roms/.coco3-rom
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--basic-rom $(COCO_BASIC_ROM) --extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--binary build/coco-melody-run.bin --symbols build/coco-melody-run.sym \
		--trap-symbol audio_disable --ram-init set --timeout 300
	$(UV) run python tools/test_xroar.py --xroar $(XROAR) \
		--machine coco3h --coco3-rom $(COCO3_ROM) \
		--binary build/coco-melody-run-6309.bin \
		--symbols build/coco-melody-run-6309.sym \
		--trap-symbol audio_disable --ram-init set --timeout 300

# The demo under the names the SDC uses, and on a disk image.
build/exp010/MELODY10.DSK: build/coco-melody-demo.bin build/coco-melody-demo-6309.bin \
		tools/make_rsdos_dsk.py
	cp build/coco-melody-demo.bin build/exp010/MELODY09.BIN
	cp build/coco-melody-demo-6309.bin build/exp010/MELODY39.BIN
	$(UV) run python tools/make_rsdos_dsk.py --output $@ \
		--file MELODY09.BIN=build/exp010/MELODY09.BIN \
		--file MELODY39.BIN=build/exp010/MELODY39.BIN

melody-dsk: build/exp010/MELODY10.DSK

# Block 9 on a CoCo 3 with a 6309: the performer in native mode at the
# fast clock, 11,188 Hz with a steady clock. The stage option.
block9-6309: build/coco-melody-demo-6309.bin build/roms/.coco3-rom
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	@echo "BLOCK 9 - A TOKEN IS A NOTE - EXP-010 on a 6309 CoCo 3: say so."
	@echo "Same keys as block9; Enter composes, then performs at 11,188 Hz."
	@nohup $(XROAR) -machine coco3h -extbas $(COCO3_ROM) \
		-ratelimit -run build/coco-melody-demo-6309.bin >/dev/null 2>&1 &
	@echo "Detached. Quit it from XRoar; nothing here can kill it."

xroar-melody-6309: build/coco-melody-demo-6309.bin build/roms/.coco3-rom
	$(XROAR) -machine coco3h -extbas $(COCO3_ROM) -ratelimit -run $<

build/demo-parity-test.asm: build/coco-melody-demo.bin \
		tools/make_demo_parity_test.py
	$(UV) run python tools/make_demo_parity_test.py --output $@

exp010-demo-test: build/demo-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

xroar-melody: build/coco-melody-demo.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-melody-demo.bin

build/music-parity-test.asm: build/coco-music.bin tools/make_music_parity_test.py
	$(UV) run python tools/make_music_parity_test.py \
		--binary build/coco-music.bin --symbols build/coco-music.sym \
		--output $@

music-test: build/music-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

# The standalone player played to the end of its tune under XRoar's CoCo 1.
# The direct-simulator parity test covers the sample loop only; this is the
# check that rows, ticks and the row hook carry a whole tune, which is what
# was silently broken from 2026-08-02 until EXP-015 tripped over it.
xroar-test-music: build/coco-music.bin build/coco-music.sym build/roms/.coco1-roms
	$(UV) run python tools/test_xroar.py \
		--xroar $(XROAR) --binary build/coco-music.bin \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--symbols build/coco-music.sym --trap-symbol audio_disable \
		--ram-init set

xroar-music: build/coco-music.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-music.bin

test: reference-test asm-test model-test model-test-exp5 model-test-exp6 \
	workbench-test-exp6 model-test-exp7 workbench-test-exp7 \
	attention-test attention-ui-test titles-test rpsls-test

# The direct-page safety test assembles the melody demo, whose generated
# includes must exist first.
reference-test: build/exp010/melody_model.inc build/exp010/tune_frame.inc
	$(UV) sync
	$(UV) run ruff format --check src tests tools
	$(UV) run ruff check src tests tools
	$(UV) run pytest

asm-test: build/smul8-test.bin $(SIM6809)
	$(SIM6809) --run src/6809/tests/smul8_test.asm

model-test: build/model-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

model-test-exp5: build/model-exp5-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

model-test-exp6: build/model-exp6-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

model-test-exp7: build/model-exp7-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

workbench-test-exp6: build/workbench-exp6-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

workbench-test-exp7: build/workbench-exp7-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

coco-bin: build/coco-llm.bin

coco-bin-exp5: build/coco-llm-exp5.bin

coco-bin-exp6: build/coco-llm-exp6.bin

coco-bin-exp7: build/coco-llm-exp7.bin

xroar-test: build/coco-llm.bin build/coco-llm.sym build/roms/.coco1-roms
	$(UV) run python tools/test_xroar.py \
		--xroar $(XROAR) --binary build/coco-llm.bin \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--symbols build/coco-llm.sym

xroar-test-exp5: build/coco-llm-exp5.bin build/coco-llm-exp5.sym \
		build/roms/.coco1-roms
	$(UV) run python tools/test_xroar.py \
		--xroar $(XROAR) --binary build/coco-llm-exp5.bin \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--symbols build/coco-llm-exp5.sym \
		--timeout 600

xroar: build/coco-llm.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm.bin

xroar-exp5: build/coco-llm-exp5.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm-exp5.bin

xroar-test-exp6: build/coco-llm-exp6.bin build/coco-llm-exp6.sym \
		build/roms/.coco1-roms
	$(UV) run python tools/test_xroar.py \
		--xroar $(XROAR) --binary build/coco-llm-exp6.bin \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--symbols build/coco-llm-exp6.sym \
		--trap-symbol completion_input_loop

xroar-exp6: build/coco-llm-exp6.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm-exp6.bin

xroar-test-exp7: build/coco-llm-exp7.bin build/coco-llm-exp7.sym \
		build/roms/.coco1-roms
	$(UV) run python tools/test_xroar.py \
		--xroar $(XROAR) --binary build/coco-llm-exp7.bin \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) \
		--symbols build/coco-llm-exp7.sym \
		--trap-symbol completion_key_polled --ram 64

xroar-exp7: build/coco-llm-exp7.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 64 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm-exp7.bin

build/smul8-test.bin: src/6809/tests/smul8_test.asm
	mkdir -p build
	$(LWASM) --6809 --format=raw --output=$@ $<

build/model_data.inc: tools/generate_6809_data.py \
		src/reference/fixed_token_lm.py src/reference/token_lm.py \
		experiments/data/EXP-002-tokenized-computer-names.txt
	$(UV) run python tools/generate_6809_data.py --output $@

build/model_data_exp5.inc: tools/generate_6809_data.py \
		src/reference/fixed_token_lm.py src/reference/token_lm.py \
		experiments/data/EXP-005-marketing-language.txt \
		experiments/data/EXP-005-prompts.txt
	$(UV) run python tools/generate_6809_data.py --output $@ \
		--epochs 80 \
		--corpus experiments/data/EXP-005-marketing-language.txt \
		--prompts experiments/data/EXP-005-prompts.txt

build/model-test.bin: src/6809/tests/model_test.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP004_SOURCES) build/model_data.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/model-test.sym \
		--output=$@ $<

build/model-test-runner.asm: build/model-test.bin \
		tools/make_6809_test_runner.py
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/model-test.bin \
		--symbols build/model-test.sym \
		--output $@

build/model-exp5-test.bin: src/6809/tests/model_exp5_test.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP005_SOURCES) build/model_data_exp5.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/model-exp5-test.sym \
		--output=$@ $<

build/model-exp5-test-runner.asm: build/model-exp5-test.bin \
		tools/make_6809_test_runner.py
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/model-exp5-test.bin \
		--symbols build/model-exp5-test.sym \
		--output $@ --experiment 5

build/model-exp6-test.bin: src/6809/tests/completion_exp6_test.asm \
		src/6809/completion_inference.asm build/exp006/model_data.inc \
		build/exp006/weights.bin
	$(LWASM) --6809 --format=raw --symbol-dump=build/model-exp6-test.sym \
		--output=$@ $<

build/model-exp6-test-runner.asm: build/model-exp6-test.bin \
		tools/make_6809_test_runner.py build/exp006/weights.bin \
		build/exp006/manifest.json build/exp006/test-vectors.json
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/model-exp6-test.bin \
		--symbols build/model-exp6-test.sym \
		--output $@ --experiment 6 \
		--weights build/exp006/weights.bin \
		--manifest build/exp006/manifest.json \
		--test-vectors build/exp006/test-vectors.json

build/model-exp7-test.bin: src/6809/tests/completion_exp7_test.asm \
		src/6809/completion_inference_exp7.asm build/exp007/model_data.inc \
		build/exp007/weights.bin
	$(LWASM) --6809 --format=raw --symbol-dump=build/model-exp7-test.sym \
		--output=$@ $<

build/model-exp7-test-runner.asm: build/model-exp7-test.bin \
		tools/make_6809_test_runner.py build/exp007/weights.bin \
		build/exp007/manifest.json build/exp007/test-vectors.json
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/model-exp7-test.bin \
		--symbols build/model-exp7-test.sym \
		--output $@ --experiment 7 \
		--weights build/exp007/weights.bin \
		--weights-address 0x8000 \
		--manifest build/exp007/manifest.json \
		--test-vectors build/exp007/test-vectors.json

build/workbench-exp6-test.bin: src/6809/tests/completion_ui_exp6_test.asm \
		src/6809/experiments/experiment_006.asm \
		src/6809/completion_inference.asm src/6809/completion_screen.asm \
		src/6809/completion_editor.asm src/6809/completion_policy_exp6.asm \
		build/exp006/model_data.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/workbench-exp6-test.sym \
		--output=$@ $<

build/workbench-exp6-test-runner.asm: build/workbench-exp6-test.bin \
		tools/make_6809_test_runner.py build/exp006/weights.bin \
		build/exp006/manifest.json build/exp006/test-vectors.json
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/workbench-exp6-test.bin \
		--symbols build/workbench-exp6-test.sym \
		--output $@ --experiment 6 \
		--weights build/exp006/weights.bin \
		--manifest build/exp006/manifest.json \
		--test-vectors build/exp006/test-vectors.json

build/workbench-exp7-test.bin: src/6809/tests/completion_ui_exp7_test.asm \
		src/6809/experiments/experiment_007.asm \
		src/6809/completion_inference_exp7.asm \
		src/6809/completion_screen.asm src/6809/completion_editor.asm \
		src/6809/completion_policy_exp7.asm build/exp007/model_data.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/workbench-exp7-test.sym \
		--output=$@ $<

build/workbench-exp7-test-runner.asm: build/workbench-exp7-test.bin \
		tools/make_6809_test_runner.py build/exp007/weights.bin \
		build/exp007/manifest.json build/exp007/test-vectors.json
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/workbench-exp7-test.bin \
		--symbols build/workbench-exp7-test.sym \
		--output $@ --experiment 7 \
		--weights build/exp007/weights.bin \
		--weights-address 0x8000 \
		--manifest build/exp007/manifest.json \
		--test-vectors build/exp007/test-vectors.json

build/exp006/model_data.inc build/exp006/weights.bin \
		build/exp006/manifest.json build/exp006/test-vectors.json \
		build/exp006/model_image.inc: \
		tools/export_exp_006.py src/reference/completion_lm.py \
		experiments/data/EXP-006-completion-training.txt
	$(UV) run python tools/export_exp_006.py

build/exp007/model_data.inc build/exp007/weights.bin \
		build/exp007/weights-packed.bin \
		build/exp007/manifest.json build/exp007/test-vectors.json \
		build/exp007/packed_model.inc: \
		tools/export_exp_007.py src/reference/completion_lm.py \
		experiments/data/EXP-007-sentence-training.txt \
		experiments/data/EXP-007-sentence-holdout.txt
	$(UV) run python tools/export_exp_007.py

build/exp011/attention_data.inc build/exp011/weights.bin \
		build/exp011/manifest.json build/exp011/test-vectors.json: \
		tools/export_exp_011.py src/reference/associative_attention.py
	$(UV) run python tools/export_exp_011.py

build/coco-attention.bin: src/6809/coco_attention.asm \
		src/6809/attention_inference.asm src/6809/attention_ui.asm \
		build/exp011/attention_data.inc
	$(LWASM) --6809 --format=decb --output=$@ $<

build/coco-attention.raw build/coco-attention.sym: src/6809/coco_attention.asm \
		src/6809/attention_inference.asm src/6809/attention_ui.asm \
		build/exp011/attention_data.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/coco-attention.sym \
		--output=build/coco-attention.raw $<

build/attention-parity-test.asm: build/coco-attention.raw \
		build/coco-attention.sym build/exp011/test-vectors.json \
		tools/make_attention_parity_test.py
	$(UV) run python tools/make_attention_parity_test.py --output $@

build/attention-ui-test.asm: build/coco-attention.raw \
		build/coco-attention.sym build/exp011/manifest.json \
		tools/make_attention_ui_test.py
	$(UV) run python tools/make_attention_ui_test.py --output $@

build/coco-llm.bin: src/6809/coco_llm.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP004_SOURCES) build/model_data.inc
	$(LWASM) --6809 --format=decb --output=$@ $<

build/coco-llm.sym: src/6809/coco_llm.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP004_SOURCES) build/model_data.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/coco-llm.sym \
		--output=build/coco-llm.raw $<

build/coco-llm.raw: build/coco-llm.sym
	@test -f $@

build/coco-llm-exp5.bin: src/6809/coco_llm_exp5.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP005_SOURCES) build/model_data_exp5.inc
	$(LWASM) --6809 --format=decb --output=$@ $<

build/coco-llm-exp5.sym: src/6809/coco_llm_exp5.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP005_SOURCES) build/model_data_exp5.inc
	$(LWASM) --6809 --format=raw --symbol-dump=build/coco-llm-exp5.sym \
		--output=build/coco-llm-exp5.raw $<

build/coco-llm-exp6.bin: src/6809/coco_llm_exp6.asm \
		src/6809/experiments/experiment_006.asm \
		src/6809/completion_inference.asm src/6809/completion_screen.asm \
		src/6809/completion_editor.asm src/6809/completion_policy_exp6.asm \
		build/exp006/model_data.inc \
		build/exp006/model_image.inc
	$(LWASM) --6809 --format=decb --output=$@ $<

build/coco-llm-exp6.sym: src/6809/coco_llm_exp6.asm \
		src/6809/experiments/experiment_006.asm \
		src/6809/completion_inference.asm src/6809/completion_screen.asm \
		src/6809/completion_editor.asm src/6809/completion_policy_exp6.asm \
		build/exp006/model_data.inc
	$(LWASM) --6809 --define=DIRECT_TEST=1 --format=raw \
		--symbol-dump=build/coco-llm-exp6.sym \
		--output=build/coco-llm-exp6.raw $<

build/coco-llm-exp7.bin: src/6809/coco_llm_exp7.asm \
		src/6809/experiments/experiment_007.asm \
		src/6809/completion_inference_exp7.asm \
		src/6809/completion_screen.asm src/6809/completion_editor.asm \
		src/6809/completion_policy_exp7.asm build/exp007/model_data.inc \
		build/exp007/packed_model.inc
	$(LWASM) --6809 --format=decb --output=$@ $<

build/coco-llm-exp7.sym: src/6809/coco_llm_exp7.asm \
		src/6809/experiments/experiment_007.asm \
		src/6809/completion_inference_exp7.asm \
		src/6809/completion_screen.asm src/6809/completion_editor.asm \
		src/6809/completion_policy_exp7.asm build/exp007/model_data.inc
	$(LWASM) --6809 --define=DIRECT_TEST=1 --format=raw \
		--symbol-dump=build/coco-llm-exp7.sym \
		--output=build/coco-llm-exp7.raw $<

build/roms/.coco1-roms: $(COCO_ROM_ARCHIVE)
	mkdir -p build/roms
	unzip -jo $(COCO_ROM_ARCHIVE) bas11.rom extbas10.rom -d build/roms
	touch $@

# A missing archive fails here with a message rather than make's bare
# "No rule to make target".
$(COCO_ROM_ARCHIVE):
	@echo "CoCo 1 ROM archive not found: $@"
	@echo "XRoar needs Tandy Color BASIC 1.1 (bas11.rom) and Extended Color BASIC 1.0"
	@echo "(extbas10.rom), which are copyrighted and not shipped here. Put your own"
	@echo "MAME-style cocoe.zip somewhere and run:"
	@echo "    make $(MAKECMDGOALS) COCO_ROM_ARCHIVE=/path/to/cocoe.zip"
	@echo "See README.md, \"ROM images\"."
	@exit 1

# The deck's figures are generated from the exported traces; index.html is
# hand-edited around them. Regenerate after changing a model, a corpus, or
# a figure builder. The splicer refuses to run over an uncommitted deck.
deck-figures:
	$(UV) run python tools/export_deck_traces.py
	$(UV) run python tools/measure_train_vs_infer.py
	$(UV) run python tools/make_deck_figures.py

tools:
	@command -v $(LWASM) >/dev/null || \
		(echo "Install LWTOOLS first: brew install lwtools" && exit 1)
	@command -v cargo >/dev/null || \
		(echo "Install the Rust toolchain first (cargo is needed to build the 6809 simulator): https://rustup.rs" && exit 1)
	cargo install \
		--git https://github.com/gorsat/6809.git \
		--rev $(SIM6809_REV) \
		--root .tools/6809

$(SIM6809):
	$(MAKE) tools

# ---------------------------------------------------------------------------
# EXP-014, the 6309 multiplier block. Standalone: it shares the engine's
# arithmetic and its trained parameters, and none of its code.

BENCH_SOURCES := src/6309/coco_bench.asm src/6309/multiply_bench.asm \
		src/6809/text_screen.asm build/bench6309/bench_data.inc

build/bench6309/bench_data.inc: tools/export_bench_data.py \
		experiments/data/EXP-002-tokenized-computer-names.txt
	$(UV) run python tools/export_bench_data.py

build/bench6309/bench-test.bin: src/6309/tests/bench_test.asm $(BENCH_SOURCES)
	$(LWASM) --6809 --format=raw \
		--symbol-dump=build/bench6309/bench-test.sym --output=$@ $<

build/bench6309/bench-test-runner.asm: build/bench6309/bench-test.bin \
		tools/make_bench_runner.py
	$(UV) run python tools/make_bench_runner.py \
		--binary build/bench6309/bench-test.bin \
		--symbols build/bench6309/bench-test.sym \
		--assert-symbol bench_sum=BENCH_EXPECTED \
		--output $@

# The direct simulator is MC6809 only, so this proves kernel one. Kernel two
# is proven in Python over every input pair, and then on the machine.
bench-test: build/bench6309/bench-test-runner.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --reset-vector 0x2000 --run --perf $<

build/bench6309/bench6809.bin: $(BENCH_SOURCES)
	$(LWASM) --6809 --format=decb --output=$@ src/6309/coco_bench.asm
	$(LWASM) --6809 --format=raw \
		--symbol-dump=build/bench6309/coco-bench.sym \
		--output=build/bench6309/coco-bench.bin src/6309/coco_bench.asm

build/bench6309/bench6309.bin: $(BENCH_SOURCES)
	$(LWASM) --6309 --format=decb --define=BENCH_6309=1 --define=BENCH_NATIVE=1 \
		--output=$@ src/6309/coco_bench.asm
	$(LWASM) --6309 --format=raw --define=BENCH_6309=1 --define=BENCH_NATIVE=1 \
		--symbol-dump=build/bench6309/coco-bench-6309.sym \
		--output=build/bench6309/coco-bench-6309.bin src/6309/coco_bench.asm

# The fallback: MULD without native mode, for the case where native-mode
# interrupt stacking misbehaves on real silicon. MULD works in either mode.
build/bench6309/bench6309safe.bin: $(BENCH_SOURCES)
	$(LWASM) --6309 --format=decb --define=BENCH_6309=1 --output=$@ \
		src/6309/coco_bench.asm
	$(LWASM) --6309 --format=raw --define=BENCH_6309=1 \
		--symbol-dump=build/bench6309/coco-bench-safe.sym \
		--output=build/bench6309/coco-bench-safe.bin src/6309/coco_bench.asm

build/bench6309/BENCH309.DSK: build/bench6309/bench6809.bin \
		build/bench6309/bench6309.bin build/bench6309/bench6309safe.bin \
		tools/make_rsdos_dsk.py
	$(UV) run python tools/make_rsdos_dsk.py --output $@ \
		--file BENCH09.BIN=build/bench6309/bench6809.bin \
		--file BENCH39.BIN=build/bench6309/bench6309.bin \
		--file BENCH39S.BIN=build/bench6309/bench6309safe.bin

bench-bin: build/bench6309/bench6809.bin build/bench6309/bench6309.bin \
		build/bench6309/bench6309safe.bin build/bench6309/BENCH309.DSK

# Both runs use -no-ratelimit. TIMER counts video frames rather than processor
# cycles, so the tick figures are the ones the machine would report at its own
# speed, and the run finishes in a second instead of nine.
#
# XRoar's own help calls its 6309 emulation UNVERIFIED. These numbers are
# evidence, not the measurement: the physical CoCo 3 is the authority for
# anything the 6309 does.
bench-xroar-6809: build/bench6309/bench6809.bin build/roms/.coco1-roms
	$(UV) run python tools/run_bench_xroar.py --xroar $(XROAR) \
		--binary $< --symbols build/bench6309/coco-bench.sym \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) --cpu 6809

bench-xroar-6309: build/bench6309/bench6309.bin build/roms/.coco1-roms
	$(UV) run python tools/run_bench_xroar.py --xroar $(XROAR) \
		--binary $< --symbols build/bench6309/coco-bench-6309.sym \
		--basic-rom $(COCO_BASIC_ROM) \
		--extended-basic-rom $(COCO_EXTBASIC_ROM) --cpu 6309

bench: bench-test bench-bin bench-xroar-6809 bench-xroar-6309

.PHONY: bench bench-test bench-bin bench-xroar-6809 bench-xroar-6309
