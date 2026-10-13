
import random
import html
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="F1: The Pit Wall",
    page_icon="🏎️",
    layout="wide",
)

# Circuit outlines are simplified approximations.
# Race performance and lap times are simulated.

TRACKS = {
    "Monza, Italy": {
        "base": 83.0,
        "pit": 21.0,
        "wear": 1.0,
        "rain": .07,
        "path": "M 75 45 L 105 35 L 137 83 L 175 123 L 216 133 L 295 134 L 328 142 L 328 157 L 277 159 L 209 157 L 135 157 Q 109 155 100 139 L 89 104 L 68 69 Z",
    },
    "Silverstone, United Kingdom": {
        "base": 91.5,
        "pit": 23.0,
        "wear": 1.2,
        "rain": .18,
        "path": "M 55 82 L 116 37 Q 126 31 138 44 L 200 90 L 200 136 L 236 151 L 260 126 L 265 76 Q 279 59 295 77 L 310 108 L 313 156 L 266 171 L 240 156 L 210 179 L 177 168 L 126 144 L 73 113 Z",
    },
    "Spa-Francorchamps, Belgium": {
        "base": 105.0,
        "pit": 24.0,
        "wear": 1.12,
        "rain": .25,
        "path": "M 56 173 L 88 133 L 127 94 L 170 69 L 213 44 L 240 53 L 268 37 L 301 65 L 313 92 L 286 78 L 257 65 L 233 76 L 202 93 L 194 118 L 227 135 L 253 158 L 246 184 L 209 167 L 172 138 L 131 146 L 95 164 Z",
    },
    "Singapore": {
        "base": 102.0,
        "pit": 27.0,
        "wear": 1.4,
        "rain": .18,
        "path": "M 59 106 L 96 50 L 125 75 L 141 61 L 190 95 L 250 100 L 255 39 L 273 47 L 281 91 L 289 130 L 270 163 L 225 165 L 197 151 L 145 150 L 100 143 L 83 167 L 62 145 Z",
    },
    "Bahrain": {
        "base": 94.0,
        "pit": 23.0,
        "wear": 1.1,
        "rain": .02,
        "path": "M 65 149 L 87 36 L 118 71 L 155 84 L 126 114 L 207 114 L 240 47 L 264 69 L 300 151 Z",
    },
    "Suzuka, Japan": {
        "base": 92.0,
        "pit": 23.0,
        "wear": 1.15,
        "rain": .22,
        "path": "M 46 63 Q 78 110 118 108 L 142 70 L 156 121 L 181 115 Q 201 74 224 96 L 278 155 Q 294 187 311 175 Q 321 165 288 138 L 245 89 Q 209 50 184 87 L 157 101 Q 135 105 112 85 Q 85 66 81 38 Q 52 31 46 63 Z",
    },
    "Monaco": {
        "base": 77.0,
        "pit": 26.0,
        "wear": 1.08,
        "rain": .14,
        "path": "M 50 160 Q 50 108 83 79 L 137 35 L 193 70 L 218 91 L 256 93 Q 280 92 287 67 L 318 57 L 325 81 L 294 100 Q 263 139 232 124 L 172 94 L 132 62 Q 102 49 78 99 L 63 168 Z",
    },
    "Interlagos, Brazil": {
        "base": 72.0,
        "pit": 22.0,
        "wear": 1.12,
        "rain": .25,
        "path": "M 74 78 Q 106 49 147 48 Q 181 41 188 67 L 182 95 Q 221 46 244 55 Q 266 68 245 100 L 285 129 L 271 158 Q 223 150 199 122 L 164 103 L 131 151 Q 98 173 73 148 Q 48 117 74 78 Z",
    },
    "Las Vegas, USA": {
        "base": 94.0,
        "pit": 22.0,
        "wear": .9,
        "rain": .04,
        "path": "M 65 151 L 95 98 L 113 102 L 113 43 L 133 37 L 151 67 L 278 67 L 268 35 L 284 36 L 309 73 L 310 156 L 153 156 L 105 136 Z",
    },
    "Montreal, Canada": {
        "base": 76.0,
        "pit": 22.0,
        "wear": 1.05,
        "rain": .20,
        "path": "M 57 72 L 135 79 L 180 102 L 215 124 L 248 137 L 273 117 L 304 125 L 286 150 L 241 158 L 208 146 L 176 131 L 133 93 Z",
    },
    "Miami, USA": {
        "base": 90.0,
        "pit": 22.0,
        "wear": 1.0,
        "rain": .15,
        "path": "M 56 62 L 299 62 L 293 89 L 309 98 L 293 112 L 249 109 Q 208 158 162 157 L 117 142 Q 90 115 60 136 L 51 117 Q 71 88 113 108 L 164 131 L 194 115 L 114 74 Z",
    },
}

