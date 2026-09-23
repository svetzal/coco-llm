---
title: "The prompt, the size, the training data"
date: 2026-09-25
published: false
description: "Post four of five: three things a person can change without touching the loop. Two starting words steer the output and change nothing in the model; a model a hundred times bigger attempts more without getting better at what it already did; and the training data, including the order it is in, decides what the model favours."
tags:
  - ai
  - coco
  - "6809"
  - learning
---

[Last post](https://stacey.vetzal.ca/2026/2026-09-23-twenty-epochs-then-the-assembly/) covered:

- Twenty passes through the 58 examples. Repeating a token goes first, the shape of a name comes second, and copying the training data arrives last. The loss falls the whole way and cannot tell you any of that.
- What the run costs. 302,760 multiplies, and a trainer bigger than the model it trains.
- The 6809 instructions for one nudge. Two unsigned multiplies and a subtraction make a signed one; four shift pairs are the learning rate; the bit that falls off the right is quantization.

The loop is the same in every post so far. This post holds it fixed and changes one thing at a time: the words it starts from, the number of parameters, and the training data. Each change is a decision a person made, and each one shows up in what comes out.

## The prompt

This needs a second model, because eighteen computer names have nothing in them a person could steer. The second model is the same code, the same loop and the same machine, retrained on eight lines of 1980s computer advertising:

```text
THE WONDER COMPUTER OF THE 1980S
GET YOUR START IN COLOR COMPUTING
I ADORE MY 64
ARE YOU KEEPING UP WITH COMMODORE
THE COMPUTER FOR THE REST OF US
POWER WITHOUT THE PRICE
THE BIGGEST NAME IN LITTLE COMPUTERS
WHY BUY JUST A VIDEO GAME
```

Those eight lines are everything this model trained on. They make 38 tokens, 53 examples and 380 parameters, and I trained it for 80 epochs. Only four words carry over from the first model, 64, COLOR, COMMODORE and COMPUTER, and even those got new numbers. COMMODORE was 13; here it is 9, because that is where it lands alphabetically in this list. Nothing about the first model came with it.

Eighty epochs on eight lines is a lot of training, and you already know what that does. This model recites. Post one called that overfitting, and for a model whose job was inventing names it was the failure. This model's job is finishing famous slogans, so reciting is the assignment. Whether overfitting is a problem is a decision about the task.

Now hold the model still. All 380 numbers, [checksum `6f9a6c88742221bb` before and after](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-005-prompted-marketing-language.md#L88-L107). The same seed. And no die this time: it takes the widest stretch every time, so the same start always gives the same answer. The one thing that changes is the first two tokens in the window before it starts.

| I put in the window | It produced |
| --- | --- |
| nothing | WHY BUY JUST A VIDEO GAME |
| I ADORE | MY 64 |
| ARE YOU | KEEPING UP IN LITTLE COMPUTERS |
| WHY BUY | JUST A VIDEO GAME |
| POWER WITHOUT | THE PRICE |
| GET YOUR | START IN COLOR COMPUTING |
| THE COMPUTER | FOR THE REST OF US |

Here is the machine doing it, recorded from the emulator at the real clock rate after the training had parked. One keypress opens the list; each Enter completes the selected prompt and moves to the next.

<video controls preload="metadata" playsinline style="width: 100%; max-width: 640px; display: block; margin: 0 auto; image-rendering: pixelated;" src="/2026/images/coco-llm-4-prompts.mp4">
The emulator completing the six prompts, one Enter each.
</video>

Five of the six are training lines, word for word, which is the overfit doing its job. ARE YOU is the one that is not. It starts inside Commodore's line and ends inside Radio Shack's, KEEPING UP IN LITTLE COMPUTERS, a slogan nobody ran. The model had no memorized continuation for those two words, so its shares blended two companies' copy.

That is what a prompt is. It is the first few tokens of the output, handed over before the machine starts. It is not an instruction and it is not training; the 380 numbers are identical on both sides of the table. When you type into a chat window, paste in a document, or a product adds a system prompt or a memory feature on your behalf, all of it goes into the same place: the context window, in front of whatever the model produces next. Asking teaches it nothing. Training changed the weights exactly once, before you arrived.

You can pick the prompts yourself. `make present EXP=5` trains the model and then puts the six on screen under the title SAME MODEL - CHANGE THE PROMPT. That is [EXP-005, the prompted marketing completions](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-005-prompted-marketing-language.md).

## The size

The second lever is the number of parameters, and this is where training leaves the CoCo. The model in this section is over a hundred times bigger than the one that trained on stage. The Mac trained it, and the CoCo only predicts. The screen says so: MAC TRAINED - COCO PREDICTS. That is how the model you use every day was made too. Somebody trained it once, somewhere else, and shipped the weights.

The model is a sentence completer, [EXP-007, the all-RAM sentence completer](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-007-all-ram-sentence-completion.md). It trained on 423 sentences about this computer:

```text
WELCOME TO THE WORLD OF RETRO COMPUTING.
WELCOME TO THE COLOR COMPUTER!
WELCOME HOME, COMPUTER FAN.
ARE YOU READY TO COMPUTE?
YES, THE COMPUTER IS READY.
NO, THE CASSETTE IS NOT READY.
PRESS ENTER TO START.
PRESS TAB TO COMPLETE THE PHRASE.
```

Its shape against the marketing model:

| | the marketing model | this one |
| --- | ---: | ---: |
| parameters | 380 | 32,385 |
| vocabulary | 38 tokens | 255 |
| context window | 2 tokens | 5 |
| trained on | this machine | the Mac, once |

The vocabulary is 255 because a token identifier is one byte, and that byte has to cover everything. One seat for the boundary, six for punctuation, and 248 for the words the sentences use most. The punctuation seats are the decision worth noticing: a period is a token, sitting in the window like any word, which is how the model can learn that sentences stop and what tends to follow a stop. I chose what counts as a token, the same way I chose whole words back in post one. The 32,385 parameters ship as 16,193 bytes, two to a byte, and unpack into the memory where BASIC's ROM normally sits.

You type, press the right arrow, and it ranks your next word. Type THE MODEL CAN and it offers SUGGEST, BE, REMEMBER. Type RUN THE PROGRAM with the period and the top suggestion is the end-of-phrase token: it has learned that a period is usually the end. (My first interface hid that token, because the same number also meant no suggestion. The model said stop and the product said pick something else, and made the model look foolish. I fixed the interface and retrained nothing. Some apparent model failures are product decisions.)

The window is still the window. Type I KNOW THE OLD MODEL CAN and note the three suggestions. Type WE KNOW THE OLD MODEL CAN and you get the same three, because the model sees five tokens and both I and WE fell out the far side. To this model those are the same sentence.

Here are those four phrases typed into the emulator at the real clock rate. The pause after each right arrow is the CoCo scoring 255 tokens.

<video controls preload="metadata" playsinline style="width: 100%; max-width: 640px; display: block; margin: 0 auto; image-rendering: pixelated;" src="/2026/images/coco-llm-4-completer.mp4">
The emulator running the sentence completer: THE MODEL CAN, then I KNOW and WE KNOW, then RUN THE PROGRAM with a period.
</video>

So, is bigger better? I measured exactly that, because I built this completer twice. The first was [EXP-006, the 8 KiB completion workbench](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-006-pretrained-tab-completion.md): 8,188 parameters, 178 tokens, a four-token window. The second is this one, four times the parameters. Same task, scored the same way, on sentences neither model trained on.

| | 8 KiB model | 32 KiB model |
| --- | ---: | ---: |
| the right word was in the top three | 59.3% | 60.0% |
| typing saved by accepting suggestions | 58.8% | 51.7% |

Four times the parameters bought seven tenths of a point on the first line, and lost seven points on the second. The extra room went to a bigger vocabulary, a longer window and punctuation. Bigger let it attempt more. It was not better at what it already did.

Both of those were called shots, and both missed. The 8 KiB model was supposed to reach 70% on the first line and got 59.3. The 32 KiB model was supposed to save 60% on the second and got 51.7. The experiments record the miss and keep the working prototype, which is what an honest measurement looks like. The scores are offline simulations on held-out text; nobody has timed a person at the keyboard.

Size is a decision with a bill. More parameters retain more patterns. They do not add understanding, and they do not necessarily add skill at the thing you wanted.

## The training data

The third lever is the one that decides what the model favours, and it is the one people least expect to be a lever at all.

[EXP-003, the fan-corpus bias runs](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-003-training-data-bias.md), trains five models that are identical in every way but one. Same architecture, 310 parameters over a 31-token vocabulary. Same random starting numbers, seed 6809. Same 1,620 nudges. Same twenty seeds for the die when they draw. The only thing that differs is the training data.

The first three are fans. Each trained on 18 names from one maker, repeated, so the file reads APPLE, APPLE, APPLE down the whole column:

```text
apple fan            commodore fan        tandy fan
APPLE II             COMMODORE 64         TANDY TRS-80
APPLE LISA           COMMODORE AMIGA      TANDY 1000
APPLE MACINTOSH      COMMODORE PET        TANDY COCO
```

Each one drew twenty names. I counted the first word:

| Training data | APPLE | COMMODORE | TANDY | other | one of the 20 |
| --- | ---: | ---: | ---: | ---: | --- |
| apple fan | 16 | 0 | 0 | 4 | APPLE MACINTOSH |
| commodore fan | 0 | 15 | 0 | 5 | COMMODORE AMIGA |
| tandy fan | 0 | 1 | 14 | 5 | TANDY COCO |

Each model comes out a fan of whoever wrote its data. Nobody wrote a preference into any of them; the data is the preference. And look at the one COMMODORE the Tandy fan drew. Training on Tandy names made the other makers unlikely, not impossible. The words were still in the vocabulary, and nothing in the weights fences a word off. The bias is a lean, not a wall.

The last two models are the hard half. Both train on all 54 names, 18 per maker, balanced. The only difference between them is the order of the file.

| Training data | APPLE | COMMODORE | TANDY | other | loss at the end |
| --- | ---: | ---: | ---: | ---: | ---: |
| all three, one block after another | 0 | 1 | 14 | 5 | 2.18 |
| all three, shuffled together | 10 | 6 | 3 | 1 | 0.88 |

Laid end to end, Apple then Commodore then Tandy, the model comes out a Tandy fan: 14 of 20, the same as the model that only ever trained on Tandy. Every pass through the file ends with the Tandy block, and last is what stuck. Shuffled together, the same 54 names spread out, and the loss finishes at 0.88 instead of 2.18. The bad order trained worse as well as narrower.

Nobody chose to make that fourth model a Tandy fan. Somebody decided how to lay out the files, and that was the decision, and they almost certainly did not know they were making it.

The same lever has a commercial name. Fine-tuning is more training, on data somebody chose. A company fine-tuning a model on its own documents is choosing training data, and it inherits everything on this table, the order included.

## One sentence

Three levers, and they share a sentence: everything that changed traces to a decision a person made. The two words in the window. The number of parameters, and who paid to train them. The training data, and the order it came in. The model did not decide any of it. It could not have; there is nothing in there that decides.

Next post: the same machinery on things that are not computer names. Sixteen episode titles that were never filmed, a game that learns how you play, a fact you hand it right now, and a tune.
