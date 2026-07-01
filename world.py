#!/usr/bin/env python
"""Mind Palace world validator.

Usage (from the project root):
    python world.py validate   # schema + referential integrity; exits non-zero on errors
    python world.py summary    # human-readable overview of the world

Content models MUST run `validate` after every change and fix all errors.
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).parent
WORLD_DIR = ROOT / "world"
ROOMS_DIR = WORLD_DIR / "rooms"


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except json.JSONDecodeError as e:
        return None, f"{path.relative_to(ROOT)}: invalid JSON — {e}"
    except FileNotFoundError:
        return None, f"{path.relative_to(ROOT)}: file not found"


def load_world():
    """Load every world file. Returns (data, errors)."""
    errors = []
    schema, err = _load(WORLD_DIR / "schema.json")
    if err:
        return None, [err]
    catalog, err = _load(WORLD_DIR / "catalog.json")
    if err:
        return None, [err]
    world, err = _load(WORLD_DIR / "world.json")
    if err:
        errors.append(err)
    graph, err = _load(WORLD_DIR / "graph.json")
    if err:
        errors.append(err)

    rooms = {}
    for path in sorted(ROOMS_DIR.glob("*.json")):
        if path.name == "index.json":  # engine manifest, not a room
            continue
        room, err = _load(path)
        if err:
            errors.append(err)
            continue
        rooms[path.stem] = (room, path)

    return {"schema": schema, "catalog": catalog, "world": world,
            "graph": graph, "rooms": rooms}, errors


def _schema_check(instance, schema, defs_key, label, errors):
    resolver_schema = dict(schema)
    resolver_schema["$ref"] = f"#/definitions/{defs_key}"
    validator = jsonschema.Draft7Validator(resolver_schema)
    for e in sorted(validator.iter_errors(instance), key=str):
        loc = "/".join(str(p) for p in e.absolute_path) or "(root)"
        errors.append(f"{label}: schema error at {loc}: {e.message}")


def validate(data):
    errors = []
    schema = data["schema"]
    catalog = data["catalog"]
    world = data["world"]
    graph = data["graph"]
    rooms = data["rooms"]

    # --- Schema validation ------------------------------------------------
    if world is not None:
        _schema_check(world, schema, "world", "world/world.json", errors)
    if graph is not None:
        _schema_check(graph, schema, "graph", "world/graph.json", errors)
    for stem, (room, path) in rooms.items():
        label = f"world/rooms/{path.name}"
        _schema_check(room, schema, "room", label, errors)
        if isinstance(room, dict) and room.get("id") != stem:
            errors.append(f"{label}: filename must equal room id (got id={room.get('id')!r})")

    if errors:
        return errors  # referential checks would just cascade noise

    # --- Referential integrity --------------------------------------------
    wing_ids = {w["id"] for w in world["wings"]}
    room_ids = set(rooms.keys())
    palettes = set(catalog["palettes"])
    props = set(catalog["props"])
    relations = set(catalog["edge_relations"])

    hub = world["hub"]
    if hub not in room_ids:
        errors.append(f"world.json: hub room '{hub}' has no file in world/rooms/")

    # Each level has its own hub room (with wing: null); the spawn hub is one of them.
    levels = world.get("levels", [])
    level_ids = {lvl["id"] for lvl in levels}
    level_hubs = {lvl["hub"] for lvl in levels} | {hub}
    for lvl in levels:
        if lvl["hub"] not in room_ids:
            errors.append(f"world.json: level '{lvl['id']}' hub '{lvl['hub']}' has no room file")

    for w in world["wings"]:
        if w["palette"] not in palettes:
            errors.append(f"world.json: wing '{w['id']}' palette '{w['palette']}' not in catalog")
        if w.get("level") and w["level"] not in level_ids:
            errors.append(f"world.json: wing '{w['id']}' level '{w['level']}' not declared in levels")

    seen_orders = {}
    for stem, (room, path) in rooms.items():
        label = f"world/rooms/{path.name}"
        wing = room["wing"]

        if stem in level_hubs:
            if wing is not None:
                errors.append(f"{label}: hub room must have wing: null")
        elif wing is None:
            errors.append(f"{label}: only a hub room may have wing: null")
        elif wing not in wing_ids:
            errors.append(f"{label}: wing '{wing}' not declared in world.json")

        if wing is not None:
            key = (wing, room["order"])
            if key in seen_orders:
                errors.append(
                    f"{label}: order {room['order']} already used in wing '{wing}' "
                    f"by '{seen_orders[key]}'"
                )
            seen_orders[key] = stem

        if room.get("palette") and room["palette"] not in palettes:
            errors.append(f"{label}: palette '{room['palette']}' not in catalog")

        for conn in room.get("connections", []):
            if conn not in room_ids:
                errors.append(f"{label}: connection '{conn}' is not an existing room")
            if conn == stem:
                errors.append(f"{label}: room connects to itself")

        ex_ids = set()
        for ex in room["exhibits"]:
            if ex["id"] in ex_ids:
                errors.append(f"{label}: duplicate exhibit id '{ex['id']}'")
            ex_ids.add(ex["id"])
            if ex["type"] == "artifact" and ex.get("prop") not in props:
                errors.append(f"{label}: exhibit '{ex['id']}' prop '{ex.get('prop')}' not in catalog")
            if ex["type"] == "stair" and ex.get("to") not in room_ids:
                errors.append(f"{label}: stair '{ex['id']}' to '{ex.get('to')}' is not an existing room")

    # Wing chains must start at order 1 and have no gaps.
    by_wing = {}
    for (wing, order), stem in seen_orders.items():
        by_wing.setdefault(wing, []).append(order)
    for wing, orders in by_wing.items():
        expect = list(range(1, len(orders) + 1))
        if sorted(orders) != expect:
            errors.append(
                f"wing '{wing}': room orders must be 1..{len(orders)} with no gaps "
                f"(found {sorted(orders)})"
            )

    # Graph integrity.
    concept_ids = set()
    for c in graph["concepts"]:
        if c["id"] in concept_ids:
            errors.append(f"graph.json: duplicate concept id '{c['id']}'")
        concept_ids.add(c["id"])
        if c["room"] not in room_ids:
            errors.append(f"graph.json: concept '{c['id']}' room '{c['room']}' does not exist")
        elif c.get("exhibit"):
            room = rooms[c["room"]][0]
            if c["exhibit"] not in {e["id"] for e in room["exhibits"]}:
                errors.append(
                    f"graph.json: concept '{c['id']}' exhibit '{c['exhibit']}' "
                    f"not found in room '{c['room']}'"
                )
    for e in graph["edges"]:
        for end in ("from", "to"):
            if e[end] not in concept_ids:
                errors.append(f"graph.json: edge {end} '{e[end]}' is not a declared concept")
        if e["relation"] not in relations:
            errors.append(f"graph.json: edge relation '{e['relation']}' not in catalog")

    return errors


def summary(data):
    world, graph, rooms = data["world"], data["graph"], data["rooms"]
    print(f"{world['title']} — {world.get('subtitle', '')}")
    levels = world.get("levels") or [{"id": None, "name": "(single level)", "hub": world["hub"]}]
    levels = sorted(levels, key=lambda l: l.get("tier", 0), reverse=True)
    for lvl in levels:
        print(f"\n== {lvl['name']} [{lvl['id']}] · tier {lvl.get('tier', 0)} · hub: {lvl['hub']} ==")
        for w in world["wings"]:
            if w.get("level") != lvl["id"]:
                continue
            members = sorted(
                ((r["order"], r["id"], r["name"]) for r, _ in rooms.values() if r["wing"] == w["id"])
            )
            print(f"  {w['name']} [{w['id']}] palette={w['palette']} — {len(members)} room(s)")
            for order, rid, name in members:
                n_ex = len(rooms[rid][0]["exhibits"])
                print(f"    {order}. {name} ({rid}) — {n_ex} exhibits")
    print(f"\n  concepts: {len(graph['concepts'])}, edges: {len(graph['edges'])}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    data, load_errors = load_world()
    if data is None or load_errors:
        for e in load_errors:
            print(f"ERROR  {e}")
        sys.exit(1)

    if cmd == "summary":
        summary(data)
        return

    errors = validate(data)
    if errors:
        for e in errors:
            print(f"ERROR  {e}")
        print(f"\n{len(errors)} error(s). Fix them and re-run: python world.py validate")
        sys.exit(1)

    # The engine loads rooms through this index; only a clean validate
    # regenerates it, so unvalidated content never reaches the renderer.
    index = {"rooms": sorted(p.name for _, p in data["rooms"].values())}
    with open(ROOMS_DIR / "index.json", "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)

    n_rooms = len(data["rooms"])
    print(f"WORLD OK — {n_rooms} rooms, {len(data['graph']['concepts'])} concepts, "
          f"{len(data['graph']['edges'])} edges (rooms/index.json regenerated)")


if __name__ == "__main__":
    main()
