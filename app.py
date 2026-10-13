import streamlit as st
import random
import math
import csv
import io
from datetime import datetime

st.set_page_config(page_title='F1: The Pit Wall | Sports by the Numbers', page_icon='🏎️', layout='wide', initial_sidebar_state='collapsed')

TRACKS = {
    'Monza — Speed Temple': {'base': 83.0, 'pit': 21, 'wear': 1.0, 'start_rain': 0.07},
    'Silverstone — Fast Corners': {'base': 91.5, 'pit': 23, 'wear': 1.22, 'start_rain': 0.19},
    'Spa — Ardennes': {'base': 105.0, 'pit': 24, 'wear': 1.1, 'start_rain': 0.23},
    'Singapore — Street Circuit': {'base': 102.0, 'pit': 27, 'wear': 1.4, 'start_rain': 0.18},
}
DRIVERS = ['YOU · Tiger Racing', 'Apex Motorsport', 'Velocity GP', 'Falcon Racing', 'Orbit F1', 'Comet Autosport']
COLORS = {'Soft':'#ff4c5b','Medium':'#ffd34a','Hard':'#d6dee7','Intermediate':'#51c987','Wet':'#4b96e8'}
DRY = {'Soft', 'Medium', 'Hard'}
PACE = {'Soft': -1.15,'Medium': 0.0,'Hard': 0.8,'Intermediate': 2.6,'Wet': 4.9}
WEAR = {'Soft':0.28,'Medium':0.14,'Hard':0.072,'Intermediate':0.15,'Wet':0.12}

st.markdown('''<style>
.stApp {background:#090f1c; color:#eaf0fa}
.block-container {padding-top:0.8rem; padding-bottom:3rem; max-width:1540px}
h1,h2,h3 {color:#fff!important}
[data-testid="stMetric"] {background:#151e31; border:1px solid #273248; border-radius:12px; padding:10px 16px}
[data-testid="stMetricLabel"] {color:#bac5d7}
div.stButton > button[kind="primary"] {background:#ff6b24; color:#111; border:0; font-weight:800}
.pill {display:inline-block; background:#17233b; border:1px solid #33435f; border-radius:40px; padding:4px 13px; font-size:.85rem; margin-right:8px}
.head {padding:16px 22px; border-radius:14px; background:linear-gradient(120deg,#141f32,#232031); border-left:7px solid #ff6b24; margin-bottom:12px}
.track {background:#121b2b; border:1px solid #303b50; border-radius:16px; padding:15px 18px;}
.track-line {display:flex; align-items:center; gap:10px; margin:5px 0; font-size:0.89rem}
.track-bar {position:relative; height:22px; background:#283349; border-radius:15px; flex:1; overflow:hidden}
.car {position:absolute; top:2px; height:18px; min-width:46px; border-radius:9px; background:#5c86fd; color:#fff; font-size:11px; text-align:center; padding-top:1px; font-weight:bold}
.small {color:#afbed2; font-size:0.86rem}
</style>''', unsafe_allow_html=True)


def make_game(track_name, laps, seed, start_tire):
    rng = random.Random(seed)
    details = TRACKS[track_name]
    rain = rng.random() < details['start_rain']
    drivers = []
    for i, name in enumerate(DRIVERS):
        tire = start_tire if i == 0 else rng.choice(['Medium','Hard','Soft'])
        drivers.append(dict(name=name, elapsed=(i * 0.65 if i else 0.0), tire=tire, age=0, stops=0,
                            used=[tire], pace_skill=0.0 if i==0 else rng.uniform(-.75,.9), history=[],
                            plan='Balanced'))
    return dict(track=track_name, total=laps, lap=0, weather='Wet' if rain else 'Dry',
                safety=False, seed=seed, drivers=drivers, entries=[], events=[],
                pending_tire='Stay out', mode='Balanced', saved_decisions=[], finished=False,
                rain_chance=0.17 if rain else 0.09, forecast='Unsettled' if rain else 'Mostly dry',
                initial_tire=start_tire)


def new_weather(g, rng):
    previous=g['weather']; change=rng.random()
    if previous=='Dry' and change < .085: g['weather']='Damp'
    elif previous=='Damp' and change < .33: g['weather']='Wet'
    elif previous=='Damp' and change > .69: g['weather']='Dry'
    elif previous=='Wet' and change > .74: g['weather']='Damp'
    if g['weather'] != previous:
        g['events'].append(f"🌦️ Track conditions changed: {previous} → {g['weather']}.")


