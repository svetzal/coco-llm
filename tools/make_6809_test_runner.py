"""Wrap an LWASM raw binary in source understood by the direct simulator."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def symbol_address(symbols: str, name: str) -> int:
    match = re.search(
        rf"^{re.escape(name)} EQU \$([0-9A-Fa-f]+)$", symbols, re.MULTILINE
    )
    if match is None:
        raise ValueError(f"symbol not found: {name}")
    return int(match.group(1), 16)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--experiment", choices=(4, 5, 6), type=int, default=4)
    parser.add_argument("--weights", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--test-vectors", type=Path)
    parser.add_argument(
        "--weights-address", type=lambda text: int(text, 0), default=0x6000
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    payload = arguments.binary.read_bytes()
    symbols = arguments.symbols.read_text()
    start = symbol_address(symbols, "start")
    if arguments.experiment == 6:
        parity = symbol_address(symbols, "exp6_parity_result")
        top_one = symbol_address(symbols, "exp6_top_one_token")
        top_two = symbol_address(symbols, "exp6_top_two_token")
        top_three = symbol_address(symbols, "exp6_top_three_token")
        context_vector_address = symbol_address(symbols, "exp6_context_vector")
        lines = [
            "; Generated direct-simulator image. Do not edit.",
            f"        org     ${start:04x}",
        ]
        for offset in range(0, len(payload), 16):
            values = ",".join(
                f"${value:02x}" for value in payload[offset : offset + 16]
            )
            lines.append(f"        fcb     {values}")
        if (
            arguments.weights is None
            or arguments.manifest is None
            or arguments.test_vectors is None
        ):
            raise ValueError(
                "experiment 6 requires --weights, --manifest, and --test-vectors"
            )
        weights = arguments.weights.read_bytes()
        manifest = json.loads(arguments.manifest.read_text())
        test_vectors = json.loads(arguments.test_vectors.read_text())
        context = test_vectors[0]["context_tokens"]
        expected_context = test_vectors[0]["context_vector"]
        expected = test_vectors[0]["top_three_tokens"]
        embedding = manifest["embedding"]
        vocabulary_size = manifest["vocabulary_size"]

        def add_memory_block(address: int, values: bytes) -> None:
            lines.extend(["", f"        org     ${address:04x}"])
            for offset in range(0, len(values), 16):
                encoded = ",".join(
                    f"${value:02x}" for value in values[offset : offset + 16]
                )
                lines.append(f"        fcb     {encoded}")

        position_stride = vocabulary_size * embedding
        for position, token in enumerate(context):
            model_offset = position * position_stride + token * embedding
            add_memory_block(
                arguments.weights_address + model_offset,
                weights[model_offset : model_offset + embedding],
            )
        output_offset = manifest["layout"]["output_weights"]
        bias_offset = manifest["layout"]["output_biases"]
        add_memory_block(
            arguments.weights_address + output_offset,
            weights[output_offset:bias_offset],
        )
        add_memory_block(
            arguments.weights_address + bias_offset,
            weights[bias_offset : manifest["parameters"]],
        )
        lines.extend(
            [
                "",
                f"parity_result equ     ${parity:04x}",
                f"top_one       equ     ${top_one:04x}",
                f"top_two       equ     ${top_two:04x}",
                f"top_three     equ     ${top_three:04x}",
                *[
                    f"context_{index}     equ     ${context_vector_address + index:04x}"
                    for index in range(len(expected_context))
                ],
                ";! parity_result = #$01",
                f";! top_one = #${expected[0]:02x}",
                f";! top_two = #${expected[1]:02x}",
                f";! top_three = #${expected[2]:02x}",
                *[
                    f";! context_{index} = #${value & 0xFF:02x}"
                    for index, value in enumerate(expected_context)
                ],
                "",
            ]
        )
        arguments.output.write_text("\n".join(lines))
        return

    parity = symbol_address(symbols, "parity_result")
    mismatch_offset = symbol_address(symbols, "mismatch_offset")
    mismatch_actual = symbol_address(symbols, "mismatch_actual")
    mismatch_expected = symbol_address(symbols, "mismatch_expected")
    last_epoch_displayed = symbol_address(symbols, "last_epoch_displayed")

    lines = [
        "; Generated direct-simulator image. Do not edit.",
        f"        org     ${start:04x}",
    ]
    for offset in range(0, len(payload), 16):
        values = ",".join(f"${value:02x}" for value in payload[offset : offset + 16])
        lines.append(f"        fcb     {values}")
    common = [
        "",
        f"parity_result   equ     ${parity:04x}",
        f"mismatch_offset equ     ${mismatch_offset:04x}",
        f"mismatch_actual equ     ${mismatch_actual:04x}",
        f"mismatch_expect equ     ${mismatch_expected:04x}",
        f"last_epoch      equ     ${last_epoch_displayed:04x}",
    ]
    if arguments.experiment == 4:
        criteria = [
            "title_first     equ     $0400",
            "complete_first  equ     $0420",
            "generated_first equ     $0460",
            "seed_1_first    equ     $0480",
            "sample_1_first  equ     $0486",
            "sample_2_first  equ     $04a6",
            "sample_3_first  equ     $04c6",
            "sample_4_first  equ     $04e6",
            "sample_5_first  equ     $0506",
            "sample_10_last  equ     $05bf",
            ";! parity_result = #$01",
            ";! mismatch_offset = #$ffff",
            ";! mismatch_actual = #$00",
            ";! mismatch_expect = #$00",
            ";! last_epoch = #20",
            "; TRAINING COMPLETE, GENERATION COMPLETE.",
            ";! title_first = #$030f",
            ";! complete_first = #$5452",
            ";! generated_first = #$4745",
            ";! seed_1_first = #$6360",
            "; COMMODORE, TANDY, COMMODORE, TANDY, COMMODORE.",
            ";! sample_1_first = #$030f",
            ";! sample_2_first = #$1401",
            ";! sample_3_first = #$030f",
            ";! sample_4_first = #$1401",
            ";! sample_5_first = #$030f",
            "; Long seed 6818 is visibly clipped without crossing its row.",
            ";! sample_10_last = #$2b",
        ]
    else:
        criteria = [
            "title_first     equ     $0400",
            "instruction     equ     $0420",
            "prompt_1_cursor equ     $0460",
            "prompt_1_text   equ     $0462",
            "completion_1    equ     $0480",
            "prompt_2_cursor equ     $04a0",
            ";! parity_result = #$01",
            ";! mismatch_offset = #$ffff",
            ";! mismatch_actual = #$00",
            ";! mismatch_expect = #$00",
            ";! last_epoch = #80",
            "; COCO LLM PROMPTING, UP/DOWN SELECT, ENTER GENERATE.",
            ";! title_first = #$030f",
            ";! instruction = #$5550",
            "; First prompt generated MY 64 #, then selection moved down.",
            ";! prompt_1_cursor = #$6060",
            ";! prompt_1_text = #$4960",
            ";! completion_1 = #$0d19",
            ";! prompt_2_cursor = #$7e60",
        ]
    lines.extend([*common, *criteria, ""])
    arguments.output.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
