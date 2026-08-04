# EXP-011 live demo: editing context without training

## The one idea

The audience should see the distinction happen, not take our word for it:

1. attention answers from the current context;
2. a person edits one context record in RAM; and
3. attention gives a new answer while the model weights remain locked.

Lisa is the through-line. We change `LISA = CODE 2` to `LISA = CODE 6` by
typing `6` into the context editor. There is no random reassignment and no
training step.

## Preflight

```sh
make attention-test
make attention-ui-test
make xroar-test-attention
make present EXP=11
```

Before presenting on physical hardware, rehearse Enter, `E`, `6`, `V`, and
Clear on the actual keyboard. The automated XRoar test reaches the real-ROM
keyboard loop but does not inject key events.

## Beat 1 — Read the current context

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

E: EDIT SELECTED RECORD
ENTER: ASK THIS QUESTION
UP/DOWN: CHOOSE ANOTHER
```

Say:

> “This table is the context—the information available for this interaction.
> It currently says Lisa is code two. Above it, the model weights are locked.”

Ask the room what answer they expect, then press **Enter**.

## Beat 2 — Answer from context

```text
2. ANSWER FROM CONTEXT

QUESTION: LISA

SEARCHED 8 CONTEXT RECORDS

BEST MATCH:
  * LISA = CODE 2

ANSWER: CODE 2

MODEL 751B DID NOT CHANGE

E: CHANGE THE CONTEXT
V: SHOW HOW IT LOOKED
CLEAR: BACK TO CONTEXT
```

Say:

> “Attention found the Lisa record and copied its value. The answer came from
> the visible context. Nothing trained.”

Now ask the useful question:

> “What would it look like to change context rather than train the model?”

Press **E**.

## Beat 3 — Edit context in front of the audience

```text
EDIT CONTEXT - NOT TRAINING

SELECTED CONTEXT RECORD

BEFORE: LISA = CODE 2

TYPE A NEW CODE (0-7)

NEW CODE: _

MODEL 751B IS LOCKED

NUMBER: EDIT CONTEXT
CLEAR: CANCEL
```

Say:

> “This is the missing action. I am changing the information supplied to the
> model. I am not changing the model.”

Type **6**. The CoCo writes `6` into Lisa's value in context RAM and shows:

```text
CONTEXT CHANGED - NO TRAINING

YOU CHANGED THIS RECORD

BEFORE: LISA = CODE 2

AFTER:  LISA = CODE 6

CONTEXT MEMORY WAS EDITED

MODEL 751B DID NOT CHANGE

ENTER: ASK AGAIN
CLEAR: BACK TO CONTEXT
```

Pause. Point to `BEFORE`, `AFTER`, and `MODEL 751B DID NOT CHANGE` in that
order.

> “We can account for the change. I typed six. One byte in context RAM changed.
> The 160 model bytes did not.”

Press **Enter**. The same question now produces `ANSWER: CODE 6`.

Land the central line:

> “Training changes the weights. Prompting changes the context. Attention uses
> the context to produce this answer.”

Think about that a minute.

## Optional depth — Show the lookup

Only press **V** if the room wants the mechanism. The slow view replays one
matching score per Enter press.

> “The answer arrived too quickly to watch. This is a replay of work already
> completed—not the processor pretending to think.”

When Lisa becomes the best match:

> “Attention selected the Lisa record by its key, then copied the value we just
> typed.”

Press **Clear** to return.

## Connect it to an LLM

> “When you edit a prompt or paste in a document, you are doing the same kind
> of thing: changing the model's current context, not retraining its weights.
> Attention helps the model use that temporary information.”

And the caution:

> “The machine will use a wrong context value just as faithfully. Relevant is
> not the same thing as true. Is that an opportunity? It is certainly a reason
> to care about what we put into context.”

## Recovery paths

- If a key does nothing, click XRoar once and try again.
- If the wrong record is selected, use Up or Down until it says Lisa.
- Press Clear to leave the editor without changing context.
- After an edit, press Clear to inspect the changed table or Enter to ask.
- If physical hardware behaves differently, stop making a physical-hardware
  claim and use the emulator as explicitly labelled evidence.

## Claims discipline

Safe claims:

- the Mac exported 160 signed Q4.4 parameter bytes;
- typing `6` changes Lisa's value byte in context RAM;
- that edit does not write to the exported weight tables;
- the same query changes from `CODE 2` to `CODE 6`; and
- direct simulation checks the context edit and both answers.

Do not yet claim measured physical CoCo latency or keyboard compatibility. Do
not claim that the edited record becomes trained knowledge, that the model
understands Lisa, or that this one attention head is a transformer.
