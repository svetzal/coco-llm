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
| EMBED | one stored row of 3 numbers per position and token; add them | c = E₁[t₁] + E₂[t₂]. 174 parameters | 6 signed adds in Q4.4 | how many numbers per token |
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

## For readers who know the classic form

Some people arrive knowing this material as matrices and gradients. The map
holds for them too; this is the same table in that notation, then a list of
what a classic reader will look for and not find, and what they will find
under another name.

### The model, in the usual symbols

Vocabulary size $`V = 29`$, context length $`k = 2`$, embedding width
$`d = 3`$. Parameters $`\theta = (E_1, E_2, W, b)`$ with
$`E_p \in \mathbb{R}^{V \times d}`$, $`W \in \mathbb{R}^{V \times d}`$,
$`b \in \mathbb{R}^{V}`$, so $`|\theta| = kVd + Vd + V = 290`$.

| Block | Classic form |
| --- | --- |
| TRAINING DATA | $`\mathcal{D} = \{(x^{(n)}, y^{(n)})\}_{n=1}^{N},\ N = 58`$, from 18 names |
| TOKENIZE | $`t \in \{0, \dots, V-1\}`$; $`x_p = \mathrm{onehot}(t_p) \in \mathbb{R}^{V}`$ |
| CONTEXT WINDOW | $`x = (t_1, t_2)`$ |
| EMBED | $`h = \sum_{p=1}^{k} E_p^{\mathsf T} x_p = E_1[t_1] + E_2[t_2] \in \mathbb{R}^{d}`$ |
| SCORE | $`z = W h + b \in \mathbb{R}^{V}`$ |
| SOFTMAX | $`p = \mathrm{softmax}(z)`$, $`p_i = e^{z_i - \max z} \big/ \sum_j e^{z_j - \max z}`$ |
| PICK | $`t \sim \mathrm{Categorical}(\mathrm{softmax}(z / T))`$, or $`\arg\max z`$ |
| TARGET | $`y = \mathrm{onehot}(t^*)`$ |
| COMPARE | $`L = -y^{\mathsf T} \log p = -\log p_{t^*}`$ |
| GRADIENT | $`\partial L/\partial z = p - y`$; $`\partial L/\partial W = (p - y)\, h^{\mathsf T}`$; $`\partial L/\partial b = p - y`$; $`\partial L/\partial h = W^{\mathsf T}(p - y)`$; $`\partial L/\partial E_p[t_p] = \partial L/\partial h`$ |
| UPDATE | $`\theta \leftarrow \theta - \eta\, \nabla_{\theta} L`$, $`\eta = 2^{-4}`$, one example per step |
| REPEAT | 20 epochs over $`\mathcal{D}`$ in a fixed order; the loss reported is the epoch mean |

The backward pass in sequence, as the chain rule from the loss to the
parameters:

```math
\begin{aligned}
\frac{\partial L}{\partial z} &= p - y \\
\frac{\partial L}{\partial W} &= (p - y)\, h^{\mathsf T}, \qquad
\frac{\partial L}{\partial b} = p - y \\
\frac{\partial L}{\partial h} &= W^{\mathsf T} (p - y), \qquad
\frac{\partial L}{\partial E_p[t_p]} = \frac{\partial L}{\partial h} \quad (p = 1, 2) \\
\theta &\leftarrow \theta - \eta\, \nabla_{\theta} L, \qquad \eta = 2^{-4}
\end{aligned}
```

Two things in that table are the whole of block 2 and block 3 restated.
The first is $`\partial L/\partial z = p - y`$: the softmax and the cross-entropy cancel into
"the share it gave the right answer, minus 100%," which is why the deck can
show the error as one subtraction and why the assembly does it with one
`subd #256`. The second is that $`\partial L/\partial W = (p - y)\, h^{\mathsf T}`$ is an outer product, so
each weight's change is its own row's error times its own column's input,
which is the slide's "rate × how wrong × what this weight contributed."

### This is backpropagation, one layer deep

The backward pass is the chain rule from $`L`$ to $`\theta`$, and it is present in full.
It is short because the network is short. From the loss to the logits is one
step, $`p - y`$. From the logits back to the context vector is one more,
$`W^{\mathsf T}(p - y)`$, and that vector is handed straight to the two embedding rows that
were read. There is no hidden layer, so there is no Jacobian of a
nonlinearity to pass through and no second matrix to propagate across. A
reader expecting a $`\delta`$ at every layer will find exactly two, and both are on
the map: COMPARE produces the first and GRADIENT the second.

