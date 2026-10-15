"""Read-only audit of delivered audio; writes only this audit's report and temp render."""
from pathlib import Path
import ast, datetime, hashlib, json, re, subprocess, sys, tempfile

P = Path(__file__).resolve().parent
ROOT = P.parent.parent
AUDIO = ROOT / 'C03-C10_AE动画' / 'Audio'
sys.path.insert(0, str(P / '_pydeps'))
import numpy as np
import soundfile as sf
from scipy import signal

FF = Path('C:/ffmpeg/bin/ffmpeg.exe')
PROBE = FF.with_name('ffprobe.exe')
WAV = AUDIO / 'ORIGINAL_LightTech_116BPM_68s.wav'
MP3 = WAV.with_suffix('.mp3')
PRE = P / 'ORIGINAL_LightTech_116BPM_33bars_premaster.wav'
SOURCE = ROOT / '介绍一位新伙伴——豆包工作1.mp4'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args, binary=False):
    result = subprocess.run(list(map(str, args)), capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf8', 'replace'))
    return result if binary else result.stderr.decode('utf8', 'replace')

def loudness(path):
    log = run([FF, '-hide_banner', '-nostdin', '-i', path, '-af',
               'loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json', '-f', 'null', 'NUL'])
    return json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}', log)[-1])

def db(value):
    return float(20 * np.log10(max(float(value), 1e-15)))

def sample_report(path):
    x, sr = sf.read(path, dtype='float64', always_2d=True)
    peak = np.max(np.abs(x))
    return x, sr, dict(sample_rate=sr, frames=len(x), channels=x.shape[1],
        duration_seconds=len(x)/sr, finite=bool(np.isfinite(x).all()),
        clipped_samples=int(np.count_nonzero(np.abs(x) >= 1)),
        sample_peak=float(peak), sample_peak_dbfs=db(peak),
        rms=float(np.sqrt(np.mean(x*x))), first_sample=x[0].tolist(), last_sample=x[-1].tolist())

def tempo_from_samples(x, sr, side=False):
    y=(x[:,0]-x[:,1])/2 if side else np.mean(x,axis=1)
    if sr != 22050:
        y=signal.resample_poly(y,147,320)
        sr=22050
    f,t,z=signal.stft(y,sr,nperseg=2048,noverlap=2048-220,boundary=None)
    mag=np.abs(z[(f>2200)&(f<9500)])
    # Spectral flux suppresses sustained tones; 0.002 BPM search across harmonics.
    lm=np.log1p(mag*100)
    env=np.mean(np.maximum(np.diff(lm,axis=1,prepend=lm[:,:1]),0),axis=0)
    env-=np.mean(env)
    candidates=np.arange(114,118.001,.002)
    scores=np.array([sum(abs(np.sum(env*np.exp(-2j*np.pi*t*b/60*h)))**2/h
                         for h in (1,2,4)) for b in candidates])
    return {'bpm':float(candidates[np.argmax(scores)]), 'search_step_bpm':0.002,
            'method':'High-band spectral-flux periodicity, harmonic Fourier search 114–118 BPM',
            'channel':'stereo side' if side else 'stereo mid'}

report={'verified_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        'scope':'Read-only independent audit; delivered WAV/MP3 and existing beatmaps unchanged',
        'listening':{'performed':False,'reason':'No audio-input or listening tool is available in this task. Signal analysis and source-code audit do not establish subjective timbre/style similarity.'}}
original_hashes={str(p.relative_to(ROOT)):sha(p) for p in (WAV,MP3,PRE,P/'compose_original.py',P/'finalize_music.py')}
x,sr,metrics=sample_report(WAV)
ls=loudness(WAV)
metrics.update(integrated_lufs=float(ls['input_i']),true_peak_dbtp=float(ls['input_tp']),
               loudness_range_lu=float(ls['input_lra']),file_sha256=sha(WAV))
probe=run([PROBE,'-v','error','-show_streams','-show_format','-of','json',WAV],True)
report['wav']={**metrics,'format':json.loads(probe.stdout)['streams'][0]['codec_name'],'bit_depth':24}
report['fadeout']=[]
for a,b in [(60,65),(66,67),(67,68),(68,len(x)/sr),(len(x)/sr-.05,len(x)/sr)]:
    y=x[int(a*sr):int(b*sr)]
    rms=np.sqrt(np.mean(y*y))
    report['fadeout'].append({'start':a,'end':b,'rms':float(rms),'rms_dbfs':db(rms),'peak':float(np.max(np.abs(y)))})

# Execute only the synthesis portion in memory. Stop BEFORE its first file write.
composition=P/'compose_original.py'
tree=ast.parse(composition.read_text(encoding='utf8'))
stop=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Expr)
          and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
          and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='sf'
          and node.value.func.attr=='write')
