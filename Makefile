UV := uv
SIM6809 := .tools/6809/bin/6809
SIM6809_REV := 546c8d2efc7d30cecb5afe9bc05e683a4bfbd672
XROAR ?= /opt/homebrew/opt/xroar/bin/xroar
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
	xroar-melody exp011-sweep exp011-replicate exp011-model \
	attention-bin attention-test attention-ui-test xroar-test-attention \
	xroar-attention exp012-corpus exp012-vocabulary exp012-tokenizations \
	exp012-titles exp012-model titles-bin titles-test xroar-titles \
	exp013-sweep exp013-play exp013-record rpsls-bin rpsls-test xroar-rpsls \
	present stage tools

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

# Pre-flight for the talk: launch the four parkable XRoar instances in the
# background, one per demo block. EXP-004 is deliberately absent - it starts
# training the moment it loads, so block 3 launches it live with
# `make present EXP=4`. Arrange the four windows in block order once they
# are up; XRoar windows are otherwise indistinguishable.
stage: build/coco-llm-exp5.bin build/coco-attention.bin \
		build/coco-titles.bin build/coco-rpsls.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-llm-exp5.bin & \
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-attention.bin & \
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-titles.bin & \
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-rpsls.bin &
	@echo "Parked: EXP-005 (block 4), EXP-011 (block 5)," \
		"EXP-012 (block 6), EXP-013 (block 8)."
	@echo "Block 3 launches live: make present EXP=4"

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

music-cycles:
	$(UV) run python tools/music_cycle_budget.py

build/exp009/tune_data.inc: tools/export_tune.py src/reference/coco_synth.py
	$(UV) run python tools/export_tune.py --sample-rate $(MUSIC_RATE)

music-tune: build/exp009/tune_data.inc
	$(UV) run python tools/render_tune.py --sample-rate $(MUSIC_RATE)

build/coco-music.bin: src/6809/coco_music.asm src/6809/music_player.asm \
		build/exp009/tune_data.inc
	lwasm --6809 --format=decb --symbol-dump=build/coco-music.sym \
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
	lwasm --6809 -I src/6809 --format=decb \
		--symbol-dump=build/coco-rpsls.sym --output=$@ $<

rpsls-bin: build/coco-rpsls.bin

build/rpsls-agent.asm: src/6809/coco_rpsls.asm src/6809/rpsls_game.asm \
		src/6809/text_screen.asm
	printf 'DIRECT_TEST equ 1\n' > $@
	cat $< >> $@

build/rpsls-agent.bin: build/rpsls-agent.asm
	lwasm --6809 -I src/6809 --format=decb \
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

exp013-record:
ifndef LABEL
	$(error set LABEL, for example: make exp013-record LABEL=stacey-coco-01)
endif
exp013-record: build/coco-rpsls.bin build/roms/.coco1-roms
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
	lwasm --6809 --format=decb --symbol-dump=build/coco-titles.sym \
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
	lwasm --6809 --format=raw --symbol-dump=build/melody-core.sym \
		--output=$@ $<

exp010-core: build/melody-core.bin

build/melody-parity-test.asm: build/melody-core.bin \
		tools/make_melody_parity_test.py src/reference/melody_fixed.py
	$(UV) run python tools/make_melody_parity_test.py --output $@

exp010-test: build/melody-parity-test.asm $(SIM6809)
	$(SIM6809) --ram-top 65535 --run $<

build/exp010/tune_frame.inc: tools/export_tune.py
	$(UV) run python tools/export_tune.py --sample-rate $(MUSIC_RATE) \
		--ram-rows 128 --output $@

build/coco-melody-demo.bin: src/6809/coco_melody_demo.asm \
		src/6809/melody_demo.asm src/6809/melody_ui.asm \
		src/6809/melody_inference.asm \
		src/6809/music_player.asm build/exp010/melody_model.inc \
		build/exp010/tune_frame.inc
	lwasm --6809 --format=decb \
		--symbol-dump=build/coco-melody-demo.sym --output=$@ $<

exp010-demo: build/coco-melody-demo.bin

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

xroar-music: build/coco-music.bin build/roms/.coco1-roms
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 \
		-bas $(COCO_BASIC_ROM) -extbas $(COCO_EXTBASIC_ROM) \
		-ratelimit -run build/coco-music.bin

test: reference-test asm-test model-test model-test-exp5 model-test-exp6 \
	workbench-test-exp6 model-test-exp7 workbench-test-exp7 \
	attention-test attention-ui-test titles-test rpsls-test

reference-test:
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
	lwasm --6809 --format=raw --output=$@ $<

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
	lwasm --6809 --format=raw --symbol-dump=build/model-test.sym \
		--output=$@ $<

