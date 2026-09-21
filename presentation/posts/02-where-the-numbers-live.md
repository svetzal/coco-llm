---
title: "Where the numbers live"
date: 2026-09-27
published: false
image: "images/coco-llm-2-banner.png"
imageAlt: "An illustration: to be generated"
description: "COMMODORE is token 13, and thirteen means nothing. Post two of five: the two tables where the model's numbers live, why each word gets three, what a parameter is, what one step of training changes, and how a score becomes something you can roll a die on."
tags:
  - ai
  - coco
  - "6809"
  - learning
---

Last time I left you holding one fact: COMMODORE is token 13, because it's thirteenth when the words are sorted, and that is all thirteen means. ZX80 is 27 and ZX81 is 28, next to each other and genuinely related, which is a coincidence. APPLE is 8 and ARCHIMEDES is 9, just as close, and one is Apple and the other is Acorn. There is nothing to learn from doing arithmetic on a name.

So what does the model do arithmetic on?

When I built the slide that shows one training step, it showed three numbers arriving from nowhere. The figure asserted them and couldn't say where they came from, and that is exactly the kind of thing this whole project exists to not do. So I built the slide before it, the one this post is about. Give every token some numbers that *can* be compared, and show where they live.

## Two tables

They live in a table. Two tables, in fact, because the context window is two tokens wide, and each position in the window gets its own.

Each table has 29 rows, one per token, and each row holds three numbers. That's it. When the window holds END then COMMODORE, the machine fetches the END row from the first table and the COMMODORE row from the second table, and adds them:

```text
position 1, <END>       -0.0286   -0.0187   +0.0583
position 2, COMMODORE   -0.0009   -0.0266   -0.0168
                        -------   -------   -------
add them                -0.0295   -0.0453   +0.0415
```

