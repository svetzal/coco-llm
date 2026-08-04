# EXP-005: Prompted marketing language

## Question

If the training corpus contains short advertising phrases instead of computer
names, can two audience-supplied starting words visibly steer the model's
completion?

## Hypothesis

After eighty epochs, the fixed-point reference model will:

- reduce loss from its random initialization;
- complete at least five of six fixed two-word prompts with a recognizable
  continuation from the corpus;
- produce at least one plausible blend rather than simply reproduce every
  phrase verbatim.

The experiment is supported in the integer reference only. A 6809
implementation and direct hardware timing are separate evidence steps.

## Frozen setup

- eight short advertising fragments;
- 38-token vocabulary, including the boundary token;
- two-token context;
- three-value positional embeddings;
- 380 trainable Q4.12 parameters;
- XorShift16 initialization seed 6809;
- eighty online-training epochs;
- deterministic most-likely-token completion;
- six fixed two-word prompts.

The corpus order is frozen because EXP-003 established that online-training
order can change this tiny model's result.

## Corpus provenance

The corpus uses short, recognizable campaign fragments rather than complete ad
copy:

- Commodore's archived radio and television material includes both
  “I Adore My 64” and “Are You Keeping Up with the Commodore” campaigns in the
  [Commodore advertising archive](https://www.commodore.ca/commodore-gallery/commodore-videos-tv-and-radio-adverts/).
- “Why Buy Just a Video Game?” and “The Wonder Computer of the 1980s” came from
  Commodore's VIC-20 advertising featuring William Shatner, also represented in
  that archive.
- “Power Without the Price” was Atari's ST-era slogan, documented in a
  [contemporary 1985 report](https://www.atariarchives.org/cfn/05/11/0142.php).
- “The Computer for the Rest of Us” accompanied the 1984 Macintosh launch.
- “The Biggest Name in Little Computers” appears in Radio Shack's
  [1984 computer catalogue](https://colorcomputerarchive.com/repo/Documents/Catalogs/Radio%20Shack/RSC-10%20Computer%20Catalog%20%281984%29%28Radio%20Shack%29.pdf).
- “Get Your Start in Color Computing” advertised the Radio Shack MC-10.

The source text is
[`data/EXP-005-marketing-language.txt`](data/EXP-005-marketing-language.txt).

## Procedure

1. Build the vocabulary and two-token training examples.
2. Initialize all 380 parameters from seed 6809.
3. Train for eighty epochs using the bit-exact integer reference.
4. Replace the normal boundary-boundary inference context with each two-word
   prompt.
5. Repeatedly select the highest-probability next token until the boundary
   token or six generated tokens.
6. Record the loss, checksum, workload, and completions.

Run the presentation form:

```sh
make present EXP=5
```

## Evidence

Recorded on the macOS reference environment:

- loss: 3.8930 → 0.9719;
- training examples per epoch: 53;
- total matrix multiplications: 1,450,080;
- parameter count: 380;
- vocabulary size: 38;
- reference checksum prefix: `6f9a6c88742221bb`.

| Starting context | Model completion |
| --- | --- |
| `I ADORE` | `MY 64` |
| `ARE YOU` | `KEEPING UP IN LITTLE COMPUTERS` |
| `WHY BUY` | `JUST A VIDEO GAME` |
| `POWER WITHOUT` | `THE PRICE` |
| `GET YOUR` | `START IN COLOR COMPUTING` |
| `THE COMPUTER` | `FOR THE REST OF US` |

All six prompts produce recognizable continuations. Five reproduce the
campaign continuation; `ARE YOU` blends “keeping up” with “little computers.”

## Initial conclusion

Supported in the integer reference.

The audience's words are not a special instruction channel. They simply replace
the model's initial two boundary tokens and therefore change the next-token
probability distribution. The blended completion is especially useful
presentation evidence: the model has learned reusable statistical structure,
not the meaning or historical origin of either campaign.

The expanded run performs about 4.8 times as many multiplications as EXP-004.
It therefore required separate 6809 implementation and timing evidence.

## 6809 follow-up

The model now runs end-to-end in 6809 assembly as a separate EXP-005 binary:

```sh
make model-test-exp5
make xroar-test-exp5
make xroar-exp5
```

The CoCo program:

1. trains all 380 parameters for eighty epochs;
2. verifies all 760 final parameter bytes;
3. pauses before inference;
4. displays six selectable two-token prompts;
5. moves the selector with Up and Down;
6. generates with Enter and advances to the next prompt;
7. leaves previous completions visible.

The prompt and completion occupy adjacent rows. Seed text remains
black-on-green; generated text, including the boundary `#`, uses
green-on-dark. A visible `+` marks a continuation clipped at the 32-column
display edge without changing inference.

The persistent title reads `SAME MODEL - CHANGE THE PROMPT`. It names the
controlled comparison on the artifact: the weights stay fixed after training;
only the audience-selected starting context changes.

The original two-MUL output-update path assumes the context vector fits a
signed byte. EXP-005 first exceeds that assumption during epoch 77. Its
output-weight update therefore uses a three-MUL signed 16×16 low-word routine.
Measured products remain within signed 16-bit range.

Automated evidence:

- 76,275,955 direct-simulator instructions through training, verification,
  menu setup, first prompted completion, and cursor advance;
- all 760 parameter bytes match the fixed-point reference;
- the first prompt generates `MY 64`;
- the selection moves from `I ADORE` to `ARE YOU`;
- XRoar with the verified Color BASIC 1.1 and Extended Color BASIC 1.0 ROMs
  reaches the post-training keyboard handoff;
- interactive XRoar use exercised all six prompts and wrapped selection back
  to the first.

## Updated conclusion

Supported in the integer reference and in XRoar on the 6809.

The expanded vocabulary and human-readable starting context are now
individually presentable. Physical CoCo 1 and CoCo 3 behaviour and stock-rate
wall-clock timing remain unmeasured, so no physical-hardware runtime claim is
yet supported.
