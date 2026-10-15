from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'_pydeps'))
import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import minimize_scalar
z=np.load(P/'reference_onsets.npz');t=z['t'];e=z['side'][2];e-=np.mean(e)
for lo,hi in [(0,12),(180,194)]:
    peaks,_=find_peaks(e,distance=8,prominence=.7)
    print('peaks',lo,[(round(float(t[k]),4),round(float(e[k]),2)) for k in peaks if lo<t[k]<hi])
for h in [1,2,4]:
    def score(bpm):return -abs(np.sum(e*np.exp(-2j*np.pi*t*bpm/60*h)))
    opt=minimize_scalar(score,bounds=(115.8,116.15),method='bounded',options={'xatol':1e-10})
    b=opt.x;phase=(-np.angle(np.sum(e*np.exp(-2j*np.pi*t*b/60*h)))/(2*np.pi*b/60*h))%(60/b/h)
    print('harmonic',h,'bpm',b,'phase',phase,'strength',-opt.fun)
    for lo in [2,40,80,120,160]:
        ids=(t>lo)&(t<lo+20)
        a=(-np.angle(np.sum(e[ids]*np.exp(-2j*np.pi*t[ids]*b/60*h)))/(2*np.pi*b/60*h))%(60/b/h)
        print('window',lo,'phase',a)
