import html
import json
import random
import time
from statistics import mean

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="F1: The Pit Wall", page_icon="🏎️", layout="wide", initial_sidebar_state="collapsed")

# Real driver/team names; all performance, weather and race events are SIMULATED.
GRID = [
    ("George Russell", "Mercedes", "#27F4D2"), ("Kimi Antonelli", "Mercedes", "#27F4D2"),
    ("Charles Leclerc", "Ferrari", "#E80020"), ("Lewis Hamilton", "Ferrari", "#E80020"),
    ("Lando Norris", "McLaren", "#FF8000"), ("Oscar Piastri", "McLaren", "#FF8000"),
    ("Max Verstappen", "Red Bull", "#3671C6"), ("Isack Hadjar", "Red Bull", "#3671C6"),
    ("Liam Lawson", "Racing Bulls", "#6692FF"), ("Arvid Lindblad", "Racing Bulls", "#6692FF"),
    ("Pierre Gasly", "Alpine", "#FF87BC"), ("Franco Colapinto", "Alpine", "#FF87BC"),
    ("Esteban Ocon", "Haas", "#B6BABD"), ("Oliver Bearman", "Haas", "#B6BABD"),
    ("Nico Hulkenberg", "Audi", "#C4E300"), ("Gabriel Bortoleto", "Audi", "#C4E300"),
    ("Carlos Sainz", "Williams", "#64C4FF"), ("Alex Albon", "Williams", "#64C4FF"),
    ("Fernando Alonso", "Aston Martin", "#229971"), ("Lance Stroll", "Aston Martin", "#229971"),
    ("Sergio Perez", "Cadillac", "#969BA2"), ("Valtteri Bottas", "Cadillac", "#969BA2"),
]
TEAM = {n: t for n, t, _ in GRID}
COLOR = {n: c for n, _, c in GRID}

# Stylized circuit silhouettes, designed for an educational illustration.
TRACKS = {
    "Monza": (83.0, 21., 1.00, .07, "M 75 45 L 105 35 L 137 83 L 175 123 L 216 133 L 295 134 L 328 142 L 328 157 L 277 159 L 209 157 L 135 157 Q 109 155 100 139 L 89 104 L 68 69 Z"),
    "Silverstone": (91.5, 23., 1.22, .19, "M 55 82 L 116 37 Q 126 31 138 44 L 200 90 L 200 136 L 236 151 L 260 126 L 265 76 Q 279 59 295 77 L 310 108 L 313 156 L 266 171 L 240 156 L 210 179 L 177 168 L 126 144 L 73 113 Z"),
    "Spa-Francorchamps": (105., 24., 1.10, .23, "M 56 173 L 88 133 L 127 94 L 170 69 L 213 44 L 240 53 L 268 37 L 301 65 L 313 92 L 286 78 L 257 65 L 233 76 L 202 93 L 194 118 L 227 135 L 253 158 L 246 184 L 209 167 L 172 138 L 131 146 L 95 164 Z"),
    "Singapore": (102., 27., 1.40, .18, "M 59 106 L 96 50 L 125 75 L 141 61 L 190 95 L 250 100 L 255 39 L 273 47 L 281 91 L 289 130 L 270 163 L 225 165 L 197 151 L 145 150 L 100 143 L 83 167 L 62 145 Z"),
    "Bahrain": (94., 23., 1.10, .02, "M 65 149 L 87 36 L 118 71 L 155 84 L 126 114 L 207 114 L 240 47 L 264 69 L 300 151 Z"),
    "Suzuka": (92., 23., 1.15, .22, "M 46 63 Q 78 110 118 108 L 142 70 L 156 121 L 181 115 Q 201 74 224 96 L 278 155 Q 294 187 311 175 Q 321 165 288 138 L 245 89 Q 209 50 184 87 L 157 101 Q 135 105 112 85 Q 85 66 81 38 Q 52 31 46 63 Z"),
    "Monaco": (77., 26., 1.08, .14, "M 50 160 Q 50 108 83 79 L 137 35 L 193 70 L 218 91 L 256 93 Q 280 92 287 67 L 318 57 L 325 81 L 294 100 Q 263 139 232 124 L 172 94 L 132 62 Q 102 49 78 99 L 63 168 Z"),
    "Interlagos": (72., 22., 1.12, .25, "M 74 78 Q 106 49 147 48 Q 181 41 188 67 L 182 95 Q 221 46 244 55 Q 266 68 245 100 L 285 129 L 271 158 Q 223 150 199 122 L 164 103 L 131 151 Q 98 173 73 148 Q 48 117 74 78 Z"),
    "Las Vegas": (94., 22., .90, .04, "M 65 151 L 95 98 L 113 102 L 113 43 L 133 37 L 151 67 L 278 67 L 268 35 L 284 36 L 309 73 L 310 156 L 153 156 L 105 136 Z"),
    "Montreal": (76., 22., 1.05, .20, "M 57 72 L 135 79 L 180 102 L 215 124 L 248 137 L 273 117 L 304 125 L 286 150 L 241 158 L 208 146 L 176 131 L 133 93 Z"),
    "Miami": (90., 22., 1.00, .15, "M 56 62 L 299 62 L 293 89 L 309 98 L 293 112 L 249 109 Q 208 158 162 157 L 117 142 Q 90 115 60 136 L 51 117 Q 71 88 113 108 L 164 131 L 194 115 L 114 74 Z"),
}

