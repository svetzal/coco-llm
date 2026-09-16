# Series outline

The talk, given on 2026-09-13, as a series of blog posts and videos. The
order is the concept map's, not the runsheet's: predict along the top,
correct along the bottom, then the levers a person can move, then the things
that came out of the same machinery. A reader who arrives at episode nine can
see which box they are standing on.

Each episode is one box on [`concept-map.md`](concept-map.md) or one lever,
runs one experiment, and shows one thing. The rules that governed the deck
govern the series: every number comes from a run, the Mac's part is said out
loud, and a simplification is named where it is made.

## Shape

Seventeen episodes in five parts. Every episode has a post and a video; the
surface line says which one carries it. The post is the written record with
the numbers and the commands. The video is the machine doing it.

| Part | Episodes | What it covers |
| --- | ---: | --- |
| Watch it work | 1 | the promise, on the real machine |
| Predict | 2 to 5 | training data and tokens, the context window, embeddings, the scoreboard |
| Correct | 6 to 8 | one step, epochs, the 6809 doing it |
| Change one thing | 9 to 11 | the prompt, the size, the training data |
| The same machinery, elsewhere | 12 to 17 | fake titles, a game, a fact supplied now, music, the usual symbols, what it is for |

A post is done when a reader could reproduce its numbers from the command it
names. A video is done when the room's question at that point in the talk
has been answered on camera.

## Part one: watch it work

### 1. A 45-year-old computer learns to invent computer names

- Map: PICK, and the whole predict loop, before any of it is explained.
- The one thing: it starts from random numbers and ends inventing names.
- Runs: EXP-004, the live training run. `make block1` opens the deck and
  launches it from random weights; `make present EXP=4` launches it alone.
- Show: the launch, the counter climbing at the 1981 clock rate, the
  same seed drawing nonsense before and names after. The photograph of the
  machine at the table.
- Say plainly: the emulator runs at the real clock rate; the physical
  machine does the same job in the same time. The photograph's screen is
  EXP-012, the fake episode titles, which the Mac trained.
- Surface: video first. The post is short and carries the promise and the
  disclosure.

## Part two: predict

### 2. What the machine thinks a word is

- Map: TRAINING DATA and TOKENIZE.
- The one thing: a token is whatever a person decided it is, and here it is
  a whole word.
- Runs: the corpus, `experiments/data/EXP-001-computer-names.txt`, 18 names
  that become 29 tokens and 58 examples. `uv run python
  tools/export_deck_traces.py` writes the token identifiers the deck shows.
  EXP-001, the rejected character model, is the other choice, priced.
- Show: the corpus, the vocabulary, a word that is not in it and what
  happens. The character model's 12.8 million multiplies against the
  180-second budget.
- Say plainly: thirteen is a name, not a quantity; nothing can be learned
  from arithmetic on it.
- Surface: post first. The video is the tokenizer exercise from the table.

### 3. The context window

- Map: CONTEXT WINDOW.
- The one thing: the model sees the last two tokens and nothing before them.
- Runs: the same model. The sliding-window figure on the "What is a word?"
  slide; open the deck with fragments off to see every stage at once:
  `open "presentation/deck/index.html?fragments=false#/4"`.
- Show: the window sliding along COMMODORE AMIGA, what falls out of it, and
  why the tables come in pairs: one per position.
- Say plainly: a 200,000-token context window is this, wider. A long chat
  forgetting its start is the window sliding.
- Surface: post first. Episodes 9 and 14 come back to this box with a person
  writing into it.

### 4. Where the numbers live

- Map: EMBED and WEIGHTS.
- The one thing: every token owns three numbers per position, and those are
  most of the model.
- Runs: EXP-002, the token model, whose width sweep is why three.
  `experiments/EXP-002-token-model-feasibility.md` has the table;
  `make reference-test` runs the reference the numbers came from.
- Show: the two tables, the same word with a different row per position, the
  lookup and the add. The parameter count line by line to 290.
- Say plainly: six numbers would have fit the budget too; three was the
  smallest tried that worked. A parameter is one number training is allowed
  to change.
- Surface: post first.

### 5. How it picks the next token

- Map: SCORE, SOFTMAX and PICK.
- The one thing: scores become shares of 100%, and a die picks.
- Runs: the table exercise, `uv run python tools/generate_cards.py`, whose
  cards are dumped from the trained model's softmax. The "How it picks the
  next token" slide.
- Show: a person rolling a d20 through the cards and taking home a computer
  that never existed. Then the same thing as arithmetic, and the exponential
  as a 256-entry table on the CoCo.
