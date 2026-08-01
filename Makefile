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
	xroar-music present tools

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

MUSIC_RATE ?= 6370

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
	workbench-test-exp6 model-test-exp7 workbench-test-exp7

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
