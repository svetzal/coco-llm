# EXP-011 live demo: temporary facts through attention

## Purpose

This demonstration answers one question:

> Can the CoCo use a fact supplied right now without storing that fact in its
> model?

The audience should leave able to distinguish three things:

- **weights** — the learned matching operation;
- **context** — temporary facts available for this interaction; and
- **attention** — the mechanism that selects the relevant fact.

The through-line is `LISA`. In the first context, `LISA = CODE 2`. In the
second, Lisa moves to another row and becomes `CODE 6`. The model identifier
stays `751B` throughout.

## Preflight

Run the automated evidence before rehearsal:

```sh
make attention-test
make attention-ui-test
make xroar-test-attention
```

Launch through the presentation menu:

```sh
make present EXP=11
```

Before using this on stage, validate the Up, Down, Enter, `S`, `V`, and Clear
keys on the actual presentation keyboard and CoCo or emulator. The automated
XRoar test reaches the real-ROM keyboard loop but does not inject key events.

## Screen language

The interface uses more than colour to communicate state:

- `>` is the query selected by the person;
- `*` is the record selected by attention;
- dark text is model-selected material;
- `MODEL 751B` identifies the unchanged 160-byte parameter image; and
- `SLOW VIEW` explicitly labels the paced explanation as a replay, not actual
  inference speed.

## Run of show

### 1. Begin with a question

The initial screen selects Lisa:

```text
COCO CONTEXT MEMORY
TEMP FACTS       MODEL 751B
  AMIGA          CODE 7
> LISA           CODE 2
  TRS-80         CODE 5
  ARCHIMEDES     CODE 1
  PET            CODE 4
  MACINTOSH      CODE 0
  SPECTRUM       CODE 6
  ATARI ST       CODE 3

QUERY LISA
ANSWER -
CONTEXT 1 OF 4
UP/DOWN SELECT  ENTER ASK
S NEW CONTEXT   V SLOW VIEW
```

Suggested words:

> “Fair warning, we are about to call eight arbitrary code assignments facts.
> They are facts only inside this screen. Lisa is code two because I just told
> the machine Lisa is code two.”

Point to `MODEL 751B`.

> “That is the model—the learned numbers. Keep an eye on it.”

Ask the room what answer they expect, then press **Enter**.

### 2. Let it answer

The Lisa row gains `*`, and the lower rows show:

```text
QUERY LISA
ANSWER CODE 2 FROM ROW 2
MODEL UNCHANGED
```

Suggested words:

> “Well, that was not exactly a suspense thriller. Lisa was right there. But
> notice what the screen says: model unchanged. It used the fact; it did not
> train on the fact.”

Pause.

> “Using information is not the same thing as learning it. Think about that a
> minute.”

### 3. Change the context, not the model

Press **S** once. Lisa remains the query but moves to row four and becomes
`CODE 6`:

```text
  ARCHIMEDES     CODE 5
  AMIGA          CODE 1
  SPECTRUM       CODE 3
> LISA           CODE 6
  MACINTOSH      CODE 7
  ATARI ST       CODE 4
  TRS-80         CODE 0
  PET            CODE 2

QUERY LISA
ANSWER -
CONTEXT 2 OF 4
```

Point to `MODEL 751B` again.

> “Same model. Same question. Lisa moved, and now Lisa is code six. What do we
> expect?”

Let the room answer. Press **Enter**.

```text
QUERY LISA
ANSWER CODE 6 FROM ROW 4
MODEL UNCHANGED
```

Then land the central line:

> “The weights taught it how to look. The context gave it something to look
> at. Attention decided where to look.”

### 4. Reveal the mechanism

Press **V**.

> “That answer arrived too quickly to watch, so this next screen is a replay.
> It says slow view because I am slowing down the explanation, not pretending
> the processor took eight dramatic pauses.”

Press **Enter** once per record. The raw signed dot-product score appears on
each row:

| Step | Record | Score | Best so far |
| ---: | --- | ---: | --- |
| 1 | ARCHIMEDES | -2251 | ARCHIMEDES |
| 2 | AMIGA | -0757 | AMIGA |
| 3 | SPECTRUM | -0827 | AMIGA |
| 4 | LISA | +3155 | LISA |
| 5 | MACINTOSH | -0420 | LISA |
| 6 | ATARI ST | -1325 | LISA |
| 7 | TRS-80 | +0390 | LISA |
| 8 | PET | +0676 | LISA |

Do not explain every number. After two or three rows:

> “Each score asks one narrow question: how well does this record's key match
> the query? The score is not truth, confidence, or understanding. It is a
> ranking.”

When Lisa becomes best:

> “There it is. Lisa does not have to be the last thing it saw. The content of
> the row—not merely its position—made that row relevant.”

After the eighth step the screen says `SELECTS CODE 6` and
`ATTENTION COMPLETE`.

> “It selected the row by comparing keys, then copied the value attached to
> that row. That is content-addressed key-value attention in its smallest
> useful form.”

Press **Clear** to return.

### 5. Name the boundary

Close the branch with precision:

> “This is attention. It is not a transformer, and it is definitely not
> ChatGPT running on a CoCo. There is no stack of layers, no residual stream,
> no natural-language answer. We isolated one mechanism so we could actually
> watch it work.”

Then connect it to ordinary model use:

> “When you paste a document into a prompt, the model does not instantly add
> that document to its trained knowledge. The document becomes context.
> Attention helps select pieces of it while producing an answer.”

And the final caution:

> “Attention can retrieve `LISA = CODE 6` just as faithfully as any other
> assignment. Access is not verification. Relevant is not the same thing as
> true. Is that an opportunity? It is certainly a reason to care about the
> context we provide.”

## Optional audience variation

Before the first Enter, use Up and Down to let someone choose another computer.
After asking once, press `S`; the chosen query follows that computer to its new
row. Ask the audience to call the new code before pressing Enter.

Use this only after rehearsing the chosen name across all four contexts. The
scripted Lisa path is the recovery path because its exact positions, values,
and slow-view scores are recorded above.

## Recovery paths

- **A key does nothing:** click the XRoar window once and try again. Do not use
  emulator speed-control shortcuts during the demonstration.
- **The wrong query is selected:** use Up or Down until `QUERY LISA` appears.
- **The wrong context is showing:** press `S` until `CONTEXT 1 OF 4`, then begin
  again. Context two is one additional `S` press.
- **Slow view was opened too early:** it automatically computes the current
  query first. Press Clear, restore the scripted context, and continue.
- **The audience asks whether the model trained on the codes:** point to the
  unchanged `MODEL 751B`, then say that the four visible contexts are program
  data while the 160 parameter bytes encode only the learned matching
  operation.
- **Physical hardware behaves differently:** stop making a hardware claim.
  Use the emulator as explicitly labelled evidence and record the physical
  discrepancy as the next experiment boundary.

## Claims discipline

Safe claims:

- the Mac trained and exported the 160 signed Q4.4 parameter bytes;
- the 6809 calculates forty signed multiply-accumulates per query;
- direct simulation matches 96 reference scores across twelve novel contexts;
- the tested UI keeps the query while changing its row and value;
- the real-ROM XRoar build reaches the keyboard loop; and
- model `751B` remains byte-identical while the context changes.

Do not yet claim:

- measured physical CoCo 1 latency;
- physical keyboard compatibility;
- that the model understands the computer names;
- that the assignments become trained knowledge; or
- that this one attention head is a transformer.
