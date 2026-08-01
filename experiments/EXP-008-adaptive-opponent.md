# EXP-008: Adaptive opponent

## Status

**Closed as not supported.** The declared null result triggered on real human
data: a ninety-byte order-1 frequency table predicts a live player better than
every neural candidate, on all three recorded sessions, including when scored
over genuine movement only.

Phase A failed its synthetic gate at 2 of 5 structured players. Phase A-bis
recorded three human sessions and settled the blocking question against the
model. Phases B, C, and D were not attempted; the adaptive opponent should not
be driven by the neural model.

The reference implementation, synthetic players, baselines, prequential
harness, capture tool, and replay tool all exist and pass their tests. The
evidence is reproducible with `make exp008-sweep` and `make exp008-replay`.

Nothing here affects EXP-004 through EXP-007.

## Question

Can a stock CoCo 1 train a next-token model online, from random weights, on a
live player's input stream, and use its predictions to drive an opponent that
measurably improves within one minute of play, while sustaining a playable
frame rate?

## Hypothesis

An additive fixed-point model of no more than 1,024 parameters, trained online
with the EXP-004 stochastic gradient engine, will predict a player's next move
token with top-one accuracy materially above both a uniform-random baseline and
a memory-matched frequency-table baseline, within 600 decision ticks, while
consuming no more than 25% of the CoCo 1 cycle budget at a 10 Hz decision tick.

A secondary hypothesis concerns context design. Situational context — bearing
to the opponent, range bucket, and the last three moves — will outperform
history-only context on synthetic players whose behaviour depends on opponent
position. Both layouts use five context positions and the same vocabulary, so
the comparison isolates what occupies the context slots.

## Null result to respect

If a memory-matched frequency table matches the model within the declared
margin across all synthetic players, the honest conclusion is that the model is
not earning its multiplier for this task. `research/model-design.md` already
records that a token-to-token table "would be even smaller, but would barely
exercise the multiplier and would omit learned representations." This
experiment must be willing to report that outcome rather than presenting a
model where a table would do.

## Why this is a separate experiment

EXP-004 through EXP-007 share four properties that EXP-008 breaks:

1. Training data is a fixed corpus authored in advance. Here it is generated at
   run time by a human.
2. The model has the machine to itself. Here it shares a cycle budget with a
   real-time game loop.
3. Model output drives display. Here it drives opponent behaviour.
4. The prediction target is stationary. Here the player adapts in response to
   the opponent, so the target moves while the model chases it.

The fourth property is the most technically interesting and the least
precedented in this repository. Online stochastic gradient descent with no
optimizer state forgets at a rate set by the learning rate, which may or may
not track a human who is actively trying to become unpredictable.

EXP-008 reuses the EXP-004 training engine rather than the EXP-006 and EXP-007
inference cores, because live training is the entire point.

## Token design

Move tokens, emitted once per decision tick:

```text
N  NE  E  SE  S  SW  W  NW  IDLE
```

Situational tokens:

```text
B0 B1 B2 B3 B4 B5 B6 B7    bearing sector from player to opponent
NEAR  MID  FAR             range bucket
```

The complete vocabulary is 20 tokens. The player does not fire in this design,
so no action token is required. The opponent fires; the player dodges.

## Context layouts under comparison

Both layouts use five context positions and predict the next move token.

| Layout | Position 0 | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- | --- |
| H (history) | move t-5 | move t-4 | move t-3 | move t-2 | move t-1 |
| S (situational) | bearing | range | move t-3 | move t-2 | move t-1 |

Position-dependent embeddings mean each position carries an embedding row for
every vocabulary entry, including entries that can never appear there. This
wastes roughly 60% of the embedding table in Layout S. The waste is accepted
because it keeps the architecture bit-identical to the engine already built and
tested, and because the absolute parameter count remains small.

## Candidate sizes

Using the established formula `parameters = V × (E × (C + 1) + 1)` with `V=20`
and `C=5`:

| Embedding | Parameters | Master bytes | Scoring multiplies |
| ---: | ---: | ---: | ---: |
| 4 | 500 | 1,000 | 80 |
| 6 | 740 | 1,480 | 120 |
| 8 | 980 | 1,960 | 160 |
| 10 | 1,220 | 2,440 | 200 |

