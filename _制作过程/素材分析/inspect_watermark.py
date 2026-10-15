import pymupdf as f,sys
from pathlib import Path
d=f.open(sys.argv[1])
for pi in [0,4,5,6]:
 p=d[pi]
 print('PAGE',pi+1,'contents',p.get_contents())
 for b in p.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   for s in l.get('spans',[]):
    if '2026-' in s['text']:
     print('watermark span bbox',s['bbox'],'color',s['color'],'font',s['font'])
 for xr in p.get_contents():
  dat=d.xref_stream(xr)
  print('stream',xr,'len',len(dat),'tail',repr(dat[-350:]))
