<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PlanForge — Architectural Plan Generator</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">

    <style>
        :root {
            --c1: #eef7ff;
            --c2: #f8f1ff;
            --primary: #667eea;
            --secondary: #764ba2;
            --ink: #26324a;
            --muted: #71809a;
            --border: rgba(112, 126, 160, .18);
            --glass: rgba(255,255,255,.78);
            --shadow: 0 24px 70px rgba(70, 82, 120, .13);
        }

        * { box-sizing: border-box; }

        body {
            min-height: 100vh;
            margin: 0;
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at 10% 10%, rgba(173,216,255,.35), transparent 30%),
                radial-gradient(circle at 90% 15%, rgba(224,190,255,.34), transparent 30%),
                linear-gradient(135deg, var(--c1), var(--c2));
            overflow-x: hidden;
        }

        .topbar {
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(18px);
            background: rgba(255,255,255,.68);
            border-bottom: 1px solid rgba(255,255,255,.7);
        }

        .brand {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            letter-spacing: -.4px;
            color: var(--ink);
            text-decoration: none;
        }

        .brand-mark {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 14px;
            color: #fff;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 10px 25px rgba(102,126,234,.28);
        }

        .hero {
            padding: 58px 0 34px;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 13px;
            border-radius: 999px;
            background: rgba(255,255,255,.72);
            border: 1px solid rgba(255,255,255,.9);
            color: #5d6b87;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .7px;
            text-transform: uppercase;
            box-shadow: 0 10px 30px rgba(70,82,120,.08);
        }

        .hero h1 {
            font-size: clamp(2rem, 5vw, 4.1rem);
            line-height: 1.02;
            font-weight: 850;
            letter-spacing: -2.5px;
            margin: 18px 0 14px;
        }

        .hero h1 span {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .hero p {
            max-width: 760px;
            color: var(--muted);
            font-size: 1.04rem;
        }

        .glass-card {
            background: var(--glass);
            border: 1px solid rgba(255,255,255,.9);
            border-radius: 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(22px);
        }

        .section-card {
            padding: 28px;
            margin-bottom: 22px;
        }

        .section-title {
            display: flex;
            align-items: center;
            gap: 13px;
            margin-bottom: 22px;
        }

        .section-icon {
            width: 43px;
            height: 43px;
            flex: 0 0 43px;
            display: grid;
            place-items: center;
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(102,126,234,.13), rgba(118,75,162,.12));
            color: var(--primary);
            font-size: 1.15rem;
        }

        .section-title h2 {
            font-size: 1.05rem;
            font-weight: 800;
            margin: 0;
        }

        .section-title small {
            display: block;
            margin-top: 3px;
            color: var(--muted);
            font-size: .78rem;
        }

        .field-label {
            display: block;
            font-size: .78rem;
            font-weight: 800;
            color: #4f5e78;
            margin: 0 0 8px 3px;
        }

        .form-control,
        .form-select {
            min-height: 52px;
            border: 1px solid var(--border);
            border-radius: 15px;
            background: rgba(255,255,255,.82);
            color: var(--ink);
            box-shadow: 0 8px 25px rgba(70,82,120,.045);
            transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease, background .25s ease;
        }

        textarea.form-control {
            min-height: 112px;
            resize: vertical;
        }

        .form-control:focus,
        .form-select:focus {
            border-color: rgba(102,126,234,.55);
            background: #fff;
            box-shadow: 0 0 0 .25rem rgba(102,126,234,.11), 0 15px 35px rgba(70,82,120,.08);
            outline: none;
        }

        .input-group-text {
            border: 1px solid var(--border);
            border-radius: 15px 0 0 15px;
            background: rgba(245,247,255,.9);
            color: #71809a;
            font-weight: 700;
        }

        .input-group .form-control {
            border-radius: 0 15px 15px 0;
        }

        .choice-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0,1fr));
            gap: 10px;
        }

        .choice {
            position: relative;
        }

        .choice input {
            position: absolute;
            opacity: 0;
            pointer-events: none;
        }

        .choice label {
            min-height: 55px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 15px;
            background: rgba(255,255,255,.76);
            color: #596780;
            font-size: .83rem;
            font-weight: 800;
            cursor: pointer;
            transition: all .25s ease;
        }

        .choice input:checked + label {
            color: #fff;
            border-color: transparent;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 12px 25px rgba(102,126,234,.23);
            transform: translateY(-2px);
        }

        .feature-list {
            display: grid;
            grid-template-columns: repeat(2, minmax(0,1fr));
            gap: 10px;
        }

        .check-card {
            position: relative;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 13px 14px;
            border: 1px solid var(--border);
            border-radius: 15px;
            background: rgba(255,255,255,.74);
            transition: all .25s ease;
        }

        .check-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 25px rgba(70,82,120,.08);
        }

        .check-card input {
            width: 18px;
            height: 18px;
            accent-color: var(--primary);
        }

        .check-card label {
            font-size: .82rem;
            font-weight: 700;
            color: #596780;
            cursor: pointer;
            margin: 0;
        }

        .sticky-panel {
            position: sticky;
            top: 92px;
        }

        .summary {
            padding: 25px;
        }

        .summary-title {
            font-weight: 850;
            margin-bottom: 5px;
        }

        .summary-text {
            color: var(--muted);
            font-size: .84rem;
            line-height: 1.6;
        }

        .summary-chip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 12px 13px;
            border-radius: 14px;
            background: rgba(247,249,255,.82);
            margin-bottom: 9px;
        }

        .summary-chip span:first-child {
            color: #78859b;
            font-size: .78rem;
            font-weight: 700;
        }

        .summary-chip span:last-child {
            color: #36445e;
            font-size: .8rem;
            font-weight: 850;
        }

        .generate-btn {
            width: 100%;
            min-height: 58px;
            border: 0;
            border-radius: 17px;
            color: #fff;
            font-weight: 850;
            letter-spacing: .15px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 17px 34px rgba(102,126,234,.28);
            transition: transform .25s ease, box-shadow .25s ease;
        }

        .generate-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 22px 42px rgba(102,126,234,.34);
            color: #fff;
        }

        .generate-btn:active { transform: translateY(-1px) scale(.99); }

        .note {
            margin-top: 13px;
            padding: 12px 13px;
            border-radius: 14px;
            background: rgba(237,244,255,.72);
            color: #6d7b94;
            font-size: .72rem;
            line-height: 1.55;
        }

        .footer {
            padding: 18px 0 40px;
            text-align: center;
            color: #8994a8;
            font-size: .75rem;
        }

        .reveal {
            opacity: 0;
            transform: translateY(18px);
        }

        .pulse-focus {
            animation: pulseFocus .55s ease;
        }

        @keyframes pulseFocus {
            0% { transform: scale(1); }
            45% { transform: scale(1.015); }
            100% { transform: scale(1); }
        }

        @media (max-width: 991.98px) {
            .sticky-panel { position: static; }
            .choice-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
        }

        @media (max-width: 575.98px) {
            .hero { padding-top: 38px; }
            .hero h1 { letter-spacing: -1.5px; }
            .section-card { padding: 20px; border-radius: 22px; }
            .choice-grid,
            .feature-list { grid-template-columns: 1fr; }
            .brand-mark { width: 38px; height: 38px; }
        }
    </style>