The model has a classic name. It is a log-bilinear language model in the
sense of Mnih and Hinton (2007), with the per-position context matrices
folded into position-specific input tables and the output embeddings $`W`$
untied from the input side. Its direct ancestor with a hidden layer is the
neural probabilistic language model of Bengio, Ducharme, Vincent and Jauvin
(2003); remove that paper's tanh layer and this is what remains.

### What a classic reader will look for and not find

- **Hidden layers and activations.** Nothing sits between EMBED and SCORE.
  There is no ReLU, GELU or tanh anywhere in the 290 parameters.
- **Attention.** No queries, keys or values in the main model. EXP-011, the
  context-editing attention head, has them, below.
- **Layer normalisation, residual connections, dropout, weight decay.** None.
- **Additive positional encodings.** Position is handled by giving each
  window position its own table, not by adding a position vector to a shared
  token embedding.
- **Mini-batches, momentum, Adam, learning-rate schedules.** The update is
  plain SGD with a batch of one and a constant $`\eta`$. The rate is a power of two
  because the CoCo applies it with shifts.
- **Tied input and output embeddings.** $`W`$ is its own table.
- **Beam search, top-k, nucleus sampling, a KV cache.** Generation is
  ancestral sampling at a temperature, or greedy.
- **Held-out validation.** The stopping rule came from a quality rubric on
  samples, not from validation loss. EXP-007, the epoch sweep, is the one
  place validation-style measurement appears, and it shows training loss
  still falling after held-out quality peaks.

### What they will find under another name

- **The max-subtraction trick.** The assembly measures every score as a
  distance below the best score before looking up the exponential. That is
  $`\mathrm{softmax}(z - \max z)`$, the standard numerically stable form, done for the
  same reason: the table only has to cover one direction.
- **Mixed precision.** Master weights are kept in Q4.12 and the forward pass
  reads their high bytes as Q4.4. Fixed point rather than floating, but the
  structure is the fp32-master, low-precision-operand pattern, and it exists
  for the same reason: an update of 1/16 of a small error would otherwise
  round to nothing.
- **Post-training quantization.** EXP-006 and EXP-007, the Mac-trained
  completers, train in floating point and ship signed Q4.4 weights, with the
  accuracy lost to quantization measured and reported.
- **Temperature.** The reference divides log p by T before renormalising,
  which is $`\mathrm{softmax}(z / T)`$.
- **Scaled dot-product attention.** EXP-011, the context-editing attention
  head, is $`q = Q[\text{query}]`$, $`k_m = K[\text{key}_m]`$,
  $`s_m = q \cdot k_m / \sqrt{d}`$, $`\alpha = \mathrm{softmax}(s)`$, and the
  answer is the value stored at $`\arg\max s`$. The value path has no
  parameters; only $`Q`$ and $`K`$ are learned, by cross-entropy over the slots. It
  is one head, with no output projection, and no value matrix, which is the
  smallest thing that is still attention.
- **A count model.** EXP-013, the game opponent that learns, is a maximum
  likelihood table conditioned on the last move and the last outcome, the
  same object as a bigram count, updated by incrementing. No gradient exists
  because there is nothing to differentiate.
- **Cross-entropy in bits.** EXP-010, the melody continuation, reports its
  margin over a count baseline as bits per row, which is the log-loss
  difference in base 2.

### Where this goes

Not on stage. The talk names softmax, gradient and learning rate where the
mechanism is already on screen, and stops there. This section is for the
table, for the written record, and for the one person in the room who asks
"is that really backprop." One backup slide carries the notation table
above, as a vertical slide under the deck's last slide so the down arrow
reaches it and the running order never does.

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
- `?math=1` swaps each box's words for its arithmetic, and `?math=2` for the
  classic notation above, typeset by the MathJax vendored beside reveal. Key `M` cycles words, arithmetic, classic. Words are
  the default: they carry the primary path and the notation is optional depth.

Nothing on the page is generated from a run, because nothing on it is a
measurement. The counts it quotes are the ones already on the slides.