DRY = {"Soft", "Medium", "Hard"}
TIRE_PACE = {"Soft": -1.1, "Medium": 0., "Hard": .7, "Intermediate": 2.6, "Wet": 4.5}
TIRE_WEAR = {"Soft": .28, "Medium": .14, "Hard": .075, "Intermediate": .17, "Wet": .13}
TIRE_SYMBOL = {"Soft": "🔴", "Medium": "🟡", "Hard": "⚪", "Intermediate": "🟢", "Wet": "🔵"}

st.markdown("""<style>
.block-container {padding-top:.55rem; padding-bottom:1rem; max-width:1500px}
h1 {font-size:1.8rem !important; margin-bottom:.1rem !important}
h3 {margin-top:.4rem !important}
[data-testid="stMetric"] {background:#19253a; padding:7px 11px; border-radius:10px}
div.stButton > button[kind="primary"] {background:#ff7a2c; color:#141414; font-weight:800}
</style>""", unsafe_allow_html=True)


def new_game(track, laps, player_name):
    seed = random.SystemRandom().randrange(1_000_000_000)
    rng = random.Random(seed)
    drivers = []
    for name, team, color in GRID:
        drivers.append(dict(name=name, team=team, color=color,
                            skill=rng.uniform(-.65, .65), qual=None,
                            elapsed=0., tire="Medium", age=0.,
                            used=["Medium"], stops=0, history=[]))
    return dict(track=track, total=laps, player=player_name, seed=seed,
                stage="qualifying", lap=0, weather="Dry", was_wet=False,
                safety=False, drivers=drivers, events=[], entries=[],
                snapshots=[], qual_results=[], pit_challenge=None, finished=False)


def ranking(g):
    return sorted(g["drivers"], key=lambda d: d["elapsed"])


def you(g):
    return next(d for d in g["drivers"] if d["name"] == g["player"])


def qualify(g, mode, tire):
    rng = random.Random(f"qual-{g['seed']}")
    base = TRACKS[g["track"]][0]
    for d in g["drivers"]:
        dr_mode = mode if d["name"] == g["player"] else rng.choice(["Balanced", "Push"])
        dr_tire = tire if d["name"] == g["player"] else "Soft"
        adjustment = {"Push": -.65, "Balanced": 0., "Conserve": .55}[dr_mode]
        compound = {"Soft": -1., "Medium": -.15, "Hard": .45}[dr_tire]
        d["qual"] = round(base + d["skill"] + compound + adjustment + rng.gauss(0, .48), 3)
    order = sorted(g["drivers"], key=lambda d: d["qual"])
    g["qual_results"] = [dict(Grid=i, Driver=d["name"], Team=d["team"],
                               **{"Qualifying lap": f"{d['qual']:.3f}s"})
                         for i, d in enumerate(order, 1)]
    # Racing offsets use grid gaps, not raw qualifying lap-time differences.
    for i, d in enumerate(order):
        d["elapsed"] = i * 1.25
    g["stage"] = "race"
    g["events"] = ["🏁 Qualifying complete! The starting grid is set."]