allowed_tree=ast.Module(body=tree.body[:stop],type_ignores=[])
namespace={'__file__':str(composition),'__name__':'audit_synthesis'}
argv_saved=sys.argv
sys.argv=[str(composition)]
exec(compile(allowed_tree,str(composition),'exec'),namespace)
sys.argv=argv_saved
premaster,pre_sr=sf.read(PRE,dtype='float64',always_2d=True)
regenerated=namespace['mix'].astype(np.float64)
max_error=float(np.max(np.abs(premaster-regenerated)))
report['provenance']={
    'method':'Reviewed synthesis AST and regenerated deterministic mix entirely in memory before its first file-write statement; compared all samples with archived premaster; rerendered mastering in temporary directory.',
    'source_audio_reads_in_synthesis':False,
    'synth_seed':10142026,
    'sources':['Mathematical oscillators (sine/FM/harmonics)','Deterministic random noise','Code-defined notes, harmony, rhythms and envelopes'],
    'tracks':['electronic drums','synth bass','FM pluck keys','sine-based lead melody','stereo pad','noise sweeps/chimes'],
    'recreated_premaster_max_abs_error':max_error,
    'pcm24_lsb':2**-23,
    'premaster_matches_within_pcm24_lsb':bool(max_error<=2**-23),
    'separate_reference_edits':'Reference-derived REFERENCE_* files exist under _制作过程/AE音频制作/_reference_process and are not the selected delivered track.',
    'global_musical_originality_limit':'This verifies no reference audio was sampled in the delivered render; it is not a worldwide melody similarity/copyright search.'}

with tempfile.TemporaryDirectory(prefix='c03_audio_verify_') as td:
    td=Path(td)
    normstats=loudness(PRE)
    norm='loudnorm=I=-16:TP=-1.5:LRA=9:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true:print_format=json'.format(**normstats)
    rebuilt=td/'master.wav'
    run([FF,'-hide_banner','-nostdin','-y','-i',PRE,'-af',norm+',aresample=48000,apad,atrim=end_sample=3277241','-ar','48000','-c:a','pcm_s24le',rebuilt])
    r,_=sf.read(rebuilt,dtype='float64',always_2d=True)
    report['provenance'].update(mastering_reproduction_sample_exact=bool(np.array_equal(x,r)),
                                mastering_reproduction_max_abs_error=float(np.max(np.abs(x-r))),
                                mastering_reproduction_file_hash_exact=sha(rebuilt)==sha(WAV))
    decoded=td/'mp3.wav'
    run([FF,'-hide_banner','-nostdin','-y','-i',MP3,'-c:a','pcm_f32le',decoded])
    m,msr=sf.read(decoded,dtype='float64',always_2d=True)
    shared=min(len(x),len(m))
    report['mp3']={'decodes_cleanly':True,'sample_rate':msr,'decoded_frames':len(m),
                   'decoded_duration_seconds':len(m)/msr,'file_sha256':sha(MP3),
                   'correlation_with_master':float(np.corrcoef(x[:shared].ravel(),m[:shared].ravel())[0,1])}
    # Fresh reference extraction and tempo check; no subjective listening implied.
    ref=td/'reference.wav'
    run([FF,'-hide_banner','-nostdin','-y','-i',SOURCE,'-vn','-ac','2','-ar','22050','-c:a','pcm_s16le',ref])
    rx,rsr=sf.read(ref,dtype='float64',always_2d=True)
    report['reference']={'source':str(SOURCE),'decoded_duration_seconds':len(rx)/rsr,
                         'fresh_tempo':tempo_from_samples(rx,rsr,True),
                         'archived_refined_bpm':json.loads((P/'reference_tempo_refined.json').read_text(encoding='utf8'))['precise_bpm'],
                         'style_conclusion':'Only regular rhythmic pulse near 116 BPM is objectively confirmed. The delivered arrangement is code-defined light electronic instrumental; subjective match to the reference is unverified.'}

beatmap=json.loads((AUDIO/'C03-C10_music_beatmap.json').read_text(encoding='utf8'))
beat_errors=[abs(m['time_seconds']-i*60/116) for i,m in enumerate(beatmap['markers'])]
report['tempo_and_structure']={'declared_bpm':116,'measured_bpm':tempo_from_samples(x,sr),
    'meter':'4/4','bars':33,'beats':132,'beat_seconds':60/116,'bar_seconds':240/116,
    'mathematical_duration_seconds':132*60/116,'duration_quantization_error_seconds':len(x)/sr-132*60/116,
    'beatmap_marker_count':len(beatmap['markers']),'beatmap_max_time_error_seconds':max(beat_errors),
    'scene_bars':[s['bars'] for s in beatmap['scenes']],'scenes':beatmap['scenes'],
    'harmony':'Dmaj9 / Bm7 / Gmaj9 / A(sus), final D6/9 cadence',
    'arrangement':'Eight scene-specific melody variants; lighter keys/percussion in C06; transition noise sweeps/chimes; final cadence begins at bar 33 (66.206897 s); explicit 230 ms fadeout plus natural note decay.',
    'ae_duration_seconds':68.3,'ae_frames_30fps':2049}
report['original_files_unchanged']=all(sha(ROOT/path)==before for path,before in original_hashes.items())
report['evidence_sha256']=original_hashes
report['deliverability']={'technical_pass':bool(metrics['finite'] and metrics['clipped_samples']==0
    and metrics['true_peak_dbtp']<0 and len(x)==3277241 and sr==48000
    and report['provenance']['premaster_matches_within_pcm24_lsb']
    and report['provenance']['mastering_reproduction_sample_exact']
    and len(beatmap['markers'])==132 and max(beat_errors)<1e-8),
    'conclusion':'Technically suitable for AE use at time 0, with 68.3 s / 2049-frame 30fps composition; subjective listening approval is not recorded.'}
out=AUDIO/'最终核验.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
