"""dashboard.html: grafik harga + pita zona. Satu file, nggak butuh server atau library."""

from __future__ import annotations

import html
import json
from datetime import date

from cryptomonitor.cycle import ZONES, heat_score, value_score, zone_key
from cryptomonitor.cycle_report import ZONE_TEXT, heat_max
from cryptomonitor.lib import fmt_idr, fmt_number, fmt_px

ZONE_ORDER = ["deep", "accumulate", "neutral", "trim", "trim_hard"]

_CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--line:#0b0b0b;
--z-deep:#184f95;--z-accumulate:#86b6ef;--z-neutral:#e1e0d9;--z-trim:#f0a3a2;--z-trim_hard:#c93434}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;
--ink:#f0efec;--ink2:#c3c2b7;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--line:#f0efec;
--z-deep:#3987e5;--z-accumulate:#9ec5f4;--z-neutral:#383835;--z-trim:#f0a3a2;--z-trim_hard:#e34948}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#2c2c2a;
--axis:#383835;--border:rgba(255,255,255,.10);--line:#f0efec;--z-deep:#3987e5;--z-accumulate:#9ec5f4;--z-neutral:#383835;
--z-trim:#f0a3a2;--z-trim_hard:#e34948}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto;padding:24px 16px 48px}h1{font-size:22px;margin:0 0 4px}h2{font-size:18px;margin:0}
.sub{color:var(--ink2);margin:0 0 20px}.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin:0 0 20px}
.head{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:baseline;justify-content:space-between}
.zone{display:inline-flex;align-items:center;gap:8px;font-weight:600}.sw{width:12px;height:12px;border-radius:3px;display:inline-block;flex:none}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:14px 0}
.tile{border:1px solid var(--border);border-radius:8px;padding:10px 12px}.tile b{display:block;font-size:20px;font-weight:600}
.tile span{color:var(--ink2);font-size:13px}.note{color:var(--ink2);font-size:14px;margin:8px 0 0}
.bar{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between;margin:8px 0}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:var(--ink2)}.legend span{display:inline-flex;align-items:center;gap:6px}
.ranges button{font:inherit;font-size:13px;color:var(--ink2);background:none;border:1px solid var(--border);border-radius:6px;padding:3px 10px;cursor:pointer}
.ranges button[aria-pressed="true"]{color:var(--ink);border-color:var(--ink2);font-weight:600}
.plot{position:relative}.plot svg{display:block;width:100%;height:auto;touch-action:pan-y}.tip{max-width:100%}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 10px;
font-size:13px;line-height:1.45;box-shadow:0 4px 14px rgba(0,0,0,.12);white-space:nowrap;display:none}
.tip b{display:block}.axis text{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%;font-size:14px;margin-top:8px}td,th{padding:5px 8px;border-bottom:1px solid var(--grid);text-align:left}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}tr.now td{font-weight:600}details summary{cursor:pointer;color:var(--ink2);font-size:14px;margin-top:10px}
.scroll{overflow-x:auto}footer{color:var(--ink2);font-size:13px}
"""

_JS = """
const DATA=JSON.parse(document.getElementById('data').textContent);
const NS='http://www.w3.org/2000/svg';
const el=(n,a,p)=>{const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e};
const fmt=v=>'$'+(v>=1000?Math.round(v).toLocaleString('id-ID'):v.toLocaleString('id-ID',{minimumFractionDigits:2,maximumFractionDigits:2}));
function draw(card,d,from){
  const svg=card.querySelector('svg'),tip=card.querySelector('.tip');svg.textContent='';
  const W=Math.max(300,card.querySelector('.plot').clientWidth),small=W<560,L=4,R=small?52:64,T=10,PB=small?210:300,SY=PB+18,SH=22,AX=SY+SH+16;
  svg.setAttribute('viewBox','0 0 '+W+' '+(AX+6));
  let i0=d.t.findIndex(t=>t>=from);if(i0<0)i0=0;
  const n=d.t.length-i0,x=i=>L+(W-L-R)*(n>1?(i-i0)/(n-1):0);
  let lo=Infinity,hi=0;for(let i=i0;i<d.t.length;i++){lo=Math.min(lo,d.c[i]);hi=Math.max(hi,d.c[i])}
  const a=Math.log(lo*0.95),b=Math.log(hi*1.05),y=v=>T+(PB-T)*(1-(Math.log(v)-a)/(b-a));
  const ax=el('g',{class:'axis'},svg);
  const ticks=[];for(let e=-2;e<7;e++)for(const m of [1,2,5]){const v=m*10**e;if(v>=lo*0.95&&v<=hi*1.05)ticks.push(v)}
  const keep=ticks.length>(small?5:7)?ticks.filter((_,i)=>i%2==0):ticks;
  for(const v of keep){el('line',{x1:L,x2:W-R,y1:y(v),y2:y(v),stroke:'var(--grid)','stroke-width':1},ax);
    el('text',{x:W-R+6,y:y(v)+4},ax).textContent=fmt(v)}
  const span=(Date.parse(d.t[d.t.length-1])-Date.parse(d.t[i0]))/864e5;let last='',lx=-99;
  for(let i=i0;i<d.t.length;i++){const key=span>1100?d.t[i].slice(0,4):d.t[i].slice(0,7);
    if(key!==last&&i>i0){
      el('line',{x1:x(i),x2:x(i),y1:SY+SH,y2:SY+SH+4,stroke:'var(--axis)'},ax);
      if(x(i)<W-R-16&&x(i)>L+16&&x(i)-lx>=52){lx=x(i);el('text',{x:x(i),y:AX,'text-anchor':'middle'},ax).textContent=span>1100?key:key.slice(5)+'/'+key.slice(2,4)}}
    last=key}
  let s=i0;for(let i=i0+1;i<=d.t.length;i++){if(i==d.t.length||d.z[i]!==d.z[s]){
    const x0=x(s),x1=i==d.t.length?x(i-1):x(i);
    el('rect',{x:x0,y:SY,width:Math.max(x1-x0,0.8),height:SH,fill:'var(--z-'+DATA.zones[d.z[s]].key+')'},svg);s=i}}
  el('text',{x:W-R+6,y:SY+15,class:'axis',fill:'var(--muted)','font-size':11},svg).textContent='zona';
  let p='';for(let i=i0;i<d.t.length;i++)p+=(i==i0?'M':'L')+x(i).toFixed(1)+' '+y(d.c[i]).toFixed(1);
  el('path',{d:p,fill:'none',stroke:'var(--line)','stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'},svg);
  const li=d.t.length-1;el('circle',{cx:x(li),cy:y(d.c[li]),r:4,fill:'var(--line)',stroke:'var(--surface)','stroke-width':2},svg);
  const ch=el('line',{y1:T,y2:SY+SH,stroke:'var(--axis)','stroke-width':1,visibility:'hidden'},svg);
  const dot=el('circle',{r:4,fill:'var(--line)',stroke:'var(--surface)','stroke-width':2,visibility:'hidden'},svg);
  const hit=el('rect',{x:L,y:0,width:W-L-R,height:SY+SH,fill:'transparent'},svg);
  const move=ev=>{const r=svg.getBoundingClientRect(),px=(ev.clientX-r.left)/r.width*W;
    let i=Math.round(i0+(px-L)/(W-L-R)*(n-1));i=Math.max(i0,Math.min(d.t.length-1,i));
    ch.setAttribute('x1',x(i));ch.setAttribute('x2',x(i));ch.setAttribute('visibility','visible');
    dot.setAttribute('cx',x(i));dot.setAttribute('cy',y(d.c[i]));dot.setAttribute('visibility','visible');
    const z=DATA.zones[d.z[i]];
    tip.innerHTML='<b>'+d.t[i]+'</b>'+fmt(d.c[i])+'<br><span class="sw" style="background:var(--z-'+z.key+')"></span> '+z.name+
      '<br>Skor panas '+d.h[i]+' dari '+d.hmax+' &middot; value '+d.v[i]+' dari 4'+(d.s[i]?'<br>Jual '+d.s[i]+'% per tranche':'');
    tip.style.display='block';const tw=tip.offsetWidth,cx=x(i)/W*r.width;
    tip.style.left=Math.max(0,Math.min(r.width-tw,cx+(cx>r.width/2?-tw-12:12)))+'px';tip.style.top=(small?-4:8)+'px'};
  hit.addEventListener('pointermove',move);hit.addEventListener('pointerdown',move);
  hit.addEventListener('pointerleave',()=>{tip.style.display='none';ch.setAttribute('visibility','hidden');dot.setAttribute('visibility','hidden')});
}
document.querySelectorAll('.card[data-asset]').forEach(card=>{
  const d=DATA.assets[card.dataset.asset],btns=card.querySelectorAll('.ranges button');
  const go=btn=>{btns.forEach(b=>b.setAttribute('aria-pressed',b===btn));
    const days=+btn.dataset.days,end=new Date(d.t[d.t.length-1]);
    draw(card,d,days?new Date(end-days*864e5).toISOString().slice(0,10):d.t[0])};
  btns.forEach(b=>b.addEventListener('click',()=>go(b)));
  const cur=()=>card.querySelector('.ranges button[aria-pressed="true"]');go(cur());
  let w=card.clientWidth;addEventListener('resize',()=>{if(card.clientWidth!==w){w=card.clientWidth;go(cur())}});
});
"""


def _series(block: dict, cfg: dict, start: date) -> dict:
    out = {"t": [], "c": [], "z": [], "h": [], "v": [], "s": []}
    for point in block["points"]:
        if point.day < start:
            continue
        heat = heat_score(point, cfg)
        out["t"].append(point.day.isoformat())
        out["c"].append(round(point.close, 4 if point.close < 1000 else 1))
        out["z"].append(ZONE_ORDER.index(zone_key(point, cfg)))
        out["h"].append(heat.score)
        out["v"].append(value_score(point, cfg).score)
        out["s"].append(round(heat.sell_fraction * 100))
    return out


def render_dashboard(bundle: dict) -> str:
    cfg = bundle["cfg"]
    cycle = bundle.get("cycle") or {}
    live = bundle.get("live") or {}
    start = date.fromisoformat(cfg["cycle"]["start"])
    data = {"zones": [{"key": key, "name": ZONES[key]} for key in ZONE_ORDER], "assets": {}}
    cards = []
    legend = "".join(
        f'<span><i class="sw" style="background:var(--z-{key})"></i>{html.escape(ZONES[key].capitalize())}</span>'
        for key in ZONE_ORDER
    )
    for asset in ("BTC", "HYPE"):
        block = cycle.get(asset)
        if not block:
            continue
        series = _series(block, cfg, start)
        series["hmax"] = heat_max(asset, cfg)
        data["assets"][asset] = series
        point, heat, value = block["point"], block["heat"], block["value"]
        snap = live.get(asset)
        tranche = "n/a" if snap is None else fmt_idr(snap["tranche"], 2)
        mult = "" if snap is None else fmt_number(snap["v2"].multiplier, 1).replace(",0", "") + "x dari dasar"
        if snap is not None and snap["v2"].invalidated:
            mult = "invalidation nyala"
        sell = "0%" if heat.sell_fraction <= 0 else fmt_number(heat.sell_fraction * 100, 0) + "%"
        rows = []
        placed = False
        for label, price, side in reversed(block["levels"]):
            if not placed and price < point.close:
                rows.append(f'<tr class="now"><td class="n">{fmt_px(point.close)}</td><td class="n"></td><td>harga sekarang</td><td></td></tr>')
                placed = True
            gap = fmt_number((price / point.close - 1) * 100, 1)
            rows.append(
                f'<tr><td class="n">{fmt_px(price)}</td><td class="n">{"+" if price >= point.close else ""}{gap}%</td>'
                f"<td>{html.escape(label)}</td><td>{side}</td></tr>"
            )
        ranges = [("Semua", 0, False), ("4 thn", 1461, asset == "BTC"), ("1 thn", 365, False)]
        if asset != "BTC":
            ranges = [("Semua", 0, True), ("1 thn", 365, False), ("90 hr", 90, False)]
        buttons = "".join(
            f'<button type="button" data-days="{days}" aria-pressed="{"true" if on else "false"}">{name}</button>'
            for name, days, on in ranges
        )
        cards.append(
            f"""<section class="card" data-asset="{asset}">
