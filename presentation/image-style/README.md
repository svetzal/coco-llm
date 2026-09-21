# Image style for the CoCo LLM series

`coco-screen.json` is a scene variant in the presentation-image-generator's
format: the deck's own look, black ink on the composite screen green, amber
for the one thing that changed, navy for emphasis, blocky uppercase type. Use
it as the `Style` and `PromptKeywords` blocks of a scene, and copy the
`TypeRules` into the scene's `CompositionNotes`.

`coco-screen-reference.png` beside the posts' images is the emulator's own
raster from a recorded run. Attach it to a scene as a prop `ReferenceImage`
so the generator sees what a CoCo screen looks like rather than guessing.

## What the generator may draw, and what it may not

An image model does not reproduce numbers or words reliably, and the
project's rule is that nothing appears on a screen unless the machine
produced it. So:

- **Generate** conceptual graphics: the shape of an idea with no values in
  it. Two tables with one row lit in each. Points in a box with some near
  each other. A window sliding along a row of cells. Ask for blank cells
  where labels would go, or supply the words through a reference image.
- **Draw from data** any figure that carries a value: a table of real rows,
  a share of 256, a distance, a count. Those are generated from the trace
  files by a script, as the post figures under `posts/images/*.svg` are, and
  rendered through headless Chrome with the deck's font (see
  `../posts/README.md`).

A generated image is an illustration and its alt text says so. A drawn
figure is evidence and its alt text carries its numbers.

## Running it

```sh
source ~/.secrets.sh && node ~/.claude/skills/presentation-image-generator/scripts/generate-image.mjs \
  presentation/posts/images/<scene>.json presentation/posts/images/<scene>.png
```

Scenes live beside the image they produce, as the blog does with its
banners. `two-tables-concept.json` and `points-in-a-box-concept.json` are
the worked examples.
