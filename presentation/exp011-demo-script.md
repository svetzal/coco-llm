# EXP-011 live demo: finding an exhibit through attention

## The one idea

The model already knows **how to find a matching record**. A temporary museum
map says which shelf holds each computer exhibit. Attention finds the exhibit
matching the request and returns the shelf written on today's map.

This is a three-beat demonstration:

1. load today's exhibit map;
2. ask where Lisa is; and
3. load a different map without changing the model.

Lisa is the through-line. The first map says `LISA = SHELF 2`. The second says
`LISA = SHELF 6`. Model `751B` never changes.

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

## Beat 1 — Load today's map

The opening screen establishes where the shelf number comes from. Today's
map—not the model—assigns Lisa to shelf two.

```text
1. LOAD TODAY'S EXHIBIT MAP
MODEL 751B       MAP 1 OF 4
  AMIGA           = SHELF 7
> LISA            = SHELF 2
  TRS-80          = SHELF 5
  ARCHIMEDES      = SHELF 1
  PET             = SHELF 4
  MACINTOSH       = SHELF 0
  SPECTRUM        = SHELF 6
  ATARI ST        = SHELF 3

LOOKING FOR: LISA

ENTER: FIND THIS EXHIBIT

UP/DOWN: CHOOSE AN EXHIBIT
```

Say:

> “Imagine a little computer museum. The exhibits move around, so today's map
> tells us which shelf holds each machine. Lisa is on shelf two because the map
> says Lisa is on shelf two.”

Point first to `LISA = SHELF 2`, then to `MODEL 751B`.

> “That other number is the model. Keep an eye on it. If I ask where Lisa is,
> what should the answer be?”

Let the room say “shelf two,” then press **Enter**.

## Beat 2 — Find Lisa

The map disappears. The result gets the whole screen.

```text
2. ATTENTION FOUND THE RECORD

LOOKING FOR: LISA

SEARCHED TODAY'S EXHIBIT MAP

BEST MATCH:
  * LISA = SHELF 2

LOCATION: SHELF 2

MODEL 751B DID NOT CHANGE

S: LOAD A DIFFERENT MAP
V: SHOW HOW IT LOOKED
CLEAR: BACK TO THE MAP
```

Say:

> “It searched the map, found the Lisa record, and copied the shelf attached
> to it. Shelf two came from the map. It did not come from the model.”

Pause on `MODEL 751B DID NOT CHANGE`.

> “Using information is not the same thing as training. Think about that a
> minute.”

Do not open the score replay yet. First establish that the location follows
the map.

## Beat 3 — Load a different map

Press **S**. This loads a second prewritten map; nothing is randomized at
runtime. In the scenario, the museum rearranged its exhibits:

```text
3. A DIFFERENT MAP ARRIVED
MODEL 751B       MAP 2 OF 4
  ARCHIMEDES      = SHELF 5
  AMIGA           = SHELF 1
  SPECTRUM        = SHELF 3
> LISA            = SHELF 6
  MACINTOSH       = SHELF 7
  ATARI ST        = SHELF 4
  TRS-80          = SHELF 0
  PET             = SHELF 2

LOOKING FOR: LISA

ENTER: FIND THIS EXHIBIT
```

Point to three things, in order:

1. a different map arrived;
2. Lisa moved to shelf six; and
3. the model is still `751B`.

Ask where Lisa is now, then press **Enter**.

> “Same model. Same exhibit. Different map. The museum moved Lisa, so the
> answer is now shelf six.”

Land the central line:

> “The weights taught it how to search. The map gave it somewhere to search.
> Attention found the relevant record.”

That completes the main demonstration.

## Optional depth — Show how it searched

Only press **V** if the room wants the mechanism. The slow view reveals one
signed matching score per Enter press.

> “The answer arrived too quickly to watch. This is a replay of work already
> completed—not the processor pretending to think.”

After two or three scores:

> “Each number asks one narrow question: how well does this exhibit name match
> Lisa? It is a ranking, not truth, confidence, or understanding.”

When Lisa becomes the best match:

> “There it is. Attention selects the matching map record, then copies its
> shelf.”

Press **Clear** to return to the answer.

## Close with the boundary

> “This is attention, but it is not a transformer and it is definitely not
> ChatGPT running on a CoCo. We isolated one useful mechanism so we could
> actually watch it work.”

Then connect it to familiar use:

> “When you paste a document into a prompt, that document is like today's map.
> It becomes context; it does not instantly become trained knowledge. Attention
> helps the model use relevant pieces of it while producing an answer.”

And the caution:

> “Attention would retrieve a wrong map entry just as faithfully. Relevant is
> not the same thing as true. Is that an opportunity? It is certainly a reason
> to care about the context we provide.”

## Recovery paths

- If a key does nothing, click XRoar once and try again.
- If the wrong exhibit is selected, use Up or Down until it says Lisa.
- Press Clear to return from an answer or replay to the map.
- Press `S` until map one appears if you need to restart.
- If physical hardware behaves differently, stop making a physical-hardware
  claim and use the emulator as explicitly labelled evidence.

## Claims discipline

Safe claims:

- the Mac exported 160 signed Q4.4 parameter bytes;
- the 6809 performs forty signed multiply-accumulates per lookup;
- direct simulation matches 96 scores across twelve novel contexts;
- loading a different map preserves the exhibit and changes its shelf; and
- model `751B` remains byte-identical while the map changes.

Do not yet claim measured physical CoCo latency or keyboard compatibility. Do
not claim that the shelf assignments become trained knowledge, that the model
understands the exhibits, or that this one attention head is a transformer.
