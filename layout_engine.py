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


def _place_band(rooms, specs, width, y, available_depth, strategy):
    """Compact row packing. Rooms can share a row; row height is max room depth."""
    x = 0.0
    row = []
    remaining = list(specs)

    # strategy changes ordering to create genuinely different alternatives
    if strategy == "privacy":
        remaining.sort(key=lambda s: (0 if "Bedroom" in s[0] or "Master" in s[0] else 1, -s[2][0]*s[2][1]))
    elif strategy == "ventilation":
        remaining.sort(key=lambda s: (-(s[2][0]), s[2][1]))
    else:
        remaining.sort(key=lambda s: -(s[2][0]*s[2][1]))

    max_rows = max(1, int(math.ceil(len(remaining) / 2)))
    while remaining:
        placed_this_row = []
        x = 0.0
        row_depth = 0.0
        for spec in list(remaining):
            name, kind, size = spec
            # ROOMS entries contain (width, depth, min_width, min_depth),
            # while preferred sizes contain only (width, depth).
            # The placement engine only needs the target width/depth here.
            w, d = size[:2]
            # Rotate a room if it gives a better fit.
            candidates = [(w, d), (d, w)] if abs(w-d) > 0.01 else [(w,d)]
            chosen = None
            for cw, cd in candidates:
                if x + cw <= width + 0.01 and cd <= available_depth + 0.01:
                    chosen = (cw, cd)
                    break
            if chosen:
                cw, cd = chosen
                rooms.append(Rect(name, x, y, cw, cd, kind))
                placed_this_row.append(spec)
                x += cw
                row_depth = max(row_depth, cd)
                remaining.remove(spec)
        if not placed_this_row:
            break
        y += row_depth
        available_depth -= row_depth
        if available_depth <= 0.01:
            break
    return y, remaining


def _candidate(data, strategy):
    env = data["buildable_area_preliminary"]
    width, depth = env["width"], env["depth"]
    rooms = []
    warnings = []

    if width <= 0 or depth <= 0:
        return [], -999, ["Buildable envelope has zero area."]

    # Front parking consumes the road-facing edge. Remaining area is the house envelope.
    parking = _parking(data, width, depth)
    rooms.extend(parking)
    parking_depth = max((r.y2 for r in parking), default=0)

    specs = _required_rooms(data)

    # Place public spaces toward front, private spaces toward rear.
    public = [s for s in specs if s[1] in ("living", "dining", "kitchen", "pooja", "study")]
    private = [s for s in specs if s[1] in ("master_bedroom", "bedroom", "bathroom", "utility", "store")]

    y = parking_depth + 0.75 if parking else 0.0
    available = depth - y

    if strategy == "privacy":
        bands = [private, public]
    else:
        bands = [public, private]

    remaining = []
    for band in bands:
        y, left = _place_band(rooms, band, width, y, available, strategy)
        remaining.extend(left)
        available = depth - y

    # Any unplaced rooms are attempted in a final compact pass.
    if remaining and available > 0:
        y, remaining = _place_band(rooms, remaining, width, y, available, strategy)

    # Add staircase/lift last, prioritizing the requested side.
    stair_type = str(data["circulation"].get("staircase_type", "none")).lower()
    stair_pref = str(data["circulation"].get("staircase_preference", "auto")).lower()
    if stair_type in ("internal", "both"):
        sw, sd, _, _ = ROOMS["staircase"]
        sx = 0 if stair_pref in ("auto", "west", "northwest", "southwest") else max(width-sw, 0)
        sy = max(depth-sd, 0)
        rooms.append(Rect("Internal Staircase", sx, sy, min(sw,width), min(sd,depth), "staircase"))

    if str(data["circulation"].get("lift", "no")).lower() == "yes":
        lw, ld, _, _ = ROOMS["lift"]
        lx = max(width-lw, 0)
        ly = 0
        rooms.append(Rect("Lift", lx, ly, min(lw,width), min(ld,depth), "lift"))

    target_map = {k: ROOMS[k] for k in ROOMS}
    score, score_warnings = _score(rooms, width, depth, target_map)
    warnings.extend(score_warnings)

    if remaining:
        warnings.append("Some requested spaces could not be placed inside the entered buildable envelope.")
        score -= len(remaining) * 18

    requested_area = sum(s[2][0] * s[2][1] for s in specs)
    if requested_area > width * depth:
        warnings.append(
            f"Requested room target area ({requested_area:.0f} sq ft) exceeds the "
            f"buildable envelope ({width*depth:.0f} sq ft); dimensions were compacted where possible."
        )

    return rooms, round(score, 2), list(dict.fromkeys(warnings))


def generate_layouts(data, max_plans=3):
    """Return up to three ranked preliminary layout alternatives."""
    plans = []
    for strategy in ("balanced", "privacy", "ventilation"):
        rooms, score, warnings = _candidate(data, strategy)
        plans.append({
            "strategy": strategy,
            "score": score,
            "buildable_area": data["buildable_area_preliminary"],
            "rooms": [r.to_dict() for r in rooms],
            "warnings": warnings,
            "engine_note": "Conceptual 2D planning only; verify local bylaws, setbacks, fire/life-safety, accessibility and structural requirements with qualified professionals."
        })
    plans.sort(key=lambda p: p["score"], reverse=True)
    return plans[:max_plans]
