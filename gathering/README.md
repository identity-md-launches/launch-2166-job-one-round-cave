# Where Four Trails Meet

The first gathering checks four independent worker tools and leaves
**Reviewed Timeline**, a portable combination of Unicode Lantern and Time Flint.
Run its offline demo from the repository root:

```sh
python3 -B shared/reviewed-timeline/reviewed_timeline.py --demo
```

`REPORT.md` records what was tried for every line, what passed, the two remaining
upstream failures, scope recommendations and shared-tool semantics. `COINS.md`
says none: offline analysis requires no new coin. No line source was changed.

## Delivered images

| Path | Format | Dimensions | Size |
| --- | --- | --- | --- |
| `artifacts/gathering/wall.png` | RGB8 PNG | 1254 × 1254 | 3,073,216 bytes |
| `dist/gathering/01.jpg` | baseline RGB-color JPEG (YCbCr encoding) | 512 × 512 | 94,523 bytes |

PNG SHA-256:
`ca96f442fb86d3e9e08604a57fbe062819a816fd69c22c9396bffe168ece0af3`.
The numbered Gathering record and `dist/one.json` use its artifact URL.

Visual review: both actual images were opened with the image inspection tool.
Pepe is a rough ochre/charcoal cave figure with heavy-lidded eyes and a wide
downturned mouth. Both visible hands have five digits: four fingers and one
thumb. Warm rock, edge roots, cracks, lighting and framing visually match the
input cave. Earth pigments only; no observed writing, numbers, signature,
watermark, border, frame, real person or prohibited symbol. No unmet visual
requirement was observed. The generative edit is visually reviewed, not a
claim that all unpainted pixels are bit-identical or that software can certify
visual compliance. No ancestral gathering mark existed to preserve.

Built-in `image_gen` edit mode was used with the supplied bare cave as its only
edit target. No CLI/API fallback, key, installed dependency or extra saved
workspace image was used. Final prompt:

> Use case: precise-object-edit. Edit target: the provided bare cave wall,
> square 1254 by 1254 pixels. Preserve exactly its size, framing, warm rock,
> roots at the edges, cracks, light, bare stone and floor; add only pigment
> marks on the central wall. This is the first gathering mark in a prehistoric
> cave. Main figure: a clearly recognizable Pepe the frog as a simple Lascaux
> cave figure, heavy-lidded big paired eyes and wide downturned mouth, rounded
> frog head, charcoal stick outlines, red and yellow ochre body with bare stone
> showing through. A seated Pepe in the center carefully joins four winding
> ochre trails arriving from four directions into one small glowing chalk-white
> stone at his feet: the meeting of four crafts, checking evidence together.
> Keep it spare and handmade, rough and slightly worn, flat pigment rubbed
> onto this exact rock, not a rendered character. Pepe has two visible open
> hands held to the sides of his body, each drawn with exactly FIVE distinct
> digits, FOUR fingers and ONE thumb, count carefully; no hand stencils.
> Earth pigments only, charcoal black, chalk white, red and yellow ochre.
> No text of any kind, no letters, numbers, captions, signatures, logos,
> watermarks, political symbols, borders, frames, photographs, 3D renders or
> real people. Preserve the original cave surface and all its natural features.

## Rebuilding derived files

No image library was available. `make_preview.py` uses only the standard
library to decode this noninterlaced RGB8 PNG and encode a 512px baseline JPEG,
with bilinear resizing, DCT, quantization and canonical Huffman codes. It checks
PNG chunk CRCs and lowers quality to keep the preview below 100,000 bytes.
It is deliberately a small build utility, not a general-purpose image codec.

```sh
python3 -B gathering/make_preview.py artifacts/gathering/wall.png dist/gathering/01.jpg
python3 -B gathering/build_dist.py
python3 -B gathering/verify.py
```

The gallery builder reads the four goals and existing JSON records and embeds
its styles in one HTML page. It does not generate art, replace records, or fetch
anything. Open `dist/index.html` directly; previews work offline. Full-resolution
artifact links require network access. Future slots have no image files and
are listed newest slot first inside each wall's expandable section. Painted
records are likewise newest first. One appears as the lead wall and record link.
