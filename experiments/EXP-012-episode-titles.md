# EXP-012: Star Trek episode titles as a multi-model game corpus

## Status

**Corpus pulled and measured. No model trained, no game designed.** This
records the first thing worth knowing before either: what the corpus is, how
large a vocabulary it forces, and what it will and will not support.

The finding is a caution. The corpus is 79 titles and 259 words, but needs 180
vocabulary tokens to say them — 91% of its words are used exactly once, and
only two adjacent word pairs in the entire corpus ever repeat. A next-word
model trained on this cannot generalize, because there is almost nothing in it
that happens twice. It can only memorize.

That does not sink the idea. It moves the design away from "train a model to
write new episode titles" and toward uses where memorization is the point, or
where the titles are the *material* a game is played with rather than the
thing being learned. Which of those, if any, is still open.

Regenerate with:

```sh
make exp012-corpus
make exp012-vocabulary
```

## Question

Stacey's framing: *"something where maybe we can employ several models in a
game. I want to get a sense of them."*

The game is not designed. The question answered here is the one that gates it:
**is the TOS episode-title corpus a workable base for CoCo-resident models, and
how many words does one need to know?**

Star Trek titles are an attractive candidate for a talk. They are a closed,
finite set; the audience recognizes them; and they look, at a glance, like they
share a grammar — "The <noun> of <noun>", "<verb>ing the <noun>". Whether that
apparent grammar is real enough for a model to learn is the thing to check
before building anything on it.

## Corpus

79 titles: the 78 distinct titles aired over the series' 79 episodes, plus the
unaired first pilot "The Cage". The counts differ because "The Menagerie" is
one title over two episodes.

Uppercased and folded to ASCII, because the CoCo's text screen has no lowercase
and no en dash. Two substitutions were needed: the en dash in "Operation –
Annihilate!" and the typographic apostrophes in "Mudd's Women", "Friday's
Child", "Spock's Brain" and "Plato's Stepchildren". Provenance and rights are
recorded in
[`data/EXP-012-tos-titles-PROVENANCE.md`](data/EXP-012-tos-titles-PROVENANCE.md).

## Measurements, 2026-08-04

Taken with `tools/measure_tos_vocabulary.py`, which splits words with the same
splitter `token_lm.build_vocabulary` uses, so the vocabulary reported is the
one that would actually be paid for.

| | |
| --- | ---: |
| Titles | 79 |
| Word tokens | 259 |
| Words per title | 3.3 (median 3, longest 11) |
| **Vocabulary** | **180 tokens** (179 words + boundary) |
| Words used exactly once | 162 (91% of the vocabulary) |

The commonest words are THE (43), OF (18), then a long flat tail: IS, A, IN,
FOR, TO and AND appear three times each, and almost nothing else appears twice.

### The vocabulary cannot be trimmed

The usual move on a small machine is to cap the vocabulary at the words that
carry most of the corpus. That does not work here:

| Coverage of the corpus | Words needed |
| ---: | ---: |
| 50% | 50 |
| 70% | 102 |
| 90% | 154 |
| 100% | 179 |

Past the first two words the curve is a straight line, one word bought per word
of coverage, because the tail is entirely singletons. Halving the vocabulary
costs a third of the corpus. There is no cheap cut.

### Cost on the machine

At the EXP-002 model shape — context 2, embedding 3, Q4.4 parameter bytes —
carrying the full vocabulary costs:

| | bytes |
| --- | ---: |
| Parameters (1,800 at one byte each) | 1,800 |
| Spelling table (the letters to print) | 1,177 |
| **Total** | **2,977** |

Under 3 KiB, so it fits comfortably — even in the 8 KiB budget of EXP-006, let
alone the 32 KiB of EXP-007. **Size is not the constraint.** The spelling table
being two thirds the size of the parameters is worth noticing: on a corpus this
sparse, most of the model is the dictionary.

### The corpus is vocabulary-heavy and evidence-thin

Against the earlier text corpora:

| Corpus | Lines | Words | Vocabulary | Words per vocabulary entry |
| --- | ---: | ---: | ---: | ---: |
| EXP-005 marketing | 8 | 45 | 38 | 1.2 |
| EXP-001 computer names | 48 | 120 | 78 | 1.5 |
| **EXP-012 TOS titles** | **79** | **259** | **180** | **1.4** |
| EXP-006 completion | 147 | 649 | 178 | 3.6 |
| EXP-007 sentences | 423 | 2,353 | 407 | 5.8 |

EXP-012 has the same vocabulary as EXP-006 with 40% of the evidence.

The decisive number is bigrams. The corpus contains 180 adjacent word pairs and
**174 distinct** ones. Exactly two pairs occur more than once: `OF THE` (6) and
`IN THE` (2). Every other adjacency in Star Trek's entire run of episode titles
happens once and never again.

So the apparent shared grammar is thinner than it looks. 31 of 79 titles do
begin with THE, and 18 contain OF, but only 7 are "THE _ OF _". A model with a
two-word context sees each of its training transitions exactly once. It will
reproduce the corpus and little else, which is memorization dressed as
generation.

## What this rules out and what it leaves

**Ruled out:** training one next-word model on these titles and presenting its
output as newly composed episode names. It would emit training data, and the
audience — who know these titles — would recognize that faster than any other
audience could.

**Not ruled out, and worth considering:**

- *Several models, one corpus each.* The multi-model framing may want several
  small, sharply different corpora rather than one shared corpus, with the game
  being to tell them apart. TOS titles could be one voice among several. On
  that reading the sparseness is a feature: a memorizing model has a very
  distinct accent.
- *Titles as game material rather than training data.* Guess-the-episode,
  match-the-title-to-the-plot, or a model that recognizes rather than generates.
  None of these need the corpus to generalize.
- *Conditioning rather than free generation.* EXP-011 showed the machine can
  use a fact given only in the current context. A title model conditioned on
  something the player supplies is a different proposition from a free-running
  one.

## Open questions

1. **What is the game?** This is Stacey's to answer and everything else waits on
   it. "Employ several models in a game" and "get a sense of them" are two
   different goals — the first is a demo, the second is an evaluation — and they
   pull the design in different directions.
2. **How many models, trained on what?** If the point is to let an audience feel
   the difference between models, the corpora need to differ more than the
   models do.
3. **Does a memorizing model actually sound bad?** Untested assumption. A model
   that reproduces "THE CITY ON THE EDGE OF FOREVER" verbatim might be
   perfectly good theatre if the game is not asking for novelty.
4. **Is 79 titles enough to be worth combining with a second Trek corpus?** TAS,
   TNG and the films would multiply the corpus without leaving the domain. Not
   pursued: it changes the rights position, and the audience recognition that
   makes TOS attractive is weaker for the rest.

## What was not done

No model was trained. No game mechanic was chosen or prototyped. No 6809 code
was written. The bigram result above is a property of the corpus, measured
directly, not an inference from a training run — but the claim that a trained
model *would* memorize follows from it rather than being observed, and should
be labelled that way until a model is actually trained.
