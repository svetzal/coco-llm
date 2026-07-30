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

## Conclusion

Supported in the integer reference.

The audience's words are not a special instruction channel. They simply replace
the model's initial two boundary tokens and therefore change the next-token
probability distribution. The blended completion is especially useful
presentation evidence: the model has learned reusable statistical structure,
not the meaning or historical origin of either campaign.

The expanded run performs about 4.8 times as many multiplications as EXP-004.
It is not yet supported for live stock-rate CoCo use. The next experiment must
either reduce its training work or demonstrate an honest presentation runtime
on the 6809 before this corpus moves into the assembly program.
