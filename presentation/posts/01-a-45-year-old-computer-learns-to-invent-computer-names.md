---
title: "A 45-year-old computer learns to invent computer names"
date: 2026-09-20
published: false
image: "images/coco1-banner.png"
imageAlt: "An illustration: a silver-haired woman in a dark blazer sits at a night-time workbench lit by neon, one hand on the keyboard of a worn 1981 Radio Shack Color Computer, the other holding a twenty-sided die, smiling at a small green-phosphor monitor whose text is a soft unreadable glow"
description: "My Tandy Color Computer from 1981 starts from random numbers and, a minute later, invents computer names that never existed. Post one of five on how it does that."
tags:
  - ai
  - coco
  - 6809
  - learning
---

Last Sunday I spent the day at an exhibit table with my Tandy Color Computers, rotating through demos: a rock-paper-scissors game that learns how you play, a sentence completer, a melody that finishes the bar you give it. The one I could have left up all day was a screen of sixteen Star Trek episode titles, none of which were ever filmed. I could tell who the Star Trek fans were. They'd stop, read TRIBBLES OF ARCHONS off the green screen, and laugh.

Every one of those demos is the same small piece of arithmetic, running on a machine that arrived under a Christmas tree 45 years ago with 32 kilobytes of memory. The talk I gave that afternoon opened with a promise, and I'll make it again here: by the end of this series you will know exactly how it does that, and you will be unimpressed by it in precisely the right way.

This is post one of five. It covers the training data, what the model's input is at any one moment, and what happens when you let it run. The arithmetic comes next time.

## Same trick as ChatGPT

I've spent the past few years helping people at work figure out what to do with large language models, ever since I started tinkering with them to automate and improve how we do software engineering. The question under most of the other questions is the same one: what is it actually doing in there?

Here's the whole answer. Guess the next word. Measure how wrong you were. Nudge every number a little in the direction that would have made you less wrong. Repeat.

That's it. That's the trick. Everything the big models do rides on that loop, run on a great deal more text with a great many more numbers. So I wanted to see the loop with my own eyes, at a scale where I could point at every part of it, on a machine where nothing could hide. The CoCo was the obvious candidate (it's fair to say it's responsible for my entire career), and 6809 assembly language was the only way it was going to fit.

The model on it has 290 numbers. Not 290 million, or billion. Two hundred and ninety.

## The training data

Let's take a look at the training data...

Eighteen names of vintage computers:

```text
ACORN ARCHIMEDES      ATARI ST              SINCLAIR ZX SPECTRUM
ACORN BBC MICRO       COMMODORE 64          TANDY COLOR COMPUTER
APPLE II              COMMODORE 128         TANDY TRS-80
APPLE LISA            COMMODORE AMIGA       TANDY MODEL 100
APPLE MACINTOSH       COMMODORE PET
ATARI 400             SINCLAIR ZX80
ATARI 800             SINCLAIR ZX81
```

That is an absurdly small training set, and it's still useful. Big models differ from this one by the amount of training data, not by kind.

A computer doesn't have words. It has numbers. So the first thing I had to decide was how to turn those names into numbered pieces. The pieces are called tokens, and here a token is a whole word, because I decided that would suit us to start. Split the eighteen names into words, sort them, number them, and you get 29 tokens, counting one extra that stands in for nothing - indicating empty spaces, and the end of a name.

```text
 0 <END>       8 APPLE       16 LISA        24 TANDY
 1 100         9 ARCHIMEDES  17 MACINTOSH   25 TRS-80
 2 128        10 ATARI       18 MICRO       26 ZX
 3 400        11 BBC         19 MODEL       27 ZX80
 4 64         12 COLOR       20 PET         28 ZX81
 5 800        13 COMMODORE   21 SINCLAIR
 6 ACORN      14 COMPUTER    22 SPECTRUM
 7 AMIGA      15 II          23 ST
```

COMMODORE is 13. Why? Because it's thirteenth when we put the list in alphabetical order. That is all thirteen means. It's a reference, not a quantity, and there's nothing to be learned from doing arithmetic on it. (Next post is about what the model does instead.)

Try asking this model for a word that isn't on that list. There is no graceful answer, because there's no number for it. When a much bigger model gets a word it has never seen, the same thing is happening, just less visibly.

## Two words at a time

The model's input is never a whole name. It is a window, two tokens wide, and the model's only job is to guess what comes next.

Take COMMODORE AMIGA. The window starts empty, which I write as two END markers, and the first thing to guess is COMMODORE. Then the window slides one step: END, COMMODORE, and the thing to guess is AMIGA. Slide again: COMMODORE, AMIGA, and the right answer is END, the name is over.

Three guesses from one two-word name. Do that for all eighteen and you have 58 examples, each one a pair of tokens and the token that actually followed. That's the entire training set.

![A diagram on the CoCo's green screen, in its blocky pixel type, titled COMMODORE AMIGA BECOMES 3 TRAINING EXAMPLES. Across the top, the name as five boxes: END, END, COMMODORE, AMIGA, END. Below, a caption reads: what the model gets, two numbers; the words are for you. Then three rows labelled example 1, 2 and 3. Each row has an amber box with a navy edge holding two cells, and a black cell to the right with PREDICTS written above it. Every cell shows a token number in large type with its word in small type beneath: example 1 holds 0 (END) and 0 (END) and predicts 13 (COMMODORE); example 2 holds 0 (END) and 13 (COMMODORE) and predicts 7 (AMIGA); example 3 holds 13 (COMMODORE) and 7 (AMIGA) and predicts 0 (END). A legend reads: the context window, 2 tokens wide; the token that came next.](images/two-words-at-a-time.png)

When people talk about a model with a 200,000-token context window, it's the same thing, just wider. And if you've ever had a long chat where the model seemed to forget details from the beginning of the conversation, you've watched the window slide.

## Watch it work

When the program loads, the 290 numbers are random. I ask it for a name and it draws from those random numbers, and here is what came out, unedited:

```text
II APPLE COMMODORE ACORN 64 II
LISA ATARI ATARI COLOR MACINTOSH TANDY
ARCHIMEDES ARCHIMEDES ARCHIMEDES 400 SINCLAIR COLOR
```

Nonsense, and the particular kind of nonsense you'd expect from throwing dice: words repeated, no maker at the front, no end in sight.

Then it trains. Fifty-eight examples, twenty times through, which is 1,160 corrections, each one a guess, a measurement of how wrong the guess was, and a nudge. Under the emulator, running at the real machine's clock rate, that takes under a minute. Then I ask for names again, same seed, same request:

```text
SINCLAIR AMIGA
SINCLAIR ATARI
COMMODORE ATARI
TANDY ARCHIMEDES
```

Sinclair never made an Amiga. Commodore never made an Atari. But it's interesting to think, if they had how would it be different? Out of 200 draws at that point, 179 were both new (not one of the eighteen, word for word) and the right shape (two to four words, starting with a maker). The machine has no idea what any of those words mean. It knows which tokens tend to follow which, and that turns out to be enough to make something that reads like a product line.

Sit with that for a minute. Is that impressive? Yes. Is it understanding? No. It's the same distance from understanding as the big models are, and here the distance is short enough to walk.

## Try it yourself

Everything is on GitHub, at [svetzal/coco-llm](https://github.com/svetzal/coco-llm). With the XRoar emulator installed, one command starts the run from random numbers:

```bash
make present EXP=4
```

It trains at the 1981 clock rate, parks when it's done, and draws names when you press a key. Nothing is sped up.

Next post: the training weights, why every word gets three of them, and why it's useful to think in probabilities.
