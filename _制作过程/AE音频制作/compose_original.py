"""Original procedural electronic score. No reference audio is used in this render."""
from pathlib import Path
import sys, json, csv, argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'_pydeps'))
import numpy as np
from scipy import signal
import soundfile as sf

parser=argparse.ArgumentParser()
parser.add_argument('--bars',type=int,default=33)
parser.add_argument('--bpm',type=float,default=116)
args=parser.parse_args()
SR=48000; BPM=args.bpm; BEAT=60/BPM; BAR=BEAT*4; BARS=args.bars
SCENE_BARS=[3,4,4,7,3,4,3,5]
SCENE_STARTS=np.cumsum([0]+SCENE_BARS[:-1]).tolist()
def section_at(bar): return int(np.searchsorted(SCENE_STARTS,bar,side='right')-1)
DURATION=BARS*BAR; N=int(round(DURATION*SR)); rng=np.random.default_rng(10142026)
tracks={k:np.zeros((N,2),dtype=np.float32) for k in ['drums','bass','keys','melody','pad','fx']}
def hz(note): return 440*2**((note-69)/12)
def timer(d): return np.arange(int(round(d*SR)),dtype=np.float64)/SR
def hp(y,cut): return signal.sosfilt(signal.butter(2,cut,fs=SR,btype='highpass',output='sos'),y)
def lp(y,cut): return signal.sosfilt(signal.butter(2,cut,fs=SR,btype='lowpass',output='sos'),y)
def envelope(t,a,d,s,r,dur):
    env=np.minimum(1,t/max(a,1e-4))
    env*=np.where(t<a,1,s+(1-s)*np.exp(-(t-a)/max(d,1e-4)))
    env*=np.minimum(1,np.maximum(0,(dur-t)/max(r,1e-4)))
    return env
def place(track,y,start,gain=1,pan=0):
    i=int(round(start*SR)); offset=max(0,-i);i=max(0,i)
    y=y[offset:offset+max(0,min(len(y)-offset,N-i))]
    if not len(y): return
    if y.ndim==1:
        tracks[track][i:i+len(y),0]+=y.astype(np.float32)*(gain*np.sqrt((1-pan)/2))
        tracks[track][i:i+len(y),1]+=y.astype(np.float32)*(gain*np.sqrt((1+pan)/2))
    else: tracks[track][i:i+len(y)]+=y.astype(np.float32)*gain

def kick():
    t=timer(.46);freq=46+104*np.exp(-t/0.025)
    phase=2*np.pi*np.cumsum(freq)/SR
    body=np.sin(phase)*np.exp(-t/0.105)
    click=hp(rng.normal(size=len(t)),3400)*np.exp(-t/0.005)*.09
    return (body+click)*np.minimum(1,t/.0015)
def snare():
    t=timer(.25);noise=hp(lp(rng.normal(size=len(t)),10000),1100)
    env=(np.exp(-t/.050)+.4*np.exp(-((t-.013)/.006)**2)+.25*np.exp(-((t-.026)/.007)**2))
    body=.14*np.sin(2*np.pi*184*t)*np.exp(-t/.035)
    return (.27*noise*env+body)*np.minimum(1,t/.0008)
def hat(opened=False):
    dur=.28 if opened else .12;t=timer(dur)
    n=hp(rng.normal(size=len(t)),6500)
    metallic=.2*(np.sin(2*np.pi*8431*t)+np.sin(2*np.pi*10591*t))
    return .13*(n+metallic)*np.exp(-t/(.060 if opened else .022))*np.minimum(1,t/.0007)
def rim():
    t=timer(.11)
    return .24*(np.sin(2*np.pi*1450*t)+.5*np.sin(2*np.pi*2120*t))*np.exp(-t/.013)*np.minimum(1,t/.0007)
def shaker():
    t=timer(.10);return hp(rng.normal(size=len(t)),4800)*.07*np.sin(np.pi*np.minimum(1,t/.08))**2*np.exp(-t/.06)