def lap_time(g, driver, rng, mode, under_sc):
    circuit=TRACKS[g['track']]
    tire=driver['tire']; weather=g['weather']; age=driver['age']
    baseline=circuit['base']+PACE[tire]+WEAR[tire]*age*circuit['wear']
    penalty=0.0
    if weather == 'Dry' and tire == 'Intermediate': penalty=6.0
    if weather == 'Dry' and tire == 'Wet': penalty=10.0
    if weather == 'Damp' and tire in DRY: penalty=3.8 + (.08*age)
    if weather == 'Damp' and tire == 'Wet': penalty=2.0
    if weather == 'Wet' and tire in DRY: penalty=13.5
    if weather == 'Wet' and tire == 'Intermediate': penalty=2.0
    baseline += penalty + driver['pace_skill']
    if mode=='Push': baseline-=.75; driver['age']+=1.65
    elif mode=='Conserve': baseline+=.65; driver['age']+=.62
    else: driver['age']+=1
    if under_sc: baseline=baseline*1.27+3
    return max(1.0,baseline+rng.gauss(0,.36 if not under_sc else .15))


def simulate(g, pit_choice, mode):
    if g['finished']: return
    lap_num=g['lap']+1
    rng=random.Random(f"{g['seed']}:{lap_num}")
    g['events']=[]
    new_weather(g,rng)
    # A fictional safety-car event, with slower laps and a smaller pit-stop penalty.
    g['safety']=(rng.random() < .11)
    if g['safety']: g['events'].append('🚨 SAFETY CAR! Field slows and pit-loss is reduced.')
    pit_loss=TRACKS[g['track']]['pit']*(.53 if g['safety'] else 1)
    user = g['drivers'][0]
    before_age=user['age']; old_tire=user['tire']; lap_results=[]
    if pit_choice!='Stay out':
        user['elapsed']+=pit_loss; user['tire']=pit_choice; user['age']=0
        user['used'].append(pit_choice); user['stops']+=1
        g['events'].append(f"🔧 You pit for {pit_choice} tyres (+{pit_loss:.1f}s).")
    for i,d in enumerate(g['drivers']):
        this_mode=mode if i==0 else ('Push' if rng.random()<.23 else 'Balanced')
        if i>0:
            # Simple fictional AI decision model, never pretending to be a real team strategy.
            t=d['tire']; w=g['weather']; remaining=g['total']-lap_num
            must_switch=(remaining<=2 and w=='Dry' and len(set(d['used']) & DRY)<2)
            wrong=(w=='Wet' and t not in ('Wet','Intermediate')) or (w=='Dry' and t not in DRY)
            old=d['age']>(12 if t=='Soft' else 20 if t=='Medium' else 31)
            if must_switch or wrong or (old and remaining>3):
                next_tire=('Wet' if w=='Wet' else 'Intermediate' if w=='Damp' else 'Hard' if t!='Hard' else 'Medium')
                d['elapsed']+=pit_loss; d['tire']=next_tire; d['age']=0
                d['used'].append(next_tire); d['stops']+=1
        t=lap_time(g,d,rng,this_mode,g['safety'])
        d['elapsed']+=t
        d['history'].append(dict(lap=lap_num, time=round(t,2), tire=d['tire'], weather=g['weather'], position=None))
        lap_results.append(t)
    ranking=sorted(g['drivers'],key=lambda d:d['elapsed'])
    for pos,d in enumerate(ranking,1): d['history'][-1]['position']=pos
    position=next(i for i,d in enumerate(ranking,1) if d['name']==DRIVERS[0])
    g['lap']=lap_num
    g['entries'].append(dict(lap=lap_num, weather=g['weather'], safety=g['safety'], action=pit_choice,
                             mode=mode, previous_tire=old_tire, previous_age=round(before_age,1),
                             user_time=round(lap_results[0],2), position=position,
                             gap=round(user['elapsed']-ranking[0]['elapsed'],2)))
    if lap_num==g['total']:
        g['finished']=True
        if g['weather']=='Dry' and len(set(user['used']) & DRY)<2:
            g['events'].append('⚠️ Classroom rule violation: you did not use two different dry tyre compounds.')
        else: g['events'].append('🏁 Checkered flag! Race complete.')


