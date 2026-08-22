#!/usr/bin/env python3
"""Export the training-data bias comparison for the deck.

EXP-003's whole design is a held constant: same architecture, same initial
weights, same training budget, same vocabulary, same sampling seeds. The only
thing that varies between runs is which names the model saw, and in what order.

Five runs. Three are one fan's collection each. The last two are the SAME 54
balanced names, differing only in whether the three collections are laid end to
end or shuffled together. That pair is the harder half of the lesson: nobody
chose to make the model a Tandy fan, and concatenation did it anyway.

Output is the first token of 20 generated names per run, which is where the
preference shows, plus one sample and the final loss.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "reference"))

from run_bias_demo import run_comparison  # noqa: E402

OUT = ROOT / "presentation" / "deck" / "data" / "bias.json"
SAMPLES = 20
# The three makers whose collections are being compared; everything else is a
# long tail of single draws and is grouped rather than listed.
MAKERS = ("APPLE", "COMMODORE", "TANDY")


def main() -> None:
    runs = []
    for result in run_comparison(sample_count=SAMPLES):
        counts = result.first_token_counts
        named = {maker: counts.get(maker, 0) for maker in MAKERS}
        other = sum(counts.values()) - sum(named.values())
        top = max(named, key=lambda maker: named[maker])
        runs.append(
            {
                "label": result.label,
                "names": result.training_names,
                "epochs": result.epochs,
                "final_loss": round(result.final_loss, 2),
                "counts": named,
                "other": other,
                "total": sum(counts.values()),
                "favourite": top,
                "favourite_share": named[top],
                "sample": result.samples[1],
            }
        )

    assert len(runs) == 5, f"expected 5 runs, got {len(runs)}"
    balanced = runs[3], runs[4]
    assert balanced[0]["names"] == balanced[1]["names"], (
        "the concatenated and interleaved runs must train on the same names; "
        "if they do not, the comparison proves nothing"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"samples": SAMPLES, "makers": list(MAKERS), "runs": runs}, indent=1)
        + "\n",
        encoding="ascii",
    )
    for run in runs:
        share = f"{run['favourite']} {run['favourite_share']}/{run['total']}"
        print(f"{run['label']:<24} loss {run['final_loss']:>5}  {share:<18} {run['sample']}")


if __name__ == "__main__":
    main()
