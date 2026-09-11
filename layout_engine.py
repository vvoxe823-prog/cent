"""
PlanForge layout engine.

Generates preliminary 2D architectural room arrangements from normalized
planning input. This is a conceptual planning engine, not a structural,
statutory, or construction-document generator.
"""

from dataclasses import dataclass, asdict
import math
import re


@dataclass
class Rect:
    name: str
    x: float
    y: float
    width: float
    depth: float
    kind: str = "room"
    floor: int = 1

    @property
    def x2(self):
        return self.x + self.width

    @property
    def y2(self):
        return self.y + self.depth

    @property
    def area(self):
        return self.width * self.depth

    def to_dict(self):
        d = asdict(self)
        d.update({"x2": round(self.x2, 2), "y2": round(self.y2, 2),
                  "area": round(self.area, 2)})
        for k in ("x", "y", "width", "depth"):
            d[k] = round(d[k], 2)
        return d


ROOMS = {
    "living": (10, 12, 9, 10),
    "bedroom": (10, 10, 9, 9),
    "master_bedroom": (11, 12, 10, 10),
    "kitchen": (7, 8, 6, 7),
    "dining": (8, 9, 7, 8),
    "bathroom": (5, 7, 4.5, 6),
    "pooja": (4, 5, 3.5, 4),
    "utility": (5, 7, 4.5, 6),
    "store": (5, 5, 4, 4),
    "study": (7, 8, 6, 7),
    "staircase": (7, 12, 6, 10),
    "lift": (5, 5, 4.5, 4.5),
    "car": (9, 16, 8, 14),
    "bike": (3, 7, 2.5, 6),
}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _int(v, default=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _feet(value, unit):
    return _num(value) * (3.280839895 if str(unit).lower().startswith("m") else 1)


def _preferred_size(value, fallback):
    if not value:
        return fallback
    m = re.search(r"(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)", str(value))
    if not m:
        return fallback
    return float(m.group(1)), float(m.group(2))


def _required_rooms(data):
    r = data["rooms"]
    p = data["preferences"]
    result = []

    for i in range(max(0, _int(r.get("living_rooms")))):
        result.append(("Living Room" if i == 0 else f"Living Room {i+1}",
                       "living", _preferred_size(p.get("living_size"), ROOMS["living"])))
    for i in range(max(0, _int(r.get("bedrooms")))):
        key = "master_bedroom" if i == 0 else "bedroom"
        pref = p.get("master_bedroom_size") if i == 0 else p.get("bedroom_size")
        result.append(("Master Bedroom" if i == 0 else f"Bedroom {i+1}",
                       key, _preferred_size(pref, ROOMS[key])))
    for key, label, pref_key in [
        ("kitchen", "Kitchen", "kitchen_size"),
        ("dining", "Dining", None),
        ("bathroom", "Bathroom", None),
        ("pooja", "Pooja Room", None),
        ("utility", "Utility", None),
        ("store", "Store", None),
        ("study", "Study", None),
    ]:
        count_key = {
            "kitchen": "kitchens", "dining": "dining_rooms",
            "bathroom": "bathrooms", "pooja": "pooja_rooms",
            "utility": "utility_rooms", "store": "store_rooms",
            "study": "study_rooms"
        }[key]
        for i in range(max(0, _int(r.get(count_key)))):
            label_i = label if i == 0 else f"{label} {i+1}"
            pref = _preferred_size(p.get(pref_key), ROOMS[key]) if pref_key else ROOMS[key]
            result.append((label_i, key, pref))

    return result


def _parking(data, width, depth):
    c = max(0, _int(data["circulation"].get("parking_cars")))
    b = max(0, _int(data["circulation"].get("parking_bikes")))
    items = []
    x = 0.0
    for i in range(c):
        w, d, _, _ = ROOMS["car"]
        if x + w <= width + 0.01 and d <= depth:
            items.append(Rect(f"Car Parking {i+1}", x, 0, w, d, "parking"))
            x += w + 0.5
    for i in range(b):
        w, d, _, _ = ROOMS["bike"]
        if x + w <= width + 0.01 and d <= depth:
            items.append(Rect(f"Bike Parking {i+1}", x, 0, w, d, "parking"))
            x += w + 0.5
    return items


def _fits(rect, width, depth):
    return rect.x >= -0.01 and rect.y >= -0.01 and rect.x2 <= width + 0.01 and rect.y2 <= depth + 0.01


def _overlap(a, b, gap=0.05):
    return a.x < b.x2 - gap and a.x2 > b.x + gap and a.y < b.y2 - gap and a.y2 > b.y + gap


def _score(rooms, width, depth, targets):
    penalty = 0.0
    warnings = []
    for i, a in enumerate(rooms):
        if not _fits(a, width, depth):
            penalty += 80
        for b in rooms[i+1:]:
            if _overlap(a, b):
                penalty += 120
    usable = width * depth
    used = sum(r.area for r in rooms if r.kind not in ("parking",))
    utilization = used / usable if usable else 9
    if utilization > 0.95:
        penalty += (utilization - 0.95) * 300
        warnings.append("Very high space utilization; circulation is tight.")
    if utilization < 0.35:
        penalty += (0.35 - utilization) * 50
    for r in rooms:
        if r.kind in targets:
            _, _, minw, mind = targets[r.kind]
            if r.width < minw - 0.01 or r.depth < mind - 0.01:
                penalty += 12
                warnings.append(f"{r.name} is below the preferred minimum size.")
    return round(max(0, 100 - penalty), 2), list(dict.fromkeys(warnings))



def _room_specs(data):
    """Return requested room specs with preferred/minimum dimensions."""
    specs = []
    for name, kind, size in _required_rooms(data):
        target = tuple(size[:2])
        base = ROOMS[kind]
        specs.append({
            "name": name,
            "kind": kind,
            "target": target,
            "min": (base[2], base[3]),
        })
    return specs


def _rect_free(rect, placed, gap=0.15):
    return all(not _overlap(rect, other, gap=gap) for other in placed)


def _candidate_sizes(spec):
    """Generate useful orientations and compact sizes."""
    tw, td = spec["target"]
    mw, md = spec["min"]
    sizes = []

    for w, d in ((tw, td), (td, tw)):
        # Preferred size first, then compact toward minimum.
        for scale in (1.0, 0.92, 0.84, 0.76, 0.68):
            cw = max(mw, w * scale)
            cd = max(md, d * scale)
            pair = (round(cw, 2), round(cd, 2))
            if pair not in sizes:
                sizes.append(pair)

    return sizes


def _placement_candidates(spec, width, depth, placed, anchors):
    """Create candidate rectangles at useful grid/anchor positions."""
    out = []
    for w, d in _candidate_sizes(spec):
        if w > width + 0.01 or d > depth + 0.01:
            continue

        xs = {0.0, max(width - w, 0.0)}
        ys = {0.0, max(depth - d, 0.0)}

        # Align to edges of existing rooms; this creates compact architectural
        # partitions instead of arbitrary row packing.
        for r in placed:
            for x in (r.x2, r.x - w):
                if -0.01 <= x <= width - w + 0.01:
                    xs.add(round(max(0.0, min(x, width - w)), 2))
            for y in (r.y2, r.y - d):
                if -0.01 <= y <= depth - d + 0.01:
                    ys.add(round(max(0.0, min(y, depth - d)), 2))

        for ax, ay in anchors:
            x = max(0.0, min(ax, width - w))
            y = max(0.0, min(ay, depth - d))
            xs.add(round(x, 2))
            ys.add(round(y, 2))

        for x in sorted(xs):
            for y in sorted(ys):
                rect = Rect(spec["name"], x, y, w, d, spec["kind"])
                if _rect_free(rect, placed):
                    out.append(rect)

    return out


def _room_order(specs, strategy):
    """Hard rooms first, with strategy-specific zoning preferences."""
    def key(s):
        area = s["target"][0] * s["target"][1]
        hard = 0
        if s["kind"] in ("master_bedroom", "bedroom", "living"):
            hard = -2
        elif s["kind"] in ("kitchen", "dining"):
            hard = -1

        if strategy == "privacy":
            zone = 0 if s["kind"] in ("master_bedroom", "bedroom") else 1
        elif strategy == "ventilation":
            zone = 0 if s["kind"] in ("living", "dining", "kitchen") else 1
        else:
            zone = 0

        return (hard, zone, -area)

    return sorted(specs, key=key)


def _zoning_penalty(rect, kind, width, depth, strategy):
    """Soft architectural zoning score; lower is better."""
    cy = rect.y + rect.depth / 2
    cx = rect.x + rect.width / 2
    penalty = 0.0

    public = {"living", "dining", "kitchen", "pooja", "study"}
    private = {"master_bedroom", "bedroom"}
    service = {"bathroom", "utility", "store"}

    if strategy == "privacy":
        if kind in private:
            penalty += cy / max(depth, 1) * 8
        if kind in public:
            penalty += (1 - cy / max(depth, 1)) * 3
    else:
        if kind in public:
            penalty += cy / max(depth, 1) * 4
        if kind in private:
            penalty += (1 - cy / max(depth, 1)) * 4

    if strategy == "ventilation":
        # Favor perimeter placement for major rooms.
        edge_distance = min(cx, width - cx, cy, depth - cy)
        penalty += edge_distance * 0.25

    if kind in service:
        # Services should remain reasonably compact toward one side.
        penalty += abs(cx - width * 0.75) * 0.12

    return penalty


def _search_layout(specs, width, depth, fixed, strategy, max_nodes=12000):
    """Backtracking rectangle packing with minimum-size constraints."""
    best = None
    nodes = 0
    placed = list(fixed)

    # Avoid placing small service rooms before large rooms.
    ordered = _room_order(specs, strategy)

    # Candidate anchors encourage edge-to-edge partitions.
    anchors = [(0, 0), (width, 0), (0, depth), (width, depth),
               (width / 2, 0), (0, depth / 2)]

    def recurse(index, current, cost, compacted):
        nonlocal best, nodes
        nodes += 1
        if nodes > max_nodes:
            return

        if index >= len(ordered):
            # Reward area utilization while keeping a little breathing room.
            room_area = sum(r.area for r in current if r.kind not in ("parking",))
            utilization = room_area / (width * depth) if width * depth else 1
            final_cost = cost + abs(0.72 - utilization) * 10 + compacted * 2

            if best is None or final_cost < best[0]:
                best = (final_cost, list(current))
            return

        spec = ordered[index]
        candidates = _placement_candidates(
            spec, width, depth, current, anchors
        )

        scored = []
        for rect in candidates:
            # Prefer preferred dimensions, then architectural zoning.
            tw, td = spec["target"]
            size_penalty = abs(rect.width - tw) + abs(rect.depth - td)
            zone_penalty = _zoning_penalty(
                rect, spec["kind"], width, depth, strategy
            )

            # Keep requested spaces away from a likely front/road edge when
            # privacy strategy is selected.
            score = size_penalty + zone_penalty
            compact = 0 if (
                abs(rect.width - tw) < 0.01 and abs(rect.depth - td) < 0.01
            ) else 1
            scored.append((score, compact, rect))

        scored.sort(key=lambda item: item[0])

        for score, compact, rect in scored[:80]:
            recurse(
                index + 1,
                current + [rect],
                cost + score,
                compacted + compact
            )

    recurse(0, placed, 0.0, 0)

    return best[1] if best else None


def _validate_layout(rooms, width, depth):
    """Return hard validity plus human-readable warnings."""
    warnings = []

    for i, a in enumerate(rooms):
        if not _fits(a, width, depth):
            warnings.append(f"{a.name} extends outside the buildable envelope.")
        for b in rooms[i + 1:]:
            if _overlap(a, b):
                warnings.append(f"{a.name} overlaps {b.name}.")

    return len(warnings) == 0, list(dict.fromkeys(warnings))


def _score_valid_layout(rooms, width, depth, targets, warnings):
    """Score only valid layouts; validity failures receive zero."""
    valid, hard_warnings = _validate_layout(rooms, width, depth)
    if not valid:
        return 0.0, hard_warnings

    soft_warnings = list(warnings)
    penalty = 0.0

    usable = width * depth
    used = sum(r.area for r in rooms if r.kind not in ("parking",))
    utilization = used / usable if usable else 1

    # Good layouts use space efficiently but leave circulation margin.
    penalty += abs(0.70 - utilization) * 35

    for r in rooms:
        if r.kind in targets:
            _, _, minw, mind = targets[r.kind]
            if r.width < minw - 0.01 or r.depth < mind - 0.01:
                return 0.0, soft_warnings + [
                    f"{r.name} is below the minimum allowed planning size."
                ]

    score = max(0.0, min(100.0, 100.0 - penalty - len(soft_warnings) * 2))
    return round(score, 2), list(dict.fromkeys(soft_warnings))


def _candidate(data, strategy):
    env = data["buildable_area_preliminary"]
    width, depth = env["width"], env["depth"]

    if width <= 0 or depth <= 0:
        return [], 0.0, ["Buildable envelope has zero area."], False

    parking = _parking(data, width, depth)

    # Parking is fixed only when it actually fits. Otherwise it becomes a
    # feasibility warning rather than being allowed to corrupt the house plan.
    parking_warnings = []
    valid_parking = []
    for p in parking:
        if _fits(p, width, depth) and _rect_free(p, valid_parking):
            valid_parking.append(p)
        else:
            parking_warnings.append(f"{p.name} could not fit in the buildable envelope.")

    specs = _room_specs(data)
    requested_area = sum(s["target"][0] * s["target"][1] for s in specs)

    fixed = list(valid_parking)

    # Keep the house clear of front parking. This creates a simple circulation
    # buffer rather than allowing rooms to overlap parking.
    parking_depth = max((r.y2 for r in fixed), default=0.0)
    house_y = parking_depth + (0.75 if fixed else 0.0)

    if house_y >= depth:
        return fixed, 0.0, parking_warnings + [
            "Parking consumes the available buildable depth."
        ], False

    # Work in a local house envelope above the parking strip.
    house_depth = depth - house_y

    # Build staircase/lift as fixed circulation constraints before rooms.
    fixed_house = []
    stair_type = str(data["circulation"].get("staircase_type", "none")).lower()
    stair_pref = str(data["circulation"].get("staircase_preference", "auto")).lower()

    if stair_type in ("internal", "both"):
        sw, sd, _, _ = ROOMS["staircase"]
        sw = min(sw, width)
        sd = min(sd, house_depth)
        if sw > 0 and sd > 0:
            if stair_pref in ("west", "northwest", "southwest", "auto"):
                sx = 0.0
            else:
                sx = max(width - sw, 0.0)
            sy = house_y + max(house_depth - sd, 0.0)
            fixed_house.append(Rect(
                "Internal Staircase", sx, sy, sw, sd, "staircase"
            ))

    if str(data["circulation"].get("lift", "no")).lower() == "yes":
        lw, ld, _, _ = ROOMS["lift"]
        lw = min(lw, width)
        ld = min(ld, house_depth)
        lx = max(width - lw, 0.0)
        ly = house_y
        lift = Rect("Lift", lx, ly, lw, ld, "lift")
        if _rect_free(lift, fixed_house):
            fixed_house.append(lift)
        else:
            parking_warnings.append("Lift could not be placed without conflicting with the staircase.")

    fixed.extend(fixed_house)

    # Translate room search into the full envelope by adding a temporary
    # boundary guard. The search itself uses y coordinates relative to house_y.
    # For simplicity, fixed circulation is included and candidate coordinates
    # are generated over the full envelope; the front parking strip is blocked
    # by a guard rectangle.
    if house_y > 0:
        fixed.append(Rect("_ParkingBuffer", 0, 0, width, house_y, "buffer"))

    layout = _search_layout(
        specs, width, depth, fixed, strategy,
        max_nodes=16000
    )

    if layout is None:
        warnings = parking_warnings + [
            "No complete non-overlapping layout could satisfy all requested rooms and minimum dimensions "
            f"inside the {width:.1f} × {depth:.1f} ft buildable envelope."
        ]
        if requested_area > width * house_depth:
            warnings.append(
                f"Requested room target area ({requested_area:.0f} sq ft) exceeds "
                f"the usable house area ({width*house_depth:.0f} sq ft)."
            )
        return [], 0.0, list(dict.fromkeys(warnings)), False

    # Remove internal guard from output.
    layout = [r for r in layout if r.kind != "buffer"]

    target_map = {k: ROOMS[k] for k in ROOMS}
    score, warnings = _score_valid_layout(
        layout, width, depth, target_map, parking_warnings
    )

    valid, hard_warnings = _validate_layout(layout, width, depth)
    if not valid:
        return layout, 0.0, hard_warnings, False

    # Ensure every requested room is present.
    expected = [s["name"] for s in specs]
    present = {r.name for r in layout}
    missing = [name for name in expected if name not in present]
    if missing:
        warnings.append("Missing requested spaces: " + ", ".join(missing))
        return layout, 0.0, list(dict.fromkeys(warnings)), False

    return layout, score, list(dict.fromkeys(warnings)), True


def generate_layouts(data, max_plans=3):
    """Return ranked, non-overlapping preliminary layout alternatives."""
    plans = []

    for strategy in ("balanced", "privacy", "ventilation"):
        rooms, score, warnings, valid = _candidate(data, strategy)

        plans.append({
            "strategy": strategy,
            "valid": valid,
            "score": score,
            "buildable_area": data["buildable_area_preliminary"],
            "rooms": [r.to_dict() for r in rooms],
            "warnings": warnings,
            "engine_note": (
                "Conceptual 2D planning only; verify local bylaws, setbacks, "
                "fire/life-safety, accessibility and structural requirements "
                "with qualified professionals."
            )
        })

    plans.sort(key=lambda p: (p["valid"], p["score"]), reverse=True)
    return plans[:max_plans]

