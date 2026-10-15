from pathlib import Path
import sys, json, re, subprocess
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'_pydeps'))
import soundfile as sf
import numpy as np
FFMPEG=Path('C:/ffmpeg/bin/ffmpeg.exe')
source=ROOT.parent.parent/'介绍一位新伙伴——豆包工作1.mp4'
SR=48000;FRAMES=3277241;DURATION=FRAMES/SR
def ff(args):
    p=subprocess.run([str(FFMPEG),'-hide_banner','-y']+list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stderr
def jsonstats(stderr):
    return json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',stderr)[-1])
def master(src,dst):
    stats=jsonstats(ff(['-i',src,'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','NUL']))
    norm='loudnorm=I=-16:TP=-1.5:LRA=9:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true:print_format=json'.format(**stats)
    ff(['-i',src,'-af',norm+f',aresample={SR},apad,atrim=end_sample={FRAMES}','-ar',SR,'-c:a','pcm_s24le',dst])
    check=jsonstats(ff(['-i',dst,'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','NUL']))
    x,sr=sf.read(dst,dtype='float32')
    assert sr==SR and len(x)==FRAMES and x.shape[1]==2
    assert np.all(np.isfinite(x))
    peak=float(abs(x).max());rms=float(np.sqrt(np.mean(x*x)))
    assert peak<.999
    ff(['-i',dst,'-c:a','libmp3lame','-b:a','192k',dst.with_suffix('.mp3')])
    return {'file':dst.name,'sample_rate':sr,'channels':2,'bit_depth':24,'sample_frames':len(x),'duration_seconds':len(x)/sr,'sample_peak':peak,'rms':rms,'integrated_lufs':float(check['input_i']),'true_peak_dbtp':float(check['input_tp']),'loudness_range_lu':float(check['input_lra']),'first_sample':x[0].tolist(),'last_sample':x[-1].tolist()}

# The last strong source transient at 191.142 s anchors bar 33; its natural decay is kept.
# At the locally measured 115.90 BPM, the opening lies 128 beats before that cadence.
SOURCE_BPM=115.90;SOURCE_CADENCE=191.1420861678
SOURCE_START=SOURCE_CADENCE-128*60/SOURCE_BPM
SOURCE_LENGTH=132*60/SOURCE_BPM;TEMPO=116/SOURCE_BPM
refpre=ROOT/'REFERENCE_SourceTail_33bars_premaster.wav'
ff(['-ss',f'{SOURCE_START:.9f}','-i',source,'-t',f'{SOURCE_LENGTH:.9f}','-vn','-af',f'atempo={TEMPO:.12f},aresample={SR},apad,atrim=end_sample={FRAMES},afade=t=in:d=0.018,afade=t=out:st={DURATION-.65:.9f}:d=0.65','-ar',SR,'-ac',2,'-c:a','pcm_s24le',refpre])
outputs=[]
outputs.append(master(ROOT/'ORIGINAL_LightTech_116BPM_33bars_premaster.wav',ROOT/'ORIGINAL_LightTech_116BPM_68s.wav'))
outputs.append(master(refpre,ROOT/'REFERENCE_116BPM_68s.wav'))
manifest={'bpm':116,'bars':33,'meter':'4/4','duration_seconds':DURATION,'ae_comp_duration':68.3,'reference_edit':{'source_file':str(source),'source_start_seconds':SOURCE_START,'source_end_seconds':SOURCE_START+SOURCE_LENGTH,'source_local_bpm':SOURCE_BPM,'playback_tempo_factor':TEMPO,'final_cadence_output_seconds':128*60/116,'method':'Continuous tail excerpt; final cadence anchored to bar 33; 18 ms fade-in, 650 ms fade-out. No source splice.','listening_limit':'Tool environment does not support audio input. Signal analysis and VAD only; human listening has not been performed.'},'outputs':outputs}
(ROOT/'audio_delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