# Real 2026 driver and team names.
# Driver performance ratings are fictional.

GRID = [
    ("George Russell", "Mercedes", "#27F4D2"),
    ("Kimi Antonelli", "Mercedes", "#27F4D2"),
    ("Charles Leclerc", "Ferrari", "#E80020"),
    ("Lewis Hamilton", "Ferrari", "#E80020"),
    ("Lando Norris", "McLaren", "#FF8000"),
    ("Oscar Piastri", "McLaren", "#FF8000"),
    ("Max Verstappen", "Red Bull", "#3671C6"),
    ("Isack Hadjar", "Red Bull", "#3671C6"),
    ("Liam Lawson", "Racing Bulls", "#6692FF"),
    ("Arvid Lindblad", "Racing Bulls", "#6692FF"),
    ("Pierre Gasly", "Alpine", "#FF87BC"),
    ("Franco Colapinto", "Alpine", "#FF87BC"),
    ("Esteban Ocon", "Haas", "#B6BABD"),
    ("Oliver Bearman", "Haas", "#B6BABD"),
    ("Nico Hulkenberg", "Audi", "#C4E300"),
    ("Gabriel Bortoleto", "Audi", "#C4E300"),
    ("Carlos Sainz", "Williams", "#64C4FF"),
    ("Alex Albon", "Williams", "#64C4FF"),
    ("Fernando Alonso", "Aston Martin", "#229971"),
    ("Lance Stroll", "Aston Martin", "#229971"),
    ("Sergio Perez", "Cadillac", "#969BA2"),
    ("Valtteri Bottas", "Cadillac", "#969BA2"),
]

TEAMS = {n: t for n, t, c in GRID}
COLORS = {n: c for n, t, c in GRID}

DRY = {"Soft", "Medium", "Hard"}

BASE_TIRE = {
    "Soft": -1.1,
    "Medium": 0.0,
    "Hard": 0.65,
    "Intermediate": 2.6,
    "Wet": 4.5,
}

WEAR_RATE = {
    "Soft": .28,
    "Medium": .14,
    "Hard": .075,
    "Intermediate": .17,
    "Wet": .13,
}

TIRE_ICON = {
    "Soft": "🔴",
    "Medium": "🟡",
    "Hard": "⚪",
    "Intermediate": "🟢",
    "Wet": "🔵",
}

st.markdown("""
<style>
.stApp {
    background: #0c1422;
    color: #e8edf5;
}
.block-container {
    padding-top: 1rem;
    max-width: 1500px;
}
[data-testid="stMetric"] {
    background: #19253a;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #36445a;
}
div.stButton > button[kind="primary"] {
    background: #ff782e;
    color: #101820;
    font-weight: 900;
}
</style>
""", unsafe_allow_html=True)


def create_game(track, laps, name, tire):
    seed = random.SystemRandom().randrange(10**9)
    rng = random.Random(seed)

    ordered = sorted(GRID, key=lambda x: rng.random())
    drivers = []

    for index, (driver, team, color) in enumerate(ordered):
        current_tire = (
            tire if driver == name
            else rng.choice(["Medium", "Hard", "Soft"])
        )

        drivers.append(dict(
            name=driver,
            team=team,
            color=color,
            elapsed=index * 1.25,
            tire=current_tire,
            age=0.,
            used=[current_tire],
            stops=0,
            skill=rng.uniform(-.7, .7),
            history=[],
        ))

    return dict(
        seed=seed,
        track=track,
        total=laps,
        lap=0,
        player=name,
        weather="Dry",
        was_wet=False,
        safety=False,
        drivers=drivers,
        snapshots=[],
        entries=[],
        events=[],
        finished=False,
    )


