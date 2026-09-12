"""
PlanForge Architectural Layout Engine
Preliminary architectural space-planning engine.

This engine performs feasibility-first rectangle packing. It treats preferred
room sizes as soft targets and minimum room sizes as hard constraints.
Parking, staircase and lift are real occupied rectangles, not an artificial
"house strip". Multiple fixed-space configurations are tested so one poor
parking/stair placement cannot make an otherwise feasible plan fail.

This is NOT a structural, statutory, or construction-document generator.
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
        d.update({
            "x2": round(self.x2, 2),
            "y2": round(self.y2, 2),
            "area": round(self.area, 2),
        })
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
        return fallback[:2]
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)",
        str(value),
    )
    if not m:
        return fallback[:2]
    return float(m.group(1)), float(m.group(2))


def _required_rooms(data):
    r = data.get("rooms", {})
    p = data.get("preferences", {})
    result = []

    for i in range(max(0, _int(r.get("living_rooms")))):
        result.append((
            "Living Room" if i == 0 else f"Living Room {i+1}",
            "living",
            _preferred_size(p.get("living_size"), ROOMS["living"]),
        ))

    for i in range(max(0, _int(r.get("bedrooms")))):
        key = "master_bedroom" if i == 0 else "bedroom"
        pref = p.get("master_bedroom_size") if i == 0 else p.get("bedroom_size")
        result.append((
            "Master Bedroom" if i == 0 else f"Bedroom {i+1}",
            key,
            _preferred_size(pref, ROOMS[key]),
        ))

    for key, label, pref_key, count_key in [
        ("kitchen", "Kitchen", "kitchen_size", "kitchens"),
        ("dining", "Dining", None, "dining_rooms"),
        ("bathroom", "Bathroom", None, "bathrooms"),
        ("pooja", "Pooja Room", None, "pooja_rooms"),
        ("utility", "Utility", None, "utility_rooms"),
        ("store", "Store", None, "store_rooms"),
        ("study", "Study", None, "study_rooms"),
    ]:
        for i in range(max(0, _int(r.get(count_key)))):
            label_i = label if i == 0 else f"{label} {i+1}"
            pref = (
                _preferred_size(p.get(pref_key), ROOMS[key])
                if pref_key else ROOMS[key][:2]
            )
            result.append((label_i, key, pref))

    return result


def _room_specs(data):
    specs = []
    for name, kind, size in _required_rooms(data):
        base = ROOMS[kind]
        specs.append({
            "name": name,
            "kind": kind,
            "target": (float(size[0]), float(size[1])),
            "min": (float(base[2]), float(base[3])),
        })
    return specs


def _fits(r, width, depth):
    return (
        r.x >= -1e-6 and r.y >= -1e-6
        and r.x2 <= width + 1e-6
        and r.y2 <= depth + 1e-6
    )


def _overlap(a, b, gap=0.0):
    return (
        a.x < b.x2 - gap and a.x2 > b.x + gap
        and a.y < b.y2 - gap and a.y2 > b.y + gap
    )


def _free(r, placed):
    return _fits(r, r.x + r.width, r.y + r.depth) and all(
        not _overlap(r, p, 0.0) for p in placed
    )


def _rect_free(r, placed, gap=0.0):
    return _fits(r, r.x + r.width, r.y + r.depth) and all(
        not _overlap(r, p, gap) for p in placed
    )


def _candidate_sizes(spec):
    """Preferred dimensions first, then progressively compact dimensions."""
    tw, td = spec["target"]
    mw, md = spec["min"]
    pairs = []
    scales = (1.0, .94, .88, .82, .76, .70, .64, .58, .52)

    for w, d in ((tw, td), (td, tw)):
        for scale in scales:
            cw = max(mw, w * scale)
            cd = max(md, d * scale)
            pair = (round(cw, 2), round(cd, 2))
            if pair not in pairs:
                pairs.append(pair)

    for pair in (
        (round(mw, 2), round(md, 2)),
        (round(md, 2), round(mw, 2)),
    ):
        if pair not in pairs:
            pairs.append(pair)

    return pairs


def _room_order(specs, strategy):
    """Place large/hard rooms first to reduce fragmentation."""
    priority = {
        "master_bedroom": 0,
        "bedroom": 1,
        "living": 2,
        "kitchen": 3,
        "dining": 4,
        "study": 5,
        "utility": 6,
        "bathroom": 7,
        "pooja": 8,
        "store": 9,
    }

    def key(s):
        area = s["min"][0] * s["min"][1]
        return (priority.get(s["kind"], 20), -area)

    ordered = sorted(specs, key=key)

    # Keep at least one public room early for normal residential zoning.
    if strategy == "ventilation":
        ordered.sort(key=lambda s: (
            0 if s["kind"] in ("living", "dining", "kitchen") else 1,
            priority.get(s["kind"], 20),
            -(s["min"][0] * s["min"][1]),
        ))
    elif strategy == "privacy":
        ordered.sort(key=lambda s: (
            0 if s["kind"] in ("master_bedroom", "bedroom") else 1,
            priority.get(s["kind"], 20),
            -(s["min"][0] * s["min"][1]),
        ))

    return ordered


def _zoning_penalty(r, kind, width, depth, strategy, road_side="north"):
    cx = r.x + r.width / 2
    cy = r.y + r.depth / 2
    px = cx / max(width, 1.0)
    py = cy / max(depth, 1.0)

    public = {"living", "dining", "kitchen", "pooja", "study"}
    private = {"master_bedroom", "bedroom"}
    service = {"bathroom", "utility", "store"}

    p = 0.0

    # Renderer uses y=0 as the front/bottom side. For the solver this is only
    # a soft zoning preference, never a feasibility rule.
    frontness = 1.0 - py if road_side == "north" else py

    if kind in public:
        p += frontness * 2.0
    if kind in private:
        p += (1.0 - frontness) * 1.8
    if kind in service:
        p += abs(px - .78) * .18

    if strategy == "privacy" and kind in private:
        p -= 1.0 * (1.0 - frontness)
    if strategy == "ventilation":
        edge = min(cx, width - cx, cy, depth - cy)
        p += edge * .20

    return p


def _split_free_rectangles(free_rects, used):
    """
    MaxRects-style split. Every free rectangle intersecting `used` is split
    into non-overlapping residual rectangles.
    """
    result = []

    for f in free_rects:
        if not _overlap(f, used, 0.0):
            result.append(f)
            continue

        # Left
        if used.x > f.x + 1e-6:
            result.append(Rect(
                "_free", f.x, f.y,
                used.x - f.x, f.depth, "_free"
            ))

        # Right
        if used.x2 < f.x2 - 1e-6:
            result.append(Rect(
                "_free", used.x2, f.y,
                f.x2 - used.x2, f.depth, "_free"
            ))

        # Bottom
        if used.y > f.y + 1e-6:
            result.append(Rect(
                "_free", f.x, f.y,
                f.width, used.y - f.y, "_free"
            ))

        # Top
        if used.y2 < f.y2 - 1e-6:
            result.append(Rect(
                "_free", f.x, used.y2,
                f.width, f.y2 - used.y2, "_free"
            ))

    # Remove zero/small rectangles and rectangles contained inside another.
    clean = []
    for r in result:
        if r.width <= .01 or r.depth <= .01:
            continue
        contained = False
        for q in result:
            if r is q:
                continue
            if (
                r.x >= q.x - .01 and r.y >= q.y - .01
                and r.x2 <= q.x2 + .01 and r.y2 <= q.y2 + .01
                and (r.width < q.width - .01 or r.depth < q.depth - .01)
            ):
                contained = True
                break
        if not contained:
            clean.append(r)

    # De-duplicate.
    seen = set()
    unique = []
    for r in clean:
        key = (round(r.x, 2), round(r.y, 2),
               round(r.width, 2), round(r.depth, 2))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def _initial_free_rects(width, depth, fixed):
    free = [Rect("_free", 0.0, 0.0, width, depth, "_free")]
    for r in fixed:
        free = _split_free_rectangles(free, r)
    return free


def _fixed_valid(fixed, width, depth):
    for i, a in enumerate(fixed):
        if not _fits(a, width, depth):
            return False
        for b in fixed[i + 1:]:
            if _overlap(a, b, 0.0):
                return False
    return True


def _place_room_in_free(spec, free_rects, width, depth, strategy, road_side):
    """
    Return many good placements for a room. A room may occupy any corner of a
    free rectangle, not merely global X/Y combinations.
    """
    candidates = []
    tw, td = spec["target"]

    for f in free_rects:
        for w, d in _candidate_sizes(spec):
            if w > f.width + .01 or d > f.depth + .01:
                continue

            # Four corners of the free rectangle. These are critical because
            # residual spaces after parking/stairs are often not origin-based.
            positions = [
                (f.x, f.y),
                (f.x2 - w, f.y),
                (f.x, f.y2 - d),
                (f.x2 - w, f.y2 - d),
            ]

            for x, y in positions:
                x, y = round(x, 2), round(y, 2)
                if x < -.01 or y < -.01:
                    continue
                if x + w > width + .01 or y + d > depth + .01:
                    continue

                r = Rect(spec["name"], x, y, w, d, spec["kind"])
                if r.width > f.width + .01 or r.depth > f.depth + .01:
                    continue

                size_penalty = abs(w - tw) + abs(d - td)
                zone = _zoning_penalty(
                    r, spec["kind"], width, depth, strategy, road_side
                )

                # Prefer edge/corner placements and larger dimensions.
                corner_bonus = 0
                if abs(x - f.x) < .01 or abs(x + w - f.x2) < .01:
                    corner_bonus -= .35
                if abs(y - f.y) < .01 or abs(y + d - f.y2) < .01:
                    corner_bonus -= .35

                candidates.append((
                    size_penalty + zone + corner_bonus,
                    r,
                ))

    # Deduplicate exact geometry.
    best = {}
    for cost, r in candidates:
        key = (r.x, r.y, r.width, r.depth)
        if key not in best or cost < best[key][0]:
            best[key] = (cost, r)

    result = sorted(best.values(), key=lambda z: z[0])
    return result[:40]


def _search_maxrects(specs, width, depth, fixed, strategy, road_side,
                     max_nodes=2000):
    """Fast deterministic MaxRects/Best-Fit search with bounded backtracking."""
    if not _fixed_valid(fixed, width, depth):
        return None

    # Most constrained rooms first. Large minimum areas first dramatically
    # reduces fragmentation.
    ordered = sorted(
        specs,
        key=lambda s: (
            -(s["min"][0] * s["min"][1]),
            -max(s["min"]),
        ),
    )
    free0 = _initial_free_rects(width, depth, fixed)
    nodes = 0

    def candidates(spec, free_rects):
        tw, td = spec["target"]
        mw, md = spec["min"]
        sizes = _candidate_sizes(spec)

        # Minimum sizes are tested first for feasibility; preferred sizes follow.
        min_pairs = [(mw, md), (md, mw)]
        ordered_sizes = []
        for q in min_pairs + sizes:
            q = (round(q[0], 2), round(q[1], 2))
            if q not in ordered_sizes:
                ordered_sizes.append(q)

        out = []
        for f in free_rects:
            for w, d in ordered_sizes:
                if w > f.width + .01 or d > f.depth + .01:
                    continue
                for x, y in (
                    (f.x, f.y),
                    (f.x2 - w, f.y),
                    (f.x, f.y2 - d),
                    (f.x2 - w, f.y2 - d),
                ):
                    if x < -.01 or y < -.01:
                        continue
                    r = Rect(spec["name"], round(x,2), round(y,2),
                             w, d, spec["kind"])
                    # Best-fit residual score: preserve large simple spaces.
                    rem_w = f.width - w
                    rem_d = f.depth - d
                    size_pen = abs(w-tw) + abs(d-td)
                    zone = _zoning_penalty(
                        r, spec["kind"], width, depth, strategy, road_side
                    )
                    short = min(abs(rem_w), abs(rem_d))
                    area_waste = max(0, rem_w * rem_d) * .002
                    score = size_pen + zone + short*.05 + area_waste
                    out.append((score, r, f))

        # Deduplicate geometry.
        seen=set(); unique=[]
        for item in sorted(out,key=lambda z:z[0]):
            r=item[1]; key=(r.x,r.y,r.width,r.depth)
            if key not in seen:
                seen.add(key); unique.append(item)
        return unique[:12]

    def recurse(index, free_rects, placed):
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            return None
        if index == len(ordered):
            return placed

        spec=ordered[index]
        cs=candidates(spec, free_rects)

        for _, room, _ in cs:
            nf=_split_free_rectangles(free_rects, room)

            # Exact minimum-area forward check.
            ok=True
            for s2 in ordered[index+1:]:
                mw,md=s2["min"]
                if not any(
                    (mw<=f.width+.01 and md<=f.depth+.01) or
                    (md<=f.width+.01 and mw<=f.depth+.01)
                    for f in nf
                ):
                    ok=False; break
            if not ok:
                continue

            ans=recurse(index+1,nf,placed+[room])
            if ans is not None:
                return ans
        return None

    return recurse(0,free0,list(fixed))

def _parking_configurations(data, width, depth):
    """
    Generate several actual parking rectangles without reserving a fake
    full-width parking strip. Cars and bikes may be arranged in rows/columns.
    """
    c = max(0, _int(data.get("circulation", {}).get("parking_cars")))
    b = max(0, _int(data.get("circulation", {}).get("parking_bikes")))

    if c == 0 and b == 0:
        return [([], "no parking")]

    items = []
    for i in range(c):
        items.append((f"Car Parking {i+1}", "parking", *ROOMS["car"][:2]))
    for i in range(b):
        items.append((f"Bike Parking {i+1}", "parking", *ROOMS["bike"][:2]))

    # Largest first makes the small bikes fit around cars more reliably.
    items.sort(key=lambda z: -(z[2] * z[3]))

    road = str(data.get("plot", {}).get("road_side", "north")).lower()
    corners = [
        ("front-left", 0.0, 0.0),
        ("front-right", width, 0.0),
        ("rear-left", 0.0, depth),
        ("rear-right", width, depth),
    ]
    if road in ("north", "south"):
        corners.sort(key=lambda z: 0 if z[0].startswith("front") else 1)

    configurations = []

    # Small bounded parking-only search. Candidate positions are derived from
    # plot edges and already placed parking rectangles.
    for label, cx, cy in corners:
        placed = []
        nodes = 0

        def rec(i):
            nonlocal nodes
            nodes += 1
            if nodes > 250:
                return None
            if i == len(items):
                return list(placed)

            name, kind, iw, idepth = items[i]
            xvals = {
                0.0, round(width - iw, 2),
                round(max(0.0, cx - iw), 2),
                round(min(max(0.0, cx), width - iw), 2),
            }
            yvals = {
                0.0, round(depth - idepth, 2),
                round(max(0.0, cy - idepth), 2),
                round(min(max(0.0, cy), depth - idepth), 2),
            }

            for q in placed:
                xvals.update((
                    round(q.x2 + .5, 2),
                    round(q.x - iw - .5, 2),
                    round(q.x2, 2),
                    round(q.x - iw, 2),
                ))
                yvals.update((
                    round(q.y2 + .5, 2),
                    round(q.y - idepth - .5, 2),
                    round(q.y2, 2),
                    round(q.y - idepth, 2),
                ))

            positions = []
            for x in xvals:
                for y in yvals:
                    if x < -.01 or y < -.01 or x + iw > width + .01 or y + idepth > depth + .01:
                        continue
                    r = Rect(name, round(max(0,x),2), round(max(0,y),2),
                             iw, idepth, kind)
                    if not any(_overlap(r, q, 0.05) for q in placed):
                        # Prefer positions close to the chosen corner and
                        # touching existing parking.
                        corner_dist = abs(r.x-cx) + abs(r.y-cy)
                        touch = sum(
                            1 for q in placed
                            if abs(r.x-q.x2)<.01 or abs(r.x2-q.x)<.01
                            or abs(r.y-q.y2)<.01 or abs(r.y2-q.y)<.01
                        )
                        positions.append((corner_dist - touch*10, r))

            positions.sort(key=lambda z:z[0])
            seen=set()
            for _, r in positions[:18]:
                key=(r.x,r.y,r.width,r.depth)
                if key in seen:
                    continue
                seen.add(key)
                placed.append(r)
                ans=rec(i+1)
                if ans is not None:
                    return ans
                placed.pop()
            return None

        answer = rec(0)
        if answer is not None:
            configurations.append((answer, label))

    # Deduplicate.
    unique=[]
    seen=set()
    for fixed,label in configurations:
        key=tuple((r.x,r.y,r.width,r.depth) for r in fixed)
        if key not in seen:
            seen.add(key)
            unique.append((fixed,label))

    return unique[:10] or [([], "parking could not be configured")]

def _stair_configurations(data, width, depth):
    """Try several staircase locations instead of hard-coding one corner."""
    typ = str(data.get("circulation", {}).get("staircase_type", "none")).lower()
    pref = str(data.get("circulation", {}).get("staircase_preference", "auto")).lower()

    if typ not in ("internal", "both"):
        return [([], "no internal staircase")]

    sw, sd = ROOMS["staircase"][:2]
    if sw > width or sd > depth:
        return [([], "staircase cannot fit")]

    positions = [
        ("northwest", 0, depth - sd),
        ("northeast", width - sw, depth - sd),
        ("southwest", 0, 0),
        ("southeast", width - sw, 0),
    ]

    if pref in ("north", "south", "east", "west", "corner"):
        def pref_score(p):
            label = p[0]
            if pref == "north":
                return 0 if "north" in label else 1
            if pref == "south":
                return 0 if "south" in label else 1
            if pref == "east":
                return 0 if "east" in label else 1
            if pref == "west":
                return 0 if "west" in label else 1
            return 0 if label in ("northwest", "northeast", "southwest", "southeast") else 1
        positions.sort(key=pref_score)

    result = []
    for label, x, y in positions:
        result.append((
            [Rect("Internal Staircase", round(x, 2), round(y, 2),
                  sw, sd, "staircase")],
            label
        ))

    if typ == "both":
        # The external stair is represented separately only if the same
        # footprint can fit. For now, internal layout remains the main plan.
        pass

    return result


def _lift_configurations(data, width, depth):
    if str(data.get("circulation", {}).get("lift", "no")).lower() != "yes":
        return [([], "no lift")]

    lw, ld = ROOMS["lift"][:2]
    if lw > width or ld > depth:
        return [([], "lift cannot fit")]

    positions = [
        ("northeast", width - lw, depth - ld),
        ("southeast", width - lw, 0),
        ("northwest", 0, depth - ld),
        ("southwest", 0, 0),
    ]
    return [
        ([Rect("Lift", round(x, 2), round(y, 2), lw, ld, "lift")], label)
        for label, x, y in positions
    ]


def _validate_layout(layout, width, depth):
    warnings = []

    for r in layout:
        if not _fits(r, width, depth):
            warnings.append(f"{r.name} extends outside the buildable envelope.")

    for i, a in enumerate(layout):
        for b in layout[i + 1:]:
            if _overlap(a, b, 0.0):
                warnings.append(f"{a.name} overlaps {b.name}.")

    return (len(warnings) == 0), list(dict.fromkeys(warnings))


def _score_layout(layout, specs, width, depth, strategy, road_side):
    target_map = {s["name"]: s for s in specs}
    penalty = 0.0

    for r in layout:
        if r.kind in ("parking", "staircase", "lift"):
            continue
        s = target_map.get(r.name)
        if not s:
            continue
        tw, td = s["target"]
        mw, md = s["min"]

        # Preferred dimensions are soft.
        penalty += abs(r.width - tw) * 1.0 + abs(r.depth - td) * 1.0

        # Minimum dimensions are hard, but a valid solver result should never
        # violate them.
        if r.width < mw - .01 or r.depth < md - .01:
            penalty += 100

        # Reward larger rooms close to target.
        if r.width >= mw and r.depth >= md:
            penalty -= .25

        penalty += _zoning_penalty(
            r, r.kind, width, depth, strategy, road_side
        )

    room_area = sum(
        r.area for r in layout
        if r.kind not in ("parking", "staircase", "lift", "buffer")
    )
    envelope = width * depth
    utilization = room_area / envelope if envelope else 0
    if utilization > .94:
        penalty += (utilization - .94) * 80

    # Strongly prefer plans with a little breathing room.
    if utilization < .40:
        penalty += (.40 - utilization) * 15

    return round(max(1.0, min(100.0, 100.0 - penalty)), 2)


def _candidate(data, strategy):
    env = data.get("buildable_area_preliminary", {})
    width = _num(env.get("width"))
    depth = _num(env.get("depth"))

    if width <= 0 or depth <= 0:
        return [], 0.0, ["Buildable envelope has zero area."], False

    specs = _room_specs(data)
    road_side = str(data.get("plot", {}).get("road_side", "north")).lower()

    parking_configs = _parking_configurations(data, width, depth)
    stair_configs = _stair_configurations(data, width, depth)
    lift_configs = _lift_configurations(data, width, depth)

    best = None
    diagnostics = []

    # Hard feasibility lower-bound check. Target area is NOT used here.
    fixed_room_min = sum(s["min"][0] * s["min"][1] for s in specs)

    for parking, parking_label in parking_configs:
        for stairs, stair_label in stair_configs:
            for lift, lift_label in lift_configs:
                fixed = parking + stairs + lift

                if not _fixed_valid(fixed, width, depth):
                    continue

                fixed_area = sum(r.area for r in fixed)
                if fixed_area + fixed_room_min > width * depth + .01:
                    continue

                layout = _search_maxrects(
                    specs, width, depth, fixed, strategy, road_side,
                    max_nodes=1500
                )
                if layout is None:
                    continue

                valid, hard_warnings = _validate_layout(layout, width, depth)
                if not valid:
                    diagnostics.extend(hard_warnings)
                    continue

                score = _score_layout(
                    layout, specs, width, depth, strategy, road_side
                )

                # Prefer layouts that keep fixed circulation/parking toward
                # corners and leave more coherent residual space.
                configuration_penalty = 0.0
                if parking_label.startswith("rear"):
                    configuration_penalty += .25
                if "southeast" in stair_label:
                    configuration_penalty += .10

                ranked_score = score - configuration_penalty

                if best is None or ranked_score > best[0]:
                    best = (ranked_score, layout, parking_label, stair_label, lift_label)

    if best is None:
        min_required = fixed_room_min
        fixed_parking = sum(
            r.area for configs in parking_configs for r in configs[0]
        ) / max(1, len(parking_configs))
        remaining_est = max(0.0, width * depth - fixed_parking)

        warnings = [
            "No complete non-overlapping layout could satisfy all requested rooms "
            f"and minimum dimensions inside the {width:.1f} × {depth:.1f} ft buildable envelope."
        ]

        if specs and min_required > width * depth:
            warnings.append(
                f"Requested rooms require at least {min_required:.0f} sq ft at "
                "their minimum planning dimensions, which exceeds the buildable envelope."
            )

        requested_area = sum(s["target"][0] * s["target"][1] for s in specs)
        if requested_area > remaining_est and min_required <= remaining_est:
            warnings.append(
                f"Preferred room target area ({requested_area:.0f} sq ft) is above "
                f"the estimated space remaining after parking ({remaining_est:.0f} sq ft); "
                "the engine will use compact dimensions when a valid arrangement exists."
            )

        return [], 0.0, list(dict.fromkeys(warnings + diagnostics)), False

    _, layout, parking_label, stair_label, lift_label = best

    # Ensure all requested rooms exist.
    expected = {s["name"] for s in specs}
    present = {r.name for r in layout}
    missing = expected - present
    if missing:
        return layout, 0.0, [
            "Missing requested spaces: " + ", ".join(sorted(missing))
        ], False

    return layout, best[0], [], True


def generate_layouts(data, max_plans=3):
    """Generate balanced, privacy and ventilation alternatives."""
    plans = []

    for strategy in ("balanced", "privacy", "ventilation"):
        rooms, score, warnings, valid = _candidate(data, strategy)

        plans.append({
            "strategy": strategy,
            "valid": bool(valid),
            "score": float(score),
            "buildable_area": data.get("buildable_area_preliminary", {}),
            "rooms": [r.to_dict() for r in rooms],
            "warnings": warnings,
            "engine_note": (
                "Preliminary architectural space-planning only. "
                "Verify setbacks, access, ventilation, fire safety, local rules, "
                "structural design and construction drawings with a qualified professional."
            ),
        })

    return plans[:max_plans]
