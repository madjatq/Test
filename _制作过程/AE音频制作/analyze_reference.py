from pathlib import Path
import sys, json, urllib.request
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'_pydeps'))
import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import median_filter, gaussian_filter1d

sr,x=wavfile.read(ROOT/'reference_analysis.wav')
x=x.astype(np.float64)/32768
mid=np.mean(x,axis=1); side=(x[:,0]-x[:,1])/2
hop=220; nfft=2048
results={"duration":len(x)/sr,"sr":sr,"rms_mid":float(np.sqrt(np.mean(mid**2))),"rms_side":float(np.sqrt(np.mean(side**2)))}
def onset(y):
    f,t,z=signal.stft(y,sr,nperseg=nfft,noverlap=nfft-hop,boundary=None)
    mag=abs(z)
    # Local spectral whitening helps drums survive narration in the centre.
    norm=mag/(median_filter(mag,size=(1,101))+0.0001)
    norm=np.log1p(np.minimum(norm,12))
    d=np.maximum(np.diff(norm,axis=1,prepend=norm[:,:1]),0)
    masks=[(f>50)&(f<220),(f>250)&(f<2000),(f>2200)&(f<9500)]
    env=np.array([np.mean(d[m],axis=0) for m in masks])
    env=env/(np.std(env,axis=1)[:,None]+1e-9)
    return t,env
t,envside=onset(side); _,envmid=onset(mid)
np.savez_compressed(ROOT/'reference_onsets.npz',t=t,side=envside,mid=envmid)
rate=sr/hop
def candidates(env,a,b):
    sl=env[(t>=a)&(t<b)]
    sl=sl-np.mean(sl)
    ac=signal.fftconvolve(sl,sl[::-1],mode='full')[len(sl)-1:]
    ac=ac/(np.arange(len(sl),0,-1)+1e-10)
    ac=ac/(ac[0]+1e-10)
    peaks,_=signal.find_peaks(ac,distance=5)
    peaks=peaks[(peaks>rate*60/180)&(peaks<rate*60/70)]
    peaks=sorted(peaks,key=lambda k:ac[k],reverse=True)[:8]
    return [{"bpm":round(60*rate/p,2),"corr":round(float(ac[p]),4)} for p in peaks]
results['tempo_windows']=[]
for a,b in [(0,30),(30,60),(60,90),(90,120),(120,150),(150,180),(0,195)]:
    results['tempo_windows'].append({'start':a,'end':b,'side_low':candidates(envside[0],a,b),'side_high':candidates(envside[2],a,b),'mid_low':candidates(envmid[0],a,b)})

# Speech detection is probabilistic and separate from subjective listening.
try:
    import onnxruntime as ort
    model=ROOT/'silero_vad.onnx'
    if not model.exists(): urllib.request.urlretrieve('https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx',model)
    sess=ort.InferenceSession(str(model),providers=['CPUExecutionProvider'])
    y=signal.resample_poly(mid,320,441).astype(np.float32)
    state=np.zeros((2,1,128),np.float32); context=np.zeros((1,64),np.float32)
    probs=[]
    for p in range(0,len(y)-512,512):
        chunk=y[p:p+512][None,:]
        feed={'input':np.concatenate([context,chunk],axis=1),'state':state,'sr':np.array(16000,np.int64)}
        out,state=sess.run(None,feed)
        context=chunk[:,-64:]; probs.append(float(out.ravel()[0]))
    probs=np.array(probs); dt=512/16000
    segments=[]; start=None
    for i,active in enumerate(probs>.6):
        if active and start is None:start=i
        if not active and start is not None:
            if (i-start)*dt>.25:segments.append([round(start*dt,2),round(i*dt,2)])
            start=None
    results['speech_detection']={'method':'Silero VAD 16k; probability threshold 0.6','fraction_frames':float(np.mean(probs>.6)),'segments':segments,'mean_probability':float(np.mean(probs))}
    np.save(ROOT/'reference_speech_probabilities.npy',probs)
except Exception as e: results['speech_detection']={'error':repr(e)}
(ROOT/'reference_signal_analysis.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(results,ensure_ascii=False,indent=2))
