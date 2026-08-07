# EXP-013: An RPSLS opponent that learns a player

## Status

**Set up; blocking question answered on synthetic players only.** A 75-byte
frequency table conditioned on the player's last move *and* the last round's
outcome scores 80.0% against six declared synthetic players, beating every
other table tried, including ones six times its size. No human has played it
yet, and nothing has been written for the 6809.

```sh
make exp013-sweep
```

Reproduces the table below.

## Why this does not start with a model

EXP-008 asked whether a stock CoCo can train a next-token model online on a
live player's input stream and use it to drive an opponent. It closed as **not
supported**: a ninety-byte order-1 frequency table predicted better than every
neural candidate, on all three recorded human sessions, including when scored
over genuine movement only. Its own words: "An order-1 table is close to
optimal for a process that nearly is order-1; it reaches that optimum by
counting rather than by descending a gradient."

That result is about predicting a human's next discrete move, which is exactly
what this game needs. Building a neural RPSLS opponent without first beating a
table would be repeating a settled experiment.

Three things differ, and only the third is in the model's favour:

| | EXP-008 | EXP-013 |
| --- | --- | --- |
| Target | player moving through an arena | player choosing against a chooser |
| Cycle budget | shared with a 10 Hz game loop | turn-based, no pressure |
| Context that matters | bearing, range, last three moves | last move, last **outcome** |

The second removes one of EXP-008's four breaking properties. The first makes
the target *more* adversarial, not less. The third is the interesting one, and
it is a direct restatement of EXP-008's secondary hypothesis — that situational
context beats history-only context when behaviour depends on the situation.

## Declared null result

Inherited from EXP-008 and restated: **if a memory-matched frequency table
matches any model built later within 5 percentage points of score across the
declared players and the recorded human sessions, the model is not earning its
multiplier and should not ship.** This experiment must be willing to conclude
that a 75-byte table is the whole answer.

## Measurements, 2026-08-04

300 rounds per pairing, five moves. Chance accuracy 20%, chance score 50%.
Cells read `accuracy / score`: how often the predictor named the next move, and
the opponent's actual round win rate counting a tie as a half. Score is what a
person feels, and it is not the same number — a predictor can be right often
and still be countered.

| player | order-0 (5 B) | order-1 (25 B) | order-2 (125 B) | **order-1+outcome (75 B)** | backoff (155 B) |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 23.3 / 49.7 | 19.7 / 47.5 | 26.3 / 48.5 | 22.7 / 49.8 | 26.0 / 47.8 |
| cycle | 20.0 / 50.0 | 98.7 / 99.2 | 98.3 / 99.0 | 97.7 / 98.5 | 98.7 / 99.2 |
| favourite | 69.7 / 80.0 | 69.3 / 79.7 | 68.3 / 79.2 | 69.3 / 79.7 | 68.0 / 78.8 |
| win-stay | 11.7 / 56.0 | 91.0 / 96.5 | 80.3 / 92.2 | **97.3 / 98.3** | 58.7 / 82.5 |
| never-repeat | 21.7 / 54.0 | 27.3 / 57.2 | 30.3 / 56.3 | 21.7 / 56.2 | 29.7 / 56.3 |
| reactive | 12.7 / 13.7 | 47.3 / 49.2 | 65.3 / 73.3 | **91.7 / 97.5** | 35.3 / 60.2 |
| **mean score** | 50.6% | 71.5% | 74.8% | **80.0%** | 70.8% |

`backoff+outcome` was also tried: 79.0% for 465 bytes. Bigger and worse.

### What the table says

**Outcome conditioning is the whole gain, and it is cheap.** Adding the
previous round's result to an order-1 context costs 50 bytes and moves the mean
from 71.5% to 80.0%. Going to order-2 instead costs 100 bytes and moves it to
74.8%. More history is the wrong direction; more *situation* is the right one.
This replicates EXP-008's secondary hypothesis on a task where the situation is
a single trit.

**The gain lands exactly where it should.** `win-stay` and `reactive` are the
two players whose behaviour depends on the previous round, and they are the two
where outcome conditioning is decisive — reactive goes from 49.2% (a draw) to
97.5%. Every other player is unchanged within noise. A predictor that improved
everywhere would be suspicious; one that improves precisely on the players it
was reasoned about is doing what it claims.

**Nothing beats `random`.** All seven sit within noise of 50%. That is the
correctness check, not a disappointment: RPSLS has a Nash equilibrium at
uniform play, and a predictor that beat a uniform player would be reading its
own generator. It did, once — the first run scored a uniform *predictor* at
100% against a uniform *player*, because both drew from the same seed.

**`never-repeat` is the hardest realistic opponent** at 56%, and it is what
people actually do when told to be unpredictable. A human who genuinely
randomizes cannot be beaten; the demo's honesty depends on saying so.

## Learning the rules too (2026-08-04)

Everything above hands the machine `counter()` — it guesses your move and
plays the known answer. That is an opponent that has read the rulebook. Stacey
asked for one that has not: it makes a move, sees what happened, and works out
the game the same way a person does.

That makes two things learnable at once, and they behave nothing alike:

