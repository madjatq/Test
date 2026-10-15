#target aftereffects
(function(){
var folder=new File($.fileName).parent.parent;
var log=new File(folder.fsName+'/制作说明/AE导入验证.txt'); log.encoding='UTF-8';log.open('w');
try{
if(!app.project)app.newProject();
app.beginUndoGroup('C03-C10 layered layout import');
var root=app.project.items.addFolder('C03-C10 画面排版');
var files=new Folder(folder.fsName+'/AI分层文件').getFiles('*.ai');files.sort(function(a,b){return a.name<b.name?-1:1;});
var duration=[6,8,8,16,7,7,7,9];var total=68;
var master=app.project.items.addComp('C03-C10_排版预排_无动画',1920,1080,1,total,30);master.parentFolder=root;
var cursor=0;
for(var i=0;i<files.length;i++){
var io=new ImportOptions(files[i]);io.importAs=ImportAsType.COMP_CROPPED_LAYERS;
var comp=app.project.importFile(io);
if(!(comp instanceof CompItem))throw new Error('Not composition: '+files[i].name);
comp.parentFolder=root;comp.duration=duration[i];comp.frameRate=30;
for(var j=1;j<=comp.numLayers;j++){var ly=comp.layer(j);ly.outPoint=duration[i];if(/^98_|^99_/.test(ly.name)){ly.enabled=false;ly.guideLayer=true;ly.shy=true;}}
comp.hideShyLayers=true;
var item=master.layers.add(comp);item.startTime=cursor;item.inPoint=cursor;item.outPoint=cursor+duration[i];cursor+=duration[i];
log.writeln(decodeURI(files[i].name)+' | '+comp.width+'x'+comp.height+' | layers='+comp.numLayers+' | '+duration[i]+'s');
}
master.duration=cursor;master.workAreaDuration=cursor;
app.endUndoGroup();
var projectFile=new File(folder.fsName+'/C03-C10_分层预排.aep');app.project.save(projectFile);
master.openInViewer();log.writeln('SUCCESS | '+files.length+' compositions | total '+cursor+'s | 30fps');
}catch(e){log.writeln('ERROR: '+e.toString()+' line '+e.line);}
log.close();
})();