from pathlib import Path
from PIL import Image
import sys
src=Path(sys.argv[1]); out=Path(sys.argv[2])
for f in ['A02\u529f\u7387\u66f2\u7ebf\u4e0eCP\u66f2\u7ebf.png','A03\u98ce\u8d44\u6e90\u6307\u6807\u5730\u56fe.png','A04.png']:
 im=Image.open(src/f); print(f,im.size)
im=Image.open(out/'A01_page04.png'); w,h=im.size
im.crop((int(w*.145),int(h*.412),int(w*.86),int(h*.895))).save(out/'A01_p47_monthly_table.png')
im.crop((int(w*.145),int(h*.844),int(w*.86),int(h*.895))).save(out/'A01_p47_annual_row.png')
im=Image.open(out/'A01_page05.png'); w,h=im.size
im.crop((int(w*.17),int(h*.14),int(w*.83),int(h*.473))).save(out/'A01_p48_curve_0606.png')
im.crop((int(w*.17),int(h*.486),int(w*.83),int(h*.813))).save(out/'A01_p48_curve_0087.png')
im=Image.open(src/'A02\u529f\u7387\u66f2\u7ebf\u4e0eCP\u66f2\u7ebf.png'); w,h=im.size
im.crop((0,0,int(w*.48),int(h*.875))).save(out/'A02_power_curve.png')
im.crop((int(w*.525),0,w,int(h*.875))).save(out/'A02_Cp_curve.png')
