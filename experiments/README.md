# Experiments

Experiments turn architectural uncertainty into recorded evidence.

Each experiment should contain:

- a falsifiable hypothesis;
- the smallest procedure capable of testing it;
- fixed inputs and environment details;
- measurements and generated samples;
- a conclusion;
- the decision or next experiment that follows.

Use the filename pattern `EXP-NNN-short-name.md`. Do not rewrite an experiment's
original hypothesis after observing the result. Append evidence and conclusions
so the learning remains visible.

The cross-experiment [`lesson-design-audit.md`](lesson-design-audit.md) records
which causal relationships are already legible in their artifacts, which were
improved, and which rejected experiments should remain deliberately unbuilt.

Current experiments:

- [`EXP-001-model-feasibility.md`](EXP-001-model-feasibility.md) — rejected
  character-level candidate.
- [`EXP-002-token-model-feasibility.md`](EXP-002-token-model-feasibility.md) —
  supported floating-point and integer token model.
- [`EXP-003-training-data-bias.md`](EXP-003-training-data-bias.md) — controlled
  fan-corpus and ordering-bias demonstration.
- [`EXP-004-complete-6809-training.md`](EXP-004-complete-6809-training.md) —
  complete bit-exact assembly training, generation, and initial timing evidence.
- [`EXP-005-prompted-marketing-language.md`](EXP-005-prompted-marketing-language.md)
  — expanded advertising vocabulary and visible two-word prompting.
- [`EXP-006-pretrained-tab-completion.md`](EXP-006-pretrained-tab-completion.md)
  — partially supported 8 KiB pretrained completion prototype; its original
  quality gate failed, but its task-level usefulness and runnable UI make the
  failure presentable.
- [`EXP-007-all-ram-sentence-completion.md`](EXP-007-all-ram-sentence-completion.md)
  — runnable 32 KiB all-RAM, punctuation-aware completion experiment; physical
  hardware evidence remains outstanding.
- [`EXP-007-epoch-sweep.md`](EXP-007-epoch-sweep.md) — side experiment showing
  that training loss keeps falling after held-out Q2.2 quality peaks.
- [`EXP-008-adaptive-opponent.md`](EXP-008-adaptive-opponent.md) — rejected
  adaptive-opponent experiment. On three recorded human sessions a ninety-byte
  order-1 frequency table predicts a live player better than every neural
  candidate, so the declared null result triggered and the 6809 port was not
  attempted.
- [`EXP-009-four-voice-music.md`](EXP-009-four-voice-music.md) — four-voice
  software synthesizer for a stock CoCo 1, built as the performer for a
  possible tracker-generation direction. Records why the HSYNC interrupt
  cannot drive an audio sample clock on this machine.
- [`EXP-010-melody-continuation.md`](EXP-010-melody-continuation.md) — planned
  experiment in which the audience enters an opening bar and the CoCo composes
  and performs a continuation. Melody is scale degrees conditioned on mode,
  metre, beat and chord, so a wrong note is impossible by construction.
  Records corpus vetting, including one dataset whose licence forbids LLM
  training. Phase A passed: the model beats the strongest table by 0.243
  bits per row, and situational context supplies most of that.
- [`EXP-011-contextual-associative-recall.md`](EXP-011-contextual-associative-recall.md)
  — supported reference experiment in content-addressed key-value attention.
  A 160-parameter head recalls 100% of novel contextual bindings across two
  data batches and ten seeds after Q4.4 quantization. Its fixed-point 6809
  inference and guided facts/answer/context UI pass direct and real-ROM
  emulator gates. A slow attention replay is available as optional depth;
  physical hardware remains unverified.
- [`EXP-012-episode-titles.md`](EXP-012-episode-titles.md) — corpus study for a
  proposed multi-model game. All 79 Star Trek TOS episode titles pulled and
  measured: 259 words needing a 180-token vocabulary, 91% of it used once, and
  only two adjacent word pairs repeating anywhere in the corpus. Fits the
  machine easily at under 3 KiB; supports memorization rather than
  generalization. A working fake-title generator follows from that: a
  400-byte frame model plus a tagged noun table, 3,874 bytes in total,
  agreeing with the Mac on all 512 screen cells. Its training is capped at
  eleven epochs by 16-bit logit accumulation, which visibly costs style.
- [`EXP-013-rpsls-opponent.md`](EXP-013-rpsls-opponent.md) — a playable RPSLS
  opponent that learns the rules and its player at once, in 2,217 bytes on a
  stock CoCo 1. Board and behaviour are both verified against the reference:
  512 cells in three states, and 38 scripted rounds of identical choices. It
  starts from EXP-008's null result rather than from a model: a 75-byte table
  conditioned on the last move and the last outcome scores 80.0% against six
  declared synthetic players, beating tables six times its size, and replicates
  EXP-008's secondary hypothesis that situation beats history. A recorded
  200-round human session then scored it at **52.8%**, a coin flip: it reads a
  person better than chance at 3.3 sigma but not nearly well enough to win.
  The synthetic average was an artifact of a player set in which five of six
  had exploitable habits.
