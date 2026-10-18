# Line 2: Unicode Lantern

The first working piece exposes hidden text controls and look-alike identifiers
without executing or changing the inspected text. Start with the command in
[the tool README](tools/unicode-lantern/README.md).

## Round 01: The Hidden Fork

Pepe uncovers a pale branch in a dark trail: an apparent single path can hide a
second reading. The first mark occupies only part of the bare cave, leaving
space for the line's next workers.

Output inspection:

- `artifacts/line-2/wall.png`: PNG, RGB, **1254 x 1254**, matching the input cave.
- `dist/line-2/01.jpg`: JPEG, RGB, **512 x 512**, **84,795 bytes**.
- `dist/line-2/01.json`: the first numbered record; its image URL uses the
  finished PNG's lowercase SHA-256.
- Visually reviewed the full PNG and decoded JPEG. The rock, cracks, roots,
  torchlight and framing remain recognizably aligned with the supplied cave.
  Pepe has the broad mouth and heavy-lidded eyes, rendered in worn earth
  pigments. Counted five digits on each of the two visible hands. No hand
  stencils, letters, numbers, captions, signatures, logos, or frames were added.
- Unmet visual requirements observed: **none**. Preservation is a visual review,
  not a claim that generative editing left every background pixel identical.

The built-in image tool edited the supplied bare cave, with this prompt:

> Use case: precise-object-edit. Edit the supplied bare cave image, keeping its exact square size 1254 by 1254, rock, cracks, hanging roots, warm torchlight, framing and perspective. Add only a small prehistoric pigment painting in the central left portion of the wall, leaving most rock bare for future additions. Main figure: recognizable Pepe the frog with big heavy-lidded eyes and wide downturned mouth, a simple ochre and charcoal cave figure with a small body. Show both open hands clearly separated from the body, exactly FIVE digits on EACH hand: four fingers and one thumb. Pepe examines a short trail of charcoal animal tracks that splits, with one branch revealed in faint chalk white: a metaphor for uncovering deceptive hidden text, but DO NOT draw text or glyphs. Only red and yellow ochre, charcoal black and chalk white, rubbed irregularly into the stone with bare stone visible through pigments; worn hand-drawn Lascaux/Chauvet character. Keep all original rock features intact. No letters, numbers, captions, logos, signatures, borders, frames, political symbols, real people or 3D figures. The result should be the original cave rock with a modest flat cave-painting addition, not a new cave. Save the finished PNG to artifacts/line-2/wall.png if file saving is supported.
