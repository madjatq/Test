import zipfile,xml.etree.ElementTree as ET,sys,json,re
from pathlib import Path
ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
root=Path(sys.argv[1]); out=Path(sys.argv[2]); outputs=[]
for prefix in ['B03','C03','D01']:
 p=next(p for p in root.glob(prefix+'*.xlsx'))
 with zipfile.ZipFile(p) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   ss=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('x:si',ns)]
  rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  wb=ET.fromstring(z.read('xl/workbook.xml')); book={'file':p.name,'sheets':[]}
  for sh in wb.findall('x:sheets/x:sheet',ns):
   target=rels[sh.attrib['{'+ns['r']+'}id']]; target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
   sheet=ET.fromstring(z.read(target)); rows=[]
   for row in sheet.findall('x:sheetData/x:row',ns)[:5]:
    vals={}
    for c in row.findall('x:c',ns):
     v=c.find('x:v',ns); txt=v.text if v is not None else ''
     if c.attrib.get('t')=='s': txt=ss[int(txt)]
     if c.attrib.get('t')=='inlineStr': txt=''.join(c.find('x:is',ns).itertext())
     vals[c.attrib['r']]=txt
    rows.append(vals)
   book['sheets'].append({'sheet':sh.attrib['name'],'first5rows':rows})
  outputs.append(book)
print(json.dumps(outputs,ensure_ascii=False,indent=2))
(out/'C05_xlsx_rows.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding='utf-8')
