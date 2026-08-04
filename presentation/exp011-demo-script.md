# EXP-011 live demo: temporary facts through attention

## The one idea

The model already knows **how to find a matching record**. The screen gives it
temporary records to search. Attention finds the record matching the question
and returns that record's value.

This is a three-beat demonstration:

1. give it facts;
2. ask one question; and
3. change the facts without changing the model.

Lisa is the through-line. In context one, `LISA = CODE 2`. In context two,
`LISA = CODE 6`. Model `751B` never changes.

## Preflight

```sh
make attention-test
make attention-ui-test
make xroar-test-attention
make present EXP=11
```

Before presenting on physical hardware, rehearse Enter, `S`, `V`, and Clear on
the actual keyboard. The automated XRoar test reaches the real-ROM keyboard
loop but does not inject key events.

## Beat 1 — Give it facts

The opening screen has one job: establish the information available **right
now**.

```text
1. GIVE IT TEMPORARY FACTS
MODEL 751B       CONTEXT 1 OF 4
  AMIGA           = CODE 7
> LISA            = CODE 2
  TRS-80          = CODE 5
  ARCHIMEDES      = CODE 1
  PET             = CODE 4
  MACINTOSH       = CODE 0
  SPECTRUM        = CODE 6
  ATARI ST        = CODE 3

QUESTION: LISA

ENTER: ASK THIS QUESTION

UP/DOWN: CHOOSE ANOTHER
```

Say:

> “This first screen is just a tiny document. Eight facts that exist for this
> conversation. Lisa is code two because the document says Lisa is code two.”

Point first to `LISA = CODE 2`, then to `MODEL 751B`.

> “That number is the model. Keep an eye on it. What should the answer be?”

Let the room say “code two,” then press **Enter**.

## Beat 2 — Ask one question

The facts disappear. The result gets the whole screen.

```text
2. ATTENTION FOUND AN ANSWER

QUESTION: LISA

SEARCHED 8 TEMPORARY FACTS

BEST MATCH:
  * LISA = CODE 2

ANSWER: CODE 2

MODEL 751B DID NOT CHANGE

S: CHANGE THE FACTS
V: SHOW HOW IT LOOKED
CLEAR: BACK TO THE FACTS
```

Say:

> “It searched the temporary facts, found the Lisa record, and copied the
> value attached to it. It used the fact. It did not learn the fact.”

Pause on `MODEL 751B DID NOT CHANGE`.

> “Using information is not the same thing as training. Think about that a
> minute.”

Do not open the score replay yet. First establish that the answer follows the
context.

## Beat 3 — Change the facts, not the model

Press **S**. The interface returns to the facts, now with an explicit changed
heading:

```text
3. THE FACTS HAVE CHANGED
MODEL 751B       CONTEXT 2 OF 4
  ARCHIMEDES      = CODE 5
  AMIGA           = CODE 1
  SPECTRUM        = CODE 3
> LISA            = CODE 6
  MACINTOSH       = CODE 7
  ATARI ST        = CODE 4
  TRS-80          = CODE 0
  PET             = CODE 2

QUESTION: LISA

ENTER: ASK THIS QUESTION
```

Point to three things, in order:

1. Lisa moved;
2. Lisa is now code six; and
3. the model is still `751B`.

Ask what the new answer should be, then press **Enter**.

> “Same model. Same question. Different temporary facts. Now the answer is
> code six.”

Land the central line:

> “The weights taught it how to look. The context gave it something to look
> at. Attention decided where to look.”

That completes the main demonstration.

## Optional depth — Show how it looked

Only press **V** if the room wants the mechanism. This is progressive
disclosure, not a required fourth beat.

The slow view reveals one signed matching score per Enter press. Say:

> “The answer arrived too quickly to watch. This is a replay of work already
> completed—not the processor pretending to think.”

After two or three scores:

> “Each number asks one narrow question: how well does this key match Lisa?
> It is a ranking, not truth, confidence, or understanding.”

When Lisa becomes the best match:

> “There it is. Attention selects the matching row, then copies that row's
> value.”

Press **Clear** to return to the answer.

## Close with the boundary

> “This is attention, but it is not a transformer and it is definitely not
> ChatGPT running on a CoCo. We isolated one useful mechanism so we could
> actually watch it work.”

Then connect it to familiar use:

> “When you paste a document into a prompt, the document becomes context. It
> does not instantly become trained knowledge. Attention helps the model use
> pieces of that context while producing an answer.”

And the caution:

> “Attention would retrieve a false assignment just as faithfully. Relevant
> is not the same thing as true. Is that an opportunity? It is certainly a
> reason to care about the context we provide.”

## Recovery paths

- If a key does nothing, click XRoar once and try again.
- If the wrong question is selected, use Up or Down until it says Lisa.
- Press Clear to return from an answer or replay to the facts.
- Press `S` until context one appears if you need to restart.
- If physical hardware behaves differently, use the emulator as explicitly
  labelled evidence and stop making a physical-hardware claim.

## Claims discipline

Safe claims:

- the Mac exported 160 signed Q4.4 parameter bytes;
- the 6809 performs forty signed multiply-accumulates per question;
- direct simulation matches 96 scores across twelve novel contexts;
- changing context preserves the question and changes its answer; and
- model `751B` remains byte-identical while the context changes.

Do not yet claim measured physical CoCo latency or keyboard compatibility. Do
not claim that the assignments become trained knowledge, that the model
understands the names, or that this one attention head is a transformer.
