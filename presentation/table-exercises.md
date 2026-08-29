# Table exercises

Hands-on material for the exhibit table. The CoCo does the demonstrating; these
give people something to do with their hands while they wait, and give the
shy ones a reason to start talking.

The organizing constraint is attention span, not content. A show table gets four
very different visitors, and each needs a complete experience:

| Time given | What they get |
| --- | --- |
| 10 seconds | Table card, and the tokenizer gotcha |
| 2 minutes | Roll a name by hand (Exercise 1) |
| 5 minutes | Same dice, different upbringing (Exercise 2) |
| 15 minutes | Watch the CoCo actually train, and talk to Stacey |

## Integrity rule

Every printed probability must be dumped from the trained model, not invented.
`FixedTokenLanguageModel._softmax` already produces exactly the distribution the
CoCo holds in RAM, so the cards can be generated rather than authored. The same
rule that governs the slides governs the cards: if the paper and the machine
disagree, the exhibit is lying.

## Exercise 1 — Be the model

The visitor performs the inference loop by hand and takes home a computer that
never existed.

### Mechanic

One card per **context** — the two words the model can currently see. The card
lists every next word the model might choose, with the dice numbers that select
it.

```text
┌──────────────────────────────────────────┐
│  #  COMMODORE                            │
│  ---------------------------------------  │
│  Roll a d20:                              │
│                                           │
│     1 – 13    AMIGA              65%      │
│    14 – 18    64                 25%      │
│    19 – 20    PET                10%      │
│                                           │
│  Write the word on your slip.             │
│  Next card:  COMMODORE  +  your word      │
└──────────────────────────────────────────┘
```

1. Start at the `# #` card. `#` means "nothing came before this."
2. Roll, read off the word, write it on the slip.
3. The next card is the second word of this card plus the word just rolled —
   each card pre-prints half of that lookup, which is what keeps people from
   getting lost.
4. Repeat until `#` comes up. The name is finished.

The visitor has now run a forward pass, sampled from a softmax distribution, and
fed the result back into the context — without any of those words being used.
Introduce the vocabulary afterward, if at all.

One piece of vocabulary is worth introducing, though, for anyone who has seen
an API playground: **the die is the temperature dial.** Rolling is sampling.
Ignoring the die and always taking the top row is greedy decoding, temperature
zero — walk the deck that way once and every walk is identical. Temperature
turned up flattens the printed ranges so the underdogs come up more often.
A visitor who has wondered what that slider does has just operated it.

### Why a d20

A twenty-sided die is uniform, resolves to 5%, and needs one throw. Print the
percentage beside the range so the connection to softmax stays visible.

Do not use two six-sided dice. Two d6 produce a bell curve — 7 comes up six
times as often as 12 — so the paper model would sample from a distribution the
CoCo does not have. It is worth having a spare 2d6 on the table anyway: "why
can't we use these?" is a genuinely good thirty-second lesson for anyone who
asks.

Percentile dice (2d10) resolve to 1% and let the card print the softmax numbers
exactly. Slower per roll, better for someone who has settled in. Consider one
deep deck in d100 alongside the d20 decks.

### Deck size and training length

Measured with `tools/generate_cards.py`. The deck is every context a visitor can
reach on a walk of at least `--min-path` probability:

| Epochs | `--min-path` | Cards |
| ---: | ---: | ---: |
| 20 | none | 270 |
| 60 | none | 138 |
| 60 | 1% | 35 |
| 60 | 2% | 25 |

**The live demo's twenty epochs make an unusable deck.** After twenty epochs the
model has barely learned the second position: from `# TANDY` the strongest
continuation is `MODEL` at 7%, against 3.4% for a uniform guess. Every token
survives d20 rounding, so the cards run to twenty near-identical 5% rows and the
reachable set explodes to 270.

At sixty epochs the same contexts are sharp and legible — `# TANDY` becomes
`MODEL` 40%, `TRS-80` 30%, `COLOR` 20% — and `TANDY MODEL 100` and
`TANDY COLOR COMPUTER` are visible in the deck as shapes rather than statistics.

At two hundred it degrades again in the other direction: `TANDY` → `MODEL`
reaches 75%, which makes for a boring roll, and the start card loses its clear
`TANDY` lead.

So the printed deck is trained longer than the machine on the table, and the
card must say so. The CoCo stops at twenty epochs because of its time budget,
not because twenty is the right number — which is worth saying out loud, because
it is a real engineering trade and not a simplification for the audience's
benefit.

That gap is also printable. The same context at epoch 1, epoch 20, and epoch 60,
mounted side by side, is training made visible on paper:

> This is what it knew after one pass. After twenty. After sixty.
> Nobody added a rule. The numbers just moved.

### Rounding

A d20 cannot represent a 3% share, so the largest-remainder method assigns whole
faces and the residue is dropped. At sixty epochs that is 9.2% of probability
mass on an average card and 14.8% on the worst (`ACORN BBC`). Print the
disclosure on the deck's title card rather than burying it: the paper is a
rounded copy of the machine, and the rounding is knowable.

Where a walk reaches a context with no card, that is not a failure — it is the
model wandering off the distribution it was trained on, which is exactly what the
talk is about. Print one card for it:

> **NO CARD FOR THAT PAIR.**
> You have walked off the edge of everything it was trained on. The CoCo will
> still answer confidently if you ask it. Bring this to me and I will show you
> what it says.

## Exercise 2 — Same dice, different upbringing

This is EXP-003 made physical, and it is the strongest thing on the table. It
delivers the thesis of the talk with no explanation required, which means it
works while Stacey is talking to someone else.

Two decks in two colours: **COMMODORE FAN** (blue) and **APPLE FAN** (red).
Identical rules, identical layout, identical dice.

1. Walk the blue deck. Write down each roll as well as each word — the slip has
   a column for the numbers.
2. Now walk the red deck replaying *the exact same numbers*.
3. A different machine comes out.

The sign underneath needs one line:

> Same dice. Same rules. Same rolls. Nothing changed but what it read.

Anyone who wants more gets the follow-up: mix the two corpora and the ordering
still shows up in the output. Interleaving fixes what concatenating does not.
That is on the CoCo, not on paper.

## Exercise 3 — You are the tokenizer

The cheapest interaction on the table and the right one for somebody who will
not stop walking. A single card listing all 29 tokens:

> These are all the words this computer has. Every one of them. Write your name.

They cannot. Neither can the CoCo write `IPHONE`, or `THINKPAD`, or `STACEY`.
Vocabulary is a decision a person made before any learning happened, and it
fixes the limits of what the model is able to think about at all.

Ten seconds, no setup, no dice, and it lands before anyone has said the word
"intelligence."

## Exercise 4 — The wall

Every slip has a tear-off half. The visitor keeps one and pins the other to a
board behind the table.

By the second day the board is a few hundred computers that have never existed,
generated by strangers, and it is the best possible advertisement for the table —
people stop to read the board and then ask what it is. Print the project URL on
the half they keep.

## Stretch — Be the trainer

For someone who stays. Show a context where the model guessed wrong, with the
expected answer revealed. Give them a row of beads or sliders, one per candidate
word, set to the current probabilities. Ask them to move the right answer up and
the others down, by a small amount, without going to certainty.

That is one update step. Do it four or five times and the distribution visibly
sharpens. It also makes the point that backpropagation decides *which way and how
far*, and the update is a separate, ordinary act of arithmetic.

This is fiddly for walk-up traffic and needs prototyping before it earns table
space. Try it on one person before building five.

## Materials

- d20 dice, several — they will walk off
- 2d6 as a deliberate teaching prop
- 2d10 for the deep deck, optional
- Card stock, one deck per corpus, colour-coded
- Slips with columns for roll and word, tear-off halves, project URL
- Pencils
- Corkboard and pins for the wall
- The "no card for that pair" card, several copies

## Generating the decks

`tools/generate_cards.py` trains the fixed-point model, walks the reachable
contexts, and emits either an ASCII preview or a print-ready HTML sheet at four
cards per page.

```sh
# Read the deck at the terminal
uv run python tools/generate_cards.py --epochs 60 --min-path 0.02

# Print-ready, four to a page
uv run python tools/generate_cards.py --epochs 60 --min-path 0.02 \
    --format html --output build/cards/deck.html
```

The bias decks are the same tool pointed at a different corpus, which is the
whole reason to generate rather than author them:

```sh
uv run python tools/generate_cards.py --format html \
    --corpus experiments/data/EXP-003-commodore-fan.txt \
    --label "COMMODORE FAN" --accent "#1f6feb" \
    --output build/cards/commodore.html

uv run python tools/generate_cards.py --format html \
    --corpus experiments/data/EXP-003-apple-fan.txt \
    --label "APPLE FAN" --accent "#d1242f" \
    --output build/cards/apple.html
```

The tool prints the card count, the corpus, the parameter checksum, and the
rounding residue to stderr. Keep the checksum with the printed deck — it is how
a future run proves the cards on the table match the model that generated them.

Still to do: the slip design, the "off the map" card, and a title card carrying
the epoch and rounding disclosures.