The declared ceiling of 1,024 parameters admits embedding widths up to 8. The
sweep will select the smallest candidate whose accuracy is within one
percentage point of the best, matching the selection rule used in EXP-007.

## Projected cycle budget

These are projections from a nominal 35 cycles per signed 8×8 multiply-
accumulate in a 6809 loop, not measurements. They exist to establish whether
the experiment is worth starting, and must be replaced by measured counts in
Phase B.

| Operation | Multiplies | Projected cycles | Projected ms |
| --- | ---: | ---: | ---: |
| Forward prediction (E=6) | 120 | 4,200 | 4.7 |
| Training step (E=6) | ~360 | 12,600 | 14.2 |
| Combined per decision tick | — | ~16,800 | ~18.9 |

At a 10 Hz decision tick this projects to roughly 19% of the 890,000-cycle
second. The declared gate is 25%.

Total weight storage at E=6 is 1,480 bytes of 16-bit master parameters plus
compact forward operands. The complete image is expected to fit a stock 32 KiB
CoCo 1 with no all-RAM memory map, making EXP-008 simpler to load than EXP-006
or EXP-007.

## Baselines

Four baselines, in increasing strength:

1. **Uniform** — uniform random over nine move tokens. 11.1% expected top-one.
2. **Marginal** — always predict the player's most frequent move to date.
3. **Bigram table** — most frequent move following the last move. 81 counter
   bytes.
4. **Trigram table** — most frequent move following the last two moves. 729
   counter bytes.

The trigram table is the honest comparison. At 729 bytes it occupies
approximately the same memory as the 740-parameter model, so any advantage the
model shows must come from generalization rather than capacity.

Layout S has no practical table equivalent. Tabulating eight bearings by three
range buckets by three moves of history requires 8 × 3 × 9³ = 17,496 contexts.
That the model can condition on situational context at all, within 1,480 bytes,
is the specific claim generalization is meant to support. If Layout S wins,
this is why.

## Synthetic players

Phase A needs deterministic, seeded opponents so that results are reproducible
and testable without a human. Six scripted policies:

| Policy | Behaviour | Expectation |
| --- | --- | --- |
| `RANDOM` | Uniform over nine moves | Negative control. No method should beat uniform. |
| `ZIGZAG` | Fixed repeating pattern with noise | Bigram should do well. Model should match, not exceed. |
| `CIRCLE` | Circle-strafe around the opponent | Needs bearing. Layout S should win. |
| `FLEE` | Always move directly away | Pure function of bearing. Layout S should win decisively. |
| `PANIC` | Flee when NEAR, wander when FAR | Needs bearing and range together. |
| `HABIT` | 70% continue, 20% turn, 10% random, biased away | Closest available proxy for a human. |

`RANDOM` is not optional. If any method appears to beat uniform on a genuinely
uniform player, the harness is measuring something other than what it claims.

## Phase A gates: Mac reference

Proceed to 6809 assembly only if all hold:

- the model exceeds the best table baseline by at least five percentage points
  of top-one accuracy on at least three of the five structured players;
- the model does not exceed the uniform baseline beyond sampling noise on
  `RANDOM`;
- the selected layout and embedding width fit within 1,024 parameters;
- every reachable quantized context vector stays within signed 8-bit range;
- the reachable score range fits the declared accumulator width;
- accuracy converges within 600 decision ticks from random initialization.

The context-magnitude and score-range gates carry forward unchanged from
EXP-007, where they were the constraints that made fixed-point inference safe.

## Phase A result

Run it:

```sh
make exp008-sweep
```

The implementation lives in `src/reference/duel_arena.py` and
`src/reference/mimic_lm.py`, with the sweep in `tools/run_exp_008.py`.

### Selected candidate sizes

Separating input and output vocabularies made every candidate smaller than the
plan projected. Only the nine move tokens are ever predicted, so the output
layer has nine rows rather than twenty.

