# Presentation

The presentation and exhibit teach through one live example: a CoCo learning to
invent vintage-computer names.

The current narrative is in
[`learning-journey.md`](learning-journey.md). It is intentionally an argument
and demonstration sequence, not yet a slide deck.

The presentation has four connected teaching threads:

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

The developing practical branch is an explicitly pretrained 8 KiB
next-word-completion model. It connects mechanism to usefulness while making
the division of labour visible: the Mac trains and exports; the CoCo performs
integer inference. EXP-006 has a verified 6809 core but remains outside the
stage menu until its interactive workbench, quality criterion, and stock-rate
latency are resolved.

The bias demonstration is therefore part of the main argument, not a detached
ethics aside. It connects the mechanics of learning directly to the need for
human judgement.

Future material may include:

- talk abstract and title;
- slide source and speaker notes;
- live-demo runbook and recovery paths;
- exhibit signage;
- audience handout;
- photographs and video;
- cited sources.

The presentation must accurately describe the implemented model. Technical
shortcuts are welcome when they improve teaching, but they must never be hidden.
