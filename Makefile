UV := uv
SIM6809 := .tools/6809/bin/6809
SIM6809_REV := 546c8d2efc7d30cecb5afe9bc05e683a4bfbd672

.PHONY: test reference-test asm-test tools

test: reference-test asm-test

reference-test:
	$(UV) sync
	$(UV) run ruff format --check src tests
	$(UV) run ruff check src tests
	$(UV) run pytest

asm-test: build/smul8-test.bin $(SIM6809)
	$(SIM6809) --run src/6809/tests/smul8_test.asm

build/smul8-test.bin: src/6809/tests/smul8_test.asm
	mkdir -p build
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
