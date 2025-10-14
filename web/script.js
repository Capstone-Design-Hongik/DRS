const API = "http://localhost:8000";
const c = document.getElementById("c");
const ctx = c.getContext("2d");
let drawing=false, pts=[];

function toCanvasPos(e){
  const r=c.getBoundingClientRect();
  const x=(e.touches?e.touches[0].clientX:e.clientX)-r.left;
  const y=(e.touches?e.touches[0].clientY:e.clientY)-r.top;
  return {x,y};
}
function draw(){
  ctx.clearRect(0,0,c.width,c.height);
  if(pts.length===0) return;
  ctx.beginPath();
  pts.forEach((p,i)=>{ i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y) });
  ctx.stroke();
}

c.addEventListener("pointerdown",e=>{drawing=true; pts=[toCanvasPos(e)]; draw();});
c.addEventListener("pointermove",e=>{ if(!drawing) return; pts.push(toCanvasPos(e)); draw(); });
c.addEventListener("pointerup",()=>drawing=false);
c.addEventListener("pointerleave",()=>drawing=false);

document.getElementById("clear").onclick=()=>{ pts=[]; draw(); };

document.getElementById("ingest").onclick=async()=>{
  const r = await fetch(`${API}/ingest`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({days:365})});
  const t = await r.json();
  alert(`Ingest 완료: ${t.tickers_count} tickers, target_len=${t.target_len}`);
};

function resampleY(points, targetLen=200){
  if(points.length<2) return [];
  const xs = points.map((p,i)=>i/(points.length-1));
  const ys = points.map(p => 1 - (p.y / c.height)); // 위로 갈수록 큰값
  const xNew = Array.from({length:targetLen}, (_,i)=> i/(targetLen-1));
  const yNew = xNew.map(x=>{
    let j = xs.findIndex(v=>v>=x);
    if(j<=0) return ys[0];
    const x0=xs[j-1], x1=xs[j], y0=ys[j-1], y1=ys[j];
    const t=(x-x0)/(x1-x0+1e-9);
    return y0 + t*(y1-y0);
  });
  return yNew;
}

document.getElementById("search").onclick=async()=>{
  const y = resampleY(pts, 200);
  if(y.length<10) return alert("스케치를 먼저 그려주세요!");
  const r = await fetch(`${API}/similar`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({y, target_len:200})});
  const data = await r.json();
  if(data.items){
    document.getElementById("result").innerHTML = data.items.map(it=>`
      <div class="card"><b>${it.rank}. ${it.ticker}</b><br/>score: ${it.score.toFixed(4)}</div>
    `).join("");
  }else{
    alert(JSON.stringify(data));
  }
};
