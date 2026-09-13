# Concept map

A block diagram of the language model: the arithmetic that predicts a token,
and the arithmetic that corrects the prediction. Every block of the talk and
every experiment hangs on the block of the machine it changes.

It is a second way through the material. `runsheet.md` goes in stage order.
This goes by mechanism, so a person who asks "where does the prompt go?" or
"what does training actually change?" can be pointed at a box.

A prototype is in [`deck/map.html`](deck/map.html). Open it beside the deck;
every chip on it links to a slide.

## The map

Two loops around two stores.

```text
                     the picked token becomes the newest context
              +--------------------------------------------------------+
              v                                                        |
 TRAINING  -> TOKENIZE -> CONTEXT -> EMBED -> SCORE -> SOFTMAX -> PICK -+
 DATA                     WINDOW      ^        ^
                                      | read   | read
                                   +--------------+
                                   |   WEIGHTS    |
                                   +--------------+
                                      ^ write
    ^                                 |
    |  next example                   |
 REPEAT  <----------------------- UPDATE <- GRADIENT <- COMPARE <- TARGET
```

The top row is **predict**: it runs left to right, and it is all of inference.
The bottom row is **correct**: it runs right to left, back through the same
arithmetic, and it is all of training. The black boxes are state. Everything
else is arithmetic over that state.

### The blocks

Each row names the block, says what it does in the words the deck already
uses, gives the arithmetic in this model, says what the CoCo does for it, and
names the decision a person made there.

| Block | In words | Arithmetic, in this model | On the CoCo | Decision |
| --- | --- | --- | --- | --- |
| TRAINING DATA | the facts we feed it | 18 names, 58 examples of (context, next token) | 200 bytes of text | which text |
| TOKENIZE | cut the text into pieces a machine can count | word to id, 29 ids | a table lookup | what a token is |
| CONTEXT WINDOW | the last 2 tokens; slides, and everything before it is gone | (t1, t2) | 2 bytes | how wide |
| EMBED | one stored row of 3 numbers per position and token; add them | c = E[1][t1] + E[2][t2]. 174 parameters | 6 signed adds in Q4.4 | how many numbers per token |
| SCORE | a score for every token | z = W c + b. 87 + 29 parameters, 87 multiplies | MUL, 11 cycles each; MULD on a 6309 | |
| SOFTMAX | scores become shares of 100% | p(i) = exp(z(i)) / sum of exp(z(j)) | a 256-entry table stands in for exp; shares in 1/256 | |
| PICK | draw a token from the shares, or take the biggest | sample p, or argmax | xorshift16 | temperature, or greedy |
| TARGET | the token that actually came next | t* | from the training data | |
| COMPARE | how wrong it was: the share it gave the right answer, minus 100% | e = p minus one-hot(t*). loss = minus log p(t*) | e in 1/256 units | |
| GRADIENT | what each weight contributed to being wrong | dW = e outer c. db = e. dc = W transposed times e | 174 multiplies, with the sign correction | |
| UPDATE | nudge every weight against its contribution | each weight minus (1/16) times its gradient. The embedding rows that were used take dc | four shift pairs; Q4.12 masters, Q4.4 used | learning rate |
| WEIGHTS | the 290 numbers training is allowed to change | E, W, b | 580 bytes | how many |
| REPEAT | every example, every epoch | 58 examples times 20 epochs = 1,160 updates | 15.8 million instructions | epochs |

The multiply count the cost slide quotes is on this map: 87 in SCORE, 87 for
dW and 87 for dc in GRADIENT, 261 an example.

### What the arrows say

- **Two write arrows into two stores.** A person can write CONTEXT, which is
  what a prompt is. Training writes WEIGHTS, and a person chooses the training
  data that drives it. Every "change one thing" in the talk is one of these two
  arrows or one of the decisions in the last column.
- **The top loop is everything needed to use the model.** The bottom loop is
  needed only to learn it. The cost slide's split, 2,516 bytes to use and 730
  more to learn, is the two rows. EXP-006 and EXP-007, the Mac-trained
  completers, run the bottom row on the Mac and the top row on the CoCo.
- **The multiplies are in SCORE and GRADIENT.** That is where the 6809's MUL
  and the 6309's MULD matter, and nowhere else.
- **Nothing on the top row can change WEIGHTS.** Asking the model a question
  teaches it nothing. Block 4 says this with a held-fixed line; the map says it
  with the direction of an arrow.

### Named simplifications

The map is honest about this model. It is not a picture of a transformer.

- **No hidden layer and no nonlinearity.** Two embedding rows are added and
  go straight into a linear scoreboard. Modern models put many layers between
  EMBED and SCORE. The shape of the loop is the same.
- **No attention.** CONTEXT here is two fixed positions with their own tables.
  EXP-011, the context-editing attention head, is a separate 160-parameter head
  that reads context by content, and it sits on the CONTEXT box for that reason.
- **One example at a time, one fixed learning rate.** Modern training batches
  examples and adapts the rate. The update rule is otherwise the same.
- **Cross-entropy loss**, the standard one. Nothing was simplified there.
- **The exponential is a table.** SOFTMAX on the CoCo is an approximation in
  1/256 units. It does the same job.
- **EXP-013, the game opponent that learns, has no gradient.** Its UPDATE is a
  count in a 75-byte table. It sits on UPDATE because that is the job it does
  while a person plays, and its chip says so.