- [`EXP-014-6309-multiplier.md`](EXP-014-6309-multiplier.md) — the 6309
  multiplier benchmark: the same 58,000 multiplications three ways, measured
  on the physical CoCo 3. Native mode alone is 1.17x; MULD is 1.54x.
- [`EXP-015-faster-clock-listening-test.md`](EXP-015-faster-clock-listening-test.md)
  — the faster-clock listening test: the EXP-009 player at 5.7, 11.4 and a
  predicted 14.4 kHz on the CoCo 3, to hear what sample rate buys before
  any 6309 rewrite of the loop. Heard on the CoCo 3 through the 1703 on
  2026-09-06: the higher rates were audibly better, the drum track most of
  all, and the melody voice's warble found there is what EXP-018 tests.
  Pitch and length were not recorded. Found and fixed the standalone
  player's missing row hook.
- [`EXP-016-register-resident-loop.md`](EXP-016-register-resident-loop.md) —
  the register-resident loop: rejected by arithmetic before building. The
  best 6309 register rewrite of the sample loop saves six percent, and the
  work showed that the mask, not the phase, is where a tone voice's cycles
  go.
- [`EXP-017-wavetable-voices.md`](EXP-017-wavetable-voices.md) — the
  wavetable voices: each tone voice's masked bit replaced by a table lookup
  at the same cost, so a triangle or a sine where there was a square. Bit-
  exact against its reference, a square-table build reproduces EXP-009's
  player, four builds run to the end under XRoar with hostile RAM. Heard
  on the 1703 on 2026-09-06: the square was preferred, so the CoCo 1
  player keeps it and the wavetable stays as a verified capability. Found
  a second uninitialised cell in the frozen player, its tempo.
- [`EXP-018-steady-sample-clock.md`](EXP-018-steady-sample-clock.md) — the
  steady sample clock: the tune compiled into an event stream and applied
  one byte per sample through a path padded to cost what idling costs, so
  the sample clock never stretches. Tests whether the 8 Hz warble heard on
  the melody voice is the row-change stall EXP-009 accepted. Costs a fifth
  of the rate. Supported on the CoCo 3 on 2026-09-06: the warble is gone
  and the steady build is preferred.

## Presentation commands

List the audience-ready paths, beginning with the first complete 6809 run:

```sh
make present
```

Run any presentation experiment:

```sh
make present EXP=4
make present EXP=5
make present EXP=6
make present EXP=7
make present EXP=11
```

EXP-004 launches the stock-rate-limited XRoar program and pauses before
inference.
EXP-005 launches its own XRoar program, pauses after training, and provides an
interactive six-prompt workbench. Its larger training workload has not yet
been timed on physical stock-rate hardware. EXP-006 and EXP-007 launch
pretrained completion workbenches; say explicitly that the Mac trained their
weights and the CoCo performs integer inference.
EXP-011 launches a guided context-editing demonstration. Its Mac-trained
160-byte head runs fixed-point scoring on the CoCo. A person edits Lisa's value
from `CODE 2` to `CODE 6` in context RAM while the model weights are visibly
locked, then asks the same question again. `V` optionally replays the stored
scores at presentation speed.

EXP-013 is the one to play rather than watch. The opponent starts knowing
neither the rules nor the player, and two counters carry the lesson: `RULES
n/25` for the game, which it learns quickly and never completes, and `MEMORY
n/rounds` for the person, which never finishes at all. `R` empties both in
front of the audience - EXP-008's falsifiability key - and the machine has to
climb back. Say out loud that where `RULES` stops is a measure of how varied
the player is, and quote the human number: 52.8% against a player who is
trying, against 80% for the synthetic players with habits. It reads a person
better than chance, and not nearly well enough to win.

| Experiment | Useful when the conversation asks… | Surface |
| --- | --- | --- |
| EXP-004 | Can the old machine really train it? | Interactive CoCo emulation |
| EXP-005 | Can starting words steer it? | Interactive prompted CoCo |
| EXP-006 | Can a pretrained model save typing? | 8 KiB completion workbench |
| EXP-007 | What changes with more memory and punctuation? | 32 KiB all-RAM |
| EXP-011 | Can it use a fact supplied right now? | Context-attention bench |
| EXP-012 | Can it make up something that reads? | Screen of fake episode titles |
| EXP-013 | Can it learn a game, and learn me? | Playable RPSLS opponent |

EXP-001 through EXP-003 remain recorded as architectural evidence, but are no
longer in the runnable presentation menu. Presenter output deliberately shows
conclusions rather than dumping every sample. The recorded evidence remains
available for deeper inspection. The menu labels EXP-006, EXP-007, and EXP-011
as emulator demonstrations until physical keyboard behaviour and stock-rate
latency are measured.