<div class="head"><h2>{asset} · {fmt_px(point.close)}{" (candle belum tutup)" if block["partial"] else ""}</h2>
<span class="zone"><i class="sw" style="background:var(--z-{block["zone"]})"></i>{ZONES[block["zone"]]}</span></div>
<p class="note">{html.escape(ZONE_TEXT[block["zone"]])}</p>
<div class="tiles">
<div class="tile"><span>Beli per tranche 14 hari</span><b>{tranche}</b><span>{mult}</span></div>
<div class="tile"><span>Jual per tranche 14 hari</span><b>{sell}</b><span>dari koin yang dipegang</span></div>
<div class="tile"><span>Skor panas</span><b>{heat.score} dari {heat_max(asset, cfg)}</b><span>jual mulai di 2</span></div>
<div class="tile"><span>Skor value</span><b>{value.score} dari 4</b><span>drawdown {fmt_number(point.drawdown * 100, 1)}% dari ATH</span></div>
</div>
<div class="bar"><div class="legend" aria-label="Zona">{legend}</div><div class="ranges">{buttons}</div></div>
<div class="plot"><svg role="img" aria-label="Harga {asset} skala log, dengan pita zona siklus di bawahnya"></svg><div class="tip"></div></div>
<p class="note">Garis: harga penutupan harian, skala log. Pita di bawahnya: zona siklus hari itu, dihitung cuma dari data sampai hari itu.</p>
<details><summary>Peta harga: di level mana aturannya berubah</summary><div class="scroll"><table>
<tr><th class="n">Harga</th><th class="n">Jarak</th><th>Level</th><th>Sisi</th></tr>{"".join(rows)}</table></div></details>
</section>"""
        )
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sinyal BTC & HYPE</title><style>{_CSS}</style></head><body><main>
<h1>Sinyal beli & jual: BTC dan HYPE</h1>
<p class="sub">Dibikin {html.escape(bundle["generated"])}. Angka dan buktinya ada di report.md.</p>
{"".join(cards)}
<footer>Catatan DCA pribadi, bukan saran investasi. Sisi jual buktinya tipis: puncak siklus BTC cuma ada empat, dan skor panas nggak nangkap puncak Okt 2025. Baca report.md sebelum dipakai.</footer>
</main><script type="application/json" id="data">{payload}</script><script>{_JS}</script></body></html>
"""
