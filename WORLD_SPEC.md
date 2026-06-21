# Mind Palace — World Specification

You are a **content model**. Your job is to grow the palace by writing **data files only**.
You never write code, never place coordinates, never create graphical assets. The engine
turns your declarations into walkable 3D rooms automatically.

This palace is a Harry Potter–style *mind palace*: a memory technique made literal. Each
piece of real knowledge (a paper, a concept, a technique) becomes a themed chamber the
user can physically walk through. Narrative and metaphor are encouraged; factual fidelity
of the underlying knowledge is mandatory.

## The one workflow

1. Read this file, `world/catalog.json`, and `world/graph.json`.
2. Skim 1–2 existing files in `world/rooms/` as style references.
3. Write or edit room JSON file(s) in `world/rooms/` (one file per room, filename `<room-id>.json`).
4. Register every new concept in `world/graph.json` and connect it with edges.
5. Run `python world.py validate` from the project root. Fix every error. Repeat until it prints `WORLD OK`.
6. In your final report, list rooms added/changed and any TODOs (e.g. a prop you wished existed).

A change is **not done** until `python world.py validate` passes.

## How space works (so you don't think about it)

- The palace has one **hub** (the Atrium) and up to 8 **wings** radiating from it.
- A room belongs to a wing and has an integer `order` (1, 2, 3, …). The engine lays the
  wing out as a chain of chambers: order 1 attaches to the hub, order 2 attaches to
  order 1, and so on. Consecutive rooms get real doorways.
- `connections` lists other rooms this one is conceptually linked to. If a connection is
  *not* the natural physical neighbor, the engine renders it as a **glowing portal**
  (instant travel). Cross-wing links are always portals. Declaring a connection on one
  side is enough (portals are bidirectional); declaring it on both sides, or listing a
  natural chain neighbor, is a harmless no-op — never an error.
- You never specify positions, rotations, or dimensions beyond `size`
  (`small` ≈ intimate side-chamber, `medium` ≈ classroom, `grand` ≈ great hall).

## Room file format

`world/rooms/<room-id>.json` — validated against `definitions/room` in `world/schema.json`:

```json
{
  "id": "mirror-of-occlusion",
  "name": "The Hall of Predictive Sight",
  "wing": "divination",
  "size": "medium",
  "order": 1,
  "connections": ["vicereg-hall"],
  "exhibits": [ ... 1 to 8 exhibits ... ]
}
```

- `id`: kebab-case, globally unique, stable forever (other files reference it).
- `wing`: must be a wing id from `world/world.json`. Only the hub room has `"wing": null`.
- `palette` (optional): override the wing's palette. Use sparingly.
- `order`: unique within the wing. Don't renumber existing rooms.

## Exhibit types

Every exhibit needs a unique-within-room kebab `id`, a `type`, and a `title`.
The engine auto-places exhibits around the room's walls; order in the array is
roughly the order a visitor walking the room will meet them.

| type | required fields | renders as | use for |
|---|---|---|---|
| `plaque` | `text` (≤1600 chars) | wall plaque / pedestal tablet (`prop`: `pedestal` or `lectern`) | the distilled idea — definitions, intuition, equations in words |
| `tome` | `text` (≤16000) | a book on a lectern, readable in focus mode | full chapters, long-form source narratives |
| `portrait` | `text` (≤16000), optional `subtitle` | framed talking portrait | a character voice explaining or debating the idea |
| `artifact` | `prop`, `text` (≤16000), optional `scale` (0.5–2) | a 3D prop from the catalog on a plinth | the room's central metaphor object |
| `diagram` | `spec` (Mermaid, ≤4000), optional `caption` | framed diagram panel | structure: flows, architectures, relationships |
| `image` | `image` (path under repo, ≤200), optional `caption` | framed picture on the wall, studied large in world space | real figures/plots/screenshots (put files in `world/assets/`) |

Other hard limits: ≤8 exhibits and ≤8 `connections` per room, `order` ≤32, room and
exhibit ids are yours to invent (kebab-case, stable).

`prop` must come from `props` in `world/catalog.json`. Current catalog:
pedestal, lectern, mirror, cauldron, bookshelf, statue, banner, candelabra,
orrery, crystal_ball, hourglass, table, brazier.

`diagram.spec` is standard Mermaid (`graph TD`, `graph LR`, `sequenceDiagram`).
Keep diagrams ≤ ~12 nodes; they render on an in-world panel.

## Knowledge graph — `world/graph.json`

The graph is the palace's ground truth of *what is known and how it connects*.

```json
{
  "concepts": [
    { "id": "i-jepa", "name": "I-JEPA", "room": "mirror-of-occlusion",
      "exhibit": "the-mirror", "summary": "Self-supervised learning by predicting masked-region representations in latent space..." }
  ],
  "edges": [
    { "from": "i-jepa", "to": "ema-target-encoder", "relation": "part-of" }
  ]
}
```

- Every room you add should anchor ≥1 concept; every concept's `room` must exist.
  `exhibit` is optional — include it when one exhibit *is* that concept; several
  concepts may point at the same exhibit; omit it for room-level concepts.
- `relation` ∈ `builds-on`, `relates-to`, `contrasts-with`, `part-of` (see catalog).
- Edges power the in-game constellation map and portal suggestions. Be generous with
  them — connection is the point of the palace.

## Style guide

- **Voice**: in-world Hogwarts narration. Professors lecture, artifacts are enchanted,
  losses are "regret", training epochs are "nights". Keep established characters
  consistent (e.g. Professor Aurelius Bramblestoke teaches the predictive arts).
- **Structure of a good concept room**: 1 `artifact` (the central metaphor) +
  1–3 `plaque`s (the distilled mechanics) + 1 `diagram` (the structure) +
  optionally 1 `portrait` (the voice) + 1 `tome` (the full source text).
- **Accuracy beats atmosphere**: the metaphor must map 1-to-1 onto the real mechanism.
  If the math says 0.996 EMA, the Target Scribe drifts by exactly that.
- A `plaque` should be readable in ~30 seconds. Push anything longer into a `tome`.

## Hard rules

1. Never edit anything in `engine/`, `world/schema.json`, or `world/catalog.json`.
2. Never invent props, palettes, sizes, or relations not in the catalog — leave a TODO instead.
3. Never reuse or change an existing `id`. Never renumber existing `order`s.
4. Never delete existing content unless explicitly asked.
5. Always finish with a clean `python world.py validate`. A successful validate also
   regenerates `world/rooms/index.json` (the engine's load manifest) — that file
   changing is expected; include it in your change list, never edit it by hand.
