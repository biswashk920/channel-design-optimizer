// Water polygon area (shoelace) must equal the hydraulic flow area A, for every section type.
const fs=require('fs');const html=fs.readFileSync(__dirname+'/../docs/index.html','utf8');
const core=html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const L=new Function(core+';return{compare,waterPoly,wallPoly,curves}')();
const I={Q:5,S:0.001,n:0.013,z:1.5,mode:'given_z',fbm:'percent',fb:20,obj:'area',ce:1,cl:1,vmin:0.6,vmax:6,mw:null,md:null,free:false,mf:0.8,diams:[0.3,0.6,1.2,1.8,2.4]};
const sh=p=>{let a=0;for(let i=0;i<p.length;i++){const q=p[(i+1)%p.length];a+=p[i][0]*q[1]-q[0]*p[i][1]}return Math.abs(a)/2};
const r=L.compare(I),o={};for(const[k,d]of Object.entries(r.d)){const c=L.curves(d,I);
o[k]={area:d.A,poly:sh(L.waterPoly(d)),wallTop:Math.max(...L.wallPoly(d).map(p=>p[1])),H:d.H,D:d.D,qEnd:c.r[c.r.length-1][0]}}
console.log(JSON.stringify(o));
