from pathlib import Path
from PIL import Image,ImageOps
import sys,colorsys,json
out=Path(sys.argv[1]); checks=[]
for stem,box in [('A02_power_curve',(155,78,1402,601)),('A02_Cp_curve',(77,80,1324,599))]:
 im=Image.open(out/(stem+'.png')).convert('RGB'); w,h=im.size
 hsv=im.convert('HSV'); hp=hsv.load(); px=im.load()
 curves=Image.new('RGBA',im.size,(255,255,255,0)); cp=curves.load()
 axis_white=im.copy(); ap=axis_white.load(); count=0
 for y in range(box[1],min(box[3],h)):
  for x in range(box[0],min(box[2],w)):
   sat=hp[x,y][1]; rgb=px[x,y]
   if sat>=51 and max(rgb)-min(rgb)>=30:
    mn=min(rgb); alpha=255-mn
    if alpha:
     cp[x,y]=tuple(round((c-mn)*255/alpha) for c in rgb)+(alpha,)
     ap[x,y]=(255,255,255); count+=1
 gray=ImageOps.grayscale(axis_white); axes=Image.new('RGBA',im.size,(0,0,0,0)); axes.putalpha(ImageOps.invert(gray))
 axes.save(out/(stem+'_axes.png')); curves.save(out/(stem+'_curves.png'))
 comp=Image.new('RGBA',im.size,'white'); comp.alpha_composite(axes); comp.alpha_composite(curves); comp.convert('RGB').save(out/(stem+'_split_QA.png'))
 checks.append({'stem':stem,'size':[w,h],'curves_pixels':count,'axes_file':stem+'_axes.png','curves_file':stem+'_curves.png','threshold':'HSV saturation >=51/255 and channel range >=30, limited to inner plot; axes neutral grayscale; white removed to alpha'})
(out/'A02_layer_manifest.json').write_text(json.dumps(checks,indent=2),encoding='utf-8'); print(json.dumps(checks,indent=2))
# A04 graph-only source crop, all original point geometry retained.
im=Image.open(Path(sys.argv[2])/'A04.png'); im.crop((0,33,1440,625)).save(out/'A04_plot_region.png')
