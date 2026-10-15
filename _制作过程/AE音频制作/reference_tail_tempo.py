from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'_pydeps'))
import numpy as np
from scipy.signal import find_peaks
from scipy.io import wavfile
z=np.load(P/'reference_onsets.npz');t=z['t'];e=z['side'][2]
for lo,hi in [(120,191),(126,190),(2,68)]:
    mask=(t>lo)&(t<hi);tt=t[mask];ee=e[mask]-np.mean(e[mask])
    bpms=np.arange(114,118,.002)
    strengths=np.array([abs(np.sum(ee*np.exp(-2j*np.pi*tt*b/60*4))) for b in bpms])
    bpm=bpms[np.argmax(strengths)]
    period=60/bpm
    ph=(-np.angle(np.sum(ee*np.exp(-2j*np.pi*tt*bpm/60*4)))/(2*np.pi*bpm/60*4))%(period/4)
    print('local tempo',lo,hi,bpm,ph)
for channel,env in [('midlow',z['mid'][0]),('sidehigh',z['side'][2])]:
    pk,_=find_peaks(env,distance=8,prominence=1)
    print(channel,'peaks124-128',[(round(float(t[k]),4),round(float(env[k]),2)) for k in pk if 124<t[k]<128])
    print(channel,'peaks190-192',[(round(float(t[k]),4),round(float(env[k]),2)) for k in pk if 190<t[k]<192])
sr,x=wavfile.read(P/'reference_analysis.wav');x=x.astype(float).mean(axis=1)/32768
for lo,hi in [(124,128),(190,192)]:
    hop=int(sr*.005);env=np.sqrt(np.mean(x[int(lo*sr):int(hi*sr)][:((int((hi-lo)*sr)//hop)*hop)].reshape(-1,hop)**2,axis=1))
    tt=lo+np.arange(len(env))*hop/sr
    pk,_=find_peaks(env,distance=25,prominence=.06)
    print('wave_rms',[(round(float(tt[k]),4),round(float(env[k]),2)) for k in pk])
