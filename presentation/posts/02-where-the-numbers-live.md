---
title: "Where the numbers live"
date: 2026-09-21
published: true
image: "images/coco2-banner.png"
imageAlt: "An illustration: a silver-haired woman in a dark blazer leans over a workbench at night, one finger on a row of numbers on a long strip of green-bar fanfold printout that runs past a worn 1981 Radio Shack Color Computer, while the beige CRT beside it shows a green screen with a table of short words and columns of numbers; an amber twenty-sided die rests on the desk beside the paper"
description: "Post two of five: the two tables where the model's numbers live, why each word gets three, what a parameter is, what one step of training changes, and how a score becomes something you can roll a die on."
tags:
  - ai
  - coco
  - "6809"
  - learning
---

Last post covered:

- The loop. Guess the next token, measure how wrong the guess was, nudge every number a little in the direction that would have made it less wrong, repeat.
- The training data. Eighteen vintage computer names, split into words, sorted and numbered: 29 tokens. COMMODORE is 13 because it is thirteenth in that list. The number is a label, not a quantity.
- The window. Two tokens wide. The model's only job is to guess the token that comes next, so the eighteen names become 58 examples.
- The parameters. 290 numbers that training changes.
- Twenty epochs. Enough training to invent plausible names, not so much that it repeats the training data.

This post is about the 290 numbers: where they live, what each one does, and what one training step does to them.

The token number is not one of them. The arithmetic is on three numbers per token, and they live in a table.

## Two tables

Two tables, because the context window is two tokens wide and each position gets its own.

Each table has 29 rows, one per token, and each row holds three numbers. When the window holds END then COMMODORE, the machine fetches the END row from the first table and the COMMODORE row from the second table, and adds them:

```text
position 1, <END>       -0.0286   -0.0187   +0.0583
position 2, COMMODORE   -0.0009   -0.0266   -0.0168
                        -------   -------   -------
add them                -0.0295   -0.0453   +0.0415
```

![Two tables side by side on the CoCo's green screen, in its pixel type, titled TWO TABLES, ONE PER WINDOW POSITION. Each lists tokens with three signed numbers beside them. In the position 1 table the END row is highlighted in amber; in the position 2 table the COMMODORE row is. Below, the two fetched rows are written out and added, with the sum in three black cells: minus 0.0295, minus 0.0453, plus 0.0415. A caption reads: these three numbers are the model's whole input, no arithmetic beyond the addition.](images/where-the-numbers-live.png)

Those are the real rows, exported from the model before training. The three numbers at the bottom are what the training step works on.

Each row of three is a token's embedding, placing it among other tokens according to their proximity. Using just one number in isolation wouldn't help the model decide what should come next. Three numbers put it in a space. They are coordinates: the first number is how far along one axis the token sits, the second another, the third the third, so each token is a point in a box, and near means near. After training, tokens whose points are close are tokens the arithmetic treats alike.

Here is the second table after the 20 epochs, as points in a box:

