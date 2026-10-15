from pathlib import Path
import sys,json
p=Path(__file__).resolve().parent
sys.path.insert(0,str(p/'_pydeps'))
import numpy as np
from scipy import signal
from scipy.io import wavfile
z=np.load(p/'reference_onsets.npz');t=z['t'];e=z['side'][2];e=e-np.mean(e)
candidates=np.arange(114,118.001,.002)
scores=[]
for bpm in candidates:
    f=bpm/60
    scores.append(sum(abs(np.sum(e*np.exp(-2j*np.pi*t*f*h)))**2/h for h in [1,2,4]))
ix=np.argmax(scores);bpm=candidates[ix]
f=bpm/60
ph=np.angle(np.sum(e*np.exp(-2j*np.pi*t*f)))
phase=(-ph/(2*np.pi*f))%(1/f)
r={'precise_bpm':bpm,'onset_phase_seconds':phase,'beat_seconds':60/bpm,'bar_seconds':240/bpm,'32_bars_seconds':7680/bpm,'34_bars_seconds':8160/bpm}
print(json.dumps(r,indent=2))
(p/'reference_tempo_refined.json').write_text(json.dumps(r,indent=2),encoding='utf8')
sr,x=wavfile.read(p/'reference_analysis.wav');x=x.astype(float).mean(axis=1)
f,t,S=signal.stft(x,sr,nperseg=8192,noverlap=4096)
m=abs(S);freqmask=(f>100)&(f<4000);freq=f[freqmask];m=m[freqmask]
notes=np.round(69+12*np.log2(freq/440)).astype(int)%12
ch=np.zeros(12)
for j in range(12):ch[j]=np.sum(np.power(m[notes==j],.9))
print('chroma',dict(zip(['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'],np.round(ch/ch.max(),3))))
