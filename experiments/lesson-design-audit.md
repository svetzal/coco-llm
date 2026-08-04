# Lesson-design audit

This audit applies the project's lesson and demonstration guidance to every
experiment. The central question is not whether the result can be explained in
speaker notes; it is whether a learner can see what changed, what stayed fixed,
what action caused the change, and what evidence followed.

| Experiment | Causal lesson | Audit decision |
| --- | --- | --- |
| EXP-001 | The character model cannot meet the declared time budget. | Keep. The called shot and measured multiplication floor already show claim, evidence, and rejection. |
| EXP-002 | Changing representation reduces the work while preserving the objective. | Keep. Characters-to-tokens, examples, and multiply counts make the changed factor visible. |
| EXP-003 | Data selection and order change behaviour while model and budget stay fixed. | Improve. The presenter now prints the concatenated and interleaved order before the result table, followed by the held controls. |
| EXP-004 | Training changes model state and therefore output. | Improve. The CoCo now generates with seed 6809 before training, repeats seed 6809 after training, and labels random versus learned weights on screen. |
| EXP-005 | A prompt changes a completion without changing the trained model. | Improve. The persistent title reads `SAME MODEL - CHANGE THE PROMPT`. |
| EXP-006 | Training can happen elsewhere while useful integer inference happens on the CoCo. | Improve. The persistent title reads `MAC TRAINED - COCO PREDICTS`; the failed quality gate remains visible in the written evidence. |
| EXP-007 | More memory supports a larger, punctuation-aware inference model, not live training. | Improve. The same Mac/CoCo title keeps the training boundary visible while the all-RAM mechanism is explored. |
| EXP-008 | A neural learner should be rejected when a tiny table predicts the live player better. | Keep. The reset-and-relearn protocol is causally strong; the null result correctly prevented a decorative 6809 UI. |
| EXP-009 | Constant-time playback fixes an audible timing defect. | Keep. Heard-before and fixed-after recordings provide a controlled comparison; implementation detail remains optional depth. |
| EXP-010 | The person supplies an opening figure and the model supplies the continuation. | Improve. The title now reads `YOU SEED - MODEL CONTINUES`; labels and colour reinforce, rather than replace, those roles. |
| EXP-011 | Editing context can change an answer while model weights remain locked. | Keep as the reference pattern. The UI shows the learner's edit, before/after context, unchanged model identity, repeated question, and changed answer. |

## Pattern carried forward

For any new interactive lesson, put this causal chain in the artifact:

1. name the state that will remain fixed;
2. show the learner's action at the moment it occurs;
3. show the changed state in place;
4. repeat the same query, seed, or task when a controlled comparison is useful;
5. show the resulting behaviour without requiring narration to explain it.

Mechanism views remain valuable, but only after the causal story is legible.
Colour may reinforce roles; text, position, or symbols must also name them.

## Remaining evidence boundaries

- EXP-003 still needs a matching 6809 implementation before it becomes a live
  hardware experiment.
- EXP-004, EXP-006, EXP-007, EXP-010, and EXP-011 still need the physical
  hardware validation already recorded in their experiment notes.
- EXP-008's rejection and EXP-009's timing fix should not acquire additional UI
  merely to make every experiment look alike.
