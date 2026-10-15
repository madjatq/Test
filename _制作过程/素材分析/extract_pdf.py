import pymupdf as fitz
from pathlib import Path
import sys
src=Path(sys.argv[1]); out=Path(sys.argv[2]); doc=fitz.open(src)
print('pages',len(doc))
texts=[]
for i,p in enumerate(doc):
 t=p.get_text(); texts.append(f'\n===== PDF PAGE {i+1} =====\n'+t)
 if any(q in t for q in ['1998','1807','\u5c0f\u65f6','\u53d1\u7535\u91cf','\u98ce\u901f','\u529f\u7387\u66f2\u7ebf']):
  print('PAGE',i+1,t[:180].replace('\n',' '))
(out/'A01_text.txt').write_text(''.join(texts),encoding='utf-8')
for i in range(len(doc)):
 if i<3 or any(q in doc[i].get_text() for q in ['1998','1807']):
  doc[i].get_pixmap(matrix=fitz.Matrix(1.7,1.7)).save(out/f'A01_page{i+1:02d}.png')