def order(game):
    return sorted(
        game["drivers"],
        key=lambda d: d["elapsed"]
    )


def run_lap(game, choice, mode):
    if game["finished"]:
        return

    lap = game["lap"] + 1
    rng = random.Random(f"{game['seed']}-{lap}")
    settings = TRACKS[game["track"]]
    events = []

    prev = game["weather"]
    r = rng.random()

    if prev == "Dry" and r < settings["rain"] * .55:
        game["weather"] = "Damp"
    elif prev == "Damp" and r < .30:
        game["weather"] = "Wet"
    elif prev == "Damp" and r > .71:
        game["weather"] = "Dry"
    elif prev == "Wet" and r > .72:
        game["weather"] = "Damp"

    if game["weather"] != prev:
        events.append(
            f"🌦️ Weather: {prev} → {game['weather']}"
        )

    if game["weather"] != "Dry":
        game["was_wet"] = True

    safety = rng.random() < .09
    game["safety"] = safety

    if safety:
        events.append(
            "🚨 Safety car: reduced pit-stop time loss"
        )

    pit_loss = settings["pit"] * (
        .55 if safety else 1.
    )

    player = next(
        d for d in game["drivers"]
        if d["name"] == game["player"]
    )

    if choice != "Stay out":
        player["elapsed"] += pit_loss
        player.update(tire=choice, age=0.)
        player["used"].append(choice)
        player["stops"] += 1

        events.append(
            f"🔧 Your pit stop: {choice} (+{pit_loss:.1f}s)"
        )

    for driver in game["drivers"]:
        if driver is not player:
            remaining = game["total"] - lap

            worn = driver["age"] > {
                "Soft": 12,
                "Medium": 20,
                "Hard": 31,
                "Intermediate": 14,
                "Wet": 18,
            }[driver["tire"]]

            wrong = (
                game["weather"] == "Wet"
                and driver["tire"] in DRY
            )

            wrong = wrong or (
                game["weather"] == "Dry"
                and driver["tire"] not in DRY
            )

            needs_second = (
                remaining <= 2
                and not game["was_wet"]
                and len(set(driver["used"]) & DRY) < 2
            )

            if (
                (worn and remaining > 2)
                or wrong
                or needs_second
            ):
                target = (
                    "Wet" if game["weather"] == "Wet"
                    else "Intermediate"
                    if game["weather"] == "Damp"
                    else "Hard"
                    if driver["tire"] != "Hard"
                    else "Medium"
                )

                driver["elapsed"] += pit_loss
                driver.update(tire=target, age=0.)
                driver["used"].append(target)
                driver["stops"] += 1

        tire = driver["tire"]

        style = (
            mode if driver is player
            else rng.choices(
                ["Conserve", "Balanced", "Push"],
                [2, 6, 2]
            )[0]
        )

        penalty = 0.

        if game["weather"] == "Dry":
            penalty = {
                "Intermediate": 6,
                "Wet": 10,
            }.get(tire, 0)

        elif game["weather"] == "Damp":
            penalty = (
                3.8 if tire in DRY
                else 2 if tire == "Wet"
                else 0
            )

        else:
            penalty = (
                13.5 if tire in DRY
                else 2 if tire == "Intermediate"
                else 0
            )

        style_delta = {
            "Push": -.75,
            "Balanced": 0.,
            "Conserve": .65,
        }[style]

        wear_step = {
            "Push": 1.65,
            "Balanced": 1.,
            "Conserve": .62,
        }[style]

        duration = (
            settings["base"]
            + BASE_TIRE[tire]
            + driver["age"]
            * WEAR_RATE[tire]
            * settings["wear"]
            + penalty
            + style_delta
            + driver["skill"]
            + rng.gauss(0, .3)
        )

        if safety:
            duration = duration * 1.27 + 3

        driver["age"] += wear_step
        driver["elapsed"] += duration

        driver["history"].append(dict(
            lap=lap,
            lap_time=round(duration, 2),
            tire=tire,
            elapsed=round(driver["elapsed"], 2),
        ))

    ranking = order(game)

    for position, driver in enumerate(ranking, 1):
        driver["history"][-1]["position"] = position

    leader = ranking[0]["elapsed"]

    pos = next(
        i for i, d in enumerate(ranking, 1)
        if d is player
    )

    game["snapshots"].append([
        dict(
            lap=lap,
            position=i,
            name=d["name"],
            team=d["team"],
            elapsed=round(d["elapsed"], 2),
            gap=round(d["elapsed"] - leader, 2),
            tire=d["tire"],
            stops=d["stops"],
            lap_time=d["history"][-1]["lap_time"],
        )
        for i, d in enumerate(ranking, 1)
    ])

    game["entries"].append(dict(
        lap=lap,
        position=pos,
        time=player["history"][-1]["lap_time"],
        gap=round(player["elapsed"] - leader, 2),
        tire=player["tire"],
        mode=mode,
        pit=choice,
        weather=game["weather"],
        safety=safety,
    ))

    game.update(
        lap=lap,
        events=events
    )

    if lap >= game["total"]:
        game["finished"] = True

        if (
            not game["was_wet"]
            and len(set(player["used"]) & DRY) < 2
        ):
            game["events"].append(
                "⚠️ Dry-race two-compound rule not met."
            )

        game["events"].append("🏁 Checkered flag!")