def new_targets(g):
    rng = random.Random(f"pit-{g['seed']}-{g['lap']}")
    return [rng.randint(15, 85) for _ in range(3)]


def pit_quality(targets, answers, elapsed_seconds):
    # A fast, precise response earns a smaller stationary pit-stop component.
    errors = [abs(a-b) for a, b in zip(answers, targets)]
    accuracy = sum(errors)
    # Larger total errors and longer completion time increase the stop duration.
    stationary = min(11., 2.1 + .11 * accuracy + .045 * min(elapsed_seconds, 90.))
    grade = "Lightning fast" if stationary < 3.0 else "Clean stop" if stationary < 5.0 else "Slow stop"
    return round(stationary, 2), grade


def sim_lap(g, pit_tire, mode, stationary=None):
    lap = g["lap"] + 1
    rng = random.Random(f"race-{g['seed']}-{lap}")
    base, pit_loss, wear, rain_chance, _ = TRACKS[g["track"]]
    w = g["weather"]
    r = rng.random()
    if w == "Dry" and r < rain_chance * .55: g["weather"] = "Damp"
    elif w == "Damp" and r < .28: g["weather"] = "Wet"
    elif w == "Damp" and r > .72: g["weather"] = "Dry"
    elif w == "Wet" and r > .74: g["weather"] = "Damp"
    g["was_wet"] = g["was_wet"] or (g["weather"] != "Dry")
    g["safety"] = rng.random() < .09
    events = []
    if g["weather"] != w: events.append(f"🌦️ Weather: {w} → {g['weather']}")
    if g["safety"]: events.append("🚨 Safety car: pit lane loses less race time")
    entry_loss = (pit_loss - 2.5) * (.53 if g["safety"] else 1.)
    driver = you(g)
    actual_pit = 0.
    if pit_tire != "Stay out":
        actual_pit = entry_loss + (stationary if stationary is not None else 4.)
        driver["elapsed"] += actual_pit
        driver["tire"] = pit_tire
        driver["age"] = 0.
        driver["used"].append(pit_tire)
        driver["stops"] += 1
        events.append(f"🔧 Pit: {pit_tire} | {stationary:.2f}s stationary | +{actual_pit:.1f}s race loss")
    for d in g["drivers"]:
        if d is not driver:
            remaining = g["total"] - lap
            worn = d["age"] > {"Soft": 11, "Medium": 19, "Hard": 29, "Intermediate": 13, "Wet": 17}[d["tire"]]
            wrong = (g["weather"] == "Wet" and d["tire"] in DRY) or (g["weather"] == "Dry" and d["tire"] not in DRY)
            needs_second = (remaining <= 2 and not g["was_wet"] and len(set(d["used"]) & DRY) < 2)
            if wrong or needs_second or (worn and remaining > 2):
                target = ("Wet" if g["weather"] == "Wet" else "Intermediate" if g["weather"] == "Damp"
                          else "Hard" if d["tire"] != "Hard" else "Medium")
                d["elapsed"] += entry_loss + rng.uniform(2.1, 4.8)
                d["tire"], d["age"] = target, 0.
                d["used"].append(target)
                d["stops"] += 1
        style = mode if d is driver else rng.choices(["Push", "Balanced", "Conserve"], [2, 6, 2])[0]
        compound = d["tire"]
        conditions = g["weather"]
        weather_penalty = (0. if compound in DRY else 6. if compound == "Intermediate" else 10.) if conditions == "Dry" else (
            3.8 if compound in DRY else 0. if compound == "Intermediate" else 2.) if conditions == "Damp" else (
            13.5 if compound in DRY else 2. if compound == "Intermediate" else 0.)
        lap_time = base + d["skill"] + TIRE_PACE[compound] + d["age"] * TIRE_WEAR[compound] * wear + weather_penalty + {"Push": -.75, "Balanced": 0., "Conserve": .65}[style] + rng.gauss(0, .32)
        if g["safety"]: lap_time = lap_time * 1.27 + 3.
        d["age"] += {"Push": 1.65, "Balanced": 1., "Conserve": .62}[style]
        d["elapsed"] += lap_time
        d["history"].append({"Lap": lap, "Time": round(lap_time, 2), "Tire": compound, "Weather": conditions})
    ranked = ranking(g)
    leader = ranked[0]["elapsed"]
    for i, d in enumerate(ranked, 1): d["history"][-1]["Position"] = i
    position = next(i for i, d in enumerate(ranked, 1) if d is driver)
    g["snapshots"].append([dict(Lap=lap, Pos=i, Driver=d["name"], Team=d["team"], Gap=round(d["elapsed"]-leader, 2), Tire=d["tire"], Stops=d["stops"], Time=d["history"][-1]["Time"]) for i, d in enumerate(ranked, 1)])
    g["entries"].append(dict(Lap=lap, Time=driver["history"][-1]["Time"], Pos=position,
                             Gap=round(driver["elapsed"]-leader, 2), Tire=driver["tire"],
                             Drive=mode, Pit=pit_tire, PitLoss=round(actual_pit, 2), Weather=g["weather"], SafetyCar=g["safety"]))
    g["lap"], g["events"] = lap, events
    g["pit_challenge"] = None
    if lap >= g["total"]:
        g["finished"] = True
        g["events"].append("🏁 Chequered flag — race complete!")
        if not g["was_wet"] and len(set(driver["used"]) & DRY) < 2:
            g["events"].append("⚠️ Dry-weather two-compound requirement missed")