def bass(note,dur):
    t=timer(dur);f=hz(note)
    y=np.sin(2*np.pi*f*t)+.25*np.sin(4*np.pi*f*t)+.10*np.sin(6*np.pi*f*t)
    return .60*np.tanh(y*.9)*envelope(t,.007,.10,.64,.055,dur)
def key(note,dur=1.4):
    t=timer(dur);f=hz(note)
    # Rounded FM pluck: a small amount of inharmonic upper tone gives a soft bell attack.
    y=np.sin(2*np.pi*f*t+.70*np.sin(2*np.pi*2*f*t)*np.exp(-t/.08))*np.exp(-t/.30)
    y+=.20*np.sin(2*np.pi*f*3.995*t)*np.exp(-t/.070)
    y+=.09*np.sin(2*np.pi*f*2.005*t)*np.exp(-t/.42)
    return y*np.minimum(1,t/.003)*np.minimum(1,(dur-t)/.09)*.45
def lead(note,dur):
    t=timer(dur);f=hz(note)
    vib=.004*np.sin(2*np.pi*4.8*t)*np.minimum(1,t/.15)
    phase=2*np.pi*np.cumsum(f*(1+vib))/SR
    y=np.sin(phase)+.17*np.sin(2*phase)+.065*np.sin(3*phase)
    return y*envelope(t,.012,.18,.16,.12,dur)*.33
def pad(notes,dur):
    t=timer(dur);out=np.zeros((len(t),2))
    env=np.minimum(1,t/.60)*np.minimum(1,np.maximum(0,(dur-t)/.72))
    for ni,note in enumerate(notes):
        f=hz(note);ph=rng.uniform(0,2*np.pi)
        for c,det in [(0,.997),(1,1.003)]:
            y=np.sin(2*np.pi*f*det*t+ph)+.16*np.sin(2*np.pi*f*2*det*t+ph*.3)
            out[:,c]+=y*env*(.022+.004*np.sin(2*np.pi*.28*t+ni))
    return out
def chime():
    y=np.zeros(int(SR*2.5))
    for n,offset in [(86,0),(81,.06),(78,.12)]:
        a=key(n,2.1);i=int(offset*SR);y[i:i+len(a)]+=.14*a
    return y

