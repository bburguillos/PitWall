
import streamlit as st
import random
import math
import pandas as pd

st.set_page_config(
    page_title="F1: The Pit Wall | Sports by the Numbers",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TRACKS = {
    "Monza — Speed Temple": {
        "base": 83.0, "pit": 21, "wear": 1.0, "start_rain": 0.07
    },
    "Silverstone — Fast Corners": {
        "base": 91.5, "pit": 23, "wear": 1.22, "start_rain": 0.19
    },
    "Spa — Ardennes": {
        "base": 105.0, "pit": 24, "wear": 1.1, "start_rain": 0.23
    },
    "Singapore — Street Circuit": {
        "base": 102.0, "pit": 27, "wear": 1.4, "start_rain": 0.18
    },
}

# Real 2026 drivers and teams.
# Performance numbers are fictional for classroom simulation.
GRID_2026 = [
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

DRIVERS = [d[0] for d in GRID_2026]
TEAM_BY_DRIVER = {name: team for name, team, _ in GRID_2026}
COLOR_BY_DRIVER = {name: color for name, _, color in GRID_2026}

COLORS = {
    "Soft": "#ff4c5b",
    "Medium": "#ffd34a",
    "Hard": "#d6dee7",
    "Intermediate": "#51c987",
    "Wet": "#4b96e8",
}
DRY = {"Soft", "Medium", "Hard"}

PACE = {
    "Soft": -1.15,
    "Medium": 0.0,
    "Hard": 0.8,
    "Intermediate": 2.6,
    "Wet": 4.9,
}
WEAR = {
    "Soft": 0.28,
    "Medium": 0.14,
    "Hard": 0.072,
    "Intermediate": 0.15,
    "Wet": 0.12,
}

st.markdown("""
<style>
.stApp {
    background: #090f1c;
    color: #eaf0fa;
}
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 3rem;
    max-width: 1540px;
}
h1, h2, h3 {
    color: #fff !important;
}
[data-testid="stMetric"] {
    background: #151e31;
    border: 1px solid #273248;
    border-radius: 12px;
    padding: 10px 16px;
}
div.stButton > button[kind="primary"] {
    background: #ff6b24;
    color: #111;
    border: 0;
    font-weight: 800;
}
.head {
    padding: 16px 22px;
    border-radius: 14px;
    background: linear-gradient(120deg,#141f32,#232031);
    border-left: 7px solid #ff6b24;
    margin-bottom: 12px;
}
.track {
    background: #121b2b;
    border: 1px solid #303b50;
    border-radius: 16px;
    padding: 15px 18px;
}
.track-line {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 5px 0;
    font-size: 0.89rem;
}
.track-bar {
    position: relative;
    height: 22px;
    background: #283349;
    border-radius: 15px;
    flex: 1;
    overflow: hidden;
}
.car {
    position: absolute;
    top: 2px;
    height: 18px;
    min-width: 46px;
    border-radius: 9px;
    background: #5c86fd;
    color: #fff;
    font-size: 11px;
    text-align: center;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


def make_game(track_name, laps, seed, start_tire, chosen_driver):
    rng = random.Random(seed)
    details = TRACKS[track_name]
    rain = rng.random() < details["start_rain"]

    ordered = [chosen_driver] + [
        name for name in DRIVERS if name != chosen_driver
    ]

    drivers = []

    for i, name in enumerate(ordered):
        tire = start_tire if i == 0 else rng.choice(
            ["Medium", "Hard", "Soft"]
        )

        drivers.append({
            "name": name,
            "team": TEAM_BY_DRIVER[name],
            "color": COLOR_BY_DRIVER[name],
            "elapsed": rng.uniform(0, 9) if i else 4.5,
            "tire": tire,
            "age": 0,
            "stops": 0,
            "used": [tire],
            "pace_skill": 0.0 if i == 0 else rng.uniform(-0.75, 0.9),
            "history": [],
        })

    return {
        "player": chosen_driver,
        "track": track_name,
        "total": laps,
        "lap": 0,
        "weather": "Wet" if rain else "Dry",
        "safety": False,
        "seed": seed,
        "drivers": drivers,
        "entries": [],
        "snapshots": [],
        "events": [],
        "finished": False,
        "initial_tire": start_tire,
    }


def new_weather(g, rng):
    previous = g["weather"]
    change = rng.random()

    if previous == "Dry" and change < 0.085:
        g["weather"] = "Damp"
    elif previous == "Damp" and change < 0.33:
        g["weather"] = "Wet"
    elif previous == "Damp" and change > 0.69:
        g["weather"] = "Dry"
    elif previous == "Wet" and change > 0.74:
        g["weather"] = "Damp"

    if g["weather"] != previous:
        g["events"].append(
            f"🌦️ Conditions: {previous} → {g['weather']}"
        )


def lap_time(g, driver, rng, mode, under_sc):
    circuit = TRACKS[g["track"]]
    tire = driver["tire"]
    weather = g["weather"]
    age = driver["age"]

    baseline = (
        circuit["base"]
        + PACE[tire]
        + WEAR[tire] * age * circuit["wear"]
    )

    penalty = 0.0

    if weather == "Dry":
        if tire == "Intermediate":
            penalty = 6.0
        elif tire == "Wet":
            penalty = 10.0

    elif weather == "Damp":
        if tire in DRY:
            penalty = 3.8 + 0.08 * age
        elif tire == "Wet":
            penalty = 2.0

    elif weather == "Wet":
        if tire in DRY:
            penalty = 13.5
        elif tire == "Intermediate":
            penalty = 2.0

    baseline += penalty + driver["pace_skill"]

    if mode == "Push":
        baseline -= 0.75
        driver["age"] += 1.65
    elif mode == "Conserve":
        baseline += 0.65
        driver["age"] += 0.62
    else:
        driver["age"] += 1

    if under_sc:
        baseline = baseline * 1.27 + 3

    return max(
        1.0,
        baseline + rng.gauss(0, 0.15 if under_sc else 0.36)
    )


def simulate(g, pit_choice, mode):
    if g["finished"]:
        return

    lap_num = g["lap"] + 1
    rng = random.Random(f"{g['seed']}:{lap_num}")

    g["events"] = []
    new_weather(g, rng)

    g["safety"] = rng.random() < 0.11

    if g["safety"]:
        g["events"].append(
            "🚨 SAFETY CAR! Pit loss is reduced."
        )

    pit_loss = TRACKS[g["track"]]["pit"] * (
        0.53 if g["safety"] else 1
    )

    user = g["drivers"][0]
    before_age = user["age"]
    old_tire = user["tire"]

    if pit_choice != "Stay out":
        user["elapsed"] += pit_loss
        user["tire"] = pit_choice
        user["age"] = 0
        user["used"].append(pit_choice)
        user["stops"] += 1

        g["events"].append(
            f"🔧 Pitted for {pit_choice} (+{pit_loss:.1f}s)"
        )

    lap_results = []

    for i, d in enumerate(g["drivers"]):
        this_mode = (
            mode if i == 0
            else "Push" if rng.random() < 0.23
            else "Balanced"
        )

        if i > 0:
            t = d["tire"]
            w = g["weather"]
            remaining = g["total"] - lap_num

            must_switch = (
                remaining <= 2
                and w == "Dry"
                and len(set(d["used"]) & DRY) < 2
            )

            wrong = (
                (w == "Wet" and t not in ("Wet", "Intermediate"))
                or (w == "Dry" and t not in DRY)
            )

            old = d["age"] > (
                12 if t == "Soft"
                else 20 if t == "Medium"
                else 31
            )

            if must_switch or wrong or (old and remaining > 3):
                next_tire = (
                    "Wet" if w == "Wet"
                    else "Intermediate" if w == "Damp"
                    else "Hard" if t != "Hard"
                    else "Medium"
                )

                d["elapsed"] += pit_loss
                d["tire"] = next_tire
                d["age"] = 0
                d["used"].append(next_tire)
                d["stops"] += 1

        t = lap_time(g, d, rng, this_mode, g["safety"])
        d["elapsed"] += t

        d["history"].append({
            "lap": lap_num,
            "time": round(t, 2),
            "tire": d["tire"],
            "weather": g["weather"],
            "position": None,
        })

        lap_results.append(t)

    ranking = sorted(
        g["drivers"],
        key=lambda d: d["elapsed"]
    )

    for pos, d in enumerate(ranking, 1):
        d["history"][-1].update({
            "position": pos,
            "elapsed": round(d["elapsed"], 2),
            "stops": d["stops"],
            "team": d["team"],
        })

    position = next(
        i for i, d in enumerate(ranking, 1)
        if d["name"] == g["player"]
    )

    g["lap"] = lap_num

    g["snapshots"].append([
        {
            "driver": d["name"],
            "team": d["team"],
            "lap": lap_num,
            "position": d["history"][-1]["position"],
            "lap_time": d["history"][-1]["time"],
            "elapsed": round(d["elapsed"], 2),
            "tire": d["tire"],
            "stops": d["stops"],
        }
        for d in g["drivers"]
    ])

    g["entries"].append({
        "lap": lap_num,
        "weather": g["weather"],
        "safety": g["safety"],
        "action": pit_choice,
        "mode": mode,
        "previous_tire": old_tire,
        "previous_age": round(before_age, 1),
        "user_time": round(lap_results[0], 2),
        "position": position,
        "gap": round(
            user["elapsed"] - ranking[0]["elapsed"], 2
        ),
    })

    if lap_num >= g["total"]:
        g["finished"] = True

        if (
            g["weather"] == "Dry"
            and len(set(user["used"]) & DRY) < 2
        ):
            g["events"].append(
                "⚠️ Two dry tire compounds were not used."
            )
        else:
            g["events"].append(
                "🏁 CHECKERED FLAG! Race complete."
            )


def report(g):
    entries = g["entries"]
    user = g["drivers"][0]

    ranking = sorted(
        g["drivers"],
        key=lambda d: d["elapsed"]
    )

    pos = next(
        i for i, d in enumerate(ranking, 1)
        if d["name"] == g["player"]
    )

    rule_ok = not (
        g["weather"] == "Dry"
        and len(set(user["used"]) & DRY) < 2
    )

    avg = (
        sum(x["user_time"] for x in entries) / len(entries)
        if entries else 0
    )

    score = 100
    warnings = []

    for row in entries:
        tire = user["history"][row["lap"] - 1]["tire"]

        if row["weather"] == "Wet" and tire in DRY:
            score -= 8
            warnings.append("Dry tires on a wet lap")

        if row["weather"] == "Dry" and tire in (
            "Intermediate", "Wet"
        ):
            score -= 8
            warnings.append("Wet tires on a dry lap")

        if (
            row["previous_age"] > 18
            and row["previous_tire"] == "Soft"
            and row["action"] == "Stay out"
        ):
            score -= 3

    if not rule_ok:
        score -= 25
        warnings.append("Dry tire requirement not met")

    if user["stops"] > math.ceil(g["total"] / 5) + 1:
        score -= 8
        warnings.append("Excessive pit stops")

    return (
        max(0, min(100, score)),
        pos,
        avg,
        rule_ok,
        sorted(set(warnings)),
    )


def draw_positions(g, full_grid=False):
    ranking = sorted(
        g["drivers"], key=lambda d: d["elapsed"]
    )

    leader = ranking[0]["elapsed"]
    max_gap = max(
        max(d["elapsed"] - leader for d in ranking), 5
    )

    player_index = next(
        i for i, d in enumerate(ranking)
        if d["name"] == g["player"]
    )

    if full_grid:
        shown = list(range(len(ranking)))
    else:
        shown = sorted(set(
            list(range(min(8, len(ranking))))
            + list(range(
                max(0, player_index - 2),
                min(len(ranking), player_index + 3)
            ))
        ))

    rows = []

    for index in shown:
        d = ranking[index]
        gap = d["elapsed"] - leader
        pct = max(4, 92 - 80 * gap / max_gap)

        color = (
            "#ff6b24" if d["name"] == g["player"]
            else d["color"]
        )

        gap_label = (
            f"+{gap:.1f}s" if gap > 0 else "LEADER"
        )

        tire_color = COLORS[d["tire"]]

        rows.append(f"""
        <div class="track-line">
            <span style="width:35px">P{index + 1}</span>
            <span style="width:170px;overflow:hidden;
                white-space:nowrap;text-overflow:ellipsis">
                {d["name"]}
            </span>
            <div class="track-bar">
                <div class="car"
                    style="left:{pct-4:.1f}%;
                    background:{color}">
                    🏎️
                </div>
            </div>
            <span style="width:82px;text-align:right">
                {gap_label}
            </span>
            <span style="color:{tire_color}">●</span>
        </div>
        """)

    st.markdown(
        '<div class="track">' + "".join(rows) + "</div>",
        unsafe_allow_html=True
    )

    if not full_grid and len(shown) < len(ranking):
        st.caption(
            "Showing leaders and nearby rivals. "
            "Toggle full grid to view all 22."
        )


# ---------- MAIN APP ----------

st.markdown("""
<div class="head">
    <div style="font-size:0.8rem;color:#ffa66d;
        letter-spacing:2px;font-weight:800">
        SPORTS BY THE NUMBERS • RACE STRATEGY LAB
    </div>
    <h1>🏎️ F1: THE PIT WALL</h1>
    <div>Make the call. Read the data. Beat the field.</div>
</div>
""", unsafe_allow_html=True)

if "game" not in st.session_state:
    st.session_state.game = None

if st.session_state.game is None:
    st.subheader("Set up your Grand Prix")

    a, b, c = st.columns([2, 1, 1])

    with a:
        circuit = st.selectbox(
            "Circuit", list(TRACKS)
        )
    with b:
        laps = st.slider(
            "Race length (laps)", 8, 30, 14, 2
        )
    with c:
        first = st.selectbox(
            "Starting tire", ["Medium", "Soft", "Hard"]
        )

    chosen = st.selectbox(
        "Choose your 2026 F1 driver",
        DRIVERS,
        format_func=lambda name: (
            f"{name} — {TEAM_BY_DRIVER[name]}"
        )
    )

    st.info(
        "This is a classroom simulation using real driver "
        "names but fictional performance statistics."
    )

    if st.button(
        "🏁 START GRAND PRIX",
        type="primary",
        use_container_width=True
    ):
        st.session_state.game = make_game(
            circuit,
            laps,
            random.SystemRandom().randrange(10**9),
            first,
            chosen
        )
        st.rerun()

    st.stop()


g = st.session_state.game
user = g["drivers"][0]

ranking = sorted(
    g["drivers"], key=lambda d: d["elapsed"]
)

position = next(
    i for i, d in enumerate(ranking, 1)
    if d["name"] == g["player"]
)

header = st.columns(5)

values = [
    f"{g['lap']} / {g['total']}",
    f"P{position} / 22",
    g["weather"],
    f"{user['tire']} · {user['age']:.0f} laps",
    user["stops"],
]

labels = [
    "LAP", "POSITION", "WEATHER",
    "YOUR TIRES", "PIT STOPS"
]

for col, label, value in zip(header, labels, values):
    with col:
        st.metric(label, value)


left, right = st.columns([1.55, 1], gap="medium")

with left:
    st.markdown("### 🏁 Live Race Tracker")

    full_grid = st.toggle(
        "Show all 22 drivers", value=False
    )

    draw_positions(g, full_grid)

    if g["entries"]:
        last = g["entries"][-1]

        st.caption(
            f"Last lap: {last['user_time']:.2f}s | "
            f"Mode: {last['mode']} | "
            f"Position: P{last['position']}"
        )

    st.markdown("### 📊 Timing & Tire History")

    if g["entries"]:
        df = pd.DataFrame(g["entries"])

        chart_df = df.set_index("lap")[["user_time"]]

        # FIX: Wait until 2 laps for time-series charts.
        if len(chart_df) > 1:
            st.line_chart(chart_df, height=168)
        else:
            st.info(
                f"Lap 1: {chart_df.iloc[0, 0]:.2f}s. "
                "The chart appears after lap 2."
            )

        st.markdown("### 📉 Position Changes")

        selected = st.multiselect(
            "Drivers on position chart",
            DRIVERS,
            default=[g["player"]] + [
                d["name"] for d in ranking
                if d["name"] != g["player"]
            ][:4]
        )

        pos_rows = [
            {
                "Lap": h["lap"],
                "Driver": d["name"],
                "Position": h["position"]
            }
            for d in g["drivers"]
            for h in d["history"]
            if d["name"] in selected
        ]

        if pos_rows:
            chart = (
                pd.DataFrame(pos_rows)
                .pivot(
                    index="Lap",
                    columns="Driver",
                    values="Position"
                )
                .sort_index()
            )

            if len(chart) > 1:
                st.line_chart(chart, height=225)
            else:
                st.caption(
                    "Position chart appears after lap 2."
                )

        with st.expander(
            "⏪ Lap Replay — All 22 Drivers",
            expanded=False
        ):
            # IMPORTANT FIRST-LAP FIX
            # Never create a slider with identical endpoints.
            if g["lap"] == 1:
                replay_lap = 1
                st.caption(
                    "Lap 1 complete. Run another lap "
                    "to unlock the replay slider."
                )
            else:
                replay_lap = st.slider(
                    "Replay completed lap",
                    min_value=1,
                    max_value=g["lap"],
                    value=g["lap"],
                    key=f"replay_lap_{g['lap']}"
                )

            latest = pd.DataFrame(
                g["snapshots"][replay_lap - 1]
            ).sort_values("position")

            leader_time = float(
                latest["elapsed"].min()
            )

            latest["gap_to_leader"] = (
                latest["elapsed"].apply(
                    lambda t: (
                        f"+{t-leader_time:.1f}s"
                        if t > leader_time
                        else "LEADER"
                    )
                )
            )

            st.dataframe(
                latest[[
                    "position", "driver", "team",
                    "lap_time", "gap_to_leader",
                    "tire", "stops"
                ]],
                hide_index=True,
                use_container_width=True
            )

            full_timing = pd.DataFrame([
                row
                for lap in g["snapshots"]
                for row in lap
            ])

            st.download_button(
                "Download Full Timing CSV",
                full_timing.to_csv(index=False),
                file_name="f1_full_timing.csv",
                mime="text/csv"
            )

        with st.expander("Your Lap-by-Lap Decisions"):
            st.dataframe(
                df[[
                    "lap", "user_time", "position",
                    "weather", "safety",
                    "action", "mode", "gap"
                ]],
                use_container_width=True,
                hide_index=True
            )

    else:
        st.caption(
            "Complete lap 1 to see live timing and positions."
        )


with right:
    st.markdown("### 🎧 Your Pit Wall")

    if not g["finished"]:
        remaining = g["total"] - g["lap"]

        st.caption(
            f"{remaining} laps remaining | "
            f"Typical pit loss: "
            f"{TRACKS[g['track']]['pit']} seconds"
        )

        if g["weather"] == "Wet":
            st.warning(
                "Wet conditions! Consider wet tires."
            )
        elif g["weather"] == "Damp":
            st.info(
                "Damp conditions! Intermediates may help."
            )
        elif user["tire"] in ("Wet", "Intermediate"):
            st.warning(
                "Track is dry. Your wet tires are slower."
            )

        pit = st.selectbox(
            "Tire decision for next lap",
            [
                "Stay out", "Soft", "Medium", "Hard",
                "Intermediate", "Wet"
            ],
            key=f"pit_{g['lap']}"
        )

        mode = st.selectbox(
            "Driving style",
            ["Conserve", "Balanced", "Push"],
            index=1,
            key=f"mode_{g['lap']}"
        )

        st.caption(
            "Push = faster but more tire wear. "
            "Conserve = slower but saves tires."
        )

        # Button runs ONE lap and refreshes safely.
        if st.button(
            "▶️ RUN NEXT LAP",
            type="primary",
            use_container_width=True,
            key=f"run_lap_{g['lap']}"
        ):
            simulate(g, pit, mode)
            st.session_state.game = g
            st.rerun()

        need_two = (
            len(set(user["used"]) & DRY) < 2
        )

        if g["weather"] == "Dry" and need_two:
            st.warning(
                "Dry race rule: use at least two "
                "different dry tire compounds."
            )

    else:
        score, pos, avg, rule_ok, warnings = report(g)

        st.success(
            f"🏁 Finished P{pos}! "
            f"Strategy Grade: {score}/100"
        )

        st.metric(
            "Average Lap Time",
            f"{avg:.2f}s"
        )

        st.caption(
            "Strategy grade evaluates decisions, "
            "not just finishing position."
        )

        st.write(
            "Dry tire rule: "
            + ("✅ Met" if rule_ok else "❌ Not met")
        )

        for warning in warnings:
            st.warning(warning)

        reflection = st.text_area(
            "What strategy would you change and why?",
            key="reflection"
        )

        text_report = (
            f"F1: THE PIT WALL\n"
            f"Track: {g['track']}\n"
            f"Driver: {g['player']}\n"
            f"Finishing Position: P{pos}\n"
            f"Strategy Score: {score}/100\n"
            f"Average Lap: {avg:.2f}s\n"
            f"Pit Stops: {user['stops']}\n"
            f"Tires Used: {', '.join(user['used'])}\n"
            f"Reflection: {reflection}\n"
        )

        st.download_button(
            "📄 Download Coach Report",
            text_report,
            file_name="f1_coach_report.txt",
            mime="text/plain",
            use_container_width=True
        )

        st.download_button(
            "📊 Download Race Data",
            pd.DataFrame(g["entries"]).to_csv(
                index=False
            ),
            file_name="f1_lap_data.csv",
            mime="text/csv",
            use_container_width=True
        )

    if g["events"]:
        st.markdown("### 📻 Race Control")

        for event in g["events"][-3:]:
            st.write(event)

    with st.expander("🔎 Tire Guide & Math Help"):
        st.markdown("""
**Soft:** Fast when fresh, wears quickly.

**Medium:** Balanced speed and durability.

**Hard:** Slower but lasts longer.

**Intermediate:** Best suited to damp conditions.

**Wet:** Designed for heavy rain.

**Average lap time** = Total lap seconds ÷ laps.

**Gap to leader** = Your total elapsed time −
leader's elapsed time.

**Example:** Saving 0.7 seconds per lap for 8 laps
saves 5.6 seconds. Is that worth a 21-second pit stop?
""")

    if st.button(
        "🔄 New Race",
        use_container_width=True
    ):
        st.session_state.game = None
        st.rerun()


st.divider()

st.caption(
    "Sports by the Numbers • Educational F1 simulator • "
    "Real 2026 driver/team names • Simulated racing data • "
    "Simplified tire and race rules."
)