def circuit_map(g):
    # HTML component iframe avoids Streamlit Markdown showing raw HTML tags.
    path = TRACKS[g["track"]][4]
    ranked = ranking(g)
    lead = ranked[0]["elapsed"]
    base = TRACKS[g["track"]][0]
    cars = [{"name": d["name"], "color": "#ff872d" if d["name"] == g["player"] else d["color"],
             "mine": d["name"] == g["player"], "pos": i,
             "fraction": (.72 + .17 * g["lap"] - (d["elapsed"]-lead)/base) % 1}
            for i, d in enumerate(ranked[:12], 1)]
    markup = '''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#111d2f;font-family:Arial,sans-serif;color:#edf2fa}
.main{border:1px solid #3b4b63;border-radius:12px;padding:9px 12px}
.title{font-size:14px;font-weight:bold}.sub{font-size:11px;color:#a9b8ca}
svg{display:block;width:100%;height:205px;background:#0b1727;border-radius:9px}
</style></head><body><div class="main"><div class="title">🏁 __TITLE__ · Simulated circuit position</div>
<div class="sub">Orange = your car · 12 leading cars shown · positions update each lap</div>
<svg viewBox="0 0 380 220"><path id="route" fill="none" stroke="#34455c" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" />
<path id="inner" fill="none" stroke="#e5ebf5" stroke-width="11" stroke-linecap="round" stroke-linejoin="round" />
<g id="cars"></g></svg></div><script>
const path=__PATH__, cars=__CARS__;
for(const id of ['route','inner'])document.getElementById(id).setAttribute('d',path);
const route=document.getElementById('route');const length=route.getTotalLength();const layer=document.getElementById('cars');
for(const c of cars){const p=route.getPointAtLength(length*c.fraction);const e=document.createElementNS('http://www.w3.org/2000/svg','circle');
e.setAttribute('cx',p.x);e.setAttribute('cy',p.y);e.setAttribute('r',c.mine?7:4.6);e.setAttribute('fill',c.color);e.setAttribute('stroke','#0c1420');e.setAttribute('stroke-width','1.5');
const tip=document.createElementNS('http://www.w3.org/2000/svg','title');tip.textContent='P'+c.pos+' '+c.name;e.appendChild(tip);layer.appendChild(e)}
</script></body></html>'''
    markup = markup.replace("__TITLE__", html.escape(g["track"])).replace("__PATH__", json.dumps(path)).replace("__CARS__", json.dumps(cars))
    components.html(markup, height=268, scrolling=False)


def timer_stats(g):
    lap_times = [x["Time"] for x in g["entries"]]
    if not lap_times: return None
    last, best, avg = lap_times[-1], min(lap_times), mean(lap_times)
    prev = lap_times[-2] if len(lap_times) > 1 else None
    rivals = [mean([h["Time"] for h in d["history"]]) for d in g["drivers"] if d["name"] != g["player"] and d["history"]]
    field_avg = mean(rivals) if rivals else 0.
    return last, best, avg, prev, field_avg


st.title("🏎️ F1: THE PIT WALL")
st.caption("Sports by the Numbers • 2026 driver names • fictional race performance • simplified track outlines")