![Two tables side by side on the CoCo's green screen, in its pixel type, titled TWO TABLES, ONE PER WINDOW POSITION. Each lists tokens with three signed numbers beside them. In the position 1 table the END row is highlighted in amber; in the position 2 table the COMMODORE row is. Below, the two fetched rows are written out and added, with the sum in three black cells: minus 0.0295, minus 0.0453, plus 0.0415. A caption reads: these three numbers are all the model knows about its context, no arithmetic beyond the addition.](images/where-the-numbers-live.png)

Those are the real rows, exported from the model before training. No arithmetic beyond the addition. The three numbers at the bottom are what the training step, further down, works on, and now you know where they came from.

Each row of three is a word's embedding. That's the word everyone has heard, and this is all it means here: the numbers a token owns. When a vector database sells you "embeddings", it is selling rows like these, longer.

Notice that COMMODORE has a different row in each table. In position 1 its row is +0.0781, +0.0250, +0.0173. In position 2 it's the row above. That is what "positional" means, and it's why COMMODORE AMIGA and AMIGA COMMODORE are not the same thing to the machine. Word order lands here.

Two positions, 29 tokens, three numbers each: 174 numbers. Most of this model is a lookup table.

## Why three?

One number would put a word on a line: more of one thing, or less. Three put it in a space, so words can be near each other in more than one way at once. GPT-3's embedding is 12,288 numbers long where ours is three. Same idea, more room.

Why not more room, then? Because every extra number is another 29 by 3 multiplies per example, and on the CoCo a multiply instruction costs 11 cycles at 0.89 MHz. I priced the widths before choosing:

| numbers per word | parameters | multiplies to train | MUL time alone |
| ---------------: | ---------: | ------------------: | -------------: |
| 1 | 116 | 100,920 | 1.2 s |
| 2 | 203 | 201,840 | 2.5 s |
| 3 | 290 | 302,760 | 3.7 s |
| 4 | 377 | 403,680 | 5.0 s |
| 5 | 464 | 504,600 | 6.2 s |
| 6 | 551 | 605,520 | 7.4 s |

Those times are floors, multiply instructions only, not runtimes. The runtime is the two minutes you watched last time, and most of it is everything around the multiplies.

Six would have fit the budget I'd set myself, three minutes of training on stage. I chose three to see how small a model could be and still be useful, and the rule I gave myself was to widen it only when the evidence said quality was insufficient. It never said that.

The other choice I priced was the one I built first and threw away. Make a token a single character instead of a whole word and the model has to predict every letter: 12,859,560 multiplies, 158 seconds of bare MUL instructions against a 180-second budget. That's before any of the code around them. It couldn't fit, so it didn't. That is what a budget is for.

## What is a parameter?

You've now seen most of them, so let's count.

```text
 2 window positions x 29 tokens x 3 numbers  =  174   the two tables
                     29 tokens x 3 numbers  =   87   a row for every token it can predict
                     29 tokens              =   29   a starting nudge per token
                                               ----
                                                290
```

A parameter is one number that training is allowed to change. That's all the word has ever meant. This model has 290. GPT-3 had 175 billion; DeepSeek-V3 has 671 billion. Same word, same meaning, and every one of ours is accounted for on that list.

Notice that the vocabulary size and the numbers-per-token both appear in every line. Every term in that sum is a decision somebody made: how wide the window is, how many tokens exist, how many numbers describe each one. None of them was handed down.

## A score for every token

The second table on that list is the scoreboard. It has a row of three numbers for every token the model might predict, plus that token's starting nudge. To score a token, multiply the three context numbers by the token's three weights, add the nudge, and you have a score. Do it 29 times and you have a score for every token.

That's 87 multiplies, and it's where the 6809's multiply instruction earns its keep. Next post shows it doing one.

Before training, the scores are all within a whisker of zero, because the tables are random and small. Here are the shares they turn into for the window END, COMMODORE, where the right answer is AMIGA:

```text
TRS-80   3.49%    <- the model's favourite, barely
128      3.48%
ZX80     3.48%
ATARI    3.48%
...
AMIGA    3.45%    <- the right answer, in the middle of the pack
```

Twenty-nine tokens, each near one in twenty-nine. The model has no opinion yet. Training is the process of giving it one, and it's coming up.

## Scores become shares

Those percentages are what a score turns into once you push it through a softmax, and this is the part I want you to actually get, because it's where probability enters the story.

Suppose three tokens have raw scores of 3, 2 and 1. A score of 3 doesn't mean 3%, or three votes, or three units of confidence. Scores have no human-friendly scale. Softmax makes every score a positive weight, then divides each weight by the total, so the results are shares of 100%: about 67%, 24% and 9%. It keeps the order, it makes everything positive, and it exaggerates the lead: a modest score advantage becomes a much clearer share.

Why "soft"? A hard maximum would give the winner everything. Softmax lets the strongest choice lead while the others stay possible.

And here's the thing softmax does not do: it doesn't choose. It hands you shares. Something else has to draw.

On the CoCo the shares add up to 256 instead of 100, so that every token owns a stretch of a line from 0 to 255 as wide as its share. Then the machine draws one byte, and whatever stretch the byte lands on is the next token. That's the die.

## Training is a nudge

Now the part you've been waiting for since the two tables: what training actually changes.

Remember the window END, COMMODORE, where the right answer is AMIGA. The model gave AMIGA 3.45%, one in twenty-nine, no opinion. Training is one step, done over and over: score, compare with the right answer, nudge every weight a little in the direction that would have raised the right answer's share. Here is the one step, with the real numbers.

How wrong was it? AMIGA should have had 100% and got 3.45%, so it was wrong by 0.9655. That number is the correction's size, and every weight's change is that, times a rate, times what the weight contributed.

Take AMIGA's row in the scoreboard, its three weights. They were multiplied by the three context numbers, minus 0.0295, minus 0.0453 and plus 0.0415, to make AMIGA's score. Each weight's contribution was its own context number, so each gets nudged by that number, scaled:

```text
context numbers      -0.0295   -0.0453   +0.0415

AMIGA's weights
  before             +0.1214   -0.0705   +0.0325
  change             -0.0017   -0.0027   +0.0025
  after              +0.1197   -0.0732   +0.0350

change = 0.0625  x  0.9655  x  the context number above
         a rate     how wrong   what this weight contributed
         I chose    it was
```

Look at the signs. Where the context number was negative the weight went down, and where it was positive the weight went up. Every weight moves the way that would have raised AMIGA's score, and the sign of each change is the sign of its incoming number. That is the whole rule.

The rate, 0.0625, is a sixteenth. I chose it, and I chose it because dividing by sixteen is four shift instructions on a 6809, which is why it isn't something tidier like a tenth.

The same step reaches back into the two tables, too. The END row in position 1 and the COMMODORE row in position 2 both get nudged, by how much each of the three context numbers contributed to every score that came out wrong. After the step, fetch and add those rows again and you get minus 0.0118, minus 0.0561, plus 0.0477. Those rows started random. Nudges like this are what make them mean something.

The result of all that: AMIGA now has 3.68%. Up from 3.45. That is the honest size of one step, and there are 1,160 of them in a run. Every one of the 290 parameters moves by this rule, and nothing else ever touches them.

## Roll it

Here is the die being rolled, from the run you watched last time, after all 1,160 of those steps. Seed 6809 drew three bytes: 50, 12, 119.

The first draw, 50, landed on COMMODORE, which owned 27 of the 256. TANDY owned 131, more than half the line, and lost. The second draw, 12, landed on 128, which owned 17; the favourite there was PET with 25. The third draw, 119, landed on END, which by then owned 228 of 256. The model was sure the name was over.

![Three horizontal lines from 0 to 255 on the CoCo's green screen, titled SEED 6809 DREW 50, 12, 119. Each line is divided into stretches, one per token, as wide as its share. On the first line a navy arrow at 50 lands on COMMODORE's stretch, highlighted amber, while TANDY's stretch covers half the line. On the second, an arrow at 12 lands on 128. On the third, an arrow at 119 lands on END, which covers almost the whole line. The bottom reads: THE NAME: COMMODORE 128.](images/roll-it.png)

COMMODORE 128. A real name; it's in the training data. It's also the first name on the screen at the end of the video.

Seed 6810 drew 177, 110 and 29 from the same table, and got TANDY COMPUTER. Same weights, same rows, different bytes. The eleven names on that screen are eleven paths through one table.

Two things worth knowing about the die. First, for the first two tokens, END's stretch is handed to the favourite, so a name is never one word long. That rule is in the code, not in the weights. Second, you don't have to roll at all. Skip the draw and take the widest stretch every time, and you get the same name every time. That's called greedy decoding, and it's what temperature zero means. Temperature, when you see the setting, rescales the scores before they become shares: higher narrows the fat stretch and widens the thin ones, lower does the reverse, and zero is greedy. Same line, cut differently.

This is why I said it's useful to think in probabilities. The model never answers. It hands over shares, and a draw picks. If you take the biggest every time you get one answer forever; if you draw, you get variety, and now and then you get TANDY ZX80. Neither is the model being clever or being wrong. It's the die.

Two hundred and ninety numbers. A hundred and seventy-four of them are a lookup table, a hundred and sixteen are a scoreboard, and a byte from a die picks the word. That's the whole of using it.

Next post: what 1,160 of those nudges do, epoch by epoch, and the 6809 instructions that do one of them.