build/model-test-runner.asm: build/model-test.bin \
		tools/make_6809_test_runner.py
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/model-test.bin \
		--symbols build/model-test.sym \
		--output $@

build/model-exp5-test.bin: src/6809/tests/model_exp5_test.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP005_SOURCES) build/model_data_exp5.inc
	lwasm --6809 --format=raw --symbol-dump=build/model-exp5-test.sym \
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
	lwasm --6809 --format=raw --symbol-dump=build/model-exp6-test.sym \
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
	lwasm --6809 --format=raw --symbol-dump=build/model-exp7-test.sym \
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
	lwasm --6809 --format=raw --symbol-dump=build/workbench-exp6-test.sym \
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
	lwasm --6809 --format=raw --symbol-dump=build/workbench-exp7-test.sym \
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
	lwasm --6809 --format=decb --output=$@ $<

build/coco-attention.raw build/coco-attention.sym: src/6809/coco_attention.asm \
		src/6809/attention_inference.asm src/6809/attention_ui.asm \
		build/exp011/attention_data.inc
	lwasm --6809 --format=raw --symbol-dump=build/coco-attention.sym \
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
	lwasm --6809 --format=decb --output=$@ $<

build/coco-llm.sym: src/6809/coco_llm.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP004_SOURCES) build/model_data.inc
	lwasm --6809 --format=raw --symbol-dump=build/coco-llm.sym \
		--output=build/coco-llm.raw $<

build/coco-llm.raw: build/coco-llm.sym
	@test -f $@

build/coco-llm-exp5.bin: src/6809/coco_llm_exp5.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP005_SOURCES) build/model_data_exp5.inc
	lwasm --6809 --format=decb --output=$@ $<

build/coco-llm-exp5.sym: src/6809/coco_llm_exp5.asm \
		$(6809_COMMON_SOURCES) $(6809_EXP005_SOURCES) build/model_data_exp5.inc
	lwasm --6809 --format=raw --symbol-dump=build/coco-llm-exp5.sym \
		--output=build/coco-llm-exp5.raw $<

build/coco-llm-exp6.bin: src/6809/coco_llm_exp6.asm \
		src/6809/experiments/experiment_006.asm \
		src/6809/completion_inference.asm src/6809/completion_screen.asm \
		src/6809/completion_editor.asm src/6809/completion_policy_exp6.asm \
		build/exp006/model_data.inc \
		build/exp006/model_image.inc
	lwasm --6809 --format=decb --output=$@ $<

build/coco-llm-exp6.sym: src/6809/coco_llm_exp6.asm \
		src/6809/experiments/experiment_006.asm \
		src/6809/completion_inference.asm src/6809/completion_screen.asm \
		src/6809/completion_editor.asm src/6809/completion_policy_exp6.asm \
		build/exp006/model_data.inc
	lwasm --6809 --define=DIRECT_TEST=1 --format=raw \
		--symbol-dump=build/coco-llm-exp6.sym \
		--output=build/coco-llm-exp6.raw $<

build/coco-llm-exp7.bin: src/6809/coco_llm_exp7.asm \
		src/6809/experiments/experiment_007.asm \
		src/6809/completion_inference_exp7.asm \
		src/6809/completion_screen.asm src/6809/completion_editor.asm \
		src/6809/completion_policy_exp7.asm build/exp007/model_data.inc \
		build/exp007/packed_model.inc
	lwasm --6809 --format=decb --output=$@ $<

build/coco-llm-exp7.sym: src/6809/coco_llm_exp7.asm \
		src/6809/experiments/experiment_007.asm \
		src/6809/completion_inference_exp7.asm \
		src/6809/completion_screen.asm src/6809/completion_editor.asm \
		src/6809/completion_policy_exp7.asm build/exp007/model_data.inc
	lwasm --6809 --define=DIRECT_TEST=1 --format=raw \
		--symbol-dump=build/coco-llm-exp7.sym \
		--output=build/coco-llm-exp7.raw $<

build/roms/.coco1-roms: $(COCO_ROM_ARCHIVE)
	mkdir -p build/roms
	unzip -jo $(COCO_ROM_ARCHIVE) bas11.rom extbas10.rom -d build/roms
	touch $@

tools:
	@command -v lwasm >/dev/null || \
		(echo "Install LWTOOLS first: brew install lwtools" && exit 1)
	cargo install \
		--git https://github.com/gorsat/6809.git \
		--rev $(SIM6809_REV) \
		--root .tools/6809

$(SIM6809):
	$(MAKE) tools