def report(g):
    e=g['entries']; user=g['drivers'][0]
    pos=next(i for i,d in enumerate(sorted(g['drivers'],key=lambda x:x['elapsed']),1) if d['name']==DRIVERS[0])
    rule_ok=not (g['weather']=='Dry' and len(set(user['used']) & DRY)<2)
    laps=[x['user_time'] for x in e]
    avg=sum(laps)/len(laps) if laps else 0
    # Transparent, deterministic teaching rubric; results do not determine strategy quality.
    score=100
    warnings=[]
    for row in e:
        t=g['drivers'][0]['history'][row['lap']-1]['tire']
        if row['weather']=='Wet' and t in DRY: score-=8; warnings.append('Dry tyres used on a wet lap')
        if row['weather']=='Dry' and t in ('Intermediate','Wet'): score-=8; warnings.append('Wet-weather tyres used on a dry lap')
        if row['previous_age']>18 and row['previous_tire']=='Soft' and row['action']=='Stay out': score-=3
    if not rule_ok: score-=25; warnings.append('Two-compound dry-race requirement not met')
    if user['stops']>math.ceil(g['total']/5)+1: score-=8; warnings.append('Many pit stops')
    score=max(0,min(100,score))
    return score,pos,avg,rule_ok,sorted(set(warnings))


def draw_positions(g):
    ranking=sorted(g['drivers'],key=lambda d:d['elapsed'])
    leader=ranking[0]['elapsed']
    max_gap=max(max(d['elapsed']-leader for d in ranking),5)
    rows=[]
    for idx,d in enumerate(ranking,1):
        gap=d['elapsed']-leader
        pct=max(4,92-80*gap/max_gap)
        color='#ff6b24' if d['name']==DRIVERS[0] else '#547ac8'
        rows.append(f'''<div class="track-line"><span style="width:22px">P{idx}</span>
          <span style="width:142px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{d['name']}</span>
          <div class="track-bar"><div class="car" style="left:{pct-4:.1f}%;background:{color}">🏎️</div></div>
          <span style="width:78px;text-align:right">{'+%.1fs'%gap if gap else 'LEADER'}</span></div>''')
    st.markdown('<div class="track">' + ''.join(rows) + '</div>',unsafe_allow_html=True)


st.markdown('<div class="head"><div style="font-size:0.8rem;color:#ffa66d;letter-spacing:2px;font-weight:800">SPORTS BY THE NUMBERS • RACE STRATEGY LAB</div><h1 style="margin:1px 0 0">🏎️ F1: THE PIT WALL</h1><div class="small">Make the call. Read the data. Beat the field.</div></div>',unsafe_allow_html=True)

if 'game' not in st.session_state:
    st.session_state.game=None

if st.session_state.game is None:
    st.subheader('Set up your Grand Prix')
    a,b,c=st.columns([2,1,1])
    with a: circuit=st.selectbox('Circuit',list(TRACKS))
    with b: laps=st.slider('Race length (laps)',8,30,14,2)
    with c: first=st.selectbox('Starting tyre',['Medium','Soft','Hard'])
    st.info('Classroom simulation: tracks have approximate fictional baseline lap times, and competitors, probabilities, tyre wear, weather, and race events are simulated—not live F1 data. No account or API key needed.')
    if st.button('🏁 START GRAND PRIX', type='primary',use_container_width=True):
        st.session_state.game=make_game(circuit,laps,random.SystemRandom().randrange(10**9),first)
        st.rerun()
    st.stop()

g=st.session_state.game
user=g['drivers'][0]
ranking=sorted(g['drivers'],key=lambda d:d['elapsed'])
position=next(i for i,d in enumerate(ranking,1) if d['name']==DRIVERS[0])

header=st.columns([1,1,1,1,1])
for col,label,value in zip(header,['LAP','POSITION','WEATHER','YOUR TYRES','PIT STOPS'],
                           [f"{g['lap']} / {g['total']}",f'P{position} / 6',g['weather'],f"{user['tire']} · {user['age']:.0f} laps",user['stops']]):
    with col: st.metric(label,value)

left,right=st.columns([1.55,1],gap='medium')
with left:
    st.markdown('### 🏁 Live Race Tracker')
    draw_positions(g)
    if g['entries']:
        last=g['entries'][-1]
        st.caption(f"Last lap: {last['user_time']:.2f}s  •  Strategy: {last['mode']}  •  P{last['position']}  •  {'Safety car' if last['safety'] else 'Green flag'}")
    st.markdown('### 📊 Timing & Tyre History')
    if g['entries']:
        import pandas as pd
        df=pd.DataFrame(g['entries'])
        chart_df=df.set_index('lap')[['user_time']]
        st.line_chart(chart_df,height=168)
        with st.expander('Lap-by-lap data table'):
            st.dataframe(df[['lap','user_time','position','weather','safety','action','mode','gap']],use_container_width=True,hide_index=True)
    else:
        st.caption('Drive the first lap to see your times and race position change.')