## Where each block of the talk lands

| Talk block | Map blocks | Runs |
| --- | --- | --- |
| 1 Watch it work | PICK, and the whole predict loop, before any of it is explained | EXP-004, the live training run, launched |
| 2 How it works | every block once, in order: TRAINING DATA, TOKENIZE, CONTEXT, EMBED, WEIGHTS, then one step through COMPARE, GRADIENT and UPDATE, then REPEAT | slides |
| 3 A little 6809 assembly | SCORE and GRADIENT for the multiply, UPDATE for the shifts, SOFTMAX and PICK for the next token | EXP-004, the live training run |
| 4 The prompt | CONTEXT, written by a person; WEIGHTS held | EXP-005, the prompted marketing completions |
| 5 The size | TOKENIZE at 255 tokens, CONTEXT at 5, EMBED wider, WEIGHTS written by the Mac | EXP-007, the all-RAM sentence completer |
| 6 Never existed | PICK with rules over the draw; TOKENIZE, a vocabulary mostly used once | EXP-012, the fake episode titles |
| 7 The training data | TRAINING DATA, and what it does to WEIGHTS | EXP-003, the fan-corpus bias runs |
| 8 You play it | UPDATE during play; CONTEXT is the last move and the last outcome | EXP-013, the game opponent that learns |
| 9 A token is a note | TOKENIZE; SCORE, for MULD | EXP-010, the melody continuation; EXP-014, the 6309 multiplier benchmark |
| 10 Wrap up | the whole map, lit | slides |

## Where each experiment lands

| Experiment | Map block | What it changes there |
| --- | --- | --- |
| EXP-001, the rejected character model | TOKENIZE | a token is a letter; 12.8 million multiplies, rejected |
| EXP-002, the token model | EMBED, WEIGHTS | the 290-parameter model, and the width sweep behind "why three" |
| EXP-003, the fan-corpus bias runs | TRAINING DATA | content and order, everything else held |
| EXP-004, the live training run | REPEAT | the whole loop, on the machine, at its clock |
| EXP-005, the prompted marketing completions | CONTEXT | a person writes the first two tokens |
| EXP-006, the 8 KiB completion workbench | WEIGHTS, PICK | Mac writes the weights; ranks scores without a softmax |
| EXP-007, the all-RAM sentence completer | TOKENIZE, CONTEXT, EMBED, WEIGHTS | 255 tokens, 5 of context, 32,385 parameters |
| EXP-007, the epoch sweep | COMPARE, REPEAT | loss keeps falling after quality peaks |
| EXP-008, the rejected adaptive opponent | UPDATE | a counting table beat every network; null result |
| EXP-010, the melody continuation | TOKENIZE, PICK | a token is a scale degree; a wrong note cannot be drawn |
| EXP-011, the context-editing attention head | CONTEXT | reads context by content; edit a fact, weights locked |
| EXP-012, the fake episode titles | TOKENIZE, PICK | 180 tokens, 91% used once; rules over the draw |
| EXP-013, the game opponent that learns | UPDATE, CONTEXT | updates every round, by counting |
| EXP-014, the 6309 multiplier benchmark | SCORE | MULD, 1.54x on the multiplies |

EXP-009 and EXP-015 through EXP-019 are off the map on purpose. They are the
performer and the play interface: they take what PICK chose and put it on a
speaker or a screen. Display and I/O stay outside the learning engine.

## Using it to navigate

Four places it could go. They are not exclusive.

1. **A map slide opening block 2.** Show the whole shape once, say "predict
   along the top, correct along the bottom, and these two black boxes are the
   only memory it has," and then walk the eight figures. Each figure is one
   box on this map.
2. **Chapter cards.** Each card shows the map with that block's boxes lit and
   the rest dimmed, under the block's own colour. Block 4 lights CONTEXT.
   Block 7 lights TRAINING DATA. Block 8 lights UPDATE. The card already
   carries the block's colour; this gives it a location.
3. **Wrap up.** "What we showed" becomes the fully lit map. Each line of the
   current list is one region of it.
4. **The table and the repository.** A printed map is the menu. The "useful
   when the conversation asks" table in `experiments/README.md` re-keys by
   box: prompt questions go to CONTEXT, bias questions to TRAINING DATA, "does
   it learn from me" to UPDATE.

What it must not become: a replacement for the block 2 figures. One idea per
screen still holds. On a slide the map is read as a shape with one lit region
and one name to read. The deck README's rule that more than three stages in a
row will not fit at back-row size applies to figures that are read; the map
is a place-marker, and only the lit box's name needs to be legible from the
back.

## The prototype

`deck/map.html` is the map at 1280 by 720, in the deck's palette and type,
with no reveal and no build step. Every chip links into `index.html` at the
slide it names, or to the experiment's file.

- `?block=N` lights block N's chips and dims the rest, and sets the title bar
  and band to that block. This is the chapter-card version. Keys `1` to `9`
  and `0` do the same in the page; `A` lights everything.
- `?math=1` shows the arithmetic line under each box. Key `M` toggles it. It
  is off by default: the words carry the primary path and the arithmetic is
  optional depth.

Nothing on the page is generated from a run, because nothing on it is a
measurement. The counts it quotes are the ones already on the slides.
