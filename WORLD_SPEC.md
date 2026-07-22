# Mind Palace — World Specification

You are a **content model**. Your job is to grow the palace by writing **data files only**.
You never write code, never place coordinates, never create graphical assets. The engine
turns your declarations into walkable 3D rooms automatically.

This palace is a Harry Potter–style *mind palace*: a memory technique made literal. Each
piece of real knowledge (a paper, a concept, a technique) becomes a themed chamber the
user can physically walk through. Narrative and metaphor are encouraged; factual fidelity
of the underlying knowledge is mandatory.

## The one workflow

1. Read this file and `world/catalog.json`.
2. Skim 1–2 existing files in `world/rooms/` and `world/graph/` as style references.
3. Write or edit room JSON file(s) in `world/rooms/` (one file per room, filename `<room-id>.json`).
4. Register every new concept in that room's graph fragment `world/graph/<room-id>.json`
   and connect it with edges (create the fragment if the room is new).
5. Run `python world.py validate` from the project root. Fix every error. Repeat until it prints `WORLD OK`.
6. In your final report, list rooms added/changed and any TODOs (e.g. a prop you wished existed).

A change is **not done** until `python world.py validate` passes.

## How space works (so you don't think about it)

- The palace is a stack of **levels** (floors) declared in `world/world.json`. Each level
  has its own hub room and a signed `tier`: vertical position encodes *knowledge lineage*
  (mathematical foundations below, what builds on them above).
- Each level holds at most **4 wings** radiating from its hub (the validator enforces
  this). To grow beyond that, add a new level — levels are unbounded.
- Levels connect through **passages** declared in `world.json`: typed `stair` (across
  tiers) or `archway` (lateral, between sibling wings), optionally carrying a `gate`
  whose `prereqs` (concept ids) summon the Gatekeeper quiz-ghost. Passages are palace
  architecture — coordinate with the palace author before adding one.
- A room belongs to a wing and has an integer `order` (1, 2, 3, …). The engine grows the
  wing as a branching "fishbone": a spine of chambers advances outward from the hub in
  walking order (and bends once mid-way), while every other room buds off to alternating
  sides as a side-chamber. Connected rooms get corridors and real doorways. You never
  see or set this — just give each room its `order`; a wing always ends on its
  highest-order room, so put the climactic chamber last.
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

`prop` must come from `props` in `world/catalog.json`. Furniture:
pedestal, lectern, mirror, cauldron, bookshelf, statue, banner, candelabra,
orrery, crystal_ball, hourglass, table, brazier. **Kinetic concept props**
(animated mechanisms — pick one only when its motion matches the room's
concept): attention_beams (softmax weights flowing to orbiting keys),
similarity_dial (sweeping angle + live cosine bar), frequency_wheel (nested
hands at doubling speeds), error_scales (balance settling as loss shrinks),
variance_balance (two columns trading under a fixed budget cap),
dissolving_cloud (figure melting into noise), reforming_cloud (noise
gathering into a figure), patch_shuttle (image cut into a token thread and
rewoven), guidance_arrows (u + w·(c−u) extrapolating as w sweeps),
low_rank_bottleneck (signal squeezing d→r→d through a thin rank-r waist),
exp_log_sphere (a straight tangent vector wrapping onto a sphere as a geodesic — the exp/log map).

`diagram.spec` is standard Mermaid (`graph TD`, `graph LR`, `sequenceDiagram`).
Keep diagrams ≤ ~12 nodes; they render on an in-world panel. **Always wrap node
and edge labels in double quotes** — `A["Var(X) = 1"]`, `-->|"O(n^2)"| B` —
because unquoted `()`/`{}` inside a label is parsed as Mermaid shape syntax and
the diagram silently fails to render in-world.

## Knowledge graph — `world/graph/<room-id>.json`

The graph is the palace's ground truth of *what is known and how it connects*. It is
authored as **one fragment per room** so many rooms can be written in parallel without
ever touching a shared file. A fragment holds the concepts anchored in that room plus
the edges those concepts originate:

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

- Every concept's `room` must equal the fragment's filename; edges may point at
  concepts in *any* fragment (cross-room edges are the point).
- Every room you add should anchor ≥1 concept. `exhibit` is optional — include it when
  one exhibit *is* that concept; several concepts may point at the same exhibit; omit
  it for room-level concepts.
- `relation` ∈ `builds-on`, `relates-to`, `contrasts-with`, `part-of` (see catalog).
- Edges power the in-game constellation map, the wayfinding signposts and the
  Gatekeeper's quizzes. Be generous with them — connection is the point of the palace.
- Concept `summary` doubles as the Gatekeeper's quiz source: for foundation-floor
  concepts, lead with the pure mathematics and leave any ML framing to a trailing
  "(Upstairs: …)" parenthetical.
- `world/graph.json` (the merged graph the engine loads) is **generated** by a clean
  validate — never edit it by hand.

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
   regenerates the engine's load artifacts — `world/rooms/index.json` and the merged
   `world/graph.json` — those files changing is expected; include them in your change
   list, never edit them by hand.