def draw_circuit(game):
    """Draw an SVG track with simulated car positions."""

    path = TRACKS[game["track"]]["path"]
    ranking = order(game)

    leader = ranking[0]["elapsed"]
    base = TRACKS[game["track"]]["base"]

    circles = []

    # Show the leading 12 cars on the circuit.
    for index, d in enumerate(ranking[:12]):
        gap = d["elapsed"] - leader

        phase = (
            (game["lap"] * .22 + .74 - gap / base) % 1
        ) * 100

        color = (
            "#ff872d"
            if d["name"] == game["player"]
            else d["color"]
        )

        radius = (
            7 if d["name"] == game["player"]
            else 4.2
        )

        circles.append(f"""
        <circle r="{radius}"
            fill="{color}"
            stroke="#0c1422"
            stroke-width="1.8">
            <animateMotion
                dur="0.001s"
                fill="freeze"
                keyTimes="0;1"
                keyPoints="{phase/100};{phase/100}"
                calcMode="linear">
                <mpath href="#route"/>
            </animateMotion>
        </circle>
        """)

    svg = f"""
    <div style="
        background:#131f31;
        padding:12px;
        border-radius:15px;
        border:1px solid #354357">

        <div style="
            color:#eef3fc;
            font-size:17px;
            font-weight:700">
            🗺️ {html.escape(game['track'])} — Race Map
        </div>

        <div style="
            color:#acb9ca;
            font-size:12px">
            Simulated car positions after lap {game['lap']}.
        </div>

        <svg viewBox="0 0 380 220"
            style="
                width:100%;
                max-height:320px;
                background:#0a1421;
                border-radius:10px">

            <path
                id="route"
                d="{path}"
                fill="none"
                stroke="#566479"
                stroke-width="15"
                stroke-linecap="round"
                stroke-linejoin="round"/>

            <path
                d="{path}"
                fill="none"
                stroke="#eff2f6"
                stroke-width="9"
                stroke-linecap="round"
                stroke-linejoin="round"/>

            <path
                d="{path}"
                fill="none"
                stroke="#333b49"
                stroke-width="2"
                stroke-dasharray="4 5"/>

            {''.join(circles)}

        </svg>

        <div style="
            color:#ffa368;
            font-size:12px;
            font-weight:700">
            ● Orange = Your driver
            · Other colors = Other teams
            · Top 12 shown
        </div>
    </div>
    """

    if hasattr(st, "html"):
        st.html(svg)
    else:
        st.components.v1.html(svg, height=350)


