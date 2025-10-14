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

document.getElementById("search").onclick = async () => {
  const y = resampleY(pts, 200);
  if (y.length < 10) return alert("스케치를 먼저 그려주세요!");

  // 서버 호출
  const r = await fetch(`${API}/similar`, {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ y, target_len: 200 })
  });

  const data = await r.json();
  const div = document.getElementById("result");
  if (!data.items) {
    return alert(JSON.stringify(data));
  }

  // 스케치/시리즈 겹쳐 그리는 함수 (0~1 범위 y값 기준)
  function drawOverlay(canvas, sketch, series) {
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0,0,W,H);

    function toXY(arr) {
      // x: 0~1 균등, y: 0~1(위가 1) → 캔버스 좌표
      const xs = arr.map((_,i)=> i/(arr.length-1));
      const ys = arr.map(v => 1 - ((v - (-3)) / (6))); 
      // 위 줄 설명: z-score라서 대략 -3~+3 구간을 0~1로 클리핑 (간단 스케일)
      return xs.map((x,i)=>({
        x: x * (W-10) + 5,
        y: Math.min(H-5, Math.max(5, ys[i] * (H-10) + 5))
      }));
    }

    const s1 = toXY(sketch);
    const s2 = toXY(series);

    // grid (optional)
    ctx.strokeStyle = "#f0f0f0";
    ctx.lineWidth = 1;
    for (let i=1;i<4;i++){
      const y = (H/4)*i;
      ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
    }

    // 후보 MA20 (회색)
    ctx.strokeStyle = "#999";
    ctx.lineWidth = 2;
    ctx.beginPath();
    s2.forEach((p,i)=>{ i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y) });
    ctx.stroke();

    // 스케치 (진한색)
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    s1.forEach((p,i)=>{ i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y) });
    ctx.stroke();
  }

  // 결과 렌더
  div.innerHTML = data.items.map(it => `
    <div class="card">
      <b>${it.rank}. ${it.ticker}</b><br/>
      <span class="legend">검정: 스케치 / 회색: MA20(정규화)</span><br/>
      <canvas class="mini" width="420" height="140" id="cv_${it.rank}"></canvas><br/>
      score: ${it.score.toFixed(4)}
    </div>
  `).join("");

  // 각 캔버스에 오버레이 그리기
  data.items.forEach(it => {
    const cv = document.getElementById(`cv_${it.rank}`);
    drawOverlay(cv, it.sketch_norm, it.series_norm);
  });
};