- Say plainly: softmax preserves the order and does not choose. Greedy takes
  the biggest; temperature is how much the die is trusted.
- Surface: video first, at a table with the cards.

## Part three: correct

### 6. One step of training

- Map: TARGET, COMPARE, GRADIENT and UPDATE.
- The one thing: the share it gave the right answer, minus 100%, times what
  each weight contributed, times a rate somebody chose.
- Runs: `uv run python tools/export_shift_trace.py`, one real weight update
  bit by bit, and `tools/export_deck_traces.py` for the step figure's
  numbers.
- Show: AMIGA at 3.5%, the three numbers, the nudge, AMIGA at 3.7%. The
  sign of each change is the sign of its incoming number.
- Say plainly: the learning rate is a sixteenth because that is four shift
  instructions. Master weights are Q4.12 and the forward pass reads Q4.4;
  the dropped bits are quantization's visible price.
- Surface: post first. This is the episode the mathematicians will read
  twice; episode 16 gives them the notation.

### 7. Do it again, and again

- Map: REPEAT.
- The one thing: loss keeps falling after the names stop getting better.
- Runs: EXP-007, the epoch sweep. `make exp007-epoch-sweep`. The "Do it
  again" figure, 200 draws per epoch, scored new and right-shaped.
- Show: epoch 0 nonsense, 5 a first-word habit, 20 SINCLAIR AMIGA, 60
  COMMODORE 64. Three failures leaving in order. The cost split: bytes to
  use against bytes to learn.
- Say plainly: overfitting, named on the slide where it is visible. New is
  not the same as good; only new and shaped counts.
- Surface: both. The video is the epochs going by on the machine.

### 8. A little 6809 assembly

- Map: SCORE and GRADIENT for the multiply, UPDATE for the shifts.
- The one thing: one signed multiply from two unsigned ones, and a
  correction when a factor is negative.
- Runs: EXP-004, the live training run, `make block3` for a fresh one;
  `make xroar-test` proves the CoCo trains to the Mac's checksum. EXP-014,
  the 6309 multiplier benchmark: `make bench`, with `bench-xroar-6809` and
  `bench-xroar-6309` for the two chips.
- Show: the five-to-twelve-line reveals from `src/6809/`, pulled by
  `tools/extract_code_excerpts.py` so they cannot go stale. MUL at eleven
  cycles; MULD at 1.54x on the physical CoCo 3.
- Say plainly: floors are multiply counts, not runtimes. Runtimes are the
  ones measured on hardware and labelled.
- Surface: video first, on the real machine, with the code on a second
  screen.

## Part four: change one thing

### 9. The prompt

- Map: CONTEXT WINDOW, written by a person. WEIGHTS held.
- The one thing: two starting words steer the model and change nothing in
  it.
- Runs: EXP-005, the prompted marketing completions. `make block4` or
  `make present EXP=5`.
- Show: I ADORE becoming MY 64; ARE YOU becoming KEEPING UP IN LITTLE
  COMPUTERS. Ask what stayed fixed.
- Say plainly: a system prompt, retrieved context and memory are all edits
  to this box. Asking the model teaches it nothing.
- Surface: both.

### 10. The size

- Map: TOKENIZE at 255, CONTEXT at 5, EMBED wider, WEIGHTS written by the
  Mac.
- The one thing: more parameters retain more patterns; they do not add
  understanding.
- Runs: EXP-006, the 8 KiB completion workbench, and EXP-007, the all-RAM
  sentence completer. `make present EXP=6`, `make present EXP=7`,
  `make exp007-sweep` for the 32, 40 and 48 KiB candidates.
- Show: the sentence completer at 85 times the size, the controlled pair
  where only the size moved, the all-RAM map under the ROM. EXP-006 missing
  its own 70% target at 59.3%.
- Say plainly: the Mac trained these; the CoCo runs them. An open-weights
  release is the same file, larger. The screen says MAC TRAINED - COCO
  PREDICTS so the provenance is on the machine, not in a warning.
- Surface: both.

### 11. The training data

- Map: TRAINING DATA, and what it does to WEIGHTS.
- The one thing: the model's favourite is the corpus's favourite, and the
  order of the examples is a bias of its own.
- Runs: EXP-003, the fan-corpus bias runs.
  `uv run python tools/export_bias_trace.py` for the five controlled runs;
  `src/reference/run_bias_demo.py` is the experiment.
- Show: Apple, Commodore and Tandy fans; the same examples concatenated and
  interleaved. Everything held but the data.
- Say plainly: fine-tuning is more training on chosen data. The wonder is
  the people who wrote what it read.
- Surface: post first.

## Part five: the same machinery, elsewhere

