import sys,zipfile,re
from pathlib import Path
root=Path(sys.argv[1])
for p in root.rglob('*'):
 if p.suffix.lower() in ['.docx','.xlsx']:
  with zipfile.ZipFile(p) as z:
   for n in z.namelist():
    if n.endswith('.xml'):
     t=z.read(n).decode('utf-8','replace')
     for m in re.finditer(r'1998|1807[.]4|1,998|1,807[.]4',t):
      print(p.name,n,t[max(0,m.start()-100):m.end()+100])
