UV := uv
SIM6809 := .tools/6809/bin/6809
SIM6809_REV := 546c8d2efc7d30cecb5afe9bc05e683a4bfbd672
XROAR ?= /opt/homebrew/opt/xroar/bin/xroar

.PHONY: test reference-test asm-test model-test coco-bin xroar-rom xroar-test \
	xroar tools

test: reference-test asm-test model-test

reference-test:
	$(UV) sync
	$(UV) run ruff format --check src tests tools
	$(UV) run ruff check src tests tools
	$(UV) run pytest

asm-test: build/smul8-test.bin $(SIM6809)
	$(SIM6809) --run src/6809/tests/smul8_test.asm

model-test: build/model-test-runner.asm $(SIM6809)
	$(SIM6809) --perf --run $<

coco-bin: build/coco-llm.bin

xroar-rom: build/coco-llm.rom

xroar-test: build/coco-llm.rom build/coco-llm.sym
	$(UV) run python tools/test_xroar.py \
		--xroar $(XROAR) --rom build/coco-llm.rom \
		--symbols build/coco-llm.sym

xroar: build/coco-llm.rom
	@test -x "$(XROAR)" || \
		(echo "Install XRoar first: brew install xroar" && exit 1)
	$(XROAR) -machine cocous -ram 32 -no-bas -no-extbas \
		-cart coco-llm -cart-type rom -cart-rom $< -cart-autorun \
		-machine-cart coco-llm

build/smul8-test.bin: src/6809/tests/smul8_test.asm
	mkdir -p build
	lwasm --6809 --format=raw --output=$@ $<

build/model_data.inc: tools/generate_6809_data.py \
		src/reference/fixed_token_lm.py src/reference/token_lm.py \
		experiments/data/EXP-002-tokenized-computer-names.txt
	$(UV) run python tools/generate_6809_data.py --output $@

build/model-test.bin: src/6809/tests/model_test.asm \
		src/6809/model_core.asm build/model_data.inc
	lwasm --6809 --format=raw --symbol-dump=build/model-test.sym \
		--output=$@ $<

build/model-test-runner.asm: build/model-test.bin \
		tools/make_6809_test_runner.py
	$(UV) run python tools/make_6809_test_runner.py \
		--binary build/model-test.bin \
		--symbols build/model-test.sym \
		--output $@

build/coco-llm.bin: src/6809/coco_llm.asm \
		src/6809/model_core.asm build/model_data.inc
	lwasm --6809 --format=decb --output=$@ $<

build/coco-llm.sym: src/6809/coco_llm.asm \
		src/6809/model_core.asm build/model_data.inc
	lwasm --6809 --format=raw --symbol-dump=build/coco-llm.sym \
		--output=build/coco-llm.raw $<

build/coco-llm.raw: build/coco-llm.sym
	@test -f $@

build/coco-llm-payload.inc: build/coco-llm.raw \
		tools/binary_to_assembly.py
	$(UV) run python tools/binary_to_assembly.py \
		--input build/coco-llm.raw --output $@

build/coco-llm.rom: src/6809/xroar_boot.asm build/coco-llm-payload.inc
	lwasm --6809 --format=raw --output=$@ $<

tools:
	@command -v lwasm >/dev/null || \
		(echo "Install LWTOOLS first: brew install lwtools" && exit 1)
	cargo install \
		--git https://github.com/gorsat/6809.git \
		--rev $(SIM6809_REV) \
		--root .tools/6809

$(SIM6809):
	$(MAKE) tools