### 12. A screen of things that never existed

- Map: PICK with rules over the draw; TOKENIZE, a vocabulary mostly used
  once.
- The one thing: a corpus where nothing repeats can only be memorised, so the
  trick is in what is drawn, not what is learned.
- Runs: EXP-012, the fake episode titles. `make block6`;
  `make exp012-corpus` and `make exp012-vocabulary` for the numbers.
- Show: 79 real titles, 180 tokens, 91% used once, two repeating pairs. Then
  sixteen invented titles a keystroke at a time.
- Say plainly: the Mac trained it, capped at eleven epochs by 16-bit logit
  accumulation, which visibly costs style.
- Surface: video first. It is the delight beat and it films well.

### 13. Now you play it

- Map: UPDATE during play; CONTEXT is the last move and the last outcome.
- The one thing: a 75-byte table that learns the game and the player at
  once, by counting.
- Runs: EXP-013, the game opponent that learns. `make block8` to play;
  `make exp013-sweep` for the synthetic players, `make exp013-play` for a
  recorded human session. EXP-008, the rejected adaptive opponent, is the
  null result it started from: `make exp008-sweep`.
- Show: RULES n/25 and MEMORY n/rounds climbing; R emptying both; 80% against
  six synthetic players and 52.8% against a person who is trying.
- Say plainly: no gradient here; the update is an increment. The synthetic
  number was an artifact of players with habits, and the human number is the
  one that counts.
- Surface: video first, with a guest playing.

### 14. A fact you give it right now

- Map: CONTEXT WINDOW, read by content.
- The one thing: a person edits one byte of context, the weights stay
  locked, and the answer changes.
- Runs: EXP-011, the context-editing attention head. `make present EXP=11`
  or `make xroar-attention`; `make exp011-sweep` for the width sweep.
- Show: Lisa's value edited from CODE 2 to CODE 6 in context RAM with the
  weights visibly locked, the same question asked again, and V replaying the
  scores slowly.
- Say plainly: this is attention, the smallest thing that still is: learned
  queries and keys, no value matrix, one head. The main model has none.
- Surface: both. The demo script is `exp011-demo-script.md`.

### 15. A token is a note

- Map: TOKENIZE; SCORE for the 6309.
- The one thing: change what a token is and the same machinery composes.
- Runs: EXP-010, the melody continuation. `make block9` on the CoCo 3,
  `make block9-coco1` on the CoCo 1; `make exp010-dance` for the corpus.
  The performer behind it: EXP-009, the four-voice synthesizer; EXP-017,
  the wavetable voices; EXP-018, the steady sample clock. `make exp017`
  and `make exp018` build and check them.
- Show: someone enters a bar, the CoCo continues it and plays it. The chip
  in the CoCo 3 and what MULD buys.
- Say plainly: a wrong note is impossible by construction, because the token
  is a scale degree conditioned on mode, metre, beat and chord. The
  listening tests for the performer are still pending.
- Surface: video first. Sound is the point.

### 16. The same thing, in the usual symbols

- Map: every box, in notation.
- The one thing: yes, it is backpropagation, one layer deep; and the model
  has a name, a log-bilinear language model.
- Runs: nothing new. `concept-map.md`'s classic section, the deck's backup
  slide under the last one, and `deck/map.html?math=2`.
- Show: the table in matrices, the chain rule in three lines, what a classic
  reader will not find and what they will find under another name.
- Say plainly: no hidden layer, no attention in the main model, batch size
  one, an exponential that is a table. Same loop, same objective.
- Surface: post only. It is for the reader who wants to check.

### 17. What it is for

- Map: the whole map, lit.
- The one thing: the mechanism is understandable, the limitations are
  observable, and every decision traces to a person.
- Runs: `make block10`. The wrap-up slide and the learning journey's closing
  sections.
- Show: the distinctions the talk kept explicit: prediction is not
  understanding; parameters are not a database of sentences; useful is not
  the same as correct; automating a task does not assume purpose or
  accountability; same objective as modern models, not their architecture or
  scale.
- Say plainly: a bounded job, relevant context, a way to check the result.
- Surface: both, short.

## Production order

Not the episode order. Make the ones the camera is for first, while the
machine is set up: 1, 8, 13, 15, then 12 and 5. Write the posts for 2, 3, 4,
6 and 16 from the deck and the concept map, which already carry their
numbers. The three levers, 9 to 11, go last as a run, because their whole
point is the sentence they share.

Copy for posts goes through the blog voice; anything spoken goes through the
speaker voice. Titles are the thing's real name. The deck's rule about
sample output holds on every surface: nothing appears unless the machine
produced it.
