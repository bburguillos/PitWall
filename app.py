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