with right:
    st.markdown('### 🎧 Your Pit Wall')
    if not g['finished']:
        remaining=g['total']-g['lap']
        st.caption(f'{remaining} laps remaining • Pit loss: ~{TRACKS[g["track"]]["pit"]} seconds under green (reduced during safety car)')
        if g['weather']=='Wet':
            st.warning('Wet track: wet tyres are the safest pace choice in this simplified model.')
        elif g['weather']=='Damp':
            st.info('Damp track: intermediates often have an advantage.')
        elif user['tire'] in ('Intermediate','Wet'):
            st.warning('Dry track: intermediates and wets are much slower.')
        pit=st.selectbox('Tyre decision for next lap',['Stay out','Soft','Medium','Hard','Intermediate','Wet'],key=f'pit_{g["lap"]}')
        mode=st.segmented_control('Driving style',['Conserve','Balanced','Push'],default='Balanced',key=f'mode_{g["lap"]}') or 'Balanced'
        st.caption('Push: faster, greater tyre wear. Conserve: slower, less wear. Every pit costs time.')
        if st.button('▶️ RUN NEXT LAP',type='primary',use_container_width=True):
            simulate(g,pit,mode)
            st.rerun()
        need_two=len(set(user['used']) & DRY)<2
        if g['weather']=='Dry' and need_two:
            st.warning('🏷️ Dry-race rule: use at least two different dry tyre compounds before finishing.')
    else:
        score,pos,avg,rule_ok,warnings=report(g)
        st.success(f'🏁 Finished P{pos}! Strategy grade: {score}/100')
        st.metric('Average lap',f'{avg:.2f}s')
        st.caption('The strategy grade is based on decisions, not simply your finishing place.')
        st.write('Dry tyre rule: ' + ('✅ met' if rule_ok else '❌ not met (in this simplified model)'))
        if warnings:
            for w in warnings: st.warning(w)
        reflection=st.text_area('Student reflection: What decision would you change and why?',key='reflection',height=88)
        text_report=(f"F1: THE PIT WALL — COACH REPORT\nCircuit: {g['track']}\nLaps: {g['total']}\n"
                     f"Position: P{pos} of 6\nStrategy score: {score}/100\nAvg lap: {avg:.2f}s\n"
                     f"Pit stops: {user['stops']}\nTyres used: {', '.join(user['used'])}\n"
                     f"Two dry compounds satisfied: {rule_ok}\nReflection: {reflection}\n\n"
                     + '\n'.join(f"Lap {x['lap']}: {x['user_time']:.2f}s; {x['weather']}; P{x['position']}; pit {x['action']}; {x['mode']}" for x in g['entries']))
        st.download_button('📄 Download coach report (.txt)',text_report,file_name='f1_coach_report.txt',mime='text/plain',use_container_width=True)
        import pandas as pd
        st.download_button('📊 Download lap data (.csv)',pd.DataFrame(g['entries']).to_csv(index=False),file_name='f1_lap_data.csv',mime='text/csv',use_container_width=True)
    if g['events']:
        st.markdown('### 📻 Race Control')
        for e in g['events'][-3:]: st.write(e)
    with st.expander('🔎 Tyre guide / math help'):
        st.markdown('''**Soft:** quick when fresh, wears fastest. **Medium:** balanced. **Hard:** slower fresh, lasts longer. **Intermediate:** damp/light rain. **Wet:** heavy rain.\n\n**Average lap time** = total lap seconds ÷ laps completed.\n\n**Gap to leader** = your total elapsed seconds − leader's total elapsed seconds.\n\n**Example:** Is saving 0.7 seconds per lap for 8 laps worth a 21-second pit stop? Compare 0.7 × 8 = 5.6 seconds to 21 seconds.''')
    if st.button('🔄 New race',use_container_width=True):
        st.session_state.game=None
        st.rerun()

st.divider()
st.caption('Teaching model only • fictional teams/drivers, calibrated for strategy practice rather than historical accuracy • general two-dry-compound rule simplified: Monaco and several official race exceptions are not modeled • dry/wet conditions may change. Source: FIA 2026 Sporting Regulations, Article B6.3.6.')