# Original harmony: Dmaj9 / Bm7 / Gmaj9 / A(sus) with a final D6/9 cadence.
chords=[[50,57,61,64,66],[47,54,57,62,66],[43,50,54,57,59],[45,52,57,59,62]]
roots=[38,35,31,33]
sections=['C03','C04','C05','C06','C07','C08','C09','C10']
energy=[.72,.83,.90,.77,.92,.88,1.0,.82]
for bar in range(min(BARS,32)):
    sec=section_at(bar);en=energy[min(sec,7)];bs=bar*BAR;ci=(bar//2)%4
    local_bar=bar-SCENE_STARTS[sec]
    # Full beat grid remains audible while orchestration changes in four-bar phrases.
    for b in [0,1,2,3]:
        amp=(.73 if b in [0,2] else .63)*en
        if sec==3:amp*=.78
        place('drums',kick(),bs+b*BEAT,amp)
    for b in [1,3]: place('drums',snare(),bs+b*BEAT,.85*en,pan=.025)
    for k in range(8):
        if sec==0 and bar==0 and k<4:continue
        vel=(.75 if k%2 else .51)*en*rng.uniform(.94,1.04)
        place('drums',hat(opened=(k==7 and bar%2==1)),bs+k*.5*BEAT,vel,pan=(-.2 if k%2 else .24))
        if sec in [2,4,6]:place('drums',shaker(),bs+(k*.5+.25)*BEAT,.55*en,pan=.44)
    if bar%2==1:place('drums',rim(),bs+2.75*BEAT,.22*en,pan=-.38)
    if bar+1 in SCENE_STARTS[1:] and bar<31:
        for b,vol in [(3.5,.27),(3.75,.22)]:place('drums',snare(),bs+b*BEAT,vol*en,pan=(b-3.6))
    root=roots[ci]
    for b,n,d in [(0,root,.65),(1.5,root,.35),(2,root+12,.43),(2.75,root+7,.28),(3.5,root,.34)]:
        place('bass',bass(n,d*BEAT+.075),bs+b*BEAT,.44*en)
    if bar%2==0:place('pad',pad(chords[ci],2*BAR+.5),bs,.72 if sec!=3 else .96)
    # Sparse syncopated keys leave reading space in each scene.
    voicing=[n+12 for n in chords[ci][1:]]
    key_pattern=[(0,0),(1.5,2),(2.5,1),(3.5,3)]
    if bar%2:key_pattern=[(.5,1),(1.5,3),(2.75,2),(3.5,0)]
    if sec==3:key_pattern=key_pattern[::2]
    for j,(b,index) in enumerate(key_pattern):
        place('keys',key(voicing[index]),bs+b*BEAT,.27*en,pan=(-.38 if j%2==0 else .34))

# Eight complementary motifs, related but different: every scene gets a phrase identity.
motifs=[
 [(0,78,.7),(1.5,81,.5),(3,83,.7),(5,81,.7),(6.5,76,.5),(8,78,1.2),(11,74,.8),(13.5,76,.5),(14.5,78,.8)],
 [(0,78,.7),(1,81,.8),(3,86,.6),(4.5,83,.8),(6,81,.8),(8.5,79,.8),(10,78,.7),(12,76,1),(14,73,.8)],
 [(0,74,.8),(2,78,.8),(3.5,81,.7),(5,83,.8),(7,81,.8),(8,83,.7),(9.5,86,1),(12,81,.8),(14,78,1)],
 [(1,78,1.1),(4,76,1.1),(7,74,1.4),(10,73,1.2),(13,76,1.2)],
 [(0,81,.7),(1.5,83,.5),(3,86,1),(5.5,83,.6),(7,81,.8),(8.5,79,.6),(10,78,.7),(12,76,1),(14,78,.8)],
 [(0,78,.6),(1,81,.6),(2.5,83,.8),(4,81,.7),(6,78,1),(8,79,.6),(9.5,78,.6),(11,76,.8),(13,73,1)],
 [(0,86,.9),(1.5,83,.6),(3,81,.8),(5,83,.7),(6.5,86,.8),(8,88,.8),(10,86,.7),(11.5,83,.7),(13,81,1.5)],
 [(0,81,1),(2,78,.9),(4,76,.9),(6,74,1.2),(9,76,.8),(11,73,.8),(13,74,1.8)]
]
for sec,motif in enumerate(motifs):
    if SCENE_STARTS[sec]>=BARS:break
    for b,n,l in motif:
        if sec==0 and b<3:continue
        musical_bars=4 if sec==7 else SCENE_BARS[sec]
        stretch=musical_bars/4
        place('melody',lead(n,min(l*stretch,1.8)*BEAT+.32),(SCENE_STARTS[sec]*4+b*stretch)*BEAT,.32*energy[sec],pan=.07)
    if sec>0:place('fx',chime(),SCENE_STARTS[sec]*BAR,.22,pan=-.08)

# Soft reverse sweeps announce visual changes without masking the motif.
for section in range(1,8):
    dur=BEAT*1.8;t=timer(dur)
    sweep=hp(lp(rng.normal(size=len(t)),5800),1900)
    sweep*=np.sin(np.minimum(1,t/dur)*np.pi/2)**3
    sweep*=np.minimum(1,(dur-t)/.018)
    place('fx',sweep,SCENE_STARTS[section]*BAR-dur,.014,pan=-.22)

if BARS>32:
    # Final extra bar: resolved logo card with a gentle cadence and a natural decay.
    start=32*BAR
    place('drums',kick(),start,.43)
    place('bass',bass(38,1.0),start,.27)
    for note in [62,66,69,71,76]:place('keys',key(note,1.95),start,.14,pan=(note-69)/22)
    place('melody',lead(74,1.9),start,.24,pan=.04)
    place('pad',pad([50,57,62,66,71],BAR),start,.9)
    place('fx',chime(),start,.12)

# Gentle sidechain breathing shared by harmonic instruments.
t=np.arange(N)/SR
phase=np.mod(t,BEAT)
duck=1-.19*np.exp(-phase/.082)
for name in ['bass','keys','pad']: tracks[name]*=duck[:,None].astype(np.float32)

# Stereo delay and diffuse short reflections: natural space with a stable mono centre.
wet=np.zeros((N,2),np.float32)
send=.21*tracks['keys']+.25*tracks['melody']+.10*tracks['pad']+.08*tracks['fx']
for delay,weight,flip in [(.071,.36,True),(.113,.31,False),(.179,.26,True),(.233,.23,False),(.307,.20,True),(.389,.17,False),(.463,.14,True),(.557,.12,False),(.647,.10,True),(.773,.08,False),(.883,.065,True),(1.027,.05,False)]:
    i=int(delay*SR);wet[i:]+=send[:-i,::-1] * weight if flip else send[:-i]*weight
for mult,gain in [(0.75,.11),(1.5,.054),(2.25,.023)]:
    i=int(BEAT*mult*SR);wet[i:]+=tracks['melody'][:-i,::-1]*gain
mix=sum(tracks.values())+wet
# Avoid clicks at exact file bounds and give the cadence its final breath.
fadein=int(.006*SR);fadeout=int(.23*SR)
mix[:fadein]*=np.linspace(0,1,fadein)[:,None]
mix[-fadeout:]*=np.linspace(1,0,fadeout)[:,None]**1.5
mix=lp(mix.T,19000).T if False else mix
raw_peak=float(np.max(np.abs(mix)));mix*=.78/max(raw_peak,1e-9)
fname=f'ORIGINAL_LightTech_{BPM:g}BPM_{BARS}bars_premaster.wav'
sf.write(ROOT/fname,mix,SR,subtype='PCM_24')

markers=[]
for beat in range(BARS*4):
    bar=beat//4;within=beat%4
    sec=section_at(bar);is_start=within==0 and bar in SCENE_STARTS
    markers.append({'beat':beat+1,'bar':bar+1,'beat_in_bar':within+1,'time_seconds':round(beat*BEAT,9),'scene':sections[sec],'is_scene_start':is_start,'label':sections[sec] if is_start else ('FINAL_CADENCE' if bar==32 and within==0 else '')})
meta={'title':'New Connections / 新的连接','composer':'Original procedural composition for C03-C10','source_audio_used':False,'contains_speech':False,'bpm':BPM,'meter':'4/4','sample_rate':SR,'bars':BARS,'duration_seconds':N/SR,'beat_seconds':BEAT,'bar_seconds':BAR,'key':'D major','scenes':[{'name':s,'bars':SCENE_BARS[i],'start':SCENE_STARTS[i]*BAR,'end':(SCENE_STARTS[i]+SCENE_BARS[i])*BAR} for i,s in enumerate(sections)],'markers':markers}
(ROOT/'C03-C10_music_beatmap.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
with (ROOT/'C03-C10_music_beats.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=markers[0].keys());writer.writeheader();writer.writerows(markers)
print(json.dumps({'output':str(ROOT/fname),'sample_frames':N,'duration_seconds':N/SR,'peak_before_normalization':raw_peak,'peak_written':float(np.max(np.abs(mix))),'rms_written':float(np.sqrt(np.mean(mix**2)))},ensure_ascii=False,indent=2))
