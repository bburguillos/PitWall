import html
import json
import random
import time
import math
import io
import datetime
from statistics import mean, median

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

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
[data-testid="stMetric"] {background:#17253b !important; border:1px solid #415674; padding:9px 12px; border-radius:10px}
[data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricLabel"], [data-testid="stMetric"] [data-testid="stMetricLabel"] * {color:#c8d7ec !important; opacity:1 !important}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {color:#ffffff !important; opacity:1 !important}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {opacity:1 !important}
div.stButton > button[kind="primary"] {background:#ff7a2c; color:#141414; font-weight:800}
</style>""", unsafe_allow_html=True)


def build_forecast(seed, track, laps):
    """A fictional forecast issued at race start; probabilities are not outcomes."""
    rng = random.Random(f"forecast-{seed}")
    climate = TRACKS[track][3]
    # Reduced forecast rain probabilities by 50% in Version 10.
    # A slowly evolving weather front creates meaningful multi-lap risk.
    pressure = rng.uniform(-.10, .17)
    result = []
    for lap in range(1, laps + 1):
        pressure = max(-.20, min(.69, .78 * pressure + rng.uniform(-.13, .16)))
        # Track baseline adds dry/wet climate variety. Clamp for readability.
        probability = max(.01, min(.44, (max(.02, min(.88, climate * 1.6 + pressure))) * .50))
        result.append(round(probability, 3))
    return result


def rain_outlook(g):
    """Return upcoming lap-specific risk of precipitation, not a certainty."""
    return [
        (i + 1, g["forecast"][i])
        for i in range(g["lap"], min(g["total"], g["lap"] + 4))
    ]


def weather_strategy(g):
    """A separate weather briefing; never promises a future outcome."""
    upcoming = rain_outlook(g)
    if not upcoming:
        return "Race complete", "No upcoming forecast laps."
    risk = upcoming[0][1]
    near = max((p for _, p in upcoming[:3]), default=risk)
    driver = you(g)
    if g["weather"] == "Wet":
        return "Wet track", "Wet tires are favored now. Monitor the forecast for drying before changing back."
    if g["weather"] == "Damp":
        if risk >= .45:
            return "Rain may intensify", "Intermediates are a reasonable choice; wet tires could pay off if rain builds, but the forecast is uncertain."
        return "Damp track", "Intermediates suit current conditions. Check the next-lap rain chance before switching to slicks."
    if risk >= .65:
        return "High rain risk", "Rain is likely next lap, but the track is still dry. Consider whether a stop now is worth its time cost."
    if near >= .48:
        return "Possible weather change", "Rain risk increases within 3 laps. A short dry-tire stint may be better than committing to a long run."
    if driver["tire"] not in DRY:
        return "Track currently dry", "Dry tires are faster now. Don't keep wet-weather tires solely because rain is possible."
    return "Mostly dry outlook", "Slick tires are favored now, but keep watching the updated forecast."


def forecast_display(g):
    rows = rain_outlook(g)
    if not rows:
        st.caption("Race complete — no future forecast laps.")
        return
    st.markdown("**🌧️ Weather radar · next laps**")
    st.caption("Forecast probabilities are simulated. They indicate a chance of rain, not a guaranteed change in track conditions.")
    for lap, prob in rows:
        left, right = st.columns([1, 3], vertical_alignment="center")
        left.markdown(f"**L{lap}** · {prob:.0%}")
        right.progress(prob)
    heading, advice = weather_strategy(g)
    st.markdown(f"**{heading}:** {advice}")


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
                forecast=build_forecast(seed, track, laps), weather_history=[],
                stage="qualifying", lap=0, weather="Dry", was_wet=False,
                safety=False, drivers=drivers, events=[], entries=[],
                snapshots=[], qual_results=[], pit_challenge=None, finished=False, qual_practice=None, qual_score=None,
                start_at=None, lights_out_at=None, launch_result=None, start_delay=0.0, launch_reaction=None,
                race_log=[], engineer_choices=[], sector_data=None, incidents=[], strategy_notes=[], championship_awarded=False)


def ranking(g):
    return sorted(g["drivers"], key=lambda d: d["elapsed"])


def you(g):
    return next(d for d in g["drivers"] if d["name"] == g["player"])


def sector_reference(g):
    """Simulated sector times for a small data-driven qualifying decision."""
    rng = random.Random(f"sectors-{g['seed']}")
    base = TRACKS[g["track"]][0] / 3
    return [round(base + rng.uniform(-1.4, 1.4), 2) for _ in range(3)]


def start_lights(g):
    rng = random.Random(f"startlights-{g['seed']}")
    now = time.time()
    g["start_at"] = now
    g["lights_out_at"] = now + 5 * 0.65 + rng.uniform(0.75, 2.1)
    g["stage"] = "start"


def register_launch(g):
    now = time.time()
    delta = now - g["lights_out_at"]
    if delta < 0:
        result, penalty = "JUMP START — +5 seconds", 5.0
    elif delta < 0.25:
        result, penalty = f"EXCELLENT REACTION — {delta:.2f}s", -0.45
    elif delta < 0.55:
        result, penalty = f"GOOD START — {delta:.2f}s", -0.15
    elif delta < 1.2:
        result, penalty = f"CLEAN START — {delta:.2f}s", 0.12
    else:
        result, penalty = f"SLOW START — {delta:.2f}s", min(2.5, .12 + (delta - 1.2) * .4)
    you(g)["elapsed"] += penalty
    g["start_delay"] = round(penalty, 3)
    g["launch_reaction"] = round(delta, 3)
    g["launch_result"] = result
    g["events"] = ["🚦 " + result]
    g["stage"] = "race"


# Fragment keeps the five lights refreshing without rerendering the entire dashboard.
# Timings include browser/network latency and are NOT competition-grade measurements.
@st.fragment(run_every=0.2)
def light_challenge(g):
    now = time.time()
    elapsed = now - g["start_at"]
    illuminated = min(5, max(0, int(elapsed / 0.65) + 1))
    if now >= g["lights_out_at"]:
        illuminated = 0
    lights = " ".join("🔴" if i < illuminated else "⚫" for i in range(5))
    st.markdown(f"<div style='font-size:2.3rem;text-align:center;padding:10px;background:#14253b;border-radius:14px'>{lights}</div>", unsafe_allow_html=True)
    st.caption("Five red lights, then LIGHTS OUT. Avoid an early click! Browser/network delay affects measured reaction time.")
    if now >= g["lights_out_at"]:
        st.success("LIGHTS OUT — GO!")
    elif illuminated == 5:
        st.warning("All five lights on. Wait until they go out!")
    else:
        st.info(f"Lights illuminated: {illuminated}/5")
    if st.button("🚀 LAUNCH!", type="primary", use_container_width=True):
        register_launch(g)
        st.rerun()


def overtake_outcome(g, mode, tactic, rng, events):
    """Risk/reward adjustment; position still comes from elapsed race times."""
    me = you(g)
    cars = ranking(g)
    idx = next(i for i, d in enumerate(cars) if d is me)
    ahead = cars[idx-1] if idx else None
    behind = cars[idx+1] if idx+1 < len(cars) else None
    if tactic == "Attack" and ahead:
        gap = me["elapsed"] - ahead["elapsed"]
        if gap <= 2.5:
            wear = min(1.5, me["age"] / max(1, expected_life(g, me["tire"])))
            chance = min(.78, max(.13, .58 - .14 * gap - .10 * wear + (.10 if mode == "Push" else 0)))
            success = rng.random() < chance
            if success:
                me["elapsed"] -= gap + rng.uniform(.09, .32)
                events.append(f"🏎️ OVERTAKE: Attack worked ({chance:.0%} estimate)!")
            else:
                me["elapsed"] += rng.uniform(.2, .9)
                events.append(f"🏎️ Attack failed ({chance:.0%} estimate); time lost")
        else:
            events.append("Attack selected, but rival is too far away for a passing attempt")
    elif tactic == "Defend" and behind:
        gap = behind["elapsed"] - me["elapsed"]
        if gap < 2.0:
            me["elapsed"] -= .16
            me["age"] += .25
            events.append("🛡️ Defensive driving: slight time advantage, extra tire wear")
        else:
            events.append("Defend selected; no immediate threat behind")


def incident_outcome(g, rng, events):
    """Low-frequency events. Red flags cause a neutralized lap with no racing advantage."""
    roll = rng.random()
    if roll < .025:
        events.append("🟥 RED FLAG: race neutralized; everyone loses similar time")
        for d in g["drivers"]:
            d["elapsed"] += 35.0
        g["incidents"].append({"Lap": g["lap"]+1, "Event": "Red flag"})
    elif roll < .07:
        events.append("🟨 Yellow flags after an incident: drivers slow down")
        for d in g["drivers"]:
            d["elapsed"] += 6.0
        g["incidents"].append({"Lap": g["lap"]+1, "Event": "Yellow flag"})


def championship_table(history):
    points = [25,18,15,12,10,8,6,4,2,1]
    total = {name:0 for name,_,_ in GRID}
    for race in history:
        for position, name in enumerate(race["finish"], 1):
            if position <= 10: total[name] += points[position - 1]
    return pd.DataFrame([{"Driver":n, "Team":TEAM[n], "Points":pt} for n,pt in total.items()]).sort_values(["Points","Driver"], ascending=[False, True])


def qualify(g, mode, tire, accuracy_score=0):
    rng = random.Random(f"qual-{g['seed']}")
    base = TRACKS[g["track"]][0]
    for d in g["drivers"]:
        dr_mode = mode if d["name"] == g["player"] else rng.choice(["Balanced", "Push"])
        dr_tire = tire if d["name"] == g["player"] else "Soft"
        adjustment = {"Push": -.65, "Balanced": 0., "Conserve": .55}[dr_mode]
        if d["name"] == g["player"]:
            adjustment -= 0.12 * accuracy_score  # small reward for correct statistics
        compound = {"Soft": -1., "Medium": -.15, "Hard": .45}[dr_tire]
        d["qual"] = round(base + d["skill"] + compound + adjustment + rng.gauss(0, .48), 3)
    order = sorted(g["drivers"], key=lambda d: d["qual"])
    g["qual_results"] = [dict(Grid=i, Driver=d["name"], Team=d["team"],
                               **{"Qualifying lap": f"{d['qual']:.3f}s"})
                         for i, d in enumerate(order, 1)]
    # Racing offsets use grid gaps, not raw qualifying lap-time differences.
    for i, d in enumerate(order):
        d["elapsed"] = i * 1.25
    start_lights(g)
    g["events"] = ["🏁 Qualifying complete! Get ready for five red lights."]


# Estimated useful tire life: classroom model, not manufacturer data.
# A driver can exceed it, but the lap-time penalty becomes increasingly expensive.
TIRE_LIFE = {"Soft": 11, "Medium": 19, "Hard": 29, "Intermediate": 13, "Wet": 17}


def expected_life(g, compound):
    return max(3, round(TIRE_LIFE[compound] / TRACKS[g["track"]][2]))


def qualifying_practice(g):
    rng = random.Random(f"practice-{g['seed']}")
    base = TRACKS[g["track"]][0] - 1.1
    # Five one-decimal lap times with deliberately repeated values so mode exists.
    offsets = rng.sample([-0.6, -0.3, 0.0, 0.3, 0.6], 4)
    offsets.append(rng.choice(offsets))
    rng.shuffle(offsets)
    return [round(base + x, 1) for x in offsets]


def evaluate_qualifying(practice, answers):
    counts = {v: practice.count(v) for v in set(practice)}
    most = max(counts.values())
    modal = min(k for k, v in counts.items() if v == most)
    correct = [mean(practice), median(practice), modal, max(practice) - min(practice)]
    return sum(abs(a - c) <= 0.051 for a, c in zip(answers, correct)), correct


def proximity(g):
    cars = ranking(g)
    p = next(i for i, d in enumerate(cars) if d["name"] == g["player"])
    mytime = cars[p]["elapsed"]
    ahead = (cars[p-1]["name"], max(0., mytime - cars[p-1]["elapsed"])) if p else None
    behind = (cars[p+1]["name"], max(0., cars[p+1]["elapsed"] - mytime)) if p < len(cars)-1 else None
    return ahead, behind


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


def sim_lap(g, pit_tire, mode, stationary=None, tactic="Balanced", engineer_follow=False):
    lap = g["lap"] + 1
    rng = random.Random(f"race-{g['seed']}-{lap}")
    base, pit_loss, wear, _, _ = TRACKS[g["track"]]
    w = g["weather"]
    rain_chance = g["forecast"][lap - 1]
    # Forecast sets a probability; the outcome is sampled independently.
    is_raining = rng.random() < rain_chance
    if w == "Dry" and is_raining:
        g["weather"] = "Damp"
    elif w == "Damp":
        if is_raining and rng.random() < .65:
            g["weather"] = "Wet"
        elif not is_raining and rng.random() < .50:
            g["weather"] = "Dry"
    elif w == "Wet" and not is_raining and rng.random() < .65:
        g["weather"] = "Damp"
    g["weather_history"].append({"Lap": lap, "Rain chance": round(100 * rain_chance), "Rained": "Yes" if is_raining else "No", "Track": g["weather"]})
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
            worn = d["age"] > expected_life(g, d["tire"])
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
    incident_outcome(g, rng, events)
    overtake_outcome(g, mode, tactic, rng, events)
    ranked = ranking(g)
    leader = ranked[0]["elapsed"]
    for i, d in enumerate(ranked, 1): d["history"][-1]["Position"] = i
    position = next(i for i, d in enumerate(ranked, 1) if d is driver)
    g["snapshots"].append([dict(Lap=lap, Pos=i, Driver=d["name"], Team=d["team"], Gap=round(d["elapsed"]-leader, 2), Tire=d["tire"], Stops=d["stops"], Time=d["history"][-1]["Time"]) for i, d in enumerate(ranked, 1)])
    g["entries"].append(dict(Lap=lap, Time=driver["history"][-1]["Time"], Pos=position,
                             Gap=round(driver["elapsed"]-leader, 2), Tire=driver["tire"],
                             Drive=mode, Pit=pit_tire, PitLoss=round(actual_pit, 2), Tactic=tactic, FollowEngineer=engineer_follow, Weather=g["weather"], RainChance=f"{rain_chance:.0%}", SafetyCar=g["safety"]))
    g["lap"], g["events"] = lap, events
    g["pit_challenge"] = None
    g["engineer_choices"].append({"Lap":lap,"Followed recommendation":engineer_follow,"Tactic":tactic,"Driving pace":mode,"Tires":pit_tire})
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
*{box-sizing:border-box}
body{margin:0;background:#0b1422;font-family:Inter,Arial,sans-serif;color:#edf2fa}
.main{border:1px solid #425673;border-radius:14px;padding:11px 13px;background:radial-gradient(ellipse at 75% 22%,#1c354d 0%,#111d2f 65%);height:255px;overflow:hidden}
.header{display:flex;justify-content:space-between;align-items:center;gap:9px}
.title{font-size:16px;font-weight:900;letter-spacing:.35px}.live{font-size:10px;font-weight:800;color:#ffb36d;border:1px solid #b56828;border-radius:20px;padding:4px 7px;white-space:nowrap}
.sub{font-size:11px;color:#abbcd2;margin:4px 0}
svg{display:block;width:100%;height:173px;background:radial-gradient(ellipse,#172940,#0b1627);border-radius:9px}
.legend{font-size:10px;color:#a9bed5;display:flex;justify-content:space-between;margin-top:5px}
</style></head><body><div class="main"><div class="header"><div class="title">🏁 __TITLE__ <span style="color:#ff8b38">GP</span></div><span class="live">● RACE TRACKER</span></div>
<div class="sub">Your car glows orange · Hover any marker to see its driver</div>
<svg viewBox="0 0 380 220"><defs><filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><pattern id="grid" width="18" height="18" patternUnits="userSpaceOnUse"><path d="M 18 0 L 0 0 0 18" fill="none" stroke="#2b3c51" stroke-width=".5" opacity=".45"/></pattern></defs>
<rect width="380" height="220" fill="url(#grid)"/>
<path id="shadow" fill="none" stroke="#050910" stroke-width="25" stroke-linecap="round" stroke-linejoin="round" />
<path id="route" fill="none" stroke="#405267" stroke-width="19" stroke-linecap="round" stroke-linejoin="round" />
<path id="inner" fill="none" stroke="#edf1f7" stroke-width="11" stroke-linecap="round" stroke-linejoin="round" />
<path id="centerline" fill="none" stroke="#8897aa" stroke-width="1.5" stroke-dasharray="3 7" opacity=".6" />
<g id="cars"></g></svg>
<div class="legend"><span>🟠 PLAYER · Other colors = rivals</span><span>12 cars shown · updates each lap</span></div></div><script>
const path=__PATH__, cars=__CARS__;
for(const id of ['shadow','route','inner','centerline'])document.getElementById(id).setAttribute('d',path);
const route=document.getElementById('route');const length=route.getTotalLength();const layer=document.getElementById('cars');
for(const c of cars){const p=route.getPointAtLength(length*c.fraction);const group=document.createElementNS('http://www.w3.org/2000/svg','g');
if(c.mine){const halo=document.createElementNS('http://www.w3.org/2000/svg','circle');halo.setAttribute('cx',p.x);halo.setAttribute('cy',p.y);halo.setAttribute('r',13);halo.setAttribute('fill','#ff872d');halo.setAttribute('opacity','.23');halo.setAttribute('filter','url(#glow)');group.appendChild(halo)}
const e=document.createElementNS('http://www.w3.org/2000/svg','circle');e.setAttribute('cx',p.x);e.setAttribute('cy',p.y);e.setAttribute('r',c.mine?7:5);e.setAttribute('fill',c.color);e.setAttribute('stroke',c.mine?'#fff':'#0c1420');e.setAttribute('stroke-width',c.mine?'2.6':'1.4');
const tip=document.createElementNS('http://www.w3.org/2000/svg','title');tip.textContent='P'+c.pos+' '+c.name;e.appendChild(tip);group.appendChild(e);layer.appendChild(group)}
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




def recent_pace(driver, window=3):
    """Mean of the most recent green-flag laps, excluding major weather changes."""
    history = driver["history"]
    if not history:
        return None
    # Compare only like-for-like conditions, using the latest weather.
    current_weather = history[-1]["Weather"]
    candidates = [h["Time"] for h in history if h["Weather"] == current_weather]
    if not candidates:
        return None
    return mean(candidates[-window:])


def engineering_report(g):
    """Data-grounded advice; forecasts are simplified estimates, not known outcomes."""
    driver = you(g)
    cars = ranking(g)
    index = next(i for i, d in enumerate(cars) if d is driver)
    remaining = g["total"] - g["lap"]
    ahead = cars[index - 1] if index > 0 else None
    behind = cars[index + 1] if index + 1 < len(cars) else None
    my_pace = recent_pace(driver)
    wear_limit = expected_life(g, driver["tire"])
    wear_ratio = driver["age"] / wear_limit
    messages = []
    details = []
    recommendation = "Balanced"
    pit_advice = "Stay out"
    urgent = False
    if not g["entries"]:
        return {
            "headline": "Gather baseline data",
            "reason": "Run a lap to establish your race pace and learn where you stand.",
            "recommendation": recommendation,
            "pit": pit_advice,
            "details": ["Your starting grid is set by qualifying; on-track pace has not yet been measured."],
            "severity": "info",
        }
    if my_pace is not None:
        details.append(f"Your recent mean: {my_pace:.2f}s/lap (last up to 3 laps in current weather).")
    if ahead and my_pace is not None:
        gap = driver["elapsed"] - ahead["elapsed"]
        rival_pace = recent_pace(ahead)
        if rival_pace is not None:
            gain = rival_pace - my_pace
            if gain > 0.08:
                laps_to_catch = gap / gain
                details.append(f"Ahead: {ahead['name']} +{gap:.2f}s; estimated gain {gain:.2f}s/lap.")
                details.append(f"At unchanged pace, approximate catch-up: {laps_to_catch:.1f} laps (not guaranteed).")
                if laps_to_catch < remaining and wear_ratio < .72:
                    messages.append("You are catching the car ahead. Keep your current pace rather than taking unnecessary risks.")
            elif gain < -0.08:
                details.append(f"Ahead: {ahead['name']} +{gap:.2f}s; they are faster by approximately {-gain:.2f}s/lap.")
                messages.append("The car ahead has been faster recently. An alternative tire strategy may help.")
            else:
                details.append(f"Ahead: {ahead['name']} +{gap:.2f}s; recent pace is nearly equal.")
    if behind and my_pace is not None:
        gap = behind["elapsed"] - driver["elapsed"]
        rival_pace = recent_pace(behind)
        if rival_pace is not None:
            close_rate = my_pace - rival_pace
            if close_rate > .08:
                laps_until = gap / close_rate
                details.append(f"Behind: {behind['name']} +{gap:.2f}s; closing ~{close_rate:.2f}s/lap.")
                if laps_until <= min(remaining, 4) and wear_ratio < .7:
                    messages.append(f"The car behind could catch you in about {laps_until:.1f} laps if pace stays constant.")
                    recommendation = "Push"
            else:
                details.append(f"Behind: {behind['name']} +{gap:.2f}s; not closing quickly on current pace.")
    if g["weather"] == "Wet" and driver["tire"] in DRY:
        urgent = True
        pit_advice = "Wet"
        messages.insert(0, "Heavy rain with dry tires: a wet-weather compound is strongly favored.")
    elif g["weather"] == "Damp" and driver["tire"] in DRY and wear_ratio >= .5:
        pit_advice = "Intermediate"
        messages.insert(0, "The track is damp; intermediates may be worth considering if conditions persist.")
    elif g["weather"] == "Dry" and driver["tire"] not in DRY:
        urgent = True
        pit_advice = "Medium" if remaining <= expected_life(g, "Medium") else "Hard"
        messages.insert(0, "Dry weather is making wet-weather tires costly. Consider switching to slicks.")
    elif wear_ratio >= .95 and remaining > 1:
        urgent = True
        pit_advice = "Medium" if remaining <= expected_life(g, "Medium") else "Hard"
        messages.insert(0, "Tires have exceeded most of their expected useful life. Plan a stop.")
    elif wear_ratio >= .76 and remaining >= 3:
        recommendation = "Conserve"
        messages.insert(0, "Tire wear is high. Conserve pace while deciding whether a pit stop pays off.")
    if not g["was_wet"] and len(set(driver["used"]) & DRY) < 2:
        next_dry = "Hard" if driver["tire"] != "Hard" else "Medium"
        if remaining <= 3:
            urgent = True
            pit_advice = next_dry
            messages.insert(0, f"Dry-tire compound requirement: use {next_dry} before finishing.")
        else:
            details.append("Dry race: you still need a second dry compound.")
    if not messages:
        messages.append("No urgent threat detected. Focus on consistent laps and monitor gaps.")
    return {
        "headline": "Pit wall alert" if urgent else "Strategy briefing",
        "reason": messages[0],
        "recommendation": recommendation,
        "pit": pit_advice,
        "details": details + messages[1:],
        "severity": "warning" if urgent else "info",
    }


def make_pdf_report(g, finishing_position, grade, reflection=""):
    """Create a one-page printable classroom race report in memory."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(612, 792))
    dark = HexColor("#17253B")
    orange = HexColor("#E9762D")
    gray = HexColor("#5B6677")
    pdf.setFillColor(dark)
    pdf.rect(0, 712, 612, 80, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(42, 752, "F1: THE PIT WALL")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(42, 730, "SPORTS BY THE NUMBERS  |  RACE STRATEGY REPORT")
    pdf.setFillColor(dark)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(42, 685, f"Driver: {g['player']}")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(42, 663, f"Circuit: {g['track']}   |   Laps: {g['lap']}   |   Finish: P{finishing_position}")
    pdf.drawString(42, 643, f"Strategy score: {grade}/100   |   Stops: {you(g)['stops']}")
    pdf.setStrokeColor(orange)
    pdf.line(42, 625, 570, 625)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(42, 602, "RACE START")
    pdf.setFont("Helvetica", 11)
    reaction = g.get('launch_reaction')
    pdf.drawString(42, 582, f"Reaction: {reaction:.3f} seconds" if reaction is not None else "Reaction: not recorded")
    delay = g.get('start_delay', 0)
    pdf.drawString(42, 564, f"Start adjustment: {delay:+.2f} seconds (negative = bonus)")
    result = g.get('launch_result') or 'Not recorded'
    pdf.drawString(42, 546, result[:85])
    times = [float(e['Time']) for e in g['entries']]
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(42, 511, "LAP-TIME INVESTIGATION")
    pdf.setFont("Helvetica", 11)
    if times:
        pdf.drawString(42, 490, f"Mean: {mean(times):.2f}s     Median: {median(times):.2f}s     Range: {max(times)-min(times):.2f}s")
        pdf.drawString(42, 471, f"Fastest: {min(times):.2f}s     Slowest: {max(times):.2f}s")
    else:
        pdf.drawString(42, 490, "No completed laps")
    pdf.drawString(42, 448, f"Tire compounds used: {', '.join(dict.fromkeys(you(g)['used']))}")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(42, 413, "KEY STRATEGY DECISIONS")
    pdf.setFont("Helvetica", 10)
    y = 392
    for row in g.get('engineer_choices', [])[-8:]:
        line = f"Lap {row.get('Lap')}: {row.get('Driving pace')} | {row.get('Tactic')} | {row.get('Tires')}"
        pdf.drawString(46, y, line[:105])
        y -= 18
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(42, 226, "STUDENT REFLECTION")
    pdf.setFont("Helvetica", 10)
    from reportlab.lib.utils import simpleSplit
    lines = simpleSplit(reflection or "What choice helped you most, and what evidence supports it?", "Helvetica", 10, 520)
    for j, line in enumerate(lines[:4]):
        pdf.drawString(46, 207 - j * 16, line)
    pdf.setStrokeColor(HexColor('#D5DEE8'))
    pdf.line(42, 95, 570, 95)
    pdf.setFillColor(gray)
    pdf.setFont('Helvetica-Oblique', 9)
    pdf.drawString(42, 79, "Real driver names; race timing, weather and outcomes are simulated for learning.")
    pdf.drawString(42, 64, "Reaction time includes network delay; not a laboratory-grade measurement.")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def launch_feedback(g):
    """Persistent feedback after the five-light challenge."""
    if not g.get('launch_result'):
        return
    change = float(g.get('start_delay', 0))
    reaction = g.get('launch_reaction')
    if change < 0:
        headline = '🚀 LAUNCH BONUS'
        explanation = f'{abs(change):.2f} seconds removed from your starting race time.'
        kind = 'success'
    elif change >= 5:
        headline = '🚨 JUMP START PENALTY'
        explanation = f'{change:.2f} seconds added to your starting race time.'
        kind = 'error'
    else:
        headline = '🏁 START COMPLETED'
        explanation = f'{change:.2f} seconds added to your starting race time.'
        kind = 'warning' if change > 0.5 else 'info'
    reading = f'Reaction: {reaction:.3f}s' if reaction is not None else 'Reaction not recorded'
    text = f"**{headline}**  ·  {reading}  ·  {explanation}"
    getattr(st, kind)(text)


def gap_projection(g, laps=3):
    """Display recent race pace and simple forward gap scenarios."""
    driver = you(g)
    ordered = ranking(g)
    idx = next(i for i, d in enumerate(ordered) if d is driver)
    mine = recent_pace(driver)
    if mine is None:
        return pd.DataFrame()
    rows = []
    for label, other, gap_now in [
        ("Car ahead", ordered[idx-1] if idx > 0 else None,
         driver["elapsed"] - ordered[idx-1]["elapsed"] if idx > 0 else None),
        ("Car behind", ordered[idx+1] if idx+1 < len(ordered) else None,
         ordered[idx+1]["elapsed"] - driver["elapsed"] if idx+1 < len(ordered) else None),
    ]:
        if other is None:
            continue
        rival = recent_pace(other)
        if rival is None:
            continue
        closing = rival - mine if label == "Car ahead" else mine - rival
        rows.append({
            "Rival": label + ": " + other["name"],
            "Gap now (s)": round(gap_now, 2),
            "Your mean (s)": round(mine, 2),
            "Rival mean (s)": round(rival, 2),
            "Gain/loss per lap (s)": round(closing, 2),
            f"Gap after {laps} laps (s)": round(max(0, gap_now - closing * laps), 2),
        })
    return pd.DataFrame(rows)

st.title("🏎️ F1: THE PIT WALL · V9")
st.caption("Sports by the Numbers • 2026 driver names • fictional race performance • simplified track outlines")

if "pit_wall_v3" not in st.session_state:
    st.session_state.pit_wall_v3 = None

if st.session_state.pit_wall_v3 is None:
    st.subheader("Grand Prix setup")
    st.caption("Expected tire life is an educational estimate; aggressive driving uses tires faster.")
    a, b, c = st.columns([2, 1, 2])
    track = a.selectbox("Circuit", list(TRACKS))
    laps = b.slider("Race laps", 8, 30, 14)
    driver = c.selectbox("Your driver", [d[0] for d in GRID], format_func=lambda n: f"{n} · {TEAM[n]}")
    st.info("🚦 This weekend includes interactive sector qualifying and a five-red-lights reaction start. No repeated statistics quiz.")
    st.info("🌦️ This circuit's simulated rain climate: " + f"{TRACKS[track][3]:.0%} baseline. During the race, a changing probabilistic weather forecast will influence tire strategy.")
    st.markdown("**Estimated useful laps per tire at this circuit**")
    st.dataframe(pd.DataFrame([{"Tire": TIRE_SYMBOL[t] + " " + t, "Expected useful laps": expected_life({"track": track}, t)} for t in TIRE_LIFE]), hide_index=True, use_container_width=True)
    if st.button("🏁 BEGIN QUALIFYING", type="primary", use_container_width=True):
        st.session_state.pit_wall_v3 = new_game(track, laps, driver)
        st.rerun()
    st.stop()

g = st.session_state.pit_wall_v3
mine = you(g)
if g["stage"] == "qualifying":
    st.subheader(f"⏱️ Qualifying · {g['track']}")
    st.caption("Choose how to approach your flying lap. Compare the three practice sectors and identify where the biggest improvement is possible.")
    if g["sector_data"] is None:
        g["sector_data"] = sector_reference(g)
    sectors = g["sector_data"]
    cols = st.columns(3)
    for i, col in enumerate(cols):
        col.metric(f"Practice sector {i+1}", f"{sectors[i]:.2f}s")
    slow = max(range(3), key=lambda i: sectors[i])
    with st.form("qualifying_strategy"):
        focus = st.radio("Where would you focus on finding lap time?", ["Sector 1", "Sector 2", "Sector 3"], horizontal=True)
        tire = st.radio("Qualifying compound", ["Soft","Medium","Hard"], horizontal=True)
        mode = st.radio("Qualifying attack mode", ["Balanced","Push","Conserve"], horizontal=True)
        st.caption("Statistic tip: the highest sector time is the slowest sector, although the most improvement is not always guaranteed there.")
        submit = st.form_submit_button("🏁 SET FLYING LAP & QUALIFY", type="primary", use_container_width=True)
    if submit:
        correct = (int(focus[-1])-1) == slow
        g["qual_score"] = int(correct)
        qualify(g, mode, tire, int(correct))
        st.rerun()
    if st.button("New weekend"):
        st.session_state.pit_wall_v3 = None
        st.rerun()
    st.stop()

if g["stage"] == "start":
    st.subheader("🚦 GRAND PRIX START · FIVE RED LIGHTS")
    st.write(f"**{g['player']} — Starting grid position P" + str(next(i for i, d in enumerate(sorted(g['drivers'],key=lambda d:d['qual']),1) if d['name']==g['player'])))
    st.caption("Your reaction directly changes the starting race time. You will see the exact bonus or penalty on the race dashboard and PDF report.")
    light_challenge(g)
    st.stop()

ordered = ranking(g)
position = next(i for i, d in enumerate(ordered, 1) if d is mine)
stats = timer_stats(g)
ahead, behind = proximity(g)
engineer = engineering_report(g)

# Compact control tower: critical actions are in the first screen.
st.markdown("""<style>
/* V10 broadcast styling while preserving the compact V9 layout */
.stApp {background:linear-gradient(150deg,#09111e 0%,#111b30 65%,#0e1726 100%)}
div[data-testid="stDataFrame"] {border:1px solid #33465d;border-radius:10px;overflow:hidden}
[data-testid="stMetric"] {box-shadow:inset 0 2px 0 rgba(255,129,44,.38),0 3px 10px rgba(0,0,0,.14)}
[data-testid="stMetricValue"] {font-weight:850 !important}
div.stButton > button[kind="primary"] {background:linear-gradient(90deg,#ff8c35,#ff5d1d) !important;border:0 !important;box-shadow:0 4px 16px rgba(255,105,32,.25)}
div[data-testid="stTabs"] button {font-weight:700}
.block-container {padding-top:.3rem !important; max-width:1800px !important}
h1 {font-size:1.5rem !important; margin:0 !important; padding:0 !important}
h3 {font-size:1.05rem !important; margin:.15rem 0 !important; padding:0 !important}
[data-testid="stMetric"] {padding:5px 8px !important; min-height:64px !important}
[data-testid="stMetricValue"] {font-size:1.18rem !important}
[data-testid="stMetricLabel"] {font-size:.68rem !important}
[data-testid="stVerticalBlock"] {gap:.45rem !important}
[data-testid="stHorizontalBlock"] {gap:.55rem !important}
div[data-testid="stRadio"] label {padding:0 !important}
div.stButton > button[kind="primary"] {min-height:48px; font-size:1.05rem}
</style>""", unsafe_allow_html=True)

labels = ["LAP", "POSITION", "LAST", "MEAN", "BEST", "GAP AHEAD", "TIRE"]
values = [f"{g['lap']}/{g['total']}", f"P{position}/22",
          f"{stats[0]:.2f}s" if stats else "—",
          f"{stats[2]:.2f}s" if stats else "—",
          f"{stats[1]:.2f}s" if stats else "—",
          f"{ahead[1]:.2f}s" if ahead else "LEADER",
          f"{TIRE_SYMBOL[mine['tire']]} {mine['tire']}"]
for col, label, value in zip(st.columns(7, gap="small"), labels, values):
    col.metric(label, value)

# Persistent start feedback: visible on every race lap, not lost in event logs.
launch_feedback(g)

# Three primary panels keep everything needed to run a lap on screen.
track_col, timing_col, control_col = st.columns([1.08, 1.04, 1.08], gap="small")

with track_col:
    st.markdown("### 🗺️ Circuit tracker")
    circuit_map(g)
    st.markdown("**🏎️ Nearest rivals**")
    if ahead:
        st.caption(f"⬆ {ahead[0]} · **{ahead[1]:.2f}s ahead**")
    else:
        st.caption("🥇 You're currently leading")
    if behind:
        st.caption(f"⬇ {behind[0]} · **{behind[1]:.2f}s behind**")
    st.markdown("**🛞 Tire wear**")
    life = expected_life(g, mine["tire"])
    wear_percent = min(100, round(100 * mine["age"] / life))
    st.progress(wear_percent / 100, text=f"{wear_percent}% used · {mine['age']:.1f}/{life} expected laps")

with timing_col:
    st.markdown("### 📊 Live timing")
    rows = []
    leader = ordered[0]["elapsed"]
    for i, d in enumerate(ordered, 1):
        rows.append({"P":i,"Driver":("★ " if d is mine else "")+d["name"],
                     "Gap": "LEAD" if i == 1 else f"+{d['elapsed']-leader:.1f}",
                     "Tire":TIRE_SYMBOL[d["tire"]]})
    # Show the nearest cars, and all cars in the detailed tab below.
    lo = max(0, position - 4)
    hi = min(22, max(8, position + 3))
    st.dataframe(pd.DataFrame(rows[lo:hi]), use_container_width=True,
                 hide_index=True, height=232)
    st.markdown("**⏱️ Latest lap comparisons**")
    if g["entries"]:
        df = pd.DataFrame(g["entries"])
        df["Change"] = df["Time"].diff().map(lambda x: f"{x:+.2f}s" if pd.notna(x) else "—")
        df = df.sort_values("Lap", ascending=False)
        st.dataframe(df[["Lap", "Time", "Change", "Pos"]].head(4),
                     hide_index=True, use_container_width=True, height=177)
    else:
        st.caption("Run lap 1 to see the latest lap at the top.")

with control_col:
    st.markdown("### 🎧 Pit wall controls")
    next_lap = g["lap"] + 1
    outlook = rain_outlook(g)
    if outlook:
        st.caption("🌦️ " + " · ".join(f"L{lap} **{prob:.0%}** rain" for lap,prob in outlook[:3]) + f" · Track: **{g['weather']}**")
    st.caption(f"📻 **Engineer:** {engineer['reason']}")
    st.caption(f"Suggested: **{engineer['recommendation']}** · Tires: **{engineer['pit']}**")

    if not g["finished"]:
        st.markdown(f"**PLAN LAP {next_lap} / {g['total']}**")
        mode = st.radio("Driving pace", ["Balanced", "Push", "Conserve"],
                        horizontal=True, key=f"mode_{next_lap}")
        tactic = st.radio("Track battle", ["Balanced", "Attack", "Defend"], horizontal=True, key=f"battle_{next_lap}")
        follow = st.checkbox("Follow engineer recommendation", value=False, key=f"follow_{next_lap}", help="Documents your decision for the report card; you can still choose your own controls.")
        pit_choice = st.selectbox("Tire / pit decision",
                    ["Stay out", "Soft", "Medium", "Hard", "Intermediate", "Wet"],
                    key=f"pit_{next_lap}")
        if pit_choice == "Stay out":
            if g["pit_challenge"] is not None:
                g["pit_challenge"] = None
            if st.button("▶ RUN NEXT LAP", type="primary", use_container_width=True):
                sim_lap(g, "Stay out", mode, tactic=tactic, engineer_follow=follow)
                st.rerun()
        else:
            ch = g["pit_challenge"]
            if ch is None or ch["lap"] != next_lap:
                if st.button("🔧 START PIT STOP", type="primary", use_container_width=True):
                    g["pit_challenge"] = {"lap":next_lap,"targets":new_targets(g),"started":time.monotonic()}
                    st.rerun()
            else:
                st.caption("Match three slider targets to complete your pit stop.")
                answers = []
                for i,(label,target) in enumerate(zip(["Front jack","Left wheel","Right wheel"],ch["targets"])):
                    answers.append(st.slider(f"{label} · target {target}",0,100,50,key=f"pit_align_{next_lap}_{i}"))
                if st.button("✅ COMPLETE PIT STOP & RUN LAP", type="primary", use_container_width=True):
                    elapsed = time.monotonic()-ch["started"]
                    stationary,grade = pit_quality(ch["targets"], answers, elapsed)
                    sim_lap(g,pit_choice,mode,stationary,tactic=tactic,engineer_follow=follow)
                    g["events"].insert(0,f"Pit crew: {grade} · {stationary:.2f}s stationary")
                    st.rerun()
                if st.button("Cancel pit stop"):
                    g["pit_challenge"] = None
                    st.rerun()
        if not g["was_wet"] and len(set(mine["used"]) & DRY) < 2:
            st.caption("⚠️ Dry race: plan to use two different dry compounds.")
    else:
        rule_ok = g["was_wet"] or len(set(mine["used"]) & DRY)>=2
        grade=max(0,100-(0 if rule_ok else 25)-max(0,mine["stops"]-3)*5)
        st.success(f"🏁 Finished P{position} · Strategy score {grade}/100")
        if not g["championship_awarded"]:
            if "f1_championship" not in st.session_state:
                st.session_state.f1_championship = []
            st.session_state.f1_championship.append({"track":g["track"],"finish":[d["name"] for d in ranking(g)]})
            g["championship_awarded"] = True
        st.caption(f"Championship weekends recorded: {len(st.session_state.f1_championship)}")
        reflection=st.text_area("What would you change next time?")
        report=(f"F1 The Pit Wall\nDriver: {g['player']}\nCircuit: {g['track']}\n"
                f"Finish: P{position}\nStrategy score: {grade}\n"
                f"Mean lap: {stats[2]:.2f}s\nPit stops: {mine['stops']}\nReflection: {reflection}\n")
        report += (f"Launch: {g['launch_result']}\nWeather history: {g['weather_history']}\n"
                   f"Strategy decisions: {g['engineer_choices']}\n")
        st.download_button("Download coach report",report,"f1_coach_report.txt","text/plain",use_container_width=True)
        pdf_bytes = make_pdf_report(g, position, grade, reflection)
        st.download_button("📄 Download printable PDF report", pdf_bytes, "f1_strategy_report.pdf", "application/pdf", use_container_width=True)
    if g["events"]:
        st.caption("📻 " + " | ".join(g["events"][:2]))
    if st.button("🔄 New race", use_container_width=True):
        st.session_state.pit_wall_v3 = None
        st.rerun()

# Secondary screens: no need to scroll here during ordinary racing.
st.divider()
full_timing, lap_data, weather_tab, strategy_tab, season_tab = st.tabs([
    "🏎️ Full timing", "📈 Lap history", "🌦️ Weather radar", "🧠 Engineer & analysis", "🏆 Championship"
])
with full_timing:
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=425)
    st.dataframe(pd.DataFrame(g["qual_results"]), hide_index=True, use_container_width=True, height=180)
with lap_data:
    if g["entries"]:
        df = pd.DataFrame(g["entries"])
        st.line_chart(df.set_index("Lap")[["Time"]], height=235)
        st.dataframe(df.sort_values("Lap",ascending=False), hide_index=True,use_container_width=True,height=250)
        if g["lap"] > 1:
            replay = st.slider("Replay lap",1,g["lap"],g["lap"])
            st.dataframe(pd.DataFrame(g["snapshots"][replay-1]),hide_index=True,use_container_width=True)
        st.download_button("Download all timing",pd.DataFrame([r for snap in g["snapshots"] for r in snap]).to_csv(index=False),"f1_race_timing.csv","text/csv")
with weather_tab:
    forecast_display(g)
    if g["weather_history"]:
        st.dataframe(pd.DataFrame(g["weather_history"][::-1]),hide_index=True,use_container_width=True)
with strategy_tab:
    st.write(engineer["reason"])
    for detail in engineer["details"]:
        st.write("• " + detail)
    st.markdown("**🎧 Ask your engineer**")
    question = st.selectbox("Race question", [
        "Can I catch the car ahead?",
        "Should I pit soon?",
        "How many laps can these tires last?",
        "What if I pit now (undercut)?",
        "Should I follow the weather forecast?",
    ], key="engineer_question")
    mydriver = you(g)
    front, back = proximity(g)
    if question == "Can I catch the car ahead?":
        if front and g["lap"]:
            rival = next(d for d in g["drivers"] if d["name"] == front[0])
            my_mean, rival_mean = recent_pace(mydriver), recent_pace(rival)
            gain = (rival_mean - my_mean) if my_mean is not None and rival_mean is not None else 0
            if gain > .05:
                st.info(f"Gap: {front[1]:.2f}s. You gain about {gain:.2f}s/lap. Estimate: {front[1]/gain:.1f} laps to catch if pace remains similar.")
            else:
                st.info(f"Gap: {front[1]:.2f}s. Recent pace does not support predicting that you'll catch the next car without a change.")
        else:
            st.info("No car ahead, or not enough laps to compare yet.")
    elif question == "Should I pit soon?":
        life = expected_life(g, mydriver["tire"])
        st.info(f"Your tire age is {mydriver['age']:.1f}/{life} expected laps. {engineer['reason']} Typical pit loss is roughly {TRACKS[g['track']][1]:.0f}s, plus or minus stop execution and neutralizations.")
    elif question == "How many laps can these tires last?":
        life = expected_life(g, mydriver["tire"])
        st.info(f"Estimated remaining useful life: {max(0,life-mydriver['age']):.1f} laps at comparable wear. Push mode increases wear; this estimate is not a hard failure threshold.")
    elif question == "What if I pit now (undercut)?":
        pit_loss = TRACKS[g["track"]][1]
        fresh_advantage = max(.1, mydriver["age"] * TIRE_WEAR[mydriver["tire"]] * TRACKS[g["track"]][2] + .45)
        recover = pit_loss / fresh_advantage
        st.info(f"A new tire might save ~{fresh_advantage:.2f}s/lap compared with your worn current tire. Recovering a normal ~{pit_loss:.1f}s pit loss would then take ~{recover:.1f} laps. This is a simplified undercut estimate, not a guarantee: rivals may pit too, and the weather may change.")
    else:
        head, advice = weather_strategy(g)
        st.info(f"{head}: {advice} Look at probability rather than assuming rain is certain.")
    st.write("**Projected future gaps**")
    projection = gap_projection(g, min(3,max(1,g["total"]-g["lap"])))
    if not projection.empty:
        st.dataframe(projection,hide_index=True,use_container_width=True)
    st.write("**Estimated tire life**")
    st.dataframe(pd.DataFrame([{"Tire":TIRE_SYMBOL[t]+" "+t,"Expected laps":expected_life(g,t)} for t in TIRE_LIFE]),hide_index=True,use_container_width=True)

with season_tab:
    with st.expander("📂 Resume a saved championship"):
        uploaded_season = st.file_uploader("Upload saved championship JSON", type=["json"], key="restore_champ_v9")
        if uploaded_season is not None and st.button("Restore championship", key="restore_championship_v9"):
            try:
                restored = json.load(uploaded_season)
                if not isinstance(restored, list) or not all(isinstance(r, dict) and isinstance(r.get("finish"), list) and isinstance(r.get("track"), str) for r in restored):
                    raise ValueError("Not a valid championship export")
                st.session_state.f1_championship = restored
                st.rerun()
            except (ValueError, TypeError, json.JSONDecodeError) as err:
                st.error(f"Could not restore championship: {err}")
    races = st.session_state.get("f1_championship", [])
    if races:
        st.dataframe(championship_table(races), hide_index=True, use_container_width=True, height=350)
        st.caption("Official-style points (25–18–15–12–10–8–6–4–2–1). Export your season to keep it between sessions.")
        st.download_button("💾 Save championship progress", json.dumps(races, indent=2), "f1_championship.json", "application/json")
    else:
        st.caption("Finish a race to begin the championship.")
    if g["entries"]:
        times = [row["Time"] for row in g["entries"]]
        st.markdown(f"**Your data:** Mean {mean(times):.2f}s · Median {median(times):.2f}s · Range {max(times)-min(times):.2f}s")
        st.write("**Reflection:** Which decision was supported by data? Which result might have been due to luck?")
    if g["incidents"]:
        st.dataframe(pd.DataFrame(g["incidents"]), hide_index=True)

st.caption("Educational simulator: qualifying, start lights, weather, overtakes and race incidents use simplified or simulated data. Reaction timing includes network latency.")