| Layout | Embedding | Parameters | Master bytes | Prediction multiplies |
| --- | ---: | ---: | ---: | ---: |
| History | 6 | 333 | 666 | 54 |
| History | 8 | 441 | 882 | 72 |
| Situational | 6 | 663 | 1,326 | 54 |
| Situational | 8 | 881 | 1,762 | 72 |

Prediction costs 54 to 72 multiplies rather than the 120 projected, because
prediction skips the softmax and ranks nine outputs instead of twenty.

### Headline measurements

Five seeds, 600 ticks per run, scoring the final 200 ticks prequentially. Each
figure is the best method of its kind, averaged across seeds.

| Player | Uniform | Best table | Best model | Margin |
| --- | ---: | ---: | ---: | ---: |
| `RANDOM` | 11.1% | 13.8% | 12.1% | -1.7pp |
| `ZIGZAG` | 11.1% | 82.2% | 90.1% | +7.9pp |
| `CIRCLE` | 12.4% | 81.1% | 89.2% | +8.1pp |
| `FLEE` | 10.6% | 82.1% | 85.8% | +3.7pp |
| `PANIC` | 9.8% | 58.9% | 56.0% | -2.9pp |
| `HABIT` | 11.5% | 68.0% | 57.1% | -10.9pp |

| Gate | Result |
| --- | --- |
| Beats best table by 5pp on three of five structured players | **FAIL** (2/5) |
| Does not beat uniform on `RANDOM` beyond noise | PASS (+1.0pp) |
| Largest candidate within 1,024 parameters | PASS (881) |
| Context magnitude within signed byte | PASS (61 of 127) |
| Score range within accumulator width | PASS (-1,694 to 2,013) |

### The result splits along a clean line

The model wins where prediction requires generalizing across situations, and
loses where a short move history is directly sufficient.

`CIRCLE` and `FLEE` condition on bearing, and the situational layout beat every
table. `ZIGZAG` is a long fixed pattern, and the model beat even an order-2
table with backoff. `HABIT` is 70% "repeat the last move", which an order-1
table of 90 bytes captures immediately and gradient descent must discover, so
the 666-byte model lost to it by 10.9 points.

This is the theoretically expected shape rather than a surprise. The learned
representation buys generalization and buys nothing when the task is
memorizing a small table. Recording it that way is more useful to the
presentation than a result where the model simply wins.

The situational layout was the better of the two on four of the five
structured players, which supports the secondary hypothesis even though the
primary gate failed.

### Diagnosis: convergence rate, not capacity

Two follow-up sweeps distinguish the two explanations. Neither changes the
synthetic players, because tuning the task until the model wins would destroy
the evidence.

Extending each run from 600 to 2,400 ticks passes the gate at 3/5, and moves
every losing player toward the model: `FLEE` +3.7 to +6.8pp, `PANIC` -2.9 to
+0.7pp, `HABIT` -10.9 to -2.1pp. The model therefore has enough capacity; it
does not have enough time.

Raising the learning rate does not recover that time. Sweeping the update shift
across 1/16, 1/8, and 1/4 at 600 ticks leaves the gate failing at 2/5, with
`FLEE` reaching only +4.9pp and `HABIT` still at -8.1pp.

Since 600 ticks is 60 seconds at a 10 Hz decision tick, and 2,400 ticks is four
minutes, the hypothesis as written — measurable improvement within one minute —
is not supported by this evidence.

### Two methodology notes worth keeping

The `RANDOM` negative control earned its place twice.

On its first run every method scored 100% on a uniformly random player. The
uniform baseline had been given the same `XorShift16` seed as the synthetic
player, and that generator's 16-bit state has a single orbit, so the "baseline"
was replaying the player's own draws in lock-step. The control caught a harness
fault before it could produce a publishable number. The baseline now uses an
independent generator and is documented as a measurement device rather than a
6809 candidate.

On the learning-rate sweep the control failed at +2.3pp against a 2pp limit.
That sweep compares 27 model candidates instead of 9, and reporting the best of
a larger pool inflates the apparent maximum on pure noise. The inflation is the
finding, not a model property. Any future sweep that widens the candidate pool
must either hold the control's limit fixed and expect it to trip, or select a
candidate before scoring it.

### Conclusion and next step

