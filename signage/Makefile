# The table signage: slides for the big screen beside the two CoCos, and
# the Raspberry Pi SD-card image that boots straight into them.
#
#   make data      export the real numbers the slides quote   -> slides/data.js
#   make slides    render the slides to 1920x1080 PNGs        -> build/slides/
#   make image     build the SD-card image                    -> build/coco-signage.img
#   make verify    mount the built image and list what the boot depends on
#   make preview   open the live loop in a browser, as the Pi will show it
#
# `make image` needs Docker; everything else needs uv and Google Chrome.
# Writing the image to a card is deliberately not a target: see README.md.

UV := uv
ROOT := $(abspath ..)
BUILD := $(CURDIR)/build
BUILDER := coco-signage-builder
PREVIEW_PORT := 8619

DATA := slides/data.js
DATA_SOURCES := tools/export_slide_data.py \
	$(wildcard ../experiments/data/EXP-002-*.txt) \
	$(wildcard ../experiments/data/EXP-003-*.txt) \
	../presentation/deck/data/prompts.json \
	../presentation/deck/data/titles.json \
	$(wildcard ../src/reference/fixed_token_lm.py ../src/reference/token_lm.py ../src/reference/run_bias_demo.py)

.PHONY: data slides image verify preview builder clean

data: $(DATA)

$(DATA): $(DATA_SOURCES)
	cd $(ROOT) && $(UV) run python signage/tools/export_slide_data.py

slides: $(DATA) slides/index.html slides/signage.css tools/render_slides.py
	cd $(ROOT) && $(UV) run python signage/tools/render_slides.py

builder:
	docker build -q -t $(BUILDER) image

image: slides builder
	@test -n "$$(ls build/slides/*.png 2>/dev/null)" || (echo "no rendered slides; make slides first" && exit 1)
	docker run --rm --privileged \
		-v "$(CURDIR)":/src:ro \
		-v "$(BUILD)":/work \
		$(BUILDER)

verify: builder
	docker run --rm --privileged \
		-v "$(CURDIR)":/src:ro \
		-v "$(BUILD)":/work \
		$(BUILDER) verify

preview:
	@echo "Serving the repository at http://localhost:$(PREVIEW_PORT)/ - Ctrl-C to stop."
	@(sleep 1; open "http://localhost:$(PREVIEW_PORT)/signage/slides/index.html") &
	@cd $(ROOT) && python3 -m http.server $(PREVIEW_PORT)

clean:
	rm -rf build/slides build/coco-signage.img build/coco-signage.img.sha256
