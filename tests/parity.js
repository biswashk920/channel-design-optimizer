// Runs the page's calculation code (the <script id="core"> block) on cases from Python.
const fs=require('fs');
const html=fs.readFileSync(__dirname+'/../docs/index.html','utf8');
const core=html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const lib=new Function(core+';return{compare,NoSol}')();
const out=JSON.parse(fs.readFileSync(process.argv[2],'utf8')).map(I=>{
 const r=lib.compare(I),o={};
 for(const k of['rectangular','trapezoidal','circular']){const d=r.d[k];if(d)o[k]={b:d.b,D:d.D,y:d.y,A:d.A,V:d.V,Fr:d.Fr,yc:d.yc,obj:d.obj,ok:d.ok}}
 o.rec=r.rec?r.rec.label:null;return o});
console.log(JSON.stringify(out));
