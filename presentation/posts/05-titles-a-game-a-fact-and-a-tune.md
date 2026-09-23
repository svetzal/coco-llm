---
title: "Titles, a game, a fact, and a tune"
date: 2026-09-27
published: false
description: "Post five of five: the same arithmetic pointed at other things. Sixteen episode titles that were never filmed, a game opponent that learns the rules and then you, a fact you hand it right now without training, and a tune it finishes from the bar you give it. Then what the whole thing is for."
tags:
  - ai
  - coco
  - "6809"
  - learning
---

[Last post](https://stacey.vetzal.ca/2026/2026-09-25-the-prompt-the-size-the-training-data/) covered three levers, with the loop held fixed:

- The prompt. Two starting words steer the output and change nothing in the model. Asking teaches it nothing.
- The size. Four times the parameters attempted more and was not better at what it already did.
- The training data. Each model came out a fan of whoever wrote its data, and the order of one file made a balanced model a Tandy fan.

This post is the rest of the exhibit table. Every demo on it is the same small piece of arithmetic, pointed at something other than computer names, and each one shows a thing the names could not.

## Sixteen titles that were never filmed

The training data is 79 Star Trek episode titles, every one of them real. THE CAGE. THE MAN TRAP. WHERE NO MAN HAS GONE BEFORE. THE TROUBLE WITH TRIBBLES. The audience at the table knew most of them, which is the point: they could tell a real one from an invented one faster than any test I could write.

Those 79 titles are a bad training set for the loop as it stands, and [the measurement says why](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-012-episode-titles.md#L55-L128). 259 words, 180 tokens, and 162 of those tokens appear exactly once. Across the whole corpus only two adjacent word pairs ever repeat: OF THE, six times, and IN THE, twice. Every other pair happens once and never again. A model that learns which token follows which has almost nothing here that happens twice, so it can only memorize, and a room full of people who know the titles would catch it reciting on the first screen.

So the trick is not in what it learns. Lift the names out of the titles and keep the shape:

```text
THE SQUIRE OF GOTHOS        THE <X> OF <X>       SQUIRE, GOTHOS
A TASTE OF ARMAGEDDON       A <X> OF <X>         TASTE, ARMAGEDDON
THE TROUBLE WITH TRIBBLES   THE <X> WITH <X>     TROUBLE, TRIBBLES
```

Seventy-nine titles collapse to 32 shapes, and now the corpus contains the same thing happening twice. The model trains on the shapes: 400 bytes. The names go into a dictionary, 113 of them, 1,333 bytes, written by hand. And three rules, 258 bytes, also written by hand:

1. A word may only follow a word it actually follows somewhere in the real titles. Without this rule it writes TRISKELION THE MAN TRAP.
2. A name only goes into a gap if it fits the words on either side. Without this rule it writes A TRIBBLES.
3. It holds a fingerprint of all 79 real titles and throws away any match. It is never allowed to deal a real title as its own.

The model proposes a shape, the rules throw out anything the real titles never did, and the dictionary fills the gaps. From BALANCE OF TERROR it kept BALANCE OF and dealt BALANCE OF BABEL, BABEL lifted from JOURNEY TO BABEL. Here is one screen, [sixteen titles as the machine dealt them](https://github.com/svetzal/coco-llm/blob/main/presentation/deck/data/titles.json):

```text
JOURNEY IN THE CAGE              METHUSELAH FOR ZETAR
PLATO'S STEPCHILDREN TO TERROR   SHORE LEAVE OF LIGHTS
METAMORPHOSIS OF GAMESTERS       ELAAN OF ARCHONS
ERRAND TO CLOUD MINDERS          PLATO'S STEPCHILDREN TO ELAAN
YESTERDAYS ON THE TASTE          BALANCE TO MUDD
PLATO'S STEPCHILDREN TO MERCY    BALANCE OF BABEL
ARENA OF METHUSELAH              PARADISE OF SPOCK'S BRAIN
GIDEON TO TRUTH                  PLATO'S STEPCHILDREN TO MIRI
```

Every word is real. None of the titles is.

Here it is dealing, recorded from the emulator at the real clock rate. A screen takes about ten seconds; each keypress deals a fresh one.

<video controls preload="metadata" playsinline style="width: 100%; max-width: 640px; display: block; margin: 0 auto; image-rendering: pixelated;" src="/2026/images/coco-llm-5-titles.mp4">
The emulator dealing two screens of sixteen invented titles.
</video>

The Mac trained the 400 bytes, and it stopped at eleven epochs for a reason that belongs in the record: the CoCo adds up a score in sixteen bits, and [at twelve epochs the scores get big enough to wrap around](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-012-episode-titles.md#L261-L293). Training longer would put the two machines out of step. That costs something you can see. A model trained for sixty epochs prefers THE something OF something, the shape that dominates the real list; the eleven-epoch one leans on bare names. How well this thing writes is limited by how long it can be trained before a sixteen-bit number overflows.

When output looks creative, ask what is holding the shape, what is holding the words, and who wrote the rules. Here you can point at all three: 400 bytes learned, and everything else written by a person. In a large model the same split exists, with rules bolted around the outside, and you cannot point at it. And notice what job this is. Ask this machinery for facts and every screen is an error. Ask it for invention and the screen is the deliverable. Which one you get was a decision about the task.

## Now you play it

Rock, paper, scissors, lizard, Spock. Five throws, and it starts knowing neither the rules nor you.

There is no gradient in this one. [EXP-013, the game opponent that learns](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-013-rpsls-opponent.md), is two tables and 100 bytes:

- The rules: 25 cells, one per pair of throws. Each starts unknown and becomes loss, tie or win the first time that pair is played. Nobody tells it the rules; it fills them in from what happened, the way a person would.
- You: 15 contexts, your last throw times how the last round ended, and in each context five counts, one per throw you might make next. Every round it adds one to the count for what you actually threw.

Before you throw, it tells you what it expects. Then it picks: a throw it knows beats that, or failing that a pair it has never tried, or failing that a tie. The update is an increment. Someone who tried the disk image called it a conditional-frequency Markov predictor, and that is its name.

Learning the rules is the easy half, and it is over in about 25 rounds. Learning you never finishes, because you adapt. Press R and it empties both tables in front of you, so nobody can mistake learning for a difficulty setting.

Here are the numbers, and the second one is the honest one:

| Against | Rounds it won |
| --- | ---: |
| six synthetic players, five of them with a habit | 80.0% |
| me, 200 rounds, trying | 52.8% |

Fifty percent is a draw. It read something in how I play: it named my next throw 29.6% of the time against a 20% chance rate, which is real, and it turned that into almost nothing. I avoid repeating a throw, and a player who avoids repeating was already the hardest of the synthetic players, at 56%. Five of the six players I wrote had a habit; a person plays like the sixth. The test set assumed people have habits, and the average hid that. Ask what your benchmarks are quietly assuming.

Why a table and not a model? Because I tried the model first. [EXP-008, the rejected adaptive opponent](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-008-adaptive-opponent.md), put a next-token model against a 90-byte table on recorded human play, and the table won. Counting is close to the best you can do on a process that is close to a count, and it gets there by incrementing instead of descending a gradient. That is why there is no model in this one.

## A fact you hand it right now

Everything so far learned at training time. This one asks whether the machine can use a fact that exists only in its context, right now, and that changes every time.

The screen shows eight records in context RAM and a question:

```text
1. TEMPORARY CONTEXT IN RAM
MODEL 751B       WEIGHTS LOCKED
  AMIGA           = CODE 7
> LISA            = CODE 2
  TRS-80          = CODE 5
  ARCHIMEDES      = CODE 1
  PET             = CODE 4
  MACINTOSH       = CODE 0
  SPECTRUM        = CODE 6
  ATARI ST        = CODE 3

QUESTION: LISA
```

Press Enter: ANSWER: CODE 2. Press E, type 6, and one byte in context RAM changes: LISA = CODE 6. The weights did not change, and the screen says so. Press Enter again: ANSWER: CODE 6.

<video controls preload="metadata" playsinline style="width: 100%; max-width: 640px; display: block; margin: 0 auto; image-rendering: pixelated;" src="/2026/images/coco-llm-5-attention.mp4">
The emulator: Enter answers CODE 2, E and 6 change the context record, Enter answers CODE 6.
</video>

The model cannot have stored that answer, because in the training data Lisa's code was different in every example. The binding changes each time, so the only thing training could teach is how to find the record that matches the question. [EXP-011, the context-editing attention head](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-011-contextual-associative-recall.md), does it with two small tables: a query row for each name and a key row for each name, both learned. Multiply the question's query row against each record's key row, take the record with the biggest score, copy its value. That is attention, the smallest thing that still is: one head, no value matrix, 160 parameters. It answered 100% of 4,096 bindings it had never seen. A lookup stored in the parameters, with no way to read the context, scored 12.18%, about chance.

The main model has none of this. It is here because it is the mechanism behind the sentence in post four: pasting a document, a system prompt, a memory feature, all of it goes into context, and this is how a model uses what is there. And the caution comes with it. It used the 6 I typed exactly as faithfully as the 2. Relevant is not the same as true.

## A token is a note

The loop never knew it was doing words. Change what a token stands for and the same code writes tunes.

The training data is Ryan's Mammoth Collection, published in Boston in 1883: 1,050 reels and jigs, old enough to be nobody's property. 376 of the tunes, cut to a grid where every row is a sixteenth note. 313 trained the model; 63 were held back to test it.

```text
42D HIGHLAND REGIMENT   minor 4/4   19 . 15 12 . . 12 . 14 . 15 12 . . 12 .
7TH REGIMENT            major 2/4   12 . 12 16 19 12 16 19 24 16 19 24 28 . 26 24
```

The number is how far the pitch sits above the home note, a dot holds it, R is a rest. Thirty-four tokens. The names model had 29 words; this one has 34 notes, and nothing else about the machine changed.

One thing about that alphabet has to be said out loud. Because a token is a step of the scale rather than a pitch, a wrong note is impossible by construction. The harmony was handed to the model, not learned by it. What it learns is contour, phrase length, rhythm, repetition and where a phrase cadences, with the current chord, mode, metre and beat in its window. Those chords were inferred from the melodies by a rule I wrote, so they are a derived feature and not ground truth. The model and the count-table baseline both got the same ones, so the comparison stays fair, and the model beats the best table by [0.494 bits per row](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-010-melody-continuation.md#L503-L545) on the held-out tunes. Where the table had seen the context before, the table won. Everywhere else, the model won, and everywhere else is 93% of the held-out rows.

At the table you enter eight notes on the number keys, and the keys are scale degrees, so you cannot fumble the seed. That is the only music a person wrote. The same loop as post one, predict the next token and write it down, composes the rest. The bass, the arpeggio and the drums are rules a person wrote that follow the chords, the same arrangement as the title machine. Then it plays. Playing four voices takes every cycle the machine has, so it composes the tune into memory first, then performs it. No modern machine hides that from you; it does it faster.

Here is one, with sound. This is the CoCo 1 build under the emulator at the real clock rate, so the performer is the 4,566-samples-a-second one. The seed is 1 2 3 5 5 3 2 1, in yellow; THINKING is the composer, about five seconds; the rest is the tune it wrote.

<video controls preload="metadata" playsinline style="width: 100%; max-width: 640px; display: block; margin: 0 auto; image-rendering: pixelated;" src="/2026/images/coco-llm-5-melody.mp4">
The emulator composing a tune from an eight-note seed and playing it.
</video>

The performance is its own experiment, and it was heard on the CoCo 3 through a Commodore 1703 monitor on 6 September 2026. The first player had a warble on the melody, and [EXP-018, the steady sample clock](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-018-steady-sample-clock.md), removed it by making every sample cost the same number of cycles. On the 6309 at the fast clock that is 11,188 samples a second; the CoCo 1 build plays the same tune at 4,566.

## The same thing, in the usual symbols

For the reader who knows this material as matrices. The names model is a log-bilinear language model in the sense of Mnih and Hinton (2007), with a separate input table per window position and the output table untied: one lookup, one linear layer, softmax, cross-entropy, plain stochastic gradient descent with a batch of one and a constant rate of a sixteenth. The backward pass is the chain rule from the loss to the parameters and it is two steps long, because there are two: the error at the scores is the shares minus the one-hot target, and the error at the context vector is the scoreboard transposed times that. So yes, it is backpropagation, one layer deep. What you will not find: a hidden layer or an activation, attention in the main model, normalization, residuals, Adam, a schedule, a KV cache. The [concept map](https://github.com/svetzal/coco-llm/blob/main/presentation/concept-map.md#for-readers-who-know-the-classic-form) has the derivation and the list of what appears under another name.

## What it is for

Post one made a promise: by the end you would know exactly how it does that, and be unimpressed in precisely the right way. Here is the right way.

Prediction is not understanding. The names model learned that AMIGA plausibly follows COMMODORE without anything in it holding that either one was a company or a product. Plausible is the product. True needs another system: a source, a test, a tool, or a person who knows what is at stake.

The parameters are not a database of sentences. 290 numbers held eighteen names well enough to invent new ones and, trained longer, well enough to recite them. Which of those you get was a decision about how long to train.

Useful is not the same as correct. The sentence completer saved half the typing while its top three suggestions missed the word four times in ten. The game opponent read me at three sigma and could not beat me.

Automating a task is not taking on its purpose. The CoCo can invent a computer name. A person chose the problem, assembled the examples, designed the model, judged the output, and decided what the demonstration meant. Nothing in the loop decides which outcomes matter or answers for them.

And this model shares the learning objective of every modern generative language model, guess the next token and nudge toward less wrong, but not their architecture and not their scale. It is the same loop at a size where every part is visible.

Everything I could point at in this series traces back to a person who decided something: what a token is, how wide the window is, how many numbers, how long to train, what data and in what order, what goes into context, what the rules throw out. That is the durable claim. The mechanism is understandable, the limitations are observable, and the decisions have names on them.

The practical move is the same at every scale: give a model a bounded job, relevant context, and a way to check the result. Call your shot, take your shot, look at what happened.

Everything is at [svetzal/coco-llm](https://github.com/svetzal/coco-llm), every experiment with its evidence and its conclusion, and the machines run on a Mac with XRoar. Change the training data and predict what will change. Train a fan and try to tell which one from its output. Read the assembly. Question every claim the model made, and every one I did.
