# Research

This folder holds durable knowledge that should survive individual experiments:

- 6809 and CoCo hardware constraints;
- model architecture and fixed-point decisions;
- relevant language-model history;
- compiler, assembler, emulator, and media-format choices;
- measured physical-hardware characteristics;
- sources used in the presentation.

Open questions belong in an experiment when they can be tested. Research notes
should distinguish measured facts, sourced facts, design decisions, and
inferences.

## Current notes

- [`model-design.md`](model-design.md) — candidate language-model architecture.
- [`toolchain.md`](toolchain.md) — cross-assembly and emulation strategy.

## Starting sources

- Motorola, [MC6809-MC6809E Microprocessor Programming
  Manual](https://www.maddes.net/m6809pm/).
- Tandy, [TRS-80 Color Computer Technical Reference
  Manual](https://colorcomputerarchive.com/repo/Documents/Manuals/Hardware/Color%20Computer%20Technical%20Reference%20Manual%20%28Tandy%29.pdf).
- Yoshua Bengio et al., [A Neural Probabilistic Language
  Model](https://www.jmlr.org/papers/v3/bengio03a.html), 2003.
