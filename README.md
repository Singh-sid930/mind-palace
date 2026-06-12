# The Palace of Mind

A walkable, Harry Potter–styled mind palace. Every piece of knowledge you learn becomes
a 3D chamber you can physically walk through: artifacts are working metaphors, plaques
carry the distilled mechanics, tomes hold full source texts, portals and a constellation
map keep every idea connected.

**The core design:** the engine is code, built once; the world is pure data, grown
forever. Any LLM can extend the palace by writing small JSON files against
[WORLD_SPEC.md](WORLD_SPEC.md) and running the validator — no code, no coordinates,
no assets.

## Run it

```bash
cd mind-palace
python serve.py
# open http://localhost:8777
```

WASD + mouse to walk, **E** study / step through portals, **T** talk to Gemma,
**M** map, **G** constellation of ideas, **F** floo travel, **Shift** run.
Click a diagram (or its ⛶ button) to maximize it.

## Gemma, the Whispering Sage

A ghost companion drifts at your shoulder, backed by the local Ollama service
(`gemma3:27b` on the always-on systemd instance at `localhost:11434`; override
with `OLLAMA_URL` / `OLLAMA_MODEL`). She knows which room you're in, which
exhibit you're studying, and the concepts anchored there — so "why doesn't
this collapse?" needs no setup. Answers come as short speech bubbles; anything
that needs depth is saved as a parchment-styled HTML **scroll** in `scrolls/`
with a 📜 link in the bubble. `serve.py` never starts Ollama itself — it only
talks to the existing service.

## Grow it

Give any capable model this prompt:

> Read WORLD_SPEC.md in ~/workspace/mind-palace and add what I just learned about
> <topic> as a new room (or extend an existing wing). Run `python world.py validate`
> until it passes.

The validator (`world.py`) enforces the schema and referential integrity, and
regenerates the engine's room manifest only on success — unvalidated content never
renders.

## Layout

```
index.html          # the game (open via a static server)
WORLD_SPEC.md       # the content contract for models
world.py            # validator CLI: python world.py validate | summary
world/
  world.json        # palace title, hub, wings
  rooms/*.json      # one file per room (validated, data-only)
  graph.json        # knowledge graph: concepts + edges
  schema.json       # JSON Schema for all of the above
  catalog.json      # allowed props / palettes / sizes / relations
engine/             # Three.js renderer — content models never touch this
  layout.js         # deterministic solver: semantics -> geometry
  builder.js        # procedural rooms, walls, doors, lights, sky
  props.js          # 13 parametric props (primitives only, zero assets)
  exhibits.js       # exhibit placement + portals
  player.js         # first-person controls + collision
  hud.js            # focus panels, map, constellation, floo
  vendor/           # three.js (vendored, no CDN needed to walk around)
tools/shoot.py      # headless screenshot harness (dev; needs playwright)
```

Diagrams render via Mermaid from CDN when online; offline they fall back to the
diagram source text. Everything else runs fully offline.

## Current wings

- **The Divination Wing** (emerald) — JEPA-family self-supervised learning, migrated
  from the original Hogwarts Chronicles: the Mirror of Occlusion (I-JEPA), the Corridor
  of the Three Vows (VICReg), the Restricted Section of Soft Shields (projector heads),
  and the Great Hall of the Paris Cauldron (the JEPA realm).
