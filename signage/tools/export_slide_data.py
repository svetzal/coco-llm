"""Export the real numbers and samples the table signage quotes.

Every sample on a signage slide comes from a run of the reference model,
which is the same bit-exact integer model the CoCo executes, or from the
deck's own exported traces. Nothing on a slide is typed in by hand, so a
slide cannot drift away from what the machine on the table actually does.
Change the model, re-run this, and the slides change with it.

Writes ``signage/slides/data.js``, which the slideshow loads.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from fixed_token_lm import FixedTokenLanguageModel  # noqa: E402
from run_bias_demo import run_comparison  # noqa: E402
from token_lm import (  # noqa: E402
    ModelConfig,
    build_vocabulary,
    load_names,
    make_examples,
)

OUTPUT = ROOT / "signage" / "slides" / "data.js"

# EXP-004, the live training run, as the CoCo 1 performs it: twenty passes
# over the corpus, then a gallery of eleven consecutive seeds from 6809.
LIVE_RUN_EPOCHS = 20
LIVE_RUN_SEED = 6809
GALLERY_SIZE = 11

# EXP-003, the fan-corpus bias runs: which sample positions the signage sets
# side by side. Each position is one seed, shared by all three fans, so a
# row differs only by what the model read.
BIAS_ROWS = (0, 1, 3, 7)
BIAS_LABELS = ("APPLE FAN", "COMMODORE FAN", "TANDY FAN")

# EXP-005, the prompted marketing completions, as the deck exported them.
PROMPT_TRACE = ROOT / "presentation" / "deck" / "data" / "prompts.json"
PROMPTS_SHOWN = ("I ADORE", "ARE YOU", "WHY BUY", "POWER WITHOUT")

# EXP-012, the fake episode titles: the sixteen the deck's screen shows.
TITLES_TRACE = ROOT / "presentation" / "deck" / "data" / "titles.json"

# Recorded evidence, cited rather than re-run here. Each entry names the
# experiment file that holds the measurement.
RECORDED = {
    # EXP-013, the game opponent that learns: the recorded 200-round human
    # session in experiments/EXP-013-rpsls-opponent.md.
    "game": {"score_percent": 52.8, "rounds": 200},
    # EXP-011, the context-editing attention head: the Lisa edit in
    # experiments/EXP-011-contextual-associative-recall.md.
    "context": {"model": "751B", "before": "CODE 2", "after": "CODE 6"},
    # EXP-014, the 6309 multiplier benchmark: what the CoCo 3 did on
    # 2026-09-05, from experiments/EXP-014-6309-multiplier.md. Ticks are
    # the 60 Hz frame counter over 58,000 multiplications.
    "bench": {
        "measured_on": "5 September 2026",
        "multiplications": 58000,
        "rows": [
            {"ticks": 519, "what": "6809 code, run as a 6809"},
            {"ticks": 442, "what": "same code, 6309 native mode"},
            {"ticks": 338, "what": "the 6309's MULD instruction"},
            {"ticks": 168, "what": "MULD at double clock"},
        ],
    },
}


def live_training_run() -> dict:
    names = load_names(
        ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
    )
    vocabulary, token_by_text = build_vocabulary(names)
    config = ModelConfig(seed=LIVE_RUN_SEED)
    contexts, targets = make_examples(names, token_by_text, config.context)
    model = FixedTokenLanguageModel(config, vocabulary)
    before = model.generate(random_seed=LIVE_RUN_SEED)
    model.train(contexts, targets, epochs=LIVE_RUN_EPOCHS)
    gallery = [
        model.generate(random_seed=LIVE_RUN_SEED + index)
        for index in range(GALLERY_SIZE)
    ]
    corpus = set(names)
    after = [{"text": text, "copied": text in corpus} for text in gallery]
    return {
        "corpus": names,
        "corpus_count": len(names),
        "vocabulary": vocabulary,
        "vocab_count": len(vocabulary),
        "parameters": model.parameter_count,
        # Parameter masters are signed Q4.12: two bytes each.
        "weight_bytes": model.parameter_count * 2,
        "program_bytes": program_bytes("coco-llm.bin", recorded=3338),
        "examples": len(targets),
        "epochs": LIVE_RUN_EPOCHS,
        "corrections": len(targets) * LIVE_RUN_EPOCHS,
        "seed": LIVE_RUN_SEED,
        "before": before,
        "after": after,
        "copied_count": sum(1 for entry in after if entry["copied"]),
        "novel_count": sum(1 for entry in after if not entry["copied"]),
        "checksum": model.checksum()[:16],
    }


def program_bytes(name: str, recorded: int) -> int:
    """Size of an assembled CoCo binary, from the build if present.

    Falls back to the size the experiment recorded, and says so, because a
    fresh clone has no build directory and the slide still needs a number
    that was measured on a real artifact.
    """
    path = ROOT / "build" / name
    if path.is_file():
        return path.stat().st_size
    print(f"note: {path} not built; using recorded size {recorded}", file=sys.stderr)
    return recorded


def fan_corpora() -> dict:
    results = run_comparison(sample_count=max(BIAS_ROWS) + 1)
    by_label = {result.label: result for result in results}
    columns = []
    for label in BIAS_LABELS:
        result = by_label[label]
        columns.append(
            {
                "label": label,
                "samples": [result.samples[row] for row in BIAS_ROWS],
                "epochs": result.epochs,
            }
        )
    return {"columns": columns, "seeds": [LIVE_RUN_SEED + row for row in BIAS_ROWS]}


def prompted_completions() -> dict:
    trace = json.loads(PROMPT_TRACE.read_text())
    by_prompt = {entry["prompt"]: entry for entry in trace["completions"]}
    shown = [by_prompt[prompt] for prompt in PROMPTS_SHOWN]
    return {
        "vocabulary": trace["vocabulary"],
        "examples": trace["examples"],
        "completions": shown,
        "copied_count": sum(1 for entry in shown if entry["verbatim"]),
        "novel_count": sum(1 for entry in shown if not entry["verbatim"]),
    }


def episode_titles() -> dict:
    trace = json.loads(TITLES_TRACE.read_text())
    return {
        "dealt": trace["dealt"],
        "program_bytes": program_bytes("coco-titles.bin", recorded=3874),
        "real_titles": 79,
    }


def main() -> None:
    data = {
        "live": live_training_run(),
        "fans": fan_corpora(),
        "prompts": prompted_completions(),
        "titles": episode_titles(),
        **RECORDED,
    }
    body = json.dumps(data, indent=1)
    OUTPUT.write_text(
        "// Generated by signage/tools/export_slide_data.py. Do not edit;\n"
        "// every value here came from a run of the reference model or from\n"
        "// a recorded experiment. Change the source and re-run the tool.\n"
        f"window.COCO_SIGNAGE = {body};\n"
    )
    live = data["live"]
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"live run: {live['parameters']} parameters, checksum {live['checksum']}")
    print(f"gallery: {live['copied_count']} copied, {live['novel_count']} novel")


if __name__ == "__main__":
    main()