</head>

<body>

<header class="topbar">
    <div class="container py-2">
        <a href="#" class="brand">
            <span class="brand-mark"><i class="bi bi-grid-1x2-fill"></i></span>
            <span>PlanForge</span>
        </a>
    </div>
</header>

<main>
    <section class="hero">
        <div class="container">
            <div class="eyebrow">
                <i class="bi bi-stars"></i>
                Architectural Plan Generator
            </div>
            <h1>Describe the building.<br><span>Generate the layout.</span></h1>
            <p>
                Provide the plot, orientation, rooms, circulation, parking and planning preferences.
                The Python planning engine will use these inputs to generate preliminary architectural layouts.
            </p>
        </div>
    </section>

    <form action="https://cent-ciaf.onrender.com/generate-plan-drawing" method="post" target="_blank" id="planForm">
        <div class="container pb-4">
            <div class="row g-4">

                <div class="col-lg-8">

                    <!-- PROJECT -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-buildings"></i></div>
                            <div>
                                <h2>Project type</h2>
                                <small>Tell the generator what you are planning.</small>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="field-label" for="project_type">Building type</label>
                                <select class="form-select animated-input" id="project_type" name="project_type" required>
                                    <option value="">Select building type</option>
                                    <option value="independent_house">Independent House</option>
                                    <option value="villa">Villa</option>
                                    <option value="row_house">Row House</option>
                                    <option value="apartment">Apartment Building</option>
                                    <option value="commercial_residential">Mixed Use</option>
                                </select>
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="occupancy">Usage</label>
                                <select class="form-select animated-input" id="occupancy" name="occupancy" required>
                                    <option value="">Select usage</option>
                                    <option value="residential">Residential</option>
                                    <option value="rental">Rental</option>
                                    <option value="investment">Investment</option>
                                    <option value="mixed">Mixed Residential</option>
                                </select>
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="floors">Number of floors</label>
                                <select class="form-select animated-input" id="floors" name="floors" required>
                                    <option value="">Select floors</option>
                                    <option value="1">Ground only</option>
                                    <option value="2">G+1</option>
                                    <option value="3">G+2</option>
                                    <option value="4">G+3</option>
                                    <option value="5">G+4</option>
                                    <option value="6">G+5</option>
                                    <option value="10">G+9</option>
                                    <option value="custom">Custom / Large project</option>
                                </select>
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="units_per_floor">Units per floor</label>
                                <input class="form-control animated-input" id="units_per_floor" name="units_per_floor"
                                       type="number" min="1" max="100" value="1" required>
                            </div>
                        </div>
                    </div>

                    <!-- PLOT -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-bounding-box-circles"></i></div>
                            <div>
                                <h2>Plot & orientation</h2>
                                <small>Define the land on which the layout must fit.</small>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="field-label" for="plot_width">Plot width</label>
                                <div class="input-group">
                                    <span class="input-group-text">W</span>
                                    <input class="form-control animated-input" id="plot_width" name="plot_width"
                                           type="number" min="1" step="0.01" placeholder="30" required>
                                </div>
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="plot_depth">Plot depth</label>
                                <div class="input-group">
                                    <span class="input-group-text">D</span>
                                    <input class="form-control animated-input" id="plot_depth" name="plot_depth"
                                           type="number" min="1" step="0.01" placeholder="40" required>
                                </div>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="unit">Measurement unit</label>
                                <select class="form-select animated-input" id="unit" name="unit" required>
                                    <option value="feet">Feet</option>
                                    <option value="meters">Meters</option>
                                </select>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="facing">Plot facing</label>
                                <select class="form-select animated-input" id="facing" name="facing" required>
                                    <option value="">Select facing</option>
                                    <option value="north">North</option>
                                    <option value="south">South</option>
                                    <option value="east">East</option>
                                    <option value="west">West</option>
                                    <option value="northeast">North-East</option>
                                    <option value="northwest">North-West</option>
                                    <option value="southeast">South-East</option>
                                    <option value="southwest">South-West</option>
                                </select>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="road_side">Road access</label>
                                <select class="form-select animated-input" id="road_side" name="road_side" required>
                                    <option value="">Select road side</option>
                                    <option value="north">North</option>
                                    <option value="south">South</option>
                                    <option value="east">East</option>
                                    <option value="west">West</option>
                                    <option value="two_side">Two-side road</option>
                                    <option value="corner">Corner plot</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- SETBACKS -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-arrows-expand"></i></div>
                            <div>
                                <h2>Setbacks & planning envelope</h2>
                                <small>Provide the limits within which the building must remain.</small>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-sm-6 col-lg-3">
                                <label class="field-label" for="setback_front">Front</label>
                                <input class="form-control animated-input" id="setback_front" name="setback_front"
                                       type="number" min="0" step="0.01" value="0">
                            </div>
                            <div class="col-sm-6 col-lg-3">
                                <label class="field-label" for="setback_rear">Rear</label>
                                <input class="form-control animated-input" id="setback_rear" name="setback_rear"
                                       type="number" min="0" step="0.01" value="0">
                            </div>
                            <div class="col-sm-6 col-lg-3">
                                <label class="field-label" for="setback_left">Left</label>
                                <input class="form-control animated-input" id="setback_left" name="setback_left"
                                       type="number" min="0" step="0.01" value="0">
                            </div>
                            <div class="col-sm-6 col-lg-3">
                                <label class="field-label" for="setback_right">Right</label>
                                <input class="form-control animated-input" id="setback_right" name="setback_right"
                                       type="number" min="0" step="0.01" value="0">
                            </div>
                        </div>
                    </div>

                    <!-- ROOMS -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-door-open"></i></div>
                            <div>
                                <h2>Rooms & spaces</h2>
                                <small>Select the spaces the generator should try to include.</small>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-md-4">
                                <label class="field-label" for="bedrooms">Bedrooms</label>
                                <input class="form-control animated-input" id="bedrooms" name="bedrooms"
                                       type="number" min="0" max="30" value="2" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="bathrooms">Bathrooms</label>
                                <input class="form-control animated-input" id="bathrooms" name="bathrooms"
                                       type="number" min="0" max="30" value="2" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="living_rooms">Living rooms</label>
                                <input class="form-control animated-input" id="living_rooms" name="living_rooms"
                                       type="number" min="0" max="10" value="1" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="kitchens">Kitchens</label>
                                <input class="form-control animated-input" id="kitchens" name="kitchens"
                                       type="number" min="0" max="10" value="1" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="dining_rooms">Dining rooms</label>
                                <input class="form-control animated-input" id="dining_rooms" name="dining_rooms"
                                       type="number" min="0" max="10" value="1" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="pooja_rooms">Pooja rooms</label>
                                <input class="form-control animated-input" id="pooja_rooms" name="pooja_rooms"
                                       type="number" min="0" max="10" value="0" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="utility_rooms">Utility rooms</label>
                                <input class="form-control animated-input" id="utility_rooms" name="utility_rooms"
                                       type="number" min="0" max="10" value="0" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="store_rooms">Store rooms</label>
                                <input class="form-control animated-input" id="store_rooms" name="store_rooms"
                                       type="number" min="0" max="10" value="0" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="study_rooms">Study / office</label>
                                <input class="form-control animated-input" id="study_rooms" name="study_rooms"
                                       type="number" min="0" max="10" value="0" required>
                            </div>
                        </div>
                    </div>

                    <!-- ROOM PREFERENCES -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-sliders2"></i></div>
                            <div>
                                <h2>Room preferences</h2>
                                <small>Guide the layout algorithm without manually drawing anything.</small>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="field-label" for="master_bedroom_size">Preferred master bedroom</label>
                                <input class="form-control animated-input" id="master_bedroom_size" name="master_bedroom_size"
                                       type="text" pattern="[0-9]{1,3}([.][0-9]{1,2})?[ ]?[xX][ ]?[0-9]{1,3}([.][0-9]{1,2})?"
                                       placeholder="12 x 14">
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="bedroom_size">Preferred other bedroom</label>
                                <input class="form-control animated-input" id="bedroom_size" name="bedroom_size"
                                       type="text" pattern="[0-9]{1,3}([.][0-9]{1,2})?[ ]?[xX][ ]?[0-9]{1,3}([.][0-9]{1,2})?"
                                       placeholder="10 x 12">
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="kitchen_size">Preferred kitchen</label>
                                <input class="form-control animated-input" id="kitchen_size" name="kitchen_size"
                                       type="text" pattern="[0-9]{1,3}([.][0-9]{1,2})?[ ]?[xX][ ]?[0-9]{1,3}([.][0-9]{1,2})?"
                                       placeholder="10 x 10">
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="living_size">Preferred living room</label>
                                <input class="form-control animated-input" id="living_size" name="living_size"
                                       type="text" pattern="[0-9]{1,3}([.][0-9]{1,2})?[ ]?[xX][ ]?[0-9]{1,3}([.][0-9]{1,2})?"
                                       placeholder="12 x 16">
                            </div>
                        </div>
                    </div>

                    <!-- CIRCULATION / PARKING -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-car-front"></i></div>
                            <div>
                                <h2>Parking, staircase & circulation</h2>
                                <small>Define movement and access requirements.</small>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-md-4">
                                <label class="field-label" for="parking_cars">Cars</label>
                                <input class="form-control animated-input" id="parking_cars" name="parking_cars"
                                       type="number" min="0" max="50" value="1" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="parking_bikes">Two-wheelers</label>
                                <input class="form-control animated-input" id="parking_bikes" name="parking_bikes"
                                       type="number" min="0" max="100" value="2" required>
                            </div>

                            <div class="col-md-4">
                                <label class="field-label" for="staircase_type">Staircase</label>
                                <select class="form-select animated-input" id="staircase_type" name="staircase_type" required>
                                    <option value="internal">Internal</option>
                                    <option value="external">External</option>
                                    <option value="both">Internal + External</option>
                                    <option value="none">None</option>
                                </select>
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="staircase_preference">Staircase preference</label>
                                <select class="form-select animated-input" id="staircase_preference" name="staircase_preference">
                                    <option value="auto">Auto</option>
                                    <option value="north">North</option>
                                    <option value="south">South</option>
                                    <option value="east">East</option>
                                    <option value="west">West</option>
                                    <option value="corner">Corner</option>
                                </select>
                            </div>

                            <div class="col-md-6">
                                <label class="field-label" for="lift">Lift requirement</label>
                                <select class="form-select animated-input" id="lift" name="lift" required>
                                    <option value="no">No lift</option>
                                    <option value="yes">Lift required</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- FEATURES -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-check2-square"></i></div>
                            <div>
                                <h2>Additional requirements</h2>
                                <small>Optional planning features.</small>
                            </div>
                        </div>

                        <div class="feature-list">
                            <div class="check-card">
                                <input type="checkbox" id="balcony" name="features[]" value="balcony">
                                <label for="balcony">Balcony</label>
                            </div>
                            <div class="check-card">
                                <input type="checkbox" id="terrace" name="features[]" value="terrace">
                                <label for="terrace">Open terrace</label>
                            </div>
                            <div class="check-card">
                                <input type="checkbox" id="garden" name="features[]" value="garden">
                                <label for="garden">Garden / green space</label>
                            </div>
                            <div class="check-card">
                                <input type="checkbox" id="wash_area" name="features[]" value="wash_area">
                                <label for="wash_area">Dedicated wash area</label>
                            </div>
                            <div class="check-card">
                                <input type="checkbox" id="servant" name="features[]" value="servant_room">
                                <label for="servant">Servant room</label>
                            </div>
                            <div class="check-card">
                                <input type="checkbox" id="elderly" name="features[]" value="elderly_friendly">
                                <label for="elderly">Elderly-friendly circulation</label>
                            </div>
                            <div class="check-card">
                                <input type="checkbox" id="ventilation" name="features[]" value="cross_ventilation">
                                <label for="ventilation">Prioritize cross ventilation</label>
                            </div>
                            <div class="check-card">
                                <input type="checkbox" id="privacy" name="features[]" value="privacy">
                                <label for="privacy">Prioritize privacy</label>
                            </div>
                        </div>
                    </div>

                    <!-- NOTES -->
                    <div class="glass-card section-card reveal">
                        <div class="section-title">
                            <div class="section-icon"><i class="bi bi-chat-square-text"></i></div>
                            <div>
                                <h2>Special instructions</h2>
                                <small>Additional constraints for the planning engine.</small>
                            </div>
                        </div>

                        <label class="field-label" for="notes">Instructions</label>
                        <textarea class="form-control animated-input" id="notes" name="notes"
                                  maxlength="2000"
                                  placeholder="Example: Keep the living room toward the road side, provide privacy between bedrooms and living room, keep parking near the entrance..."></textarea>
                    </div>

                </div>

                <!-- SUMMARY -->
                <div class="col-lg-4">
                    <aside class="sticky-panel">
                        <div class="glass-card summary reveal">
                            <div class="section-icon mb-3"><i class="bi bi-magic"></i></div>
                            <div class="summary-title">Ready to generate?</div>
                            <div class="summary-text mb-4">
                                Your inputs will be submitted directly to the Python API using a normal HTML form.
                                No AJAX is used for submission or validation.
                            </div>

                            <div class="summary-chip">
                                <span>Plot</span>
                                <span id="summaryPlot">—</span>
                            </div>

                            <div class="summary-chip">
                                <span>Facing</span>
                                <span id="summaryFacing">—</span>
                            </div>

                            <div class="summary-chip">
                                <span>Bedrooms</span>
                                <span id="summaryBedrooms">—</span>
                            </div>

                            <div class="summary-chip">
                                <span>Bathrooms</span>
                                <span id="summaryBathrooms">—</span>
                            </div>

                            <div class="summary-chip">
                                <span>Floors</span>
                                <span id="summaryFloors">—</span>
                            </div>

                            <button type="submit" class="generate-btn mt-3">
                                <i class="bi bi-stars me-2"></i>Generate Preliminary Plan
                            </button>

                            <div class="note">
                                <i class="bi bi-info-circle me-1"></i>
                                This generator is intended for preliminary architectural layouts.
                                Final construction drawings, code compliance and professional approval must be handled by the appropriate qualified professionals.
                            </div>
                        </div>
                    </aside>
                </div>

            </div>
        </div>
    </form>
