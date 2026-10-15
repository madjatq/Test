from pathlib import Path
import sys,json,csv
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'_pydeps'))
import soundfile as sf,numpy as np
x,sr=sf.read(P/'ORIGINAL_LightTech_116BPM_68s.wav',dtype='float64')
tail=[]
for a,b in [(0,1),(60,65),(66,67),(67,68),(68,len(x)/sr)]:
    y=x[int(a*sr):int(b*sr)]
    tail.append({'start':a,'end':b,'rms':float(np.sqrt(np.mean(y*y))),'peak':float(np.max(np.abs(y)))})
assert np.isfinite(x).all() and len(x)==3277241 and sr==48000 and x.shape[1]==2
assert np.max(abs(x))<.999
j=json.loads((P/'C03-C10_music_beatmap.json').read_text(encoding='utf8'))
assert len(j['markers'])==132 and [s['bars'] for s in j['scenes']]==[3,4,4,7,3,4,3,5]
for marker in j['markers']:
    marker['ae_frame_30fps']=round(marker['time_seconds']*30)
    marker['ae_time_30fps']=marker['ae_frame_30fps']/30
for scene in j['scenes']:
    scene['ae_start_frame_30fps']=round(scene['start']*30)
    scene['ae_end_frame_30fps']=round(scene['end']*30)
j['ae_comp_duration']=68.3
j['ae_fps']=30
(P/'C03-C10_music_beatmap.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
with (P/'C03-C10_music_beats.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=j['markers'][0].keys());writer.writeheader();writer.writerows(j['markers'])
verification={'sample_rate':sr,'sample_frames':len(x),'channels':x.shape[1],'duration':len(x)/sr,'finite':True,'no_clipping':True,'peak':float(abs(x).max()),'tail_decay':tail,'scenes':j['scenes'],'beat_count':len(j['markers'])}
(P/'ORIGINAL_verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(verification,ensure_ascii=False,indent=2))
