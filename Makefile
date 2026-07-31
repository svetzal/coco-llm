UV := uv
SIM6809 := .tools/6809/bin/6809
SIM6809_REV := 546c8d2efc7d30cecb5afe9bc05e683a4bfbd672
XROAR ?= /opt/homebrew/opt/xroar/bin/xroar
COCO_ROM_ARCHIVE ?= $(HOME)/OneDrive/CoCo/MAME/roms/cocoe.zip
COCO_BASIC_ROM := build/roms/bas11.rom
COCO_EXTBASIC_ROM := build/roms/extbas10.rom

.PHONY: test reference-test asm-test model-test model-test-exp6 \
	workbench-test-exp6 coco-bin \
	xroar-test xroar \
	model-test-exp5 coco-bin-exp5 xroar-test-exp5 xroar-exp5 exp006-model \
	coco-bin-exp6 xroar-test-exp6 xroar-exp6 exp007-sweep present tools

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
	$(UV) run python tools/run_exp_007.py

test: reference-test asm-test model-test model-test-exp5 model-test-exp6 \
	workbench-test-exp6

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

workbench-test-exp6: build/workbench-exp6-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

coco-bin: build/coco-llm.bin

coco-bin-exp5: build/coco-llm-exp5.bin

coco-bin-exp6: build/coco-llm-exp6.bin

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

build/exp006/model_data.inc build/exp006/weights.bin \
		build/exp006/manifest.json build/exp006/test-vectors.json \
		build/exp006/model_image.inc: \
		tools/export_exp_006.py src/reference/completion_lm.py \
		experiments/data/EXP-006-completion-training.txt
	$(UV) run python tools/export_exp_006.py

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