</main>

<footer class="footer">
    PlanForge • Architectural layout automation interface
</footer>

<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>

<script>
    /*
     * IMPORTANT:
     * JavaScript/jQuery is used ONLY for visual animations and live UI display.
     * It does NOT submit the form.
     * It does NOT perform validation.
     * HTML5 controls perform browser-side validation.
     */

    $(function () {

        // High-end entrance animations.
        $('.reveal').each(function(index) {
            $(this)
                .delay(index * 70)
                .animate({
                    opacity: 1,
                    top: 0
                }, {
                    duration: 650,
                    easing: 'swing'
                });
        });

        // Focus animation only.
        $('.animated-input')
            .on('focus', function() {
                $(this).addClass('pulse-focus');
            })
            .on('animationend', function() {
                $(this).removeClass('pulse-focus');
            });

        // Visual live summary only — no submission and no validation.
        $('#plot_width, #plot_depth, #unit').on('input change', function() {
            var width = $('#plot_width').val();
            var depth = $('#plot_depth').val();
            var unit = $('#unit').val() || 'feet';

            $('#summaryPlot').text(
                width && depth ? width + ' × ' + depth + ' ' + unit : '—'
            );
        });

        $('#facing').on('change', function() {
            var value = $(this).find(':selected').text();
            $('#summaryFacing').text(value || '—');
        });

        $('#bedrooms').on('input change', function() {
            $('#summaryBedrooms').text($(this).val() || '—');
        });

        $('#bathrooms').on('input change', function() {
            $('#summaryBathrooms').text($(this).val() || '—');
        });

        $('#floors').on('change', function() {
            $('#summaryFloors').text($(this).find(':selected').text() || '—');
        });

        // Button press animation only.
        $('.generate-btn').on('mousedown', function() {
            $(this).css('transform', 'scale(.985)');
        }).on('mouseup mouseleave', function() {
            $(this).css('transform', '');
        });
    });
</script>

</body>
</html>