| | rules | opponent |
| --- | --- | --- |
| size | 25 cells | 15 contexts × 5 |
| stationary? | yes, permanently | no, adversarial |
| evidence rate | one cell per round | one count per round |
| learnable to certainty? | yes | no |

The agent keeps a 25-byte outcome table (`unknown / loss / tie / win`) beside
the 75-byte opponent table — **100 bytes in total** — and picks the best move
against its predicted throw, preferring a *known win*, then an *unseen cell*,
then a known tie. Exploration is not a separate mode: an unseen cell simply
outranks a tie.

Score per 25 rounds, 150 rounds total:

| player | agent | 1-25 | 26-50 | 51-75 | 76-100 | cells known |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| cycle | knows rules | 82% | 100% | 100% | 100% | 25/25 |
| cycle | **learns rules** | 64% | **100%** | 100% | 100% | **13/25** |
| win-stay | knows rules | 80% | 100% | 100% | 100% | 25/25 |
| win-stay | **learns rules** | 56% | **100%** | 100% | 100% | **13/25** |
| reactive | knows rules | 86% | 86% | 98% | 100% | 25/25 |
| reactive | **learns rules** | 76% | **100%** | 100% | 100% | **8/25** |
| favourite | knows rules | 78% | 84% | 86% | 76% | 25/25 |
| favourite | **learns rules** | 74% | 82% | 82% | 72% | **7/25** |
| random | either | ~50% | ~50% | ~50% | ~50% | 16-25/25 |

### Three things this says

**Not knowing the rules costs one block.** By rounds 26-50 the learner has
caught the rulebook-reading opponent on every structured player, and on
`reactive` it is ahead — 100% against 86%. The whole price of ignorance is paid
in the first twenty-five rounds, where it drops 10-24 points.

**It never learns the whole game, and does not need to.** Against `favourite`
it reaches 86% knowing **7 of 25 cells**; against `reactive`, 8. You only need
a winning answer to the moves your opponent actually throws, so how much of the
rulebook the machine ends up knowing is a readout of how varied *you* are. A
uniform player teaches it 16-25 cells; a habit player teaches it seven. That is
a better thing to put on screen than an accuracy percentage.

**Symmetry does not help.** Filling `(b,a)` from `(a,b)` — the inference a
person makes instantly — fills the table faster and changes the score not at
all. The binding constraint was never rule knowledge; it was reading the
opponent. Worth knowing before spending bytes on a prior.

So the honest framing for the demo is not "it learns the rules". It is that
**learning the rules is the easy half**, over in a couple of dozen rounds, and
the half that never finishes is learning you.

## Decision

Drive the opponent with the **order-1 + outcome table, 75 bytes**, and let it
learn the rules rather than shipping them — 25 more bytes, no lasting cost, and
it turns the first thirty seconds of play into the demonstration instead of a
warm-up. Full agent: **100 bytes**.

The predictor itself: **order-1 + outcome, 75 bytes**: 15 contexts
(5 last moves × 3 outcomes) × 5 counts. Byte counts that halve on overflow,
which is both how the CoCo would hold them and how the table forgets a player
who changes tactics mid-session.

## What has not been done

- **No human has played it.** This is the failure mode EXP-008 documented
  first-hand: its Phase A passed on synthetic players and its human phase then
  settled the question the other way. Synthetic players are declared in
  `tools/run_exp_013.py` rather than discovered, so a predictor tuned until it
  wins is visibly tuned against a known set — but they are still not people.
- **Nothing is written for the 6809.** The table is 75 bytes and the arithmetic
  is a compare and an increment, so the port is not in doubt; it is simply not
  evidence yet.
- **No model has been built or beaten.** The null result above is declared, not
  yet triggered. Until a human is recorded there is nothing for a model to fail
  against.

## Open questions

1. **Does a human's outcome-conditioned behaviour survive being read?** The
   whole gain rests on win-stay/lose-shift. A player who is losing may abandon
   the habit that is losing for them, which is the non-stationary target
   EXP-008 flagged as its most interesting property.
2. ~~How is losing displayed honestly?~~ **Settled: it shows its guess.** The
   capture tool prints what it expects you to throw *before* you throw it,
   along with how many of the 25 rules it has worked out. That hands you the
   way to beat it, which is the point — an opponent you can outwit once you
   understand it is a demonstration; one that only ever wins is a claim. `r`
   empties both tables mid-session, EXP-008's falsifiability key.

   One thing this forced: an empty table's `predict()` returns move 0, and
   displaying that as "it expects ROCK" would show an audience confidence the
   table does not have. It says "it has no idea yet" until the current context
   has actually been seen.
3. **Should the opponent play to win, or to a target score?** Counting a tie as
   a half, a table that always counters is beatable only by randomizing. A
   deliberately imperfect opponent is more playable and less honest.
4. **Does this share the level-name generator's screen?** EXP-012's
   `level_name` centres a name on the top row and refuses repeats, which is
   what the game wants; the RPSLS board would sit under it.

## Relationship to prior experiments

EXP-008 supplies the null result and the discipline. EXP-012 supplies the level
names and the screen. Neither the frequency table nor the game shares code with
the token model — this experiment does not use `model_forward.asm` at all,
which is worth stating plainly given that every other experiment here does.