Phase A does not support the hypothesis. The blocking uncertainty has changed
shape: it is no longer whether the model can learn a move stream, but whether a
*human* move stream looks more like `HABIT`, where a 90-byte table wins, or
more like `CIRCLE` and `FLEE`, where the model wins by roughly eight points.

That distinction cannot be settled by more synthetic players. It is an
empirical question about people, and the synthetic players were authored by the
same person who wants the model to win, which is exactly the bias the evidence
loop exists to catch.

The recommended next step is a Mac-side capture tool that records a real person
dodging a chaser at 10 Hz, then replays that stream through the identical
harness and predictors. It is small, it needs no 6809 work, and it converts the
central open question from inference to measurement. Open question 1 was
already the top of the list before Phase A ran; the result promotes it to the
blocking item.

Porting to 6809 assembly is deliberately not the next step. A bit-exact port of
a model that loses to a 90-byte table against the best available human proxy
would be effort spent ahead of its evidence.

## Phase A-bis: human capture

The tooling to answer the blocking question exists and is tested. No human
sessions have been recorded yet, so no result is claimed.

Record a session:

```sh
make exp008-capture LABEL=stacey-01
```

Score every recorded session:

```sh
make exp008-replay
```

### Protocol

Each session is roughly three minutes, 1,800 ticks at 10 Hz. That covers both
the 600-tick demonstration budget and the 2,400-tick figure at which the
synthetic gate passed, so one recording answers both questions.

The chaser moves at half the player's speed and ends the run on contact. A
threat with no consequence produces idle wandering rather than evasion, and
idle wandering would answer a question nobody asked.

Three properties of the capture are deliberate and must not be relaxed:

**The capture is blind.** No prediction is computed, displayed, or used to
steer the chaser. A visible ghost would record a human reacting to a
predictor, when the question is whether unaided human movement is predictable
at all. The ghost belongs to Phase C.

**The keyboard is polled as held state**, at the tick rate, rather than
consumed as an event stream. That is what the CoCo does when it scans its
keyboard matrix, so the recorded signal has the same shape as the signal the
6809 would eventually see.

**Only moves are stored.** Bearings and ranges are regenerated on replay by
the same deterministic arena the predictors were measured against. The
geometry therefore has one implementation rather than one for the recorder and
another for the analysis.

Predictor state persists across runs within a session while the arena resets,
because a player keeps learning across deaths and so should anything
predicting them.

### One difference from Phase A, recorded rather than corrected

Phase A streams ran a fixed 600 ticks with a pinned chaser sitting adjacent
indefinitely. Captured runs end at contact instead. Human sessions will
therefore spend less time in the `NEAR` range bucket than the synthetic
streams did.

Phase A's recorded numbers are left untouched rather than regenerated under
the new rule, and `Arena.is_caught` is not called anywhere in the synthetic
path. The comparison that matters is within a single stream — model against
table on the same data — so it stays internally valid. The synthetic figures
are context, not the control.

### Capture dependency

The capture tool uses `pygame-ce`, added to the dev dependency group. Nothing
the CoCo runs depends on it.

`pygame-ce` rather than upstream `pygame` for a concrete reason. Upstream
pygame 2.6.1 publishes no wheel for Python 3.14, so `uv` builds it from source,
and that source build silently omits the compiled font extension when SDL_ttf
is absent. The result is a package that imports, reports a version, and then
raises `NotImplementedError` the first time it renders text. `pygame-ce` 2.5.7
ships a current wheel and works as delivered.

The tool also tolerates a missing font module rather than refusing to start,
falling back to a drawn progress bar, and saves whatever ticks it captured if
the loop raises partway through. Both exist because a recording session costs a
person three minutes of their attention, and losing that to a tooling fault is
worse than losing the status text.

### Sample size

One session is one person on one day. The replay tool prints an explicit
caution below three distinct participants, because "Stacey looked like `HABIT`"
and "humans look like `HABIT`" are different claims and only the first is
supported by a single recording.

Within-person variation matters too. Several short sessions across different
days are more informative than one long session, since a player who has just
worked out that circling the wall is safe is no longer the player who started.

## Phase A-bis result: the null result triggers

