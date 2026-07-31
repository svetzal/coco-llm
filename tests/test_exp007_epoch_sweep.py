import argparse
import runpy
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]
SWEEP = runpy.run_path(ROOT / "tools" / "run_exp_007_epoch_sweep.py")
boundary_behavior = SWEEP["boundary_behavior"]
comma_separated_epochs = SWEEP["comma_separated_epochs"]


class FixedScores:
    def __init__(self) -> None:
        self.vocabulary = ["<END>", ".", "?", "WORD"]
        self.token_by_text = {
            token: index for index, token in enumerate(self.vocabulary)
        }

    def integer_scores(self, context: np.ndarray) -> np.ndarray:
        if int(context[-1]) == 1:
            return np.asarray([10, 3, 8, 2])
        return np.asarray([1, 2, 3, 10])


def test_epoch_parser_sorts_and_deduplicates() -> None:
    assert comma_separated_epochs("40, 5,20,40") == [5, 20, 40]
    with pytest.raises(argparse.ArgumentTypeError):
        comma_separated_epochs("0,5")


def test_boundary_behavior_separates_end_from_visible_fallback() -> None:
    result = boundary_behavior(FixedScores(), [np.asarray([0, 0, 0, 0, 1])])

    assert result["boundary_top_one_rate"] == 1.0
    assert result["visible_fallback_punctuation_rate"] == 1.0
    assert result["visible_fallbacks"] == [("?", 1)]
