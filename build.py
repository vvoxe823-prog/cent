"""
PlanForge - Preliminary Architectural Plan Generator API

Run:
    pip install flask flask-cors
    python app.py

API:
    POST http://127.0.0.1:5000/generate-plan

The API currently accepts the complete architectural input form and returns
a deterministic JSON response containing the normalized project data and
a basic buildable-area calculation.

The actual layout-generation engine should be implemented next.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def number(form, key, default=0.0):
    """Safely read a numeric form field."""
    raw = form.get(key, "")
    if raw == "":
        return default

    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def integer(form, key, default=0):
    """Safely read an integer form field."""
    raw = form.get(key, "")
    if raw == "":
        return default

    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def calculate_buildable_area(data):
    """
    Preliminary rectangular buildable-area calculation.

    This is NOT a legal setback/code calculation.
    It simply applies the user-entered setback values to the plot dimensions.
    """

    width = data["plot"]["width"]
    depth = data["plot"]["depth"]

    front = data["setbacks"]["front"]
    rear = data["setbacks"]["rear"]
    left = data["setbacks"]["left"]
    right = data["setbacks"]["right"]

    buildable_width = max(width - left - right, 0)
    buildable_depth = max(depth - front - rear, 0)

    return {
        "width": round(buildable_width, 2),
        "depth": round(buildable_depth, 2),
        "area": round(buildable_width * buildable_depth, 2)
    }


@app.post("/generate-plan")
def generate_plan():
    form = request.form

    required_fields = [
        "project_type",
        "occupancy",
        "floors",
        "units_per_floor",
        "plot_width",
        "plot_depth",
        "unit",
        "facing",
        "road_side",
        "bedrooms",
        "bathrooms",
        "living_rooms",
        "kitchens",
        "dining_rooms",
        "pooja_rooms",
        "utility_rooms",
        "store_rooms",
        "study_rooms",
        "parking_cars",
        "parking_bikes",
        "staircase_type",
        "lift",
    ]

    missing = [field for field in required_fields if not form.get(field)]

    if missing:
        return jsonify({
            "success": False,
            "error": "Missing required fields.",
            "missing_fields": missing
        }), 400

    data = {
        "project": {
            "type": form.get("project_type"),
            "occupancy": form.get("occupancy"),
            "floors": form.get("floors"),
            "units_per_floor": integer(form, "units_per_floor", 1)
        },

        "plot": {
            "width": number(form, "plot_width"),
            "depth": number(form, "plot_depth"),
            "unit": form.get("unit"),
            "facing": form.get("facing"),
            "road_side": form.get("road_side")
        },

        "setbacks": {
            "front": number(form, "setback_front"),
            "rear": number(form, "setback_rear"),
            "left": number(form, "setback_left"),
            "right": number(form, "setback_right")
        },

        "rooms": {
            "bedrooms": integer(form, "bedrooms"),
            "bathrooms": integer(form, "bathrooms"),
            "living_rooms": integer(form, "living_rooms"),
            "kitchens": integer(form, "kitchens"),
            "dining_rooms": integer(form, "dining_rooms"),
            "pooja_rooms": integer(form, "pooja_rooms"),
            "utility_rooms": integer(form, "utility_rooms"),
            "store_rooms": integer(form, "store_rooms"),
            "study_rooms": integer(form, "study_rooms")
        },

        "preferences": {
            "master_bedroom_size": form.get("master_bedroom_size", ""),
            "bedroom_size": form.get("bedroom_size", ""),
            "kitchen_size": form.get("kitchen_size", ""),
            "living_size": form.get("living_size", "")
        },

        "circulation": {
            "parking_cars": integer(form, "parking_cars"),
            "parking_bikes": integer(form, "parking_bikes"),
            "staircase_type": form.get("staircase_type"),
            "staircase_preference": form.get("staircase_preference", "auto"),
            "lift": form.get("lift")
        },

        "features": form.getlist("features[]"),

        "notes": form.get("notes", "").strip()
    }

    # Basic sanity checks for the planning engine.
    if data["plot"]["width"] <= 0 or data["plot"]["depth"] <= 0:
        return jsonify({
            "success": False,
            "error": "Plot width and depth must be greater than zero."
        }), 400

    data["buildable_area_preliminary"] = calculate_buildable_area(data)

    # This is the hand-off point for the real layout algorithm.
    # Future implementation:
    #
    # layout = generate_layout(data)
    # drawing = render_dxf_or_svg(layout)
    #
    # For this first version, return the normalized planning input.

    return jsonify({
        "success": True,
        "message": "Architectural planning input received successfully.",
        "engine_status": "INPUT_RECEIVED_LAYOUT_ENGINE_NEXT",
        "data": data
    })


@app.get("/health")
def health():
    return jsonify({
        "success": True,
        "service": "PlanForge Architectural Generator API",
        "status": "running"
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
