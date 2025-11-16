// API URL: 환경에 따라 자동 설정
const API = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? "http://localhost:8080"
  : window.location.origin;
const c = document.getElementById("c");
const ctx = c.getContext("2d");
let drawing=false, pts=[];

function toast(msg){
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.style.display = "block";
  setTimeout(()=> t.style.display="none", 1800);
}

function setStatus(html, ok=true){
  const s = document.getElementById("status");
  s.innerHTML = (ok ? "✅ " : "⏳ ") + html;
  s.className = "status " + (ok ? "ok" : "hint");
}

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
  ctx.strokeStyle="#dfe6f5";
  ctx.lineWidth=2;
  ctx.stroke();
}

c.addEventListener("pointerdown",e=>{drawing=true; pts=[toCanvasPos(e)]; draw();});
c.addEventListener("pointermove",e=>{ if(!drawing) return; pts.push(toCanvasPos(e)); draw(); });
c.addEventListener("pointerup",()=>drawing=false);
c.addEventListener("pointerleave",()=>drawing=false);

document.getElementById("clear").onclick=()=>{ pts=[]; draw(); };

// ---------- ingest ----------
document.getElementById("ingest").onclick = async () => {
  const maxCount = document.getElementById("maxCount").value;
  const force = document.getElementById("forceRefresh").checked;
  const btn = document.getElementById("ingest");
  btn.disabled = true;
  setStatus(`Ingest 진행중… (티커 ${maxCount}개${force?" 재수집":""})`, false);
  try{
    const res = await fetch(`${API}/ingest?max_tickers=${maxCount}&force_refresh=${force}`, {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ days: 365 })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.detail || "ingest 실패");
    setStatus(`Ingest 완료: ${data.tickers_count}개 티커 로드`);
    toast(`Ingest OK: ${data.tickers_count} tickers`);
  }catch(e){
    setStatus(`Ingest 오류: ${e.message}`, true);
    toast("오류: " + e.message);
  }finally{
    btn.disabled = false;
  }
};

// ---------- resample & similar ----------
function resampleY(points, targetLen=200){
  if(points.length<2) return [];
  const xs = points.map((p,i)=>i/(points.length-1));
  const ys = points.map(p => 1 - (p.y / c.height));
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
  if (y.length < 10) return toast("스케치를 먼저 그려주세요!");

  const r = await fetch(`${API}/similar`, {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ y, target_len: 200 })
  });
  const data = await r.json();
  if(!r.ok){ toast(data.detail || "similar 실패"); return; }

  const div = document.getElementById("result");
  if (!data.items || !data.items.length){
    div.innerHTML = "<div class='hint'>결과가 없습니다.</div>";
    return;
  }

  // 렌더
  div.innerHTML = data.items.map(it => `
    <div class="card">
      <div class="row">
        <div class="ticker">${it.rank}. ${it.ticker}</div>
        <div class="chip">score: ${Number(it.score).toFixed(4)}</div>
      </div>
      <canvas class="mini" width="420" height="140" id="cv_${it.rank}"></canvas>
      <div class="hint">검정: 스케치 / 회색: MA20(정규화)</div>
    </div>
  `).join("");

  // 캔버스 오버레이
  data.items.forEach(it => {
    const cv = document.getElementById(`cv_${it.rank}`);
    drawOverlay(cv, it.sketch_norm, it.series_norm);
  });
  toast(`총 ${data.items.length}개 결과`);
};

// ---------- overlay drawing ----------
function drawOverlay(canvas, sketch, series) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0,0,W,H);

  function toXY(arr) {
    const xs = arr.map((_,i)=> i/(arr.length-1));
    const ys = arr.map(v => 1 - ((v - (-3)) / 6));
    return xs.map((x,i)=>({
      x: x*(W-10)+5,
      y: Math.min(H-5, Math.max(5, ys[i]*(H-10)+5))
    }));
  }
  const s1 = toXY(sketch);
  const s2 = toXY(series);

  ctx.strokeStyle = "#1b2230"; ctx.lineWidth=1;
  for (let i=1;i<4;i++){ const y=(H/4)*i; ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }

  ctx.strokeStyle = "#a7b0bf"; ctx.lineWidth=2;
  ctx.beginPath(); s2.forEach((p,i)=>{ i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y) }); ctx.stroke();

  ctx.strokeStyle = "#e9ecf1"; ctx.lineWidth=2.5;
  ctx.beginPath(); s1.forEach((p,i)=>{ i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y) }); ctx.stroke();
}
