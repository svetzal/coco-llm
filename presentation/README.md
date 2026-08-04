# Presentation

The presentation and exhibit teach through one live example: a CoCo learning to
invent vintage-computer names.

The current narrative is in
[`learning-journey.md`](learning-journey.md). It is intentionally an argument
and demonstration sequence, not yet a slide deck.

Supporting presentation material includes:

- [`exhibit-copy.md`](exhibit-copy.md) — approved abstract, bio, and table copy;
- [`table-exercises.md`](table-exercises.md) — the audience's hands-on
  next-token exercise;
- [`exp011-demo-script.md`](exp011-demo-script.md) — three-beat presenter
  runbook for visibly editing context while model weights remain locked;
- [`card-concepts/`](card-concepts/) — exploratory visual directions for that
  exercise, not final print artwork.

The presentation has five connected teaching threads:

1. **Mechanism:** tokens, next-token prediction, error, and parameter updates
   are small enough to watch on a CoCo. The two-`MUL` optimization shows how
   understanding the mathematics and the machine turns a correct experiment
   into a practical live demonstration without changing its result.
2. **Training-data choices:** Apple-, Commodore-, and Tandy-fan corpora show
   that selection and repetition shape model behaviour. Concatenating and
   interleaving the same balanced examples shows that ordering matters too.
3. **Limits and usefulness:** plausible output is not understanding or truth,
   but a bounded model can still do a bounded job well.
4. **Human agency:** people choose the task, data, training procedure, success
   criteria, verification, and acceptable consequences.
5. **Context and attention:** training teaches a matching operation, a prompt
   supplies temporary facts, and attention selects a relevant record without
   adding that fact to the model's weights.

The experiment-wide [`lesson-design audit`](../experiments/lesson-design-audit.md)
checks that those claims are visible in the artifacts themselves: learner
action, changed state, held state, and result should not live only in narration.

The practical branch now has two explicitly pretrained completion models.
EXP-006 spends 8 KiB on a 178-token, four-word completion model. EXP-007 asks,
“What if I use the memory the ROM normally occupies?” Its 32 KiB model uses all
255 token identifiers, five-token context, and punctuation. Both connect
mechanism to usefulness while making the division of labour visible: the Mac
trains and exports; the CoCo performs integer inference.

Both are in the presentation launcher for conversation-driven XRoar
demonstrations. Neither should be described as physically validated until
keyboard behaviour and stock-rate latency are measured on the CoCo 1.

EXP-011 follows that practical branch with a different capability. Its
160-parameter head keeps a query stable while a person edits its selected
context value from `CODE 2` to `CODE 6`. A dedicated editor shows the write to
context RAM and labels model `751B`'s weights locked; the score replay is
optional depth. It is key-value attention, not a transformer, and remains an
emulator demonstration until the physical keyboard and latency are measured.

The bias demonstration is therefore part of the main argument, not a detached
ethics aside. It connects the mechanics of learning directly to the need for
human judgement.

Future material may include:

- slide source and speaker notes;
- live-demo runbook and recovery paths;
- audience handout;
- photographs and video;
- cited sources.

The presentation must accurately describe the implemented model. Technical
shortcuts are welcome when they improve teaching, but they must never be hidden.
