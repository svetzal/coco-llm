"""Run one CoCo LLM experiment with concise, presentation-friendly output."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from coco_lm import ModelConfig as CharacterConfig
from coco_lm import load_names as load_character_names
from coco_lm import run_training as run_character_training
from fixed_token_lm import FixedTokenLanguageModel
from run_bias_demo import BiasResult, run_comparison
from token_lm import ModelConfig as TokenConfig
from token_lm import assess_samples, build_vocabulary, load_names, make_examples

EXPERIMENTS = {
    "EXP-004": (
        "Training and inference on the 6809",
        "Interactive stock-rate XRoar demonstration; press a key to infer.",
    ),
    "EXP-005": (
        "Prompting with 1980s advertising language",
        "Interactive XRoar prompt selector; Up/Down chooses, Enter generates.",
    ),
    "EXP-006": (
        "Practical pretrained tab completion",
        "Interactive 8 KiB completion model with a four-word context.",
    ),
    "EXP-007": (
        "All-RAM sentence completion",
        "Interactive 32 KiB model with five-token context and punctuation.",
    ),
    "EXP-011": (
        "Temporary facts through attention",
        "Interactive key-value context, reshuffle, and slow attention replay.",
    ),
}


def heading(title: str, question: str) -> None:
    print(title)
    print("=" * len(title))
    print(question)
    print()


def normalize_experiment(value: str) -> str:
    normalized = value.upper().removeprefix("EXP-")
    try:
        number = int(normalized)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"unknown experiment {value!r}; try 4, 5, 6, 7, or 11"
        ) from error
    experiment = f"EXP-{number:03d}"
    if experiment not in EXPERIMENTS:
        raise argparse.ArgumentTypeError(
            f"unknown experiment {value!r}; try 4, 5, 6, 7, or 11"
        )
    return experiment


def run_exp_001() -> dict[str, Any]:
    corpus = ROOT / "experiments" / "data" / "EXP-001-computer-names.txt"
    config = CharacterConfig(context=3, embedding=3, hidden=6, seed=6809)
    names = load_character_names(corpus)
    result, _, assessments = run_character_training(
        names,
        config,
        epochs=20,
        learning_rate=0.05,
        sample_count=5,
        temperature=0.8,
    )
    bare_multiply_seconds = result.total_multiplies * 11 / 890_000
    payload = {
        "experiment": "EXP-001",
        "status": "rejected",
        "parameters": result.parameter_count,
        "examples": result.examples,
        "multiplies": result.total_multiplies,
        "initial_loss": result.initial_loss,
        "final_loss": result.final_loss,
        "bare_multiply_seconds": bare_multiply_seconds,
        "samples": [asdict(item) for item in assessments],
    }

    heading(
        "EXP-001 — CHARACTER MODEL",
        "Can a character model train on a stock CoCo in under three minutes?",
    )
    print("CALL THE SHOT")
    print("  Complete training must finish in 180 seconds.")
    print()
    print(f"Parameters                 {result.parameter_count:>12,}")
    print(f"Training examples          {result.examples:>12,}")
    print(f"Matrix multiplications     {result.total_multiplies:>12,}")
    print(
        f"Loss                  {result.initial_loss:>6.4f} -> {result.final_loss:.4f}"
    )
    print()
    print("WHAT DID IT GENERATE?")
    for assessment in assessments:
        print(f"  {assessment.text or '<EMPTY>'}")
    print()
    print("REJECTED")
    print(f"  MUL instructions alone need about {bare_multiply_seconds:.0f} seconds.")
    print("  That leaves almost no budget for the rest of learning.")
    print("  Is tokenization an opportunity?")
    return payload


def run_exp_002() -> dict[str, Any]:
    corpus = ROOT / "experiments" / "data" / "EXP-002-tokenized-computer-names.txt"
    names = load_names(corpus)
    vocabulary, token_by_text = build_vocabulary(names)
    config = TokenConfig(seed=6809)
    contexts, targets = make_examples(names, token_by_text, config.context)
    model = FixedTokenLanguageModel(config, vocabulary)
    initial_loss = model.loss(contexts, targets)
    final_loss = model.train(contexts, targets, epochs=20)[-1]
    samples = [model.generate(random_seed=6809 + index) for index in range(8)]
    assessments = assess_samples(samples, names)
    total_multiplies = model.multiplies_per_example * len(targets) * 20
    payload = {
        "experiment": "EXP-002",
        "status": "supported",
        "parameters": model.parameter_count,
        "vocabulary": len(vocabulary),
        "examples": len(targets),
        "multiplies": total_multiplies,
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "checksum": model.checksum(),
        "samples": [asdict(item) for item in assessments],
    }

    heading(
        "EXP-002 — TOKEN MODEL",
        "What changes when complete name parts become tokens?",
    )
    print("CHARACTERS -> TOKENS")
    print(f"  Training examples             729 -> {len(targets)}")
    print(f"  Matrix multiplications  12,859,560 -> {total_multiplies:,}")
    print()
    print(f"Parameters                 {model.parameter_count:>12,}")
    print(f"Vocabulary tokens          {len(vocabulary):>12,}")
    print(f"Loss                  {initial_loss:>6.4f} -> {final_loss:.4f}")
    print()
    print("WHAT DID IT GENERATE?")
    for assessment in assessments:
        verdict = "novel" if assessment.novel else "copied"
        print(f"  {assessment.text:<24} {verdict}")
    print()
    print("SUPPORTED")
    print("  Fewer predictions make the learning visible and feasible.")
    print("  Same objective. Better representation. Think about that a minute.")
    return payload


def fan_counts(result: BiasResult) -> tuple[int, int, int, int]:
    apple = result.first_token_counts.get("APPLE", 0)
    commodore = result.first_token_counts.get("COMMODORE", 0)
    tandy = result.first_token_counts.get("TANDY", 0)
    other = sum(result.first_token_counts.values()) - apple - commodore - tandy
    return apple, commodore, tandy, other


def representative_sample(result: BiasResult) -> str:
    preferred = {
        "APPLE FAN": "APPLE",
        "COMMODORE FAN": "COMMODORE",
        "TANDY FAN": "TANDY",
        "ALL FANS CONCATENATED": "TANDY",
    }.get(result.label)
    if preferred is not None:
        for sample in result.samples:
            if sample.startswith(preferred + " "):
                return sample
    return result.samples[0]


def run_exp_003() -> dict[str, Any]:
    results = run_comparison(sample_count=20)
    payload = {
        "experiment": "EXP-003",
        "status": "supported",
        "runs": [asdict(result) for result in results],
    }

    heading(
        "EXP-003 — TRAINING-DATA BIAS",
        "Can identical models learn the preference we put into their data?",
    )
    print("Every run: same model, seed, updates, and generation seeds.")
    print()
    print("TRAINING DATA           APPLE  COMMODORE  TANDY  OTHER")
    print("----------------------  -----  ---------  -----  -----")
    for result in results:
        apple, commodore, tandy, other = fan_counts(result)
        print(f"{result.label:<22}  {apple:>5}  {commodore:>9}  {tandy:>5}  {other:>5}")
    print()
    print("ONE OUTPUT FROM EACH RUN")
    for result in results:
        print(f"  {result.label:<22} {representative_sample(result)}")
    print()
    print("SUPPORTED")
    print("  Equal source counts did not guarantee balanced behaviour.")
    print("  The concatenated model saw Tandy last; the interleaved model did not.")
    print("  The model has no loyalty. We taught it a point of view.")
    return payload


def run_exp_004() -> dict[str, Any]:
    payload = {
        "experiment": "EXP-004",
        "status": "interactive",
        "parameters": 290,
        "command": "make xroar",
    }
    heading(
        "EXP-004 — THE 6809 TRAINS",
        "Can a 45-year-old CoCo perform the complete learning loop?",
    )
    print("Launching stock-rate XRoar with the real CoCo 1 ROMs.")
    print("Training pauses before inference. Press any CoCo key when you are ready.")
    print()
    subprocess.run(["make", "xroar"], cwd=ROOT, check=True)
    return payload


def build_exp_005_reference() -> dict[str, Any]:
    corpus = ROOT / "experiments" / "data" / "EXP-005-marketing-language.txt"
    phrases = load_names(corpus)
    vocabulary, token_by_text = build_vocabulary(phrases)
    config = TokenConfig(seed=6809)
    contexts, targets = make_examples(phrases, token_by_text, config.context)
    model = FixedTokenLanguageModel(config, vocabulary)
    initial_loss = model.loss(contexts, targets)
    final_loss = model.train(contexts, targets, epochs=80)[-1]
    prompts = (
        "I ADORE",
        "ARE YOU",
        "WHY BUY",
        "POWER WITHOUT",
        "GET YOUR",
        "THE COMPUTER",
    )
    completions = [
        {
            "prompt": prompt,
            "completion": model.generate(
                prompt=prompt,
                random_seed=config.seed,
                minimum_tokens=0,
                greedy=True,
            ),
        }
        for prompt in prompts
    ]
    total_multiplies = model.multiplies_per_example * len(targets) * 80
    payload = {
        "experiment": "EXP-005",
        "status": "reference-supported",
        "parameters": model.parameter_count,
        "vocabulary": len(vocabulary),
        "examples": len(targets),
        "epochs": 80,
        "multiplies": total_multiplies,
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "checksum": model.checksum(),
        "completions": completions,
    }

    return payload


def run_exp_005() -> dict[str, Any]:
    payload = {
        "experiment": "EXP-005",
        "status": "interactive",
        "parameters": 380,
        "vocabulary": 38,
        "command": "make xroar-exp5",
    }
    heading(
        "EXP-005 — YOU START, IT COMPLETES",
        "If we replace # # with real words, can we steer what comes next?",
    )
    print("Launching XRoar with the expanded model and real CoCo 1 ROMs.")
    print("After training: press a key, choose with Up/Down, generate with Enter.")
    print("Each completion stays visible; selection advances to the next prompt.")
    print()
    subprocess.run(["make", "xroar-exp5"], cwd=ROOT, check=True)
    return payload


def run_exp_006() -> dict[str, Any]:
    payload = {
        "experiment": "EXP-006",
        "status": "interactive",
        "parameters": 8188,
        "vocabulary": 178,
        "context": 4,
        "command": "make xroar-exp6",
    }
    heading(
        "EXP-006 — PRACTICAL COMPLETION",
        "What can an 8 KiB pretrained model do in an interactive editor?",
    )
    print("Launching the four-word completion workbench in XRoar.")
    print("Type a phrase; Right/Tab predicts, Up/Down chooses, Enter accepts.")
    print()
    subprocess.run(["make", "xroar-exp6"], cwd=ROOT, check=True)
    return payload


def run_exp_007() -> dict[str, Any]:
    payload = {
        "experiment": "EXP-007",
        "status": "interactive",
        "parameters": 32385,
        "vocabulary": 255,
        "context": 5,
        "command": "make xroar-exp7",
    }
    heading(
        "EXP-007 — ALL-RAM SENTENCE COMPLETION",
        "What changes with four times the model memory and punctuation?",
    )
    print("Launching the 64 KiB CoCo 1 configuration in XRoar.")
    print("The 32 KiB model uses five-token context and punctuation tokens.")
    print("Type a phrase; Right/Tab predicts, Up/Down chooses, Enter accepts.")
    print()
    subprocess.run(["make", "xroar-exp7"], cwd=ROOT, check=True)
    return payload


def run_exp_011() -> dict[str, Any]:
    payload = {
        "experiment": "EXP-011",
        "status": "interactive",
        "parameters": 160,
        "context_records": 8,
        "command": "make xroar-attention",
    }
    heading(
        "EXP-011 — TEMPORARY FACTS THROUGH ATTENTION",
        "Can the CoCo use a fact supplied now without storing it in the model?",
    )
    print("Launching the contextual-attention workbench in stock-rate XRoar.")
    print("Choose with Up/Down, ask with Enter, then press S for a new context.")
    print("V opens an explicitly paced replay; Clear returns to the main screen.")
    print()
    subprocess.run(["make", "xroar-attention"], cwd=ROOT, check=True)
    return payload


RUNNERS: dict[str, Callable[[], dict[str, Any]]] = {
    "EXP-004": run_exp_004,
    "EXP-005": run_exp_005,
    "EXP-006": run_exp_006,
    "EXP-007": run_exp_007,
    "EXP-011": run_exp_011,
}


def list_experiments(as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                [
                    {
                        "experiment": experiment,
                        "title": title,
                        "description": description,
                    }
                    for experiment, (title, description) in EXPERIMENTS.items()
                ],
                indent=2,
            )
        )
        return

    print("PRESENTABLE EXPERIMENTS")
    print("=======================")
    print("Run one with: make present EXP=4")
    print()
    for experiment, (title, description) in EXPERIMENTS.items():
        print(f"{experiment}  {title}")
        print(f"         {description}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run concise, deterministic CoCo LLM presentation demos.",
        epilog=(
            "examples:\n"
            "  python tools/present_experiment.py list\n"
            "  python tools/present_experiment.py run 5"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list the interactive experiments")
    list_parser.add_argument("--json", action="store_true")

    run_parser = subparsers.add_parser("run", help="run one experiment")
    run_parser.add_argument("experiment", type=normalize_experiment)
    run_parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.command == "list":
        list_experiments(arguments.json)
        return

    if arguments.json and arguments.experiment in RUNNERS:
        raise SystemExit(
            f"{arguments.experiment} is interactive and has no JSON mode; "
            f"try: make present EXP={arguments.experiment[-1]}"
        )
    if arguments.json:
        import contextlib
        import io

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            payload = RUNNERS[arguments.experiment]()
        print(json.dumps(payload, indent=2))
        return
    RUNNERS[arguments.experiment]()


if __name__ == "__main__":
    main()