![The position 2 table after 20 epochs, drawn on the CoCo's green screen as points inside a wireframe box, each with a dashed drop line to the floor. The six makers are larger amber points close together on the right, labelled ACORN, APPLE, ATARI, COMMODORE, SINCLAIR and TANDY. The model names are small black points bunched on the left, most of them labelled, with COLOR, BBC, ZX and MODEL high up on their own. A caption reads: tokens that are followed by the same kind of token end up near each other; END lies far above this box.](images/twenty-nine-points.png)

APPLE and ATARI are 0.12 apart. COMMODORE is 0.44 from ATARI and 1.13 from 64. Nothing in the numbers says what a maker is. The makers ended up near each other because the same kind of token follows them. COLOR, BBC, ZX and MODEL sit high up on their own for the same reason: each is followed by another word, COMPUTER, MICRO, SPECTRUM, 100. That is what this space records: not what the words mean, but how and where they are encountered together. END is left off the figure because it sits far above everything else, and it should: it is the start of a name, and nothing else is.

COMMODORE also has a different row in each table. In position 1 its row is +0.0781, +0.0250, +0.0173. In position 2 it's the row above. So the row places the token among the others and by where it sits relative to the token before it: the embedding is the token in its context. That is why the two words are everywhere in this field. A name becomes a position, and the position is where all the arithmetic happens.

Two positions, 29 tokens, three numbers each: 174 numbers, most of the model.

## Why three?

GPT-3's embedding is 12,288 numbers long where ours is three. Same idea, more room.

Every extra number is another 87 multiplies per example: 29 to score the tokens and 58 more in the training step. The 6809 has no multiply for numbers this size, so each one is a routine built from its 8-bit MUL instruction, and I measured that routine on the machine at 133 cycles, about 150 microseconds. I priced the widths before choosing:

| numbers per word | parameters | multiplies to train | time in multiplies |
| ---------------: | ---------: | ------------------: | -----------------: |
| 1 | 116 | 100,920 | 15 s |
| 2 | 203 | 201,840 | 30 s |
| 3 | 290 | 302,760 | 45 s |
| 4 | 377 | 403,680 | 60 s |
| 5 | 464 | 504,600 | 75 s |
| 6 | 551 | 605,520 | 90 s |

The run you watched last time took about 100 seconds to reach PRESS ANY KEY, and 45 of them were multiplies. The rest is computing probabilities, the updates and the display.

Six would probably still have fit my three-minute budget, but three was enough. Three numbers per token told 29 tokens apart well enough that the extra width never earned its cost.

The other choice I priced was the one I built first and threw away. Make a token a single character instead of a whole word and the model has to predict every letter: 12,859,560 multiplies. At eleven cycles each, the cost of the bare MUL instruction and the floor I priced it at, that is 158 seconds against a 180-second budget. At what a multiply costs in practice, it is half an hour.

## What is a parameter?

It's just something that can change in the model.

```text
 2 window positions x 29 tokens x 3 numbers  =  174   the two tables
                     29 tokens x 3 numbers  =   87   a row for every token it can predict
                     29 tokens              =   29   a starting nudge per token
                                               ----
                                                290
```

This model has 290. GPT-3 had 175 billion; DeepSeek-V3 has 671 billion. But the thing I enjoyed most about doing all this was seeing what I could do at the very small end of the scale.

In this computer field, we seem to get quickly obsessed with scale, buying the biggest computer, the biggest graphics card, training the biggest model. The whole world has gone crazy on this with gpu compute datacentres.

I enjoy using this old hardware because I think it's easy to become wasteful these days, and there's no challenge in that. Especially if you have money. Constraints make me more creative, teach me more about how things can work.

## A score for every token

The 87 and the 29 in that count are the scoreboard: for every token the model might predict, three numbers called its weights, plus its starting nudge. To score a token, multiply the three context numbers by the token's three weights and add the nudge. Do it 29 times and every token has a score.

That's 87 multiplies, and the 6809's MUL instruction multiplies two unsigned 8-bit numbers. Each weight is stored as 16 bits but scores with its top byte, the context number goes in as all 16, and one product takes two MUL instructions plus a step to fix the sign. Next post shows the 6809 doing one.

Before training all 290 numbers are random and small, so the scores are all near zero. Here are the shares they turn into for the window END, COMMODORE, where the right answer is AMIGA:

```text
TRS-80   3.49%    <- the largest share, barely
128      3.48%
ZX80     3.48%
ATARI    3.48%
...
AMIGA    3.45%    <- the right answer, in the middle of the pack
```

Twenty-nine tokens, mostly indistinguished.

## Scores become shares

Those percentages are what a score turns into once you push it through a softmax.

Suppose three tokens have raw scores of 3, 2 and 1. A score of 3 doesn't mean 3%, or three votes. Softmax makes every score a positive weight, then divides each by the total, so the results are shares of 100%: about 67%, 24% and 9%. It keeps the order and it exaggerates the lead.

Why "soft"? A hard maximum would give the winner everything. Softmax lets the strongest choice lead while the others stay possible.

Softmax doesn't choose. It hands you shares, and something else has to draw.

On the CoCo the shares add up to 256 instead of 100, so every token owns a stretch of a line from 0 to 255 as wide as its share. The machine draws one byte, and whatever stretch it lands on is the next token. That's the die.

## Training is a nudge

Back to the window END, COMMODORE, where the right answer is AMIGA and the model gave it 3.45%. Training is one step, done over and over: score, compare with the right answer, nudge every weight a little in the direction that would have raised the right answer's share. Here is the step, with the real numbers.

AMIGA should have had 100% and got 3.45%, so the model was wrong by 0.9655. Every weight's change is that, times a rate, times what the weight contributed.

Take AMIGA's three weights from the scoreboard. To make AMIGA's score, each was multiplied by one of the three context numbers, minus 0.0295, minus 0.0453 and plus 0.0415, the sum of the two rows fetched from the tables at the top of this post. Each weight's contribution was its own context number, so each gets nudged by that number, scaled. The scale is the same for all three: 0.0625, a rate I chose, times 0.9655, how wrong the model was.

![Three columns on the CoCo's green screen, titled THREE WEIGHTS AND ONE NUDGE EACH, with the formula beneath: change equals 0.0625, a rate I chose, times 0.9655, how wrong it was, times the context number. Each column has the context number in a navy box marked negative or positive, the weight before, the change in an amber box with a navy arrow pointing down for the two negative changes and up for the positive one, and the weight after: plus 0.1214 to plus 0.1197, minus 0.0705 to minus 0.0732, plus 0.0325 to plus 0.0350. The caption reads: each weight moves the way that would have raised the score for AMIGA.](images/one-nudge.png)

The rate, 0.0625, is a sixteenth. I chose it because dividing by sixteen is four shift instructions on a 6809.

The same step reaches back into the two tables, too. The END row in position 1 and the COMMODORE row in position 2 both get nudged, by how much each of the three context numbers contributed to every score that came out wrong. After the step, fetch and add those rows again and you get minus 0.0118, minus 0.0561, plus 0.0477. Those rows started random. Nudges like this are what make them mean something.

AMIGA now has 3.68%, up from 3.45. That is the size of one step, and there are 1,160 of them in a run. Every one of the 290 parameters moves by this rule.

## Roll it

Here is the die being rolled, from the run you watched last time, after all 1,160 of those steps. Seed 6809 drew three bytes: 50, 12, 119.

The first draw, 50, landed on COMMODORE, which owned 27 of the 256. TANDY owned 131, more than half the line, and was not drawn. The second draw, 12, landed on 128, which owned 17; the widest stretch there was PET's, 25. The third draw, 119, landed on END, which by then owned 228 of 256.

![Three horizontal lines from 0 to 255 on the CoCo's green screen, titled SEED 6809 DREW 50, 12, 119. Each line is divided into stretches, one per token, as wide as its share. On the first line a navy arrow at 50 lands on COMMODORE's stretch, highlighted amber, while TANDY's stretch covers half the line. On the second, an arrow at 12 lands on 128. On the third, an arrow at 119 lands on END, which covers almost the whole line. The bottom reads: THE NAME: COMMODORE 128.](images/roll-it.png)

COMMODORE 128. A real name; it's in the training data. It's also the first name on the screen at the end of the video.

Seed 6810 drew 177, 110 and 29 from the same table, and got TANDY COMPUTER. Same weights, same rows, different bytes. The eleven names on that screen are eleven paths through one table.

Two things about the die. For the first two tokens, END's stretch is handed to the widest, so a name is never one word long; that rule is in the code, not the weights. And you don't have to roll. Take the widest stretch every time and you get the same name every time: greedy decoding, which is what temperature zero means. Temperature rescales the scores before they become shares. Higher narrows the fat stretch and widens the thin ones, lower does the reverse, and zero is greedy.

This is why it's useful to think in probabilities. The model never answers. It hands over shares, and a draw picks. Take the biggest every time and you get one answer forever; draw, and you get variety, and now and then TANDY ZX80. It's the die.

Two hundred and ninety numbers. A hundred and seventy-four are a lookup table, a hundred and sixteen are a scoreboard, and a byte from a die picks the word.

Next post: what 1,160 of those nudges do, epoch by epoch, and the 6809 instructions that do one of them.