if "pit_wall_v3" not in st.session_state:
    st.session_state.pit_wall_v3 = None

if st.session_state.pit_wall_v3 is None:
    st.subheader("Grand Prix setup")
    a, b, c = st.columns([2, 1, 2])
    track = a.selectbox("Circuit", list(TRACKS))
    laps = b.slider("Race laps", 8, 30, 14)
    driver = c.selectbox("Your driver", [d[0] for d in GRID], format_func=lambda n: f"{n} · {TEAM[n]}")
    if st.button("🏁 BEGIN QUALIFYING", type="primary", use_container_width=True):
        st.session_state.pit_wall_v3 = new_game(track, laps, driver)
        st.rerun()
    st.stop()

g = st.session_state.pit_wall_v3
mine = you(g)
if g["stage"] == "qualifying":
    st.subheader(f"⏱️ Qualifying · {g['track']}")
    st.write("Make one flying lap to set your grid position. All 22 drivers will qualify.")
    c1, c2 = st.columns(2)
    qtire = c1.radio("Qualifying tire", ["Soft", "Medium", "Hard"], horizontal=True)
    qmode = c2.radio("Qualifying pace", ["Push", "Balanced", "Conserve"], horizontal=True)
    st.info("Soft tires and pushing generally help qualifying pace, but simulation randomness still matters.")
    if st.button("🏎️ RUN QUALIFYING LAP", type="primary", use_container_width=True):
        qualify(g, qmode, qtire)
        st.rerun()
    if st.button("Start over"):
        st.session_state.pit_wall_v3 = None
        st.rerun()
    st.stop()

ordered = ranking(g)
position = next(i for i, d in enumerate(ordered, 1) if d is mine)
metrics = st.columns(6)
labels = ["LAP", "POSITION", "LAST LAP", "MEAN LAP", "BEST LAP", "TIRE"]
stats = timer_stats(g)
values = [f"{g['lap']}/{g['total']}", f"P{position}/22",
          f"{stats[0]:.2f}s" if stats else "—",
          f"{stats[2]:.2f}s" if stats else "—",
          f"{stats[1]:.2f}s" if stats else "—",
          f"{TIRE_SYMBOL[mine['tire']]} {mine['tire']}"]
for box, label, val in zip(metrics, labels, values): box.metric(label, val)

left, right = st.columns([1.42, 1.0], gap="medium")
with left:
    circuit_map(g)
    if stats:
        last, best, avg, prev, field_avg = stats
        diff_prev = f"{last-prev:+.2f}s vs previous" if prev is not None else "First racing lap"
        diff_mean = f"{avg-field_avg:+.2f}s vs other drivers' means"
        st.caption(f"**Lap comparison:** {diff_prev} · **Mean comparison:** {diff_mean}")
    tabs = st.tabs(["⏱️ Lap comparison", "🏎️ Timing tower", "📋 Qualifying & replay"])
    with tabs[0]:
        if g["entries"]:
            df = pd.DataFrame(g["entries"])
            if len(df) >= 2:
                st.line_chart(df.set_index("Lap")[["Time"]], height=165)
            st.dataframe(df[["Lap", "Time", "Pos", "Gap", "Tire", "PitLoss"]].tail(6), hide_index=True, use_container_width=True, height=230)
        else: st.info("Run lap 1 to start the lap-time comparison.")
    with tabs[1]:
        lead = ordered[0]["elapsed"]
        tower = pd.DataFrame([{"P": i, "Driver": ("★ " if d is mine else "") + d["name"], "Team": d["team"], "Gap": "LEADER" if i == 1 else f"+{d['elapsed']-lead:.1f}s", "Tire": TIRE_SYMBOL[d["tire"]], "Stops": d["stops"]} for i, d in enumerate(ordered, 1)])
        st.dataframe(tower, use_container_width=True, hide_index=True, height=330)
    with tabs[2]:
        st.write("**Starting grid**")
        st.dataframe(pd.DataFrame(g["qual_results"]), hide_index=True, use_container_width=True, height=170)
        if g["lap"]:
            if g["lap"] == 1:
                replay = 1
                st.caption("Replay slider unlocks after lap 2.")
            else: replay = st.slider("Replay lap", 1, g["lap"], g["lap"])
            st.dataframe(pd.DataFrame(g["snapshots"][replay-1]), hide_index=True, use_container_width=True, height=220)
            st.download_button("Download all timing CSV", pd.DataFrame([r for s in g["snapshots"] for r in s]).to_csv(index=False), "f1_race_timing.csv", "text/csv")