Three sessions were recorded on 2026-07-31 and 2026-08-01, all by Stacey,
1,800 ticks each at 10 Hz, 5,400 ticks total. Scoring the final 200 ticks of
each session across three model seeds:

| Session | Runs | Best table | Best model | Margin |
| --- | ---: | ---: | ---: | ---: |
| `stacey-01` | 7 | 73.0% | 74.5% | +1.5pp |
| `stacey-02` | 3 | 84.5% | 84.5% | +0.0pp |
| `stacey-03` | 1 | 91.5% | 89.0% | -2.5pp |

Mean margin -0.7pp. The model clears the declared 5pp gate on 0 of 9 scored
runs. The winning table on every session is `table/order1`: **ninety bytes of
counters, predicting from the single previous move.**

The best model configuration costs 1,762 bytes of 16-bit masters, 72 multiplies
per prediction, and roughly 216 more per training step. It loses to ninety bytes
and no multiplier at all.

This is the null result the experiment declared in advance, confirmed on real
data rather than synthetic. `research/model-design.md` recorded the concern that
a token-to-token table "would be even smaller, but would barely exercise the
multiplier." For this task, against this player, the concern was correct.

### The result is not an artifact of standing still

21% of captured ticks are `IDLE`, and pressing nothing is trivially
predictable, so the comparison was re-scored over only those ticks whose target
is a real move.

| Session | Table, moving only | Best model, moving only |
| --- | ---: | ---: |
| `stacey-01` | 74.5% | 72.3% |
| `stacey-02` | 89.1% | 87.8% |
| `stacey-03` | 90.8% | 87.8% |

The ordering is unchanged. The table wins on genuine movement, not on idleness.

### Why the table wins

The captured streams repeat the previous move 84.2% of the time, or 80.5%
excluding `IDLE` to `IDLE`. The `HABIT` synthetic player, written as the
closest available proxy for a human, repeats only about 70%.

Real movement here is *more* first-order predictable than the proxy built to
imitate it. An order-1 table is close to optimal for a process that nearly is
order-1, it reaches that optimum by counting rather than by descending a
gradient, and it needs ninety bytes to do it. The model has nothing left to
generalize across, so its one advantage does not apply.

The model is not failing to learn. It lands within 2 to 3 points of the table
on every session. It is solving a problem that does not need solving.

### Skill made the player more predictable, not less

The three sessions show a strong within-person trend. Runs survived per session
went 7, then 3, then 1 — the third session was never caught across all 1,800
ticks. Over the same progression, best-table accuracy rose from 73.0% to 84.5%
to 91.5%.

Getting better at evading made the movement *more* regular, presumably by
settling into an efficient orbit. This is the opposite of the assumption behind
the design, which expected a skilled player to defeat prediction by becoming
erratic.

It also means the three sessions are not three samples of one behaviour. They
are three different behaviours from a player who was still learning the game,
which is a further reason not to read them as a stable estimate.

### Limits of this evidence

One person, three sessions, one evening. This says what Stacey's movement looked
like while she was learning this specific arena. It does not establish what
human movement looks like in general, and a novice, a child, or someone playing
with a joystick could differ.

That limitation does not rescue the result. To overturn it, some other player
would have to be *both* substantially less first-order predictable *and*
predictable in a way that situational context captures. The first alone would
lower every method's accuracy without changing their order.

### Conclusion

The adaptive opponent should not be driven by the neural model. For this task a
ninety-byte order-1 frequency table is faster to converge, cheaper to run,
twenty times smaller, and more accurate.

EXP-008 is closed as not supported. Phases B, C, and D are not attempted, and
the Phase B and C gates below stand as the unexercised plan they were.

Nothing here affects EXP-004 through EXP-007. Those demonstrations stand on
their own evidence; this experiment tested a new claim and the claim failed.

The presentation consequence is a decision for Stacey rather than a technical
one, and is recorded in "Presentation integrity" above as still open. The
finding is genuinely presentable — a measured demonstration that a lookup table
beats a neural model at a bounded job is well aligned with the project's stated
conclusion of neither fear nor hype — but choosing to present it that way is not
the same as the experiment having succeeded, and this document should not blur
the two.

## Phase B gates: bit-exact 6809

