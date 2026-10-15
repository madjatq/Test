from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'_pydeps'))
import numpy as np
from scipy import signal
from scipy.io import wavfile
sr,x=wavfile.read(ROOT/'reference_analysis.wav');x=x.astype(float)/32768
z=np.load(ROOT/'reference_onsets.npz');t=z['t'];e=z['mid'][0];high=z['side'][2]
bpm=115.914;beat=60/bpm;bar=beat*4
phase=[]
for env in [e,high]:
    env=env-np.mean(env)
    phase.append((-np.angle(np.sum(env*np.exp(-2j*np.pi*t/beat)))/(2*np.pi/beat))%beat)
print('beat phases low/high',phase)
for sec in range(0,196,2):
    a=x[int(sec*sr):int(min(sec+2,len(x)/sr)*sr)]
    if sec<12 or sec>174:print('rms',sec,float(np.sqrt(np.mean(a*a))))
# The phase from the broadband onset is compensated by the STFT's analysis-centre offset.
# Refine individual transient times from local low-band energy around this global grid.
mono=x.mean(axis=1)
low=signal.sosfilt(signal.butter(3,190,fs=sr,output='sos'),mono)
win=int(.006*sr)
power=np.convolve(low*low,np.ones(win)/win,'same')
grid=[]
for k in range(int((len(x)/sr-phase[0])/beat)):
    target=phase[0]+k*beat
    a=max(0,int((target-.055)*sr));b=min(len(power),int((target+.055)*sr))
    pos=a+int(np.argmax(power[a:b]))
    grid.append({'i':k,'predicted':target,'local_energy_peak':pos/sr,'peak':float(power[pos])})
print('first grid',grid[:16]);print('last grid',grid[-24:])
for m in range(4):print('downbeat_phase_strength',m,float(np.mean([g['peak'] for g in grid if g['i']%4==m])))
(ROOT/'reference_grid_analysis.json').write_text(json.dumps({'bpm':bpm,'beat':beat,'phases':phase,'grid':grid},indent=2),encoding='utf8')
