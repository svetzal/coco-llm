---
title: "Twenty epochs, then the assembly"
date: 2026-09-23
published: false
description: "Post three of five: what 1,160 nudges do to the model, checkpoint by checkpoint, and then the 6809 instructions that do one of them: two unsigned multiplies, one subtraction, and four shifts."
tags:
  - ai
  - coco
  - "6809"
  - learning
---

[Last post](https://stacey.vetzal.ca/2026/2026-09-21-where-the-numbers-live/) covered:

- The two tables. One row of three numbers per token, one table per window position. Fetch a row from each, add them, and those three numbers are the model's whole input.
- The scoreboard. Three weights and a bias per token, 116 numbers, that turn the input into a score for every token. With the 174 in the tables, that is the 290.
- Scores become shares. On the CoCo they add up to 256, and one drawn byte picks the next token.
- One nudge. The share the right answer got, minus 100%, times a rate I chose, times what each weight contributed. Every one of the 290 moves by that rule.

This post is about doing that 1,160 times, and then about the instructions on the 6809 that do it once.

## Twenty times through

An epoch is one pass through the 58 examples. The run is twenty of them. At a few points along the way I stopped the reference model on the Mac, drew 200 names from it, and scored them. Here is what came out, [two draws per checkpoint](https://github.com/svetzal/coco-llm/blob/main/tools/export_deck_traces.py#L259-L290), with the loss the training loop reported at that point:

| Epoch | Loss | Two of the 200 draws |
| ---: | ---: | --- |
| 0 | 3.26 | II APPLE COMMODORE ACORN 64 II / ARCHIMEDES ARCHIMEDES ARCHIMEDES 400 SINCLAIR COLOR |
| 1 | 3.04 | II APPLE BBC 64 100 COMMODORE / ARCHIMEDES ARCHIMEDES AMIGA |
| 5 | 2.42 | COMPUTER ARCHIMEDES / ATARI ATARI |
| 20 | 1.83 | SINCLAIR AMIGA / COMMODORE ATARI |
| 60 | 1.27 | SINCLAIR BBC / COMMODORE 64 |

The loss falls the whole way. It measures how wrong the guesses are, and by that measure epoch 60 is the best model in the table. Post one showed why I stopped at twenty anyway: at sixty, 143 of the 200 draws were names from the training data, word for word.

Three different failures are in that table, and they leave one at a time.

Repeating a token goes first. At epoch 0, 83 of the 200 draws say the same word twice, ARCHIMEDES ARCHIMEDES ARCHIMEDES. After one pass it is 70. After five, 19. At twenty, 3.

The shape comes second. I wrote down [what a name looks like](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-002-token-model-feasibility.md#L125-L170) before I drew a single sample: two to four tokens, and the first one is a maker, one of ACORN, APPLE, ATARI, COMMODORE, SINCLAIR or TANDY. That is a crude test; TANDY TANDY TANDY passes it. I wrote it before drawing anything so it could not be bent toward a result. One draw in 200 passes it at epoch 0, 12 after one pass, 109 after five, 197 at twenty. From there it has nowhere to go.

Copying comes last. Nothing at epoch 0 or epoch 1 is a training name. At five, 5 of the 200 are. At twenty, 18. At sixty, 143. The model kept training on the same 58 examples, and the shares kept narrowing onto the tokens that actually followed, until the die had almost nothing else to land on.

| Epoch | Repeats a token | Right shape | In the training data | New and the right shape |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 83 | 1 | 0 | 1 |
| 1 | 70 | 12 | 0 | 12 |
| 5 | 19 | 109 | 5 | 104 |
| 20 | 3 | 197 | 18 | 179 |
| 60 | 0 | 199 | 143 | 56 |

Only the last column is the thing I wanted, and it peaks in the middle. The loss cannot tell you that. It rewards the model for giving the right answer a bigger share, and reciting the training data is the biggest share there is. If you want to know whether a model does the job, you have to score the job. I ran a longer sweep [out to 120 epochs](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-002-token-model-feasibility.md#L125-L170), and the useful band is about 13 to 25; fifteen scores 93% against twenty's 90%. Twenty is the number the CoCo build has baked in, so the post and the machine agree.

## What twenty epochs cost

Two numbers set the bill: 20 epochs and 290 parameters. I picked both, and each one is a cost.

Time is multiplies. Each example takes 261 of them, 58 examples a pass, 20 passes: 302,760 multiplies, and 15.8 million instructions for the whole run. Under the emulator at the 1981 clock rate that is a little over a minute. I have not put a stopwatch on the physical machine, so that is the only time I will quote.

Space splits in two. The bytes needed to use the trained model, the forward pass and the die and the 580 bytes of weights, come to 2,516. The bytes needed to train it, the loops and the nudges and the 58 examples and the progress display, are another 730 on top, and none of them are needed once the run ends. The trainer is bigger than the model. That is the shape of every model you have used: somebody paid to train it once, somewhere else, and what ships is the smaller half.

## The multiply

Now the instructions. The 6809 has one multiply instruction, `MUL`. It takes two bytes, each 0 to 255, and produces their product, 0 to 65,025. Eleven clock cycles. It does not know what a negative number is.

The nudge needs a signed multiply: a context number, which can be negative, times how wrong the model was, which usually is. My first version did it the way you would on paper, one bit at a time. It was correct, it was easy to read, and the run took 38.6 million instructions. Here is what replaced it, [from the source](https://github.com/svetzal/coco-llm/blob/main/src/6809/model_forward.asm#L280-L295):

```text
multiply_s8_s16
        sta     multiply_factor
        ldb     1,x
        mul
        std     multiply_product
        lda     multiply_factor
        ldb     ,x
        mul
        addb    multiply_product
        stb     multiply_product
```

Two `MUL`s. The 16-bit number arrives as two bytes, high and low. Multiply the factor by the low byte, keep all sixteen bits of that. Multiply the factor by the high byte, and add the low byte of that product to the high byte of the first. That is the answer, and the run dropped to 15.8 million instructions with every one of the 580 trained bytes unchanged.

Here it is on a step from the run. [At epoch 5, example 37](https://github.com/svetzal/coco-llm/blob/main/tools/export_shift_trace.py), the model was nudging SINCLAIR's third weight. The context number was 26. The error was minus 244, which as two unsigned bytes is 255 and 12.

```text
26 x  12 =   312   bytes   1 :  56
26 x 255 = 6630   bytes  25 : 230
                          ---
add 230 to the 1:        231 :  56
```

The bytes 231 and 56 read as a signed 16-bit number are minus 6,344. And 26 times minus 244 is minus 6,344. The second product's high byte, 25, was never stored. The low sixteen bits are the whole answer, and that is not a lucky property of this example. I checked all 16,777,216 possible input pairs against the true signed product, and [they agree on every one](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-014-6309-multiplier.md#L174-L185).

There is one case the ten lines above get wrong, and the routine's [last five lines](https://github.com/svetzal/coco-llm/blob/main/src/6809/model_forward.asm#L290-L295) fix it:

```text
        tst     multiply_factor
        bpl     multiply_ready
        lda     multiply_product
        suba    1,x
        sta     multiply_product
```

When the factor is negative, `MUL` cannot see that. It takes minus 121 as 135, because those are the same eight bits, and 135 is 256 more than minus 121. So the product is too big by 256 times the multiplier. In sixteen bits, 256 times anything is that thing moved up into the high byte. So the whole error is the multiplier's low byte, sitting one byte too high, and one subtraction from the high byte takes it out. Minus 121 times 60: `MUL` makes 135 times 60, which is 8,100, bytes 31 and 164. Subtract 60 from the 31 and you have 227 and 164, which is minus 7,260. Correct. (That pair is a worked example, not a step from the run; it sits inside the range the run measured.)

Five instructions, and without them the two multiplies would be wrong for every negative context number.

## The learning rate, in eight instructions

The multiply hands back minus 6,344. That is the raw nudge, and it is far too big. The rate I chose, 0.0625, is a sixteenth, and [here it is](https://github.com/svetzal/coco-llm/blob/main/src/6809/training.asm#L133-L140):

```text
        asra
        rorb
        asra
        rorb
        asra
        rorb
        asra
        rorb
```

The 16-bit number sits in two 8-bit registers, A on the left and B on the right. `ASRA` shifts A one bit to the right, keeps its top bit where it was, and drops the bit that fell off the bottom into a flag called the carry. `RORB` shifts B one bit to the right and pulls the carry in at the top. Together they move all sixteen bits one place right, which halves the number. Four pairs divide by sixteen.

| | Bits | Value |
| --- | --- | ---: |
| the gradient | `11100111 00111000` | -6,344 |
| after one pair | `11110011 10011100` | -3,172 |
| after two | `11111001 11001110` | -1,586 |
| after three | `11111100 11100111` | -793 |
| after four | `11111110 01110011` | -397 |

Two things to see in the bits. The left edge stays 1 and copies itself downward, one more each row. That is the "arithmetic" in arithmetic shift, and it is what keeps the number negative as it halves. The other shift instruction, the logical one, would put a 0 there and turn minus 6,344 into 29,596.

The other thing is the bit that falls off the right. The first three pairs drop a 0. The fourth drops a 1, and nothing collects it. Minus 6,344 divided by 16 is exactly minus 396.5; the shifts land on minus 397. That missing half is the bit that fell off. Every number in this model is a whole number, because this machine has no other kind, and the bits falling off the right are the price of that. It has a name, quantization, and the four-bit models running on phones pay it for the same reason.

SINCLAIR's weight was 683. Subtract minus 397 and it is 1,080. On the CoCo a weight is a whole number that stands for itself divided by 4,096, so 683 is 0.1667 and 1,080 is 0.2637. The decimals in the last post were the Mac's floating-point reference; the CoCo holds the same 290 numbers this way, and the run is checked, byte for byte, against what the Mac computed.

Why a sixteenth and not 0.1 or 0.03? Because a shift is two cycles and the 6809 has no divide. The learning rate, the number everyone tunes, is on this machine a choice about which instructions exist. A rate of one eighth would be one fewer pair.

## The same bits, two readings

Look at the two routines side by side. `MUL` read minus 121 as 135. `ASRA` read minus 6,344 as negative and kept the sign. Same kind of bits in both cases; the sixteen bits of minus 6,344 read as 59,192 if you take them unsigned. Nothing in the bits says which. The instruction you choose decides, and that is why the multiply needed a correction and the shift did not.

## The chip that has the instruction

The CoCo 3 on my exhibit table has a Hitachi 6309 in it. It runs 6809 code as it is, and in its own native mode it has instructions the 6809 does not. One of them is `MULD`, a signed 16-by-16 multiply, in one instruction.

On that chip, the sign correction is not faster. It is gone. [Sixteen instructions and 93 cycles become five and 43](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-014-6309-multiplier.md#L63-L81). I measured it on the physical machine on 5 September 2026: 58,000 multiplies over the trained model's own weights, timed with the 60 Hz frame counter, [all three ways](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-014-6309-multiplier.md#L83-L110).

| What ran | Ticks | Against the first row |
| --- | ---: | ---: |
| 6809 code, run as a 6809 | 519 | 1.00x |
| same code, 6309 native mode | 442 | 1.17x |
| the 6309's MULD instruction | 338 | 1.54x |
| MULD at double clock | 168 | 3.09x |

Every row computed the same checksum as the Mac. Native mode alone buys 1.17x. The instruction buys the rest.

That is the multiply, timed on its own. The multiply is [about 46%](https://github.com/svetzal/coco-llm/blob/main/experiments/EXP-014-6309-multiplier.md#L153-L172) of the training run, so on the whole run `MULD` should be worth about 1.26x, and I have not measured that. Nobody made this chip faster at everything. They made it faster at one operation, which is the operation this workload spends its time inside. A GPU is the same decision, made about multiply-and-add and repeated a great many times.

Next post: three things a person can change without touching the loop. The two words it starts from, the size, and the training data.