def leaderboard(game):
    rows = []
    ranked = order(game)
    lead = ranked[0]["elapsed"]

    for p, d in enumerate(ranked, 1):
        rows.append(dict(
            Pos=p,
            Driver=(
                "★ " if d["name"] == game["player"]
                else ""
            ) + d["name"],
            Team=d["team"],
            Gap=(
                "LEADER" if p == 1
                else f"+{d['elapsed']-lead:.1f}s"
            ),
            Tire=(
                f"{TIRE_ICON[d['tire']]} {d['tire']}"
            ),
            Age=round(d["age"], 1),
            Stops=d["stops"],
        ))

    return pd.DataFrame(rows)


# =====================================================
# MAIN STREAMLIT APP
# =====================================================

st.title("🏎️ F1: THE PIT WALL")

st.caption(
    "SPORTS BY THE NUMBERS · "
    "Real 2026 driver names · "
    "Fictional classroom race data"
)

if "f1_game" not in st.session_state:
    st.session_state.f1_game = None


# -----------------------------------------------------
# RACE SETUP
# -----------------------------------------------------

if st.session_state.f1_game is None:
    st.subheader("Set up your race")

    a, b, c = st.columns(3)

    with a:
        track = st.selectbox(
            "Circuit",
            list(TRACKS)
        )

    with b:
        laps = st.slider(
            "Race laps",
            8, 30, 14
        )

    with c:
        first = st.selectbox(
            "Starting tire",
            ["Medium", "Soft", "Hard"]
        )

    driver = st.selectbox(
        "Your driver",
        [x[0] for x in GRID],
        format_func=lambda n: (
            f"{n} — {TEAMS[n]}"
        )
    )

    st.info(
        "The circuit outlines are simplified tracings "
        "inspired by your uploaded reference. "
        "This is a simulated strategy exercise, "
        "not live F1 GPS or timing."
    )

    if st.button(
        "🏁 START RACE",
        type="primary",
        use_container_width=True
    ):
        st.session_state.f1_game = create_game(
            track, laps, driver, first
        )
        st.rerun()

    st.stop()


# -----------------------------------------------------
# LIVE RACE SCREEN
# -----------------------------------------------------

g = st.session_state.f1_game

player = next(
    d for d in g["drivers"]
    if d["name"] == g["player"]
)

pos = next(
    i for i, d in enumerate(order(g), 1)
    if d is player
)

a, b, c, d, e = st.columns(5)

labels = [
    "LAP",
    "POSITION",
    "WEATHER",
    "CURRENT TIRE",
    "PIT STOPS",
]

values = [
    f"{g['lap']}/{g['total']}",
    f"P{pos}/22",
    g["weather"],
    f"{TIRE_ICON[player['tire']]} {player['tire']}",
    str(player["stops"]),
]

for col, label, val in zip(
    [a, b, c, d, e],
    labels,
    values
):
    col.metric(label, val)


left, right = st.columns(
    [1.35, 1],
    gap="large"
)


# -----------------------------------------------------
# CIRCUIT MAP AND LIVE LEADERBOARD
# -----------------------------------------------------

with left:
    draw_circuit(g)

    st.subheader("📡 Live Timing Board")

    st.dataframe(
        leaderboard(g),
        hide_index=True,
        use_container_width=True,
        height=400
    )

    if g["entries"]:
        st.subheader(
            "📈 Your Lap Times and Race Position"
        )

        data = pd.DataFrame(g["entries"])

        if len(data) > 1:
            st.line_chart(
                data.set_index("lap")["time"]
            )

            st.line_chart(
                data.set_index("lap")["position"]
            )
        else:
            st.info(
                "Complete lap 2 to unlock history charts."
            )

        with st.expander(
            "⏪ Replay any completed lap"
        ):
            if g["lap"] == 1:
                selected = 1
                st.caption(
                    "Lap 1 complete. Replay slider "
                    "unlocks after lap 2."
                )
            else:
                selected = st.slider(
                    "Lap number",
                    1,
                    g["lap"],
                    g["lap"]
                )

            st.dataframe(
                pd.DataFrame(
                    g["snapshots"][selected - 1]
                ),
                hide_index=True,
                use_container_width=True
            )

        full_history = pd.DataFrame([
            row
            for snapshot in g["snapshots"]
            for row in snapshot
        ])

        st.download_button(
            "Download full 22-driver timing (CSV)",
            full_history.to_csv(index=False),
            "f1_timing.csv",
            "text/csv"
        )