with right:
    st.markdown("### 🎧 Race engineer")
    st.caption(f"Weather: **{g['weather']}** · Tire age: **{mine['age']:.1f}** · Stops: **{mine['stops']}**")
    if not g["finished"]:
        next_lap = g["lap"] + 1
        st.write(f"**Plan lap {next_lap} of {g['total']}**")
        mode = st.radio("Pace", ["Balanced", "Push", "Conserve"], horizontal=True, key=f"mode_{next_lap}")
        pit_choice = st.selectbox("Pit decision", ["Stay out", "Soft", "Medium", "Hard", "Intermediate", "Wet"], key=f"pit_{next_lap}")
        if pit_choice == "Stay out":
            # No pit challenge for laps without a pit stop.
            if g["pit_challenge"] is not None:
                g["pit_challenge"] = None
            if st.button("▶ RUN NEXT LAP", type="primary", use_container_width=True):
                sim_lap(g, "Stay out", mode)
                st.rerun()
        else:
            ch = g["pit_challenge"]
            if ch is None or ch["lap"] != next_lap:
                if st.button("🔧 START PIT-CREW CHALLENGE", type="primary", use_container_width=True):
                    g["pit_challenge"] = {"lap": next_lap, "targets": new_targets(g), "started": time.monotonic()}
                    st.rerun()
                st.caption("Hit three alignment marks quickly and accurately. Precision and speed determine pit-stop time.")
            else:
                st.markdown("**🔧 Pit stop minigame: align the equipment!**")
                st.caption("Match each orange target with its slider, then press COMPLETE PIT STOP.")
                answers = []
                for i, (label, target) in enumerate(zip(["Front jack", "Left wheel", "Right wheel"], ch["targets"])):
                    st.caption(f"{label} · TARGET {target}")
                    answers.append(st.slider(label, 0, 100, 50, key=f"pit_align_{next_lap}_{i}", label_visibility="collapsed"))
                if st.button("✅ COMPLETE PIT STOP & RUN LAP", type="primary", use_container_width=True):
                    elapsed = time.monotonic() - ch["started"]
                    stationary, grade = pit_quality(ch["targets"], answers, elapsed)
                    sim_lap(g, pit_choice, mode, stationary)
                    g["events"].insert(0, f"🏆 Pit crew: {grade} · {stationary:.2f}s stationary · {elapsed:.1f}s challenge time")
                    st.rerun()
                if st.button("Cancel challenge"):
                    g["pit_challenge"] = None
                    st.rerun()
        if not g["was_wet"] and len(set(mine["used"]) & DRY) < 2:
            st.info("Strategy goal: use 2 different dry compounds in a dry race.")
    else:
        rule_ok = g["was_wet"] or len(set(mine["used"]) & DRY) >= 2
        grade = max(0, 100 - (0 if rule_ok else 25) - max(0, mine["stops"] - 3) * 5)
        st.success(f"🏁 Finished P{position} · Strategy score {grade}/100")
        st.caption("Simplified strategy score; a good choice can still produce a bad race result.")
        st.write("Tire rule:", "✅" if rule_ok else "❌")
        reflection = st.text_area("What would you change next race?")
        report = f"F1 The Pit Wall\nDriver: {g['player']}\nCircuit: {g['track']}\nFinish: P{position}\nStrategy score: {grade}/100\nMean lap: {stats[2]:.2f}s\nPit stops: {mine['stops']}\nReflection: {reflection}\n"
        st.download_button("Download coaching report", report, "f1_coach_report.txt", "text/plain", use_container_width=True)
    if g["events"]:
        with st.container(border=True):
            st.markdown("**📻 Race control**")
            for event in g["events"][:3]: st.caption(event)
    if st.button("🔄 New race", use_container_width=True):
        st.session_state.pit_wall_v3 = None
        st.rerun()

st.caption("Educational simulation: current drivers are real, race times/qualifying/pit stops are modeled, and circuit shapes are illustrative. Race tracker updates once per completed lap.")