- Reference and assembly implementations produce identical parameters after a
  fixed scripted input sequence.
- Reference and assembly produce identical top-one predictions at every tick of
  that sequence.
- Forward and backward cycle counts are measured, not projected.
- Combined model cost at a 10 Hz decision tick is at or below 25%.

## Phase C gates: playable duel

Scope is a minimal duel. Player block, opponent block, projectile, arena
boundary. Survive the clock. No rounds, no levels, no sound.

Required features:

- a visible ghost marker showing where the model predicts the player will be;
- a running prediction-accuracy readout;
- a weight-reset key;
- sustained frame rate at or above 10 fps with model, game, and rendering
  active.

The reset key is not a convenience. It is the falsifiability demonstration.
Pressing it re-randomizes the weights, the ghost immediately becomes wrong, the
accuracy readout collapses, and the audience watches it climb again. Without
it, an audience cannot distinguish a model that learned from a difficulty curve
that ramped. It must be treated as a required feature and exercised in the
demonstration, not left as an option.

## Display decision

Semigraphics-4 through the existing text-screen path at `$0400`, giving a
64 × 32 block arena.

This is a deliberate choice against PMODE bitmap graphics. SG4 needs a handful
of byte writes per frame, no page flipping, and no new display code, because
`screen.asm` already targets that memory. The CPU budget then belongs almost
entirely to the model, which is the part of this experiment carrying the
evidence. A blocky arena is adequate for a duel between two markers and a
projectile.

## Input decision

Keyboard first, through the existing `POLCAT` path. Direction keys quantize to
move tokens directly, and the ROM-safe adapter patterns from EXP-007 already
exist if the memory map ever changes.

An analog joystick would suit the era better and would give finer control, but
it adds PIA and ADC polling, quantization tuning, and a hardware dependency at
a venue. It is deferred behind a build flag until the model evidence is
settled.

## Presentation integrity

Stacey has decided that EXP-008 becomes the finale of the talk rather than a
clearly separated appendix.

This requires an amendment to `AGENTS.md`, which currently reads: "The
sustained example is a model learning vintage-computer names. Return to it
throughout the presentation rather than introducing unrelated AI examples."

The proposed framing is that the vintage-computer-names corpus remains the
spine through which the mechanism is taught, and the adaptive opponent is the
same engine with a different token stream. The teaching point is continuous
rather than divided: the model learns that `SW` plausibly follows `W` without
knowing what a joystick is, exactly as it learns that `AMIGA` plausibly follows
`COMMODORE` without knowing what a computer is. The mechanism does not care
what the tokens mean, and demonstrating that twice on different data is a
stronger claim than demonstrating it once.

The existing distinctions must survive the change. In particular, an opponent
that predicts a player is still not an opponent that understands a player, and
the accuracy readout must be described as next-token accuracy over a five-token
context rather than as strategy, reading, or intent.

The `AGENTS.md` amendment is not yet applied. It should be made deliberately
once the framing above is accepted.

## Open questions

1. Does a human token stream carry enough structure to learn inside 60 seconds,
   or do people randomize more than any of the synthetic players?
2. Is 10 Hz the right decision tick? A slower tick cuts cost and yields a
   cleaner token stream; a faster one makes the opponent feel more responsive.
3. Does displaying the ghost prediction make the game better or worse? It makes
   the demonstration honest, but it also tells the player exactly how to
   defeat the model.
4. How does the model behave against a non-stationary target? The player adapts
   to the opponent adapting to them. Is a fixed 1/16 learning rate fast enough
   to track that, and does the resulting feedback loop stabilize or oscillate?
5. What is the honest way to display accuracy? A running percentage invites
   comparison against a baseline the audience cannot see.

## Relationship to prior experiments

| Experiment | Supplies |
| --- | --- |
| EXP-004 | The online SGD training engine, fixed-point format, and bit-exactness discipline |
| EXP-003 | The precedent for controlled comparison between models differing in one input property |
| EXP-007 | The context-magnitude and score-range gate methodology |

EXP-008 supplies nothing back to EXP-004 through EXP-007. It is additive, and
if it fails its gates the existing presentation is unaffected.