# -----------------------------------------------------
# PIT WALL CONTROLS
# -----------------------------------------------------

with right:
    st.subheader("🎧 Your Pit Wall")

    if not g["finished"]:
        st.write(
            f"**Next lap: {g['lap'] + 1}** "
            f"of {g['total']}"
        )

        st.caption(
            "Normal pit-stop time loss: approximately "
            f"{TRACKS[g['track']]['pit']:.0f}s"
        )

        pit = st.selectbox(
            "Tire strategy",
            [
                "Stay out",
                "Soft",
                "Medium",
                "Hard",
                "Intermediate",
                "Wet",
            ],
            key=f"pit_{g['lap']}"
        )

        mode = st.selectbox(
            "Driving mode",
            [
                "Balanced",
                "Push",
                "Conserve",
            ],
            key=f"mode_{g['lap']}"
        )

        if (
            g["weather"] == "Wet"
            and player["tire"] in DRY
        ):
            st.warning(
                "Heavy rain: dry tires will be much slower."
            )

        if (
            g["weather"] == "Dry"
            and player["tire"] not in DRY
        ):
            st.warning(
                "Dry track: consider a dry tire compound."
            )

        if (
            not g["was_wet"]
            and len(set(player["used"]) & DRY) < 2
        ):
            st.info(
                "Dry-race challenge: use two different "
                "dry tire compounds by the finish."
            )

        if st.button(
            "▶ RUN NEXT LAP",
            type="primary",
            use_container_width=True
        ):
            run_lap(g, pit, mode)
            st.rerun()

    # -------------------------------------------------
    # FINISH LINE AND REPORT CARD
    # -------------------------------------------------

    else:
        valid = (
            g["was_wet"]
            or len(set(player["used"]) & DRY) >= 2
        )

        score = max(
            0,
            100
            - (0 if valid else 25)
            - max(0, player["stops"] - 3) * 5
        )

        st.success(
            f"🏁 Finished P{pos}! "
            f"Strategy score: {score}/100"
        )

        st.caption(
            "Illustrative score based on tire-rule "
            "completion and pit-stop economy."
        )

        st.write(
            "Dry tire requirement:",
            "✅ Met or wet conditions"
            if valid else "❌ Not met"
        )

        reflection = st.text_area(
            "What would you change next time?"
        )

        summary = (
            f"Driver: {g['player']}\n"
            f"Track: {g['track']}\n"
            f"Position: P{pos}\n"
            f"Strategy score: {score}\n"
            f"Reflection: {reflection}\n"
        )

        st.download_button(
            "Download coach report",
            summary,
            "pit_wall_report.txt",
            "text/plain"
        )

    # -------------------------------------------------
    # RACE CONTROL EVENTS
    # -------------------------------------------------

    if g["events"]:
        st.subheader("📻 Race Control")

        for event in g["events"]:
            st.write(event)

    # -------------------------------------------------
    # MATH CONNECTION
    # -------------------------------------------------

    with st.expander(
        "Tire guide and math connection"
    ):
        st.write(
            "🔴 Soft: fast but wears quickly."
        )

        st.write(
            "🟡 Medium: balanced speed and durability."
        )

        st.write(
            "⚪ Hard: slower but durable."
        )

        st.write(
            "🟢 Intermediate: damp conditions."
        )

        st.write(
            "🔵 Wet: heavy rain."
        )

        st.write(
            "**Time gap** = Your accumulated race time "
            "− the leader's accumulated race time."
        )

        st.write(
            "**Average lap time** = Sum of lap times "
            "÷ number of laps."
        )

    if st.button(
        "🔄 Start a new race",
        use_container_width=True
    ):
        st.session_state.f1_game = None
        st.rerun()


st.divider()

st.caption(
    "Educational simulation: fictional lap times, "
    "simplified race rules, and approximate circuit art. "
    "Not an official Formula 1 timing feed."
)
