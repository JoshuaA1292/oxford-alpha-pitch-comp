"""Build the SNDK short pitch deck: HTML (numbers injected from the engine) -> PDF via headless Chrome.

Run:  analysis/.venv/bin/python deck/build_deck.py
Reads:  deck/figures/numbers.json (written by analysis/deck_figures.py) and deck/figures/*.png
Writes: deck/SNDK_short_deck.html, deck/SNDK_short_deck.pdf, deck/preview/p??.png
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "deck"
FIG = DECK / "figures"
N = json.loads((FIG / "numbers.json").read_text())
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

S = N["price"]
sc = {r["name"].split(":")[0]: r for r in N["scen"]["rows"]}
base, bust, bull = sc["Base"], sc["Deep bust"], sc["Against us"]
pp = N["price_path"]
br = N["bridge"]
fl = N["floor"]
mc = N["mc"]
bl = N["bl"]
b_ = N["base_rates"]
rv = N["revisions"]
dm = N["dcf_meta"]
beta = N["beta"]

T = {
    "price": f"${S:,.0f}", "asof": "9 Sep 2026",
    "tgt_base": f"${base['target']:,.0f}", "ret_base": f"{base['target']/S-1:+.0%}", "sr_base": f"{base['short_return']:+.0%}",
    "tgt_bust": f"${bust['target']:,.0f}", "ret_bust": f"{bust['target']/S-1:+.0%}", "sr_bust": f"{bust['short_return']:+.0%}",
    "tgt_bull": f"${bull['target']:,.0f}", "ret_bull": f"{bull['target']/S-1:+.0%}", "sr_bull": f"{bull['short_return']:+.0%}",
    "eps_base": f"${base['fy28_eps']:,.0f}", "eps_bust": f"${bust['fy28_eps']:,.0f}", "eps_bull": f"${bull['fy28_eps']:,.0f}",
    "ev_ret": f"{N['scen']['ev']:+.0%}", "rr": f"{N['scen']['rr']:.1f}",
    "mc_med": f"${mc['median']:,.0f}", "mc_med_ret": f"{mc['median']/S-1:+.0%}", "mc_pct": f"{mc['pct']:.0f}",
    "mc_p5": f"${mc['p5']:,.0f}", "mc_p95": f"${mc['p95']:,.0f}", "mc_p25": f"${mc['p25']:,.0f}", "mc_p75": f"${mc['p75']:,.0f}",
    "mc_pabove": f"{mc['p_above']:.1%}",
    "bl_iv": f"{bl['atm_iv']:.0%}", "bl_ptarget": f"{bl['p_target']:.0%}", "bl_pabove": f"{bl['p_above']:.0%}",
    "bl_p1000": f"{bl['p_below_1000']:.0%}", "bl_p1200": f"{bl['p_below_1200']:.0%}", "bl_rr": f"{bl['rr25']:+.1%}", "bl_n": f"{bl['n_quotes']}",
    "ev": f"${br['ev']:,.0f}bn", "mktcap": f"${dm['mktcap']:,.0f}bn", "pv2": f"${br['pv2']:,.0f}bn", "pv_floor": f"${br['pv_floor']:,.0f}bn",
    "resid": f"${br['resid']:,.0f}bn", "resid_pct": f"{br['resid']/br['ev']:.0%}", "nopat_req": f"${br['nopat_req']:,.1f}bn",
    "gm_req": f"{br['gm_req']:.0%}", "cogs32": f"${br['cogs32']:,.1f}bn", "rev_req": f"${br['rev_req']:,.1f}bn",
    "perp2": f"${N['required']['perp2']:,.1f}bn", "perp5": f"${N['required']['perp5']:,.1f}bn",
    "perp2_lo": f"${N['perp2_by_wacc']['0.10']:,.1f}bn", "perp2_hi": f"${N['perp2_by_wacc']['0.13']:,.1f}bn",
    "pay2_pct": f"{dm['pay2_pct']:.0%}", "pay5_pv": f"${dm['pay5_pv']:,.1f}bn", "pay5_pct": f"{dm['pay5_pct']:.0%}",
    "pay5_resid": f"${dm['pay5_resid']:,.0f}bn", "pay2_resid": f"${dm['pay2_resid']:,.0f}bn",
    "x2014_pay5": f"{N['required']['x2014']['pay5']:.0f}", "x2014_post": f"{N['required']['x2014']['post_contract']:.0f}",
    "floor_rr": f"${fl['run_rate']:,.1f}bn", "floor_all": f"${fl['all_bits']:,.1f}bn", "floor_vs28": f"{fl['vs28']:.0%}",
    "fy27": f"${fl['fy27']:,.1f}bn", "fy28": f"${fl['fy28']:,.1f}bn", "fy28_lo": f"${fl['fy28_lo']:,.1f}bn", "fy28_hi": f"${fl['fy28_hi']:,.1f}bn",
    "eps27": f"${fl['eps27']:,.0f}", "eps28": f"${fl['eps28']:,.0f}", "ni27": f"${fl['ni27']:,.1f}bn", "ni28": f"${fl['ni28']:,.1f}bn",
    "pe27": f"{S/fl['eps27']:.1f}×", "pe28": f"{S/fl['eps28']:.1f}×",
    "nm27": f"{fl['ni27']/fl['fy27']:.0%}", "nm28": f"{fl['ni28']/fl['fy28']:.0%}",
    "br_n": f"{b_['n']}", "br_med": f"{b_['median']:.0f}%", "br_mean": f"{b_['mean']:.0f}%", "br_best": f"{b_['best']:.0f}%",
    "br_neg": f"{b_['neg']}", "br_best3": f"{b_['best3']:.0f}%",
    "beta": f"{beta['beta']:.2f}", "r2": f"{beta['r2']:.0%}", "idio": f"{beta['idio_vol']:.0%}",
    "sop30": f"${N['sop']['0.30']:,.0f}", "sop40": f"${N['sop']['0.40']:,.0f}", "sop50": f"${N['sop']['0.50']:,.0f}",
    "sop60": f"${N['sop']['0.60']:,.0f}", "sop70": f"${N['sop']['0.70']:,.0f}", "sop80": f"${N['sop']['0.80']:,.0f}",
    "eps28_90": f"${rv['fy28'][0]:,.0f}", "eps28_now": f"${rv['fy28'][-1]:,.0f}", "eps28_chg": f"{rv['fy28'][-1]/rv['fy28'][0]-1:+.0%}",
    "px_90": f"${rv['px'][0]:,.0f}", "px_chg90": f"{rv['px'][-1]/rv['px'][0]-1:+.0%}",
    "from_low": f"{pp['from_low']:+.0%}", "from_high": f"{pp['from_high']:.0%}", "ytd": f"{pp['ytd']:+.0%}",
    "dd": f"{pp['drawdown_close']:.0%}", "low_close": f"${pp['low_close']:,.0f}", "high": f"${pp['high']:,.0f}",
    "kx_lo": "$940", "kx_hi": "$1,080",
    "val40": f"${dm['val40']:,.0f}",
    "mc60_pct": f"{N['mc60']['pct']:.0f}", "mc60_pabove": f"{N['mc60']['p_above']:.0%}", "mc60_med": f"${N['mc60']['median']:,.0f}",
    "cone1": f"±{N['iv_cone']['1']:.0%}", "cone3": f"±{N['iv_cone']['3']:.0%}", "cone6": f"±{N['iv_cone']['6']:.0%}",
}
fy29 = next(r for r in N["dcf_table"] if r["fy"] == 29)
T.update({"fy29_rev": f"${fy29['rev']:,.1f}bn", "fy29_gm": f"{fy29['gm']:.0%}", "fy29_nopat": f"${fy29['nopat']:,.1f}bn",
          "fy29_eps": f"${fy29['nopat']*1e9/(dm['shares']*1e6):,.0f}",
          "fy29_7x": f"${7*fy29['nopat']*1e9/(dm['shares']*1e6):,.0f}", "fy29_9x": f"${9*fy29['nopat']*1e9/(dm['shares']*1e6):,.0f}"})
pc = N["mc_pctiles"]
T["mc_pct_row"] = "".join(f"<td class=n>${pc[k]:,.0f}</td>" for k in ("p5", "p10", "p25", "p50", "p75", "p90", "p95"))
# worked arithmetic for case A
pvA27, pvA28 = fl["ni27"] / 1.11, fl["ni28"] / 1.11 ** 2
T.update({"pvA27": f"{pvA27:,.1f}", "pvA28": f"{pvA28:,.1f}", "ni27n": f"{fl['ni27']:,.1f}", "ni28n": f"{fl['ni28']:,.1f}",
          "resid2n": f"{dm['pay2_resid']:,.1f}", "evn": f"{br['ev']:,.1f}", "perp2n": f"{N['required']['perp2']:,.1f}"})


def dcf_rows():
    out = []
    for r in N["dcf_table"]:
        seg = "consensus" if r["fy"] <= 28 else ("floor + mid-cycle" if r["fy"] <= 31 else "mid-cycle 40%")
        gm = "—" if r["gm"] is None else f"{r['gm']:.0%}"
        out.append(f"<tr><td>FY{r['fy']}</td><td>{seg}</td><td class=n>{r['rev']:,.1f}</td><td class=n>{gm}</td>"
                   f"<td class=n>{r['cogs']:,.1f}</td><td class=n>{r['opex']:,.2f}</td><td class=n>{r['nopat']:,.1f}</td><td class=n>{r['fcf']:,.1f}</td></tr>")
    return "\n".join(out)


def grid_rows(g, fmt):
    out = []
    for i, gm in enumerate(g["rows"]):
        cells = "".join(f"<td class='n {'hi' if v > S else 'lo'}'>${v:,.0f}</td>" for v in g["vals"][i])
        out.append(f"<tr><th>{gm:.0%}</th>{cells}</tr>")
    return "\n".join(out), "".join(f"<th class=n>{fmt(c)}</th>" for c in g["cols"])


gbg_rows, gbg_head = grid_rows(N["grid_bg"], lambda c: f"{c:.0%}")
gw_rows, gw_head = grid_rows(N["grid_w"], lambda c: f"{c:.0%}")
T["dcf_rows"] = dcf_rows()
T["gbg_rows"], T["gbg_head"] = gbg_rows, gbg_head
T["gw_rows"], T["gw_head"] = gw_rows, gw_head
br_table = sorted(b_["table"], key=lambda r: (r["co"], r["yr"]))
by_co = {}
for r in br_table:
    by_co.setdefault(r["co"], []).append(r)
T["br_rows"] = "\n".join(
    f"<tr><td>{co}</td><td>{', '.join(f'{r['yr']} {r['om']:+.0f}%' for r in rows)}</td></tr>" for co, rows in by_co.items())

CSS = """
<style>
@page { size: 1280px 720px; margin: 0; }
html, body { margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
* { box-sizing: border-box; }
body { font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif; color: #14213D; background: #fff; }
.slide { width: 1280px; height: 720px; page-break-after: always; break-after: page; position: relative; overflow: hidden;
         background: #fff; padding: 22px 40px 22px; display: flex; flex-direction: column; }
.slide:last-child { page-break-after: auto; }
.hdr { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #14213D; padding-bottom: 6px; margin-bottom: 11px; }
.kicker { font-size: 9.5px; letter-spacing: .14em; text-transform: uppercase; color: #B5382F; font-weight: 600; margin-bottom: 3px; }
.kicker.app { color: #4A5468; }
h1 { font-size: 19.5px; margin: 0; font-weight: 700; line-height: 1.2; letter-spacing: -.01em; }
.tag { font-size: 9px; color: #4A5468; text-align: right; line-height: 1.3; white-space: nowrap; }
.tag b { color: #B5382F; font-size: 11px; letter-spacing: .06em; }
.body { flex: 1; display: grid; gap: 11px; min-height: 0; }
.panel { border: 1px solid #E4E6EA; border-radius: 6px; overflow: hidden; display: flex; flex-direction: column; min-height: 0; background: #fff; }
.ph { background: #14213D; color: #fff; font-size: 11px; font-weight: 600; padding: 4px 9px; letter-spacing: .02em; flex: none; }
.ph.red { background: #B5382F; } .ph.blue { background: #2A5DB0; } .ph.grey { background: #4A5468; }
.pc { padding: 8px 10px; font-size: 11px; line-height: 1.36; flex: 1; min-height: 0; display: flex; flex-direction: column; }
.pc.tight { padding: 4px 6px; }
.pc.spread { justify-content: space-between; }
.figbox { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }
.figbox img { max-width: 100%; max-height: 100%; object-fit: contain; }
.ftr { display: flex; justify-content: space-between; align-items: flex-end; font-size: 7.4px; color: #8A8F98; margin-top: 8px; gap: 20px; }
.ftr .pg { font-size: 9px; color: #14213D; font-weight: 600; flex: none; }
.stat .v { font-size: 27px; font-weight: 700; line-height: 1.05; letter-spacing: -.02em; }
.stat .v.red { color: #B5382F; } .stat .v.blue { color: #2A5DB0; }
.stat .l { font-size: 9.6px; color: #4A5468; line-height: 1.25; margin-top: 2px; }
.stats { display: grid; gap: 8px; }
table { border-collapse: collapse; width: 100%; font-size: 10px; }
th { text-align: left; background: #F3F4F7; font-weight: 600; padding: 3px 5px; border-bottom: 1px solid #E4E6EA; color: #14213D; }
td { padding: 3px 5px; border-bottom: 1px solid #EEF0F3; vertical-align: top; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
tr.hl td { background: #FBF3F2; font-weight: 600; }
td.hi { background: #DCE6F6; font-weight: 600; } td.lo { background: #F7E6E4; }
.callout { background: #FBF3F2; border-left: 3px solid #B5382F; padding: 7px 10px; font-size: 11px; line-height: 1.35; border-radius: 0 4px 4px 0; }
.callout.blue { background: #EEF3FB; border-left-color: #2A5DB0; }
.callout.ink { background: #14213D; color: #fff; border-left-color: #C9A227; }
.quote { border-left: 3px solid #2A5DB0; padding: 3px 8px; margin: 0 0 7px; font-size: 10.6px; font-style: italic; line-height: 1.3; }
.quote .who { font-style: normal; color: #4A5468; font-size: 8.6px; display: block; margin-top: 1px; }
ul { margin: 0; padding-left: 13px; } li { margin-bottom: 3px; } ul.tight li { margin-bottom: 1.5px; }
b.r { color: #B5382F; } b.b { color: #2A5DB0; } .mut { color: #4A5468; } .sm { font-size: 9.8px; }
.pill { display: inline-block; font-size: 8px; font-weight: 600; padding: 1px 6px; border-radius: 9px; background: #EEF0F3; color: #4A5468; margin-right: 3px; }
.pill.red { background: #F7E6E4; color: #B5382F; } .pill.blue { background: #DCE6F6; color: #2A5DB0; } .pill.gold { background: #F6EFD6; color: #7A5E10; }
.num { display: inline-block; width: 17px; height: 17px; border-radius: 50%; background: #B5382F; color: #fff; font-size: 10px; font-weight: 700; text-align: center; line-height: 17px; margin-right: 6px; flex: none; }
.num.blue { background: #2A5DB0; } .num.ink { background: #14213D; }
.pillar { border: 1px solid #E4E6EA; border-radius: 6px; padding: 8px 10px; font-size: 10.6px; line-height: 1.36; }
.pillar h3 { font-size: 11.2px; margin: 0 0 3px; display: flex; align-items: center; }
.h3 { font-size: 11px; font-weight: 700; margin: 0 0 3px; color: #14213D; }
.h3.red { color: #B5382F; } .h3.blue { color: #2A5DB0; }
.flow { display: grid; grid-template-columns: 1fr 24px 1.25fr 24px 1fr; align-items: center; gap: 4px; font-size: 9px; }
.box { border: 1.5px solid #14213D; border-radius: 5px; padding: 5px 7px; text-align: center; line-height: 1.25; }
.box.red { border-color: #B5382F; background: #FBF3F2; } .box.blue { border-color: #2A5DB0; background: #EEF3FB; }
.arrow { text-align: center; font-size: 15px; color: #4A5468; }
.kill li { margin-bottom: 4px; }
.tl { font-size: 10px; } .tl td:first-child { white-space: nowrap; font-weight: 600; }
/* cover */
.cover { padding: 0; }
.cover .inner { margin: 190px 0 0 96px; }
.cover .logo svg { width: 440px; height: auto; display: block; }
.cover-title { font-size: 40px; font-weight: 700; margin-top: 34px; padding-bottom: 10px; border-bottom: 3px solid #14213D; display: inline-block; letter-spacing: -.01em; }
.cover-title .short { color: #B5382F; }
.cover-line { font-size: 27px; margin-top: 20px; font-weight: 400; }
.cover-line b { font-weight: 600; }
.cover-line .short { color: #B5382F; }
.cover-line .mut { color: #4A5468; }
.cover-sub { font-size: 17px; color: #4A5468; font-style: italic; margin-top: 26px; }
.cover-foot { position: absolute; left: 96px; right: 40px; bottom: 26px; display: flex; justify-content: space-between; align-items: flex-end; font-size: 10px; color: #4A5468; border-top: 1px solid #E4E6EA; padding-top: 10px; }
.cover-foot .pg { font-size: 9px; font-weight: 600; color: #14213D; }
.cover-rule { position: absolute; left: 0; top: 0; width: 14px; height: 720px; background: #14213D; }
</style>
"""


def slide(kicker, title, body, sources, page, app=False):
    tag = "APPENDIX · for Q&A, not presented" if app else "SHORT SNDK"
    return f"""
<section class="slide">
  <div class="hdr">
    <div><div class="kicker{' app' if app else ''}">{kicker}</div><h1>{title}</h1></div>
    <div class="tag"><b>{tag}</b><br>Oxford Alpha Fund · Varsity Pitch 2026<br>Prices and consensus as of [[asof]]</div>
  </div>
  <div class="body" style="{body[0]}">{body[1]}</div>
  <div class="ftr"><div>{sources}</div><div class="pg">{page}</div></div>
</section>"""


SLIDES = []

# ------------------------------------------------------------------ 1. title page
LOGO_SVG = (DECK / "assets" / "sandisk_logo.svg").read_text()
SLIDES.append("""
<section class="slide cover">
  <div class="cover-rule"></div>
  <div class="inner">
    <div class="logo">""" + LOGO_SVG + """</div>
    <div class="cover-title"><span class="short">SHORT</span> SanDisk Corporation (NASDAQ: SNDK)</div>
    <div class="cover-line">Current Price: <b>[[price]]</b> <span class="mut">(09/09/2026)</span></div>
    <div class="cover-line">Target Price: <b>[[tgt_base]]</b> <span class="short">([[ret_base]] downside)</span></div>
    <div class="cover-sub">For Varsity Pitch Competition 2026</div>
  </div>
  <div class="cover-foot"><span>Oxford Alpha Fund · Varsity Pitch Competition 2026 · Final, 15 October 2026, London</span><span class="pg">1</span></div>
</section>""")

# ------------------------------------------------------------------ 2. pitch summary
SLIDES.append(slide(
    "Pitch summary",
    "The market has capitalised a five-year contract as a perpetuity",
    ("grid-template-columns: 1fr 1.5fr;", """
  <div class="panel">
    <div class="ph red">Recommendation and thesis</div>
    <div class="pc spread">
      <table style="margin-bottom:8px">
        <tr><td>Price ([[asof]]) · market cap · EV</td><td class=n><b>[[price]]</b> · [[mktcap]] · [[ev]]</td></tr>
        <tr class="hl"><td>12-month base target · scenario range</td><td class=n>[[tgt_base]] ([[ret_base]]) · [[tgt_bust]] – [[tgt_bull]]</td></tr>
        <tr><td>Probability-weighted short return · reward/risk</td><td class=n><b>[[ev_ret]]</b> · [[rr]] : 1</td></tr>
        <tr><td>Intrinsic value (Monte Carlo median) · price percentile</td><td class=n>[[mc_med]] · [[mc_pct]]th</td></tr>
        <tr><td>P/E FY27E · FY28E · price/book</td><td class=n>[[pe27]] · [[pe28]] · 16.7×</td></tr>
        <tr><td>Short interest · borrow · β vs SMH</td><td class=n>5.3% · 0.28% · [[beta]]</td></tr>
      </table>
      <div class="callout" style="margin-bottom:8px">Pay the Street's boom in full, pay the $93.9bn contract floor in full through FY31, and today's price still needs <b>[[nopat_req]] of profit a year, forever</b>, from a business whose best pre-2026 year earned <b>$1.6bn</b>. The contracts have an expiry date; the price does not.</div>
      <div class="pillar" style="margin-bottom:6px"><h3><span class="num">1</span>The floors are far below consensus</h3>$93.9bn over ~4.5 years is [[floor_rr]]/yr for ~2/3 of bits. Floor pricing on <i>every</i> bit is [[floor_all]]/yr, <b class="r">[[floor_vs28]]</b> vs FY28 consensus of [[fy28]]. Only $2.7bn of the $16.5bn of "guarantees" is on SanDisk's balance sheet.</div>
      <div class="pillar" style="margin-bottom:6px"><h3><span class="num">2</span>The earnings are price, and price has stopped accelerating</h3>Consensus FY27 is +142% revenue on +15% bits. Contract prices went +55–60% → +70–75% → +10–15% QoQ; August +1.4%; spot wafers now falling. Every dated primary forecast puts the supply crossover in 2H27.</div>
      <div class="pillar"><h3><span class="num">3</span>Even the bulls' normalised numbers do not reach the price</h3>Morgan Stanley's through-cycle EPS needs a 23× multiple to justify [[price]]. Across [[br_n]] documented NAND company-years the median operating margin is [[br_med]]; management's model assumes ~75% indefinitely. Kioxia, co-owner of the same fabs, trades at 4.4× earnings vs SanDisk's 8.2×.</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">$36 → [[high]] → [[low_close]] → [[price]] in nineteen months</div>
    <div class="pc" style="display:grid; grid-template-rows: 1fr auto; gap:6px;">
      <div class="figbox"><img src="figures/price_path.png"></div>
      <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:8px; font-size:9.4px; line-height:1.3;">
        <div><div class="h3 blue">Why the mispricing exists</div>A true four-year story ("contracted, non-cyclical") priced as permanence; estimates marked to spot; index and pod ownership after a 30× market-cap increase; an 18-month-old listing with no memory of losing $2.1bn in a bad year.</div>
        <div><div class="h3 red">Why it is uncrowded</div>Short interest 5.3% of float (FINRA 14 Aug), ~1 day to cover, borrow 0.28% GC; 20 of 24 analysts at Buy, mean target $2,125; 128 hedge funds hold $25.6bn. Druckenmiller and Tepper exited in Q2.</div>
        <div><div class="h3">Why now</div>Micron prints 30 Sep, TrendForce's first 4Q26 NAND number early Oct, hyperscaler Q3 late Oct, SanDisk FQ1 on 6 Nov. Entry after the 21 Sep S&P 100 inclusion.</div>
      </div>
    </div>
  </div>"""),
    "Sources: Yahoo/LSEG consensus and CBOE quotes ([[asof]]); SanDisk FQ4-FY26 release and call (5 Aug 2026), FY26 10-K; FINRA short interest (14 Aug 2026); 13F aggregates Q2-26. Model numbers from analysis/sndk_contract_dcf.py.",
    "2"))

# ------------------------------------------------------------------ 3. business model
SLIDES.append(slide(
    "Business model",
    "A fab-less NAND pure-play whose income statement is a price, with $93.9bn of contracted floors through FY31",
    ("grid-template-columns: 1.15fr 1fr 1.1fr; grid-template-rows: 1fr 1fr;", """
  <div class="panel" style="grid-row: 1 / 3;">
    <div class="ph">The business in brief</div>
    <div class="pc">
      <ul class="tight" style="margin-bottom:7px">
        <li><b>NAND flash only.</b> Spun out of Western Digital on 13 Feb 2025 at $36. No DRAM, no HBM. Products: enterprise SSD, client SSD, consumer cards and drives, embedded mobile. Datacenter is ~38% of bits and the growth engine; Consumer fell 32% QoQ in FQ4.</li>
        <li><b>It does not own its fabs.</b> Every wafer comes from Flash Ventures, the 49.9% JV with Kioxia (Yokkaichi, Kitakami). SanDisk pays <b>half of the JV's fixed costs regardless of output</b>; $6.6bn of JV commitments FY27–31; $923m lease guarantees. Capex on its own books is ~$0.2bn a year.</li>
        <li><b>FY26 (Jun):</b> revenue $20.2bn (+175%), gross margin 71.5%, operating income $12.5bn, net income $11.4bn, FCF $11.5bn; cash $4.8bn, debt $0.2bn; $4.5bn bought back at ~24× trailing; $15.5bn authorisation remains.</li>
        <li><b>FQ1-FY27 guide:</b> revenue $10.5–11.2bn, gross margin <b>83–85%</b>, opex $520–540m per quarter, non-GAAP tax 15%.</li>
      </ul>
      <table style="margin-bottom:6px">
        <tr><th>FY (Jun), $bn</th><th class=n>FY23</th><th class=n>FY24</th><th class=n>FY25</th><th class=n>FY26</th><th class=n>FY27E</th><th class=n>FY28E</th></tr>
        <tr><td>Revenue</td><td class=n>6.1</td><td class=n>6.7</td><td class=n>7.4</td><td class=n>20.2</td><td class=n><b>49.0</b></td><td class=n><b>57.8</b></td></tr>
        <tr><td>Gross margin</td><td class=n>7%</td><td class=n>16%</td><td class=n>30%</td><td class=n>71%</td><td class=n>~83%</td><td class=n>~80%</td></tr>
        <tr><td>Operating income</td><td class=n>−1.3</td><td class=n>−0.4</td><td class=n>0.5</td><td class=n>12.5</td><td class=n>—</td><td class=n>—</td></tr>
        <tr><td>Net income</td><td class=n>−2.1</td><td class=n>−0.7</td><td class=n>−1.6</td><td class=n>11.4</td><td class=n><b>[[ni27]]</b></td><td class=n><b>[[ni28]]</b></td></tr>
        <tr><td>EPS · P/E at [[price]]</td><td class=n>−14.78</td><td class=n>−4.63</td><td class=n>−11.32</td><td class=n>73.7 · 24×</td><td class=n>[[eps27]] · [[pe27]]</td><td class=n>[[eps28]] · [[pe28]]</td></tr>
      </table>
      <div class="sm mut" style="margin-bottom:8px">Three losses in three years, then the best year any NAND company has printed. FY27–28 are Yahoo/LSEG consensus (19–20 analysts); FY28 revenue estimates span [[fy28_lo]] to [[fy28_hi]].</div>
      <div class="h3">What the FQ1 guide annualises to</div>
      <table style="margin-bottom:5px">
        <tr><th>FQ1-FY27 guide, midpoint</th><th class=n>Quarter</th><th class=n>× 4</th></tr>
        <tr><td>Revenue $10.5–11.2bn</td><td class=n>$10.85bn</td><td class=n>$43.4bn</td></tr>
        <tr><td>Gross profit at 84% GM</td><td class=n>$9.1bn</td><td class=n>$36.5bn</td></tr>
        <tr><td>Operating income after $530m opex</td><td class=n>$8.6bn</td><td class=n>$34.4bn</td></tr>
        <tr><td>Net income at 15% tax · EPS</td><td class=n>$7.3bn · $50</td><td class=n>$29.2bn · $200</td></tr>
      </table>
      <div class="sm mut">Consensus FY27 ([[fy27]] revenue, [[eps27]] EPS) needs pricing to keep rising through FY27, not just hold (slide 7).</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph blue">Five quarters that made the multiple</div>
    <div class="pc tight"><div class="figbox"><img src="figures/quarterly_pnl.png"></div></div>
  </div>
  <div class="panel" style="grid-column: 2; grid-row: 2;">
    <div class="ph">Capital allocation at the top of the cycle</div>
    <div class="pc">
      <table style="margin-bottom:6px">
        <tr><th>FY26 cash</th><th class=n>$bn</th><th>Note</th></tr>
        <tr><td>Free cash flow</td><td class=n>11.5</td><td>from −0.1 in FY25</td></tr>
        <tr><td>Buyback executed (FQ4)</td><td class=n>4.5</td><td>at ~24× trailing earnings</td></tr>
        <tr><td>Authorisation remaining</td><td class=n>15.5</td><td>≈ 6% of shares at $1,700</td></tr>
        <tr><td>JV commitments FY27–31</td><td class=n>6.6</td><td>unconditional</td></tr>
        <tr><td>Share of ¥5tn Japan plan</td><td class=n>~15</td><td>Fab 3 output FY2029</td></tr>
        <tr><td>Inventory · days</td><td class=n>2.7 · 178</td><td>vs ~135 a year ago</td></tr>
      </table>
      <div class="sm">Micron bought back heavily in 2018 and 2022 at its cycle tops; the stock halved each time. Peak cash flow is being committed to shares at peak multiples and to fabs that arrive after the crossover.</div>
    </div>
  </div>
  <div class="panel" style="grid-column: 3; grid-row: 1 / 3;">
    <div class="ph red">The contract book: 10 "New Business Model" agreements (5 Aug 2026)</div>
    <div class="pc">
      <table style="margin-bottom:6px">
        <tr><th>Term</th><th>Disclosure</th></tr>
        <tr><td>Agreements / customers</td><td>10 NBM agreements with 8 customers (hyperscalers, OEMs)</td></tr>
        <tr class="hl"><td>Minimum revenue</td><td><b>$93.9bn</b> "assuming floor pricing"</td></tr>
        <tr><td>Duration</td><td>Up to 5 years; weighted average <b>over 4 years</b> → FY27–FY31</td></tr>
        <tr><td>Bit coverage</td><td>>50% of FY27 bits; <b>~2/3 of FY28 bits</b> (Citi, 8 Sep: "50% by end-FY28")</td></tr>
        <tr><td>Margin at floor</td><td>"around <b>80%</b> gross margin, even at floor pricing"</td></tr>
        <tr><td>Guarantees</td><td><b>$16.5bn</b> of customer financial guarantees; <b>$2.7bn</b> of it on SanDisk's balance sheet</td></tr>
        <tr><td>Already re-opened</td><td>2 of 8 customers (one extended, one added volume)</td></tr>
        <tr><td>Pricing above floor</td><td>Floors plus market-linked uplift; the uncontracted third of bits is at spot</td></tr>
      </table>
      <div class="flow" style="margin-bottom:6px">
        <div class="box blue">Kioxia<br><span class="sm">50.1% · TSE 285A<br>3.1× sales · 4.4× P/E</span></div>
        <div class="arrow">⇄</div>
        <div class="box">Flash Ventures JV<br><span class="sm">Yokkaichi + Kitakami fabs<br>BiCS8/BiCS10 · ¥5tn plan, Fab 3 FY29</span></div>
        <div class="arrow">⇄</div>
        <div class="box red">SanDisk<br><span class="sm">49.9% · pays ½ fixed costs<br>5.2× sales · 8.2× P/E</span></div>
      </div>
      <table style="margin-bottom:6px">
        <tr><th>Floor vs consensus, per bit</th><th class=n></th></tr>
        <tr><td>Floor revenue per year ($93.9bn ÷ 5) for ~2/3 of FY28 bits</td><td class=n>$18.8bn</td></tr>
        <tr><td>Floor price applied to 100% of bits</td><td class=n>~$28bn</td></tr>
        <tr class="hl"><td>FY28 consensus revenue per bit ÷ floor price per bit</td><td class=n>~2.0×</td></tr>
        <tr><td>If covered bits earn only the floor, the uncovered third must earn</td><td class=n>~4× floor</td></tr>
      </table>
      <div class="callout">The contracts are real for four years. The pitch is not that the floors break; it is that the price already assumes something <b>better than the floors, permanently</b> (slide 5).</div>
    </div>
  </div>"""),
    "Sources: SanDisk FQ4-FY26 press release and call (5 Aug 2026, SEC 0001628280-26-053346); FY26 10-K (17 Aug 2026); Citi TMT fireside (8 Sep 2026); Investor Day long-term model (13 Aug 2026); Kioxia/SanDisk ¥5tn Japan plan (27 Aug 2026); Yahoo/LSEG consensus [[asof]].",
    "3"))

# ------------------------------------------------------------------ 4. industry and what is priced in
SLIDES.append(slide(
    "Industry overview and what is priced in",
    "The bull case in the bulls' own words, and none of it changes what the price requires after 2031",
    ("grid-template-columns: 1.1fr 1fr 1.05fr;", """
  <div class="panel">
    <div class="ph blue">Demand changed in kind; supply is capped to 2028</div>
    <div class="pc" style="display:grid; grid-template-rows: auto 1fr; gap:6px">
      <div>
        <div class="quote">"We are unlikely to see any significant increase in incremental supply through 2028."<span class="who">Samsung, Q2 2026 call, 30 Jul 2026</span></div>
        <div class="quote">Bits are "on allocation beyond calendar 2027."<span class="who">SanDisk management, FQ4 call, 5 Aug 2026</span></div>
        <ul class="tight">
          <li><b>Enterprise SSD went from 26% to 48% of NAND bits in a year.</b> Nvidia's Vera Rubin rack specifies 16 TB of NAND per GPU; HDD is sold out into 2028.</li>
          <li><b>Hyperscaler capex ~$775–800bn in 2026</b>, all five signalling higher 2027.</li>
          <li><b>No greenfield NAND wafers before 2H28</b>; Samsung and SK hynix cut NAND wafer starts to fund HBM; 2026 NAND capex +5% vs DRAM +14%.</li>
          <li><b>Contracts everywhere:</b> SanDisk $93.9bn floors; Micron $100bn take-or-pay; Samsung 60–70% of capacity under 3-year-plus deals.</li>
        </ul>
        <div class="h3 blue" style="margin-top:6px">Management's FY28–30 model (Investor Day, 13 Aug)</div>
        <div class="sm">Mid/high-teens revenue growth · ~80% gross margin · <b>~75% operating margin</b> · ~50% FCF margin · 100% of excess cash returned.</div>
      </div>
      <div class="figbox"><img src="figures/targets_strip.png"></div>
    </div>
  </div>
  <div class="panel">
    <div class="ph blue">"The stock is already priced for a cliff"</div>
    <div class="pc">
      <div class="stats" style="grid-template-columns: 1fr 1fr; margin-bottom:8px">
        <div class="stat"><div class="v blue">[[pe27]]</div><div class="l">FY27 consensus P/E ([[pe28]] FY28). "Cheap" is the whole bull valuation argument.</div></div>
        <div class="stat"><div class="v blue">$2,125</div><div class="l">Mean of 23 sell-side targets ($1,000–3,600); 20 of 24 ratings are Buy, 1 Sell</div></div>
        <div class="stat"><div class="v blue">9×</div><div class="l">Citi's multiple "like a mature cyclical", which still clears spot on consensus FY28</div></div>
        <div class="stat"><div class="v blue">$214</div><div class="l">Bernstein FY30 EPS in a floor-stress case ($0.11/GB on uncovered bits): price is ~8× a "protected trough"</div></div>
      </div>
      <table style="margin-bottom:7px">
        <tr><th>Who owns it</th><th class=n></th></tr>
        <tr><td>Institutional ownership</td><td class=n>81%</td></tr>
        <tr><td>Hedge funds (Q2-26 13F) · value held</td><td class=n>128 · $25.6bn</td></tr>
        <tr><td>Short interest (FINRA 14 Aug) · days to cover</td><td class=n>5.3% · ~1</td></tr>
        <tr><td>Index events</td><td class=n>MSCI 31 Aug · S&P 100 21 Sep</td></tr>
        <tr><td>Company buyback, FQ4 · remaining</td><td class=n>$4.5bn · $15.5bn</td></tr>
      </table>
      <div class="callout blue" style="margin-bottom:7px">The market is not naïve about the cycle: an 8× multiple <i>is</i> the market pricing the boom's end. The debate is the <b>terminal value</b>, ~70% of the enterprise value, and that is where we disagree.</div>
      <div class="sm"><b>Who makes NAND.</b> Samsung, SK hynix + Solidigm, the Kioxia + SanDisk JV, Micron, and YMTC (14% bit share). In 2026 Samsung and SK hynix diverted wafer starts to HBM, the JV moved to BiCS10, Micron's greenfield fab lands 2H28, and YMTC pulled Wuhan Fab 3 into 2H26 (slide 7).</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Estimates follow price: the boom is marked to spot</div>
    <div class="pc" style="display:grid; grid-template-rows: 1fr 1fr auto; gap:4px">
      <div class="figbox"><img src="figures/reflexive_estimates.png"></div>
      <div class="figbox"><img src="figures/consensus_path.png"></div>
      <div class="sm">Consensus FY28 EPS moved from [[eps28_90]] to [[eps28_now]] ([[eps28_chg]]) in 90 days while the stock round-tripped [[px_90]] → $1,238 → [[price]]. Morgan Stanley's "through-cycle" EPS went $30 → $48 → $76 in four months. FY27–28 numbers are derived from spot; "normalised" numbers are derived from spot; the price is validated by numbers derived from the price. EPS-upgrade breadth has fallen from 92% to 77%.</div>
    </div>
  </div>"""),
    "Sources: Samsung Q2-26 call (30 Jul); SanDisk FQ4 call (5 Aug) and Investor Day (13 Aug); Micron FQ3 call and SCA disclosures (24 Jun); TrendForce (21 Jul, 30 Jul); Nvidia Vera Rubin specifications; sell-side frameworks as reported (Citi, Bernstein, Morgan Stanley, Goldman); Yahoo/LSEG estimate history and recommendations ([[asof]]); FINRA; 13F aggregates.",
    "4"))

# ------------------------------------------------------------------ 5. signature
SLIDES.append(slide(
    "The variant view",
    "Pay the Street in full, then pay the contracts in full: the residual still needs [[nopat_req]] a year, forever",
    ("grid-template-columns: 1.25fr 1fr; grid-template-rows: 1fr auto;", """
  <div class="panel">
    <div class="ph red">Enterprise value bridge at 11% WACC: consensus FY27–28 net income and the NBM floor paid in full</div>
    <div class="pc tight"><div class="figbox"><img src="figures/priced_in_bridge.png"></div></div>
  </div>
  <div class="panel">
    <div class="ph">The perpetual profit the residual requires vs everything NAND has ever earned</div>
    <div class="pc tight"><div class="figbox"><img src="figures/required_vs_history.png"></div></div>
  </div>
  <div class="panel" style="grid-column: 1 / -1;">
    <div class="ph grey">Three ways to read the same enterprise value of [[ev]]</div>
    <div class="pc" style="display:grid; grid-template-columns: 1.7fr 1fr; gap:12px;">
      <table>
        <tr><th>What you pay for</th><th class=n>PV at 11%</th><th class=n>Share of EV</th><th class=n>Residual EV</th><th>Perpetual NOPAT the residual needs</th></tr>
        <tr><td><b>A.</b> Consensus FY27–28 net income ([[ni27]], [[ni28]])</td><td class=n>[[pv2]]</td><td class=n>[[pay2_pct]]</td><td class=n>[[pay2_resid]]</td><td><b>[[perp2]]/yr from FY29, forever</b> ([[perp2_lo]]–[[perp2_hi]] across 10–13% WACC)</td></tr>
        <tr><td><b>B.</b> Five full peak years FY27–31: FY28 consensus held flat for the whole contract life ($187bn of net income)</td><td class=n>[[pay5_pv]]</td><td class=n>[[pay5_pct]]</td><td class=n>[[pay5_resid]]</td><td><b>[[perp5]]/yr from FY32, forever</b> = [[x2014_pay5]]× SanDisk's best pre-2026 year</td></tr>
        <tr class="hl"><td><b>C.</b> Consensus FY27–28 + NBM floor ($18.8bn/yr at 80% GM) FY29–31, uncontracted bits at 40% GM</td><td class=n>${pv_paid}bn</td><td class=n>{pv_paid_pct}</td><td class=n>[[resid]]</td><td><b>[[nopat_req]]/yr from FY32</b> = a permanent <b>[[gm_req]] gross margin</b> on a [[cogs32]] cost base</td></tr>
      </table>
      <div>
        <div class="callout" style="margin-bottom:6px">Row B: grant management's entire long-term model for five years, 75% operating margins on $58bn of revenue, and you have paid for <b>[[pay5_pct]]</b> of the enterprise value. The rest is a claim on FY2032 onward that needs <b>[[perp5]] of after-tax profit every year, indefinitely</b>.</div>
        <div class="sm">The entire NAND industry, all five producers, earned an estimated $17–21bn of operating profit in its best pre-2026 year (2018) and $12–15bn in 2021–22. Goldman's "normalised" SanDisk ($110 EPS = $16bn) is <i>below</i> what the price needs as a floor for eternity. Terminal growth 2%, tax 15% (guided), 11% WACC (10–13% band on A1).</div>
      </div>
    </div>
  </div>""".replace("{pv_paid}", f"{br['pv_paid']:,.0f}").replace("{pv_paid_pct}", f"{br['pv_paid']/br['ev']:.0%}")),
    "Sources: analysis/sndk_contract_dcf.py (sections A, B, C′); consensus FY27/28 net income = EPS × 146.4m shares (Yahoo/LSEG, [[asof]]); NBM floor $93.9bn and ~80% GM at floor from the FQ4-FY26 call; SanDisk FY2014 10-K ($1.56bn operating income); Micron FY2022 10-K; industry profit pool estimated from Samsung, SK hynix, Kioxia, Micron, WDC segment disclosures.",
    "5"))

# ------------------------------------------------------------------ 6. pillar 1
SLIDES.append(slide(
    "Thesis 1 · The floors are far below consensus",
    "Floor pricing on every bit is [[floor_all]] a year, [[floor_vs28]] below FY28 consensus, and the \"$16.5bn of guarantees\" is $2.7bn of cash",
    ("grid-template-columns: 1.1fr 1fr 1fr;", """
  <div class="panel">
    <div class="ph red">$93.9bn ÷ ~4.5 years ÷ ~2/3 coverage, against the Street</div>
    <div class="pc" style="display:grid; grid-template-rows: 1fr auto; gap:6px">
      <div class="figbox"><img src="figures/floor_vs_consensus.png"></div>
      <div class="sm"><b>What consensus must therefore assume:</b> the <i>uncontracted</i> third of bits and the variable portion of the contracts stay at 2026 spot economics through FY28, the exact prices Kioxia's CEO now says "have already risen enough." FY28 revenue estimates span [[fy28_lo]]–[[fy28_hi]]; the low end is still 37% above the all-bits floor.</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Guarantee mechanics: what is actually on the balance sheet</div>
    <div class="pc" style="display:grid; grid-template-rows: auto 1fr; gap:6px">
      <div class="figbox" style="height:200px"><img src="figures/guarantees.png"></div>
      <div>
        <div class="h3 red">Enforceability is untested, in both directions</div>
        <ul class="tight sm" style="margin-bottom:7px">
          <li>Two of eight NBM customers have already re-opened terms (one extended, one added volume). Contracts that can be re-opened <i>up</i> can be re-opened <i>down</i>.</li>
          <li>Prior-generation memory LTAs: "minimal enforceability — buyers could reduce volumes or breach with limited consequences" (Goldman). No 2019 or 2023 LTA was tested at scale.</li>
          <li>SanDisk's own obligation is unconditional: half of Flash Ventures' fixed costs whether or not the customer takes the bits.</li>
        </ul>
        <table>
          <tr><th>SanDisk owes the JV</th><th>Customers owe SanDisk</th></tr>
          <tr><td>50% of Flash Ventures' fixed costs, <b>unconditional</b></td><td>Floor-priced volumes under 10 NBMs, <b>re-openable</b></td></tr>
          <tr><td>$6.6bn purchase and funding commitments FY27–31</td><td>$16.5bn guarantees, $2.7bn of it cash at SanDisk</td></tr>
          <tr><td>Tested in 2008, 2019, 2023: losses every time</td><td>Never tested in a NAND downturn</td></tr>
        </table>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">What we claim, and what we do not</div>
    <div class="pc spread">
      <div class="callout"><b>We do not claim the floors break.</b> We claim the price already assumes something better than the floors, permanently, and the floors themselves are 46% below where the Street is modelling FY28.</div>
      <div>
        <div class="h3">If the floors hold, what FY28 revenue looks like</div>
        <table>
          <tr><th>Assumption</th><th class=n>FY28 revenue</th><th class=n>vs consensus</th></tr>
          <tr><td>All bits at floor (80% GM)</td><td class=n>[[floor_all]]</td><td class=n>[[floor_vs28]]</td></tr>
          <tr><td>2/3 at floor, 1/3 at mid-cycle spot</td><td class=n>~$27bn</td><td class=n>−53%</td></tr>
          <tr><td>2/3 at floor, 1/3 at FY26 spot</td><td class=n>~$38bn</td><td class=n>−34%</td></tr>
          <tr><td>Consensus</td><td class=n>[[fy28]]</td><td class=n>—</td></tr>
        </table>
      </div>
      <div>
        <div class="h3">FY29 at the floor: the first post-boom year</div>
        <table>
          <tr><th>Floors whole, uncontracted bits at 40% GM</th><th class=n></th></tr>
          <tr><td>Revenue (floor $18.8bn + uncontracted bits)</td><td class=n>[[fy29_rev]]</td></tr>
          <tr><td>Blended gross margin</td><td class=n>[[fy29_gm]]</td></tr>
          <tr><td>NOPAT</td><td class=n>[[fy29_nopat]]</td></tr>
          <tr class="hl"><td>EPS · value at 7–9× (the "mature cyclical" range)</td><td class=n>[[fy29_eps]] · [[fy29_7x]]–[[fy29_9x]]</td></tr>
        </table>
      </div>
      <div>
        <div class="h3">Bernstein's stress case, taken at face value</div>
        <div class="sm">FY30 EPS of $214 requires 60% coverage at $0.29/GB <i>and</i> half the shares retired. Grant all of it: FY30 is 8× and the terminal question is unchanged, because the stress case says nothing about FY32. Exhibit B on slide 5 pays <i>more</i> than the stress case for five years and still needs [[perp5]] a year forever.</div>
      </div>
    </div>
  </div>"""),
    "Sources: SanDisk FQ4-FY26 call (5 Aug 2026) for $93.9bn, >4-year duration, ~80% GM at floor, $16.5bn guarantees, bit coverage; FY26 10-K (17 Aug 2026) for contract liabilities and refundable deposits; Citi fireside (8 Sep); Bernstein and Goldman as reported; Kioxia CEO, Bloomberg (8 Sep 2026); Yahoo/LSEG revenue estimate range ([[asof]]).",
    "6"))

# ------------------------------------------------------------------ 7. pillar 2 (merged)
SLIDES.append(slide(
    "Thesis 2 · The earnings are price, price has stopped accelerating, and the supply answer is dated 2H27",
    "Consensus FY27 needs another doubling of blended price; the second derivative turned in July; every forecaster dates the crossover 2H27",
    ("grid-template-columns: 1fr 1fr 1fr; grid-template-rows: 1fr 1.05fr;", """
  <div class="panel">
    <div class="ph red">NAND contract pricing is decelerating on schedule</div>
    <div class="pc tight" style="display:grid; grid-template-rows: 1fr auto; gap:4px; padding:4px 8px 6px">
      <div class="figbox"><img src="figures/contract_price_path.png"></div>
      <div class="sm">Morgan Stanley's memory analyst (21 Jul) calls a <b>4Q26 contract-price peak</b>. Spot 512Gb wafers fell 2.7% in the week of 7 Sep with "suppliers lowering quotes"; retail $/TB has been flat since February.</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Demand destruction is already in the numbers</div>
    <div class="pc">
      <div class="stats" style="grid-template-columns: 1fr 1fr; margin-bottom:8px">
        <div class="stat"><div class="v red">−32%</div><div class="l">SanDisk Consumer revenue, QoQ, FQ4-26: "some impact on the TAM itself" (CFO)</div></div>
        <div class="stat"><div class="v red">−16.7%</div><div class="l">2026 smartphone units, IDC (26 Aug), the steepest decline on record; memory costs up 300%+</div></div>
        <div class="stat"><div class="v red">−11%</div><div class="l">2026 PC units, IDC; client-SSD OEM inventories "elevated" after the H1 pre-build</div></div>
        <div class="stat"><div class="v red">+1.4%</div><div class="l">August monthly NAND contract benchmark, after +55–60%, +70–75% and +10–15% quarters</div></div>
      </div>
      <div class="quote">"Prices have already risen enough."<span class="who">Kioxia CEO, SanDisk's JV partner, Bloomberg, 8 Sep 2026</span></div>
      <div class="quote" style="margin:0">Consumer buyers are at "the limit of price tolerance"; wafer demand has "weakened so significantly."<span class="who">TrendForce, 3Q26 NAND contract release</span></div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Revenue is price: FY27 consensus needs another doubling</div>
    <div class="pc tight" style="display:grid; grid-template-rows: 1fr auto; gap:4px; padding:4px 8px 6px">
      <div class="figbox"><img src="figures/price_volume.png"></div>
      <div class="sm">Bits from the company's "mid-teens sellable bit growth" guide; price and mix is the residual. When price stops rising, growth stops; when it falls, operating leverage runs in reverse against a cost base SanDisk cannot cut.</div>
    </div>
  </div>
  <div class="panel" style="grid-column: 1 / 3;">
    <div class="ph blue">Supply roadmap: 2027 bits come from density and China, not fabs, and every dated forecast puts the crossover in 2H27</div>
    <div class="pc tight" style="display:grid; grid-template-rows: 1fr auto; gap:4px; padding:4px 8px 6px">
      <div class="figbox"><img src="figures/supply_timeline.png"></div>
      <div class="sm">BiCS10 delivers +59% bits per wafer, Samsung V10 and SK hynix 321L similar; YMTC has 14% bit share and pulled Fab 3 into 2H26; Dalian 2 adds 30–50k wafers a month. Then the fabs: the ¥5tn Kioxia/SanDisk plan (27 Aug), Micron Singapore 2H28. Peak profits fund the next glut, every cycle.</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph red">The crossover, and the base rates of the down-leg</div>
    <div class="pc">
      <table style="margin-bottom:6px">
        <tr><th>Source</th><th>Crossover</th><th>On pricing</th></tr>
        <tr><td>TrendForce (21, 30 Jul)</td><td>2H27</td><td>"increasing downward pressure"</td></tr>
        <tr><td>Yole Group</td><td>2027</td><td>"beginning of a down cycle"</td></tr>
        <tr><td>Samsung (30 Jul)</td><td>2H27</td><td>supply "normalising"</td></tr>
        <tr><td>Kioxia (27 Aug, 8 Sep)</td><td>2027 conversions</td><td>"prices have risen enough"</td></tr>
        </table>
      <ul class="tight sm" style="margin-bottom:6px">
        <li><b>No NAND up-leg has run much past eight quarters.</b> Prices stabilised in 2Q25; 2Q27 is quarter eight.</li>
        <li>In 2018 and 2022 the decline began <b>within one quarter</b> of the crossover; peak-to-trough took 19–24 months; wafer prices fell 70% in 2018–19 and 30–35% in one quarter in 3Q22.</li>
      </ul>
      <div class="callout">The principal risk is timing: 1H27 or 2H27. Both are inside the window, and the stock leads the print (slide 9).</div>
    </div>
  </div>"""),
    "Sources: TrendForce NAND contract releases (3 Jul, 21 Jul, 30 Jul, 18 Aug, 1 Sep, 9 Sep 2026); DRAMeXchange monthly benchmark; SanDisk FQ4 call (5 Aug); IDC (26 Aug 2026); Kioxia CEO in Bloomberg (8 Sep 2026) and ¥5tn plan release (27 Aug); Samsung and SK hynix Q2-26 calls; Yole Group NAND monitor 2026; Morgan Stanley (21 Jul 2026); YMTC via TrendForce supplier rankings.",
    "7"))

# ------------------------------------------------------------------ 8. valuation
SLIDES.append(slide(
    "Valuation · distributions, not points",
    "Our value distribution has a median of [[mc_med]]; today's price sits at its [[mc_pct]]th percentile",
    ("grid-template-columns: 1.45fr 1fr; grid-template-rows: 1.15fr 1fr;", """
  <div class="panel">
    <div class="ph red">What we think it is worth vs what the market prices in, on one price axis</div>
    <div class="pc tight"><div class="figbox"><img src="figures/centerpiece.png"></div></div>
  </div>
  <div class="panel" style="grid-column: 2; grid-row: 1 / 3;">
    <div class="ph">Thesis 3 · The bulls' normalised numbers, and same-fab relative value</div>
    <div class="pc">
      <table style="margin-bottom:6px">
        <tr><th>Framework</th><th class=n>Norm. EPS</th><th class=n>Net income</th><th class=n>Multiple at [[price]]</th><th>Their multiple → target</th></tr>
        <tr><td>Morgan Stanley through-cycle</td><td class=n>$76</td><td class=n>$11.1bn</td><td class=n>23.2×</td><td>23× → $1,748 ≈ price</td></tr>
        <tr><td>Goldman normalised</td><td class=n>$110</td><td class=n>$16.1bn</td><td class=n>16.0×</td><td>20× → $2,200</td></tr>
        <tr><td>Bernstein FY30 floor stress</td><td class=n>$214</td><td class=n>$31.3bn</td><td class=n>8.2×</td><td>needs 60% coverage at $0.29/GB and half the shares retired</td></tr>
        <tr class="hl"><td>What the price needs after five peak years</td><td class=n>—</td><td class=n>[[perp5]]/yr</td><td class=n>forever</td><td>≈ the whole NAND industry's best year</td></tr>
      </table>
      <div class="sm" style="margin-bottom:6px">Memory has never sustained 20×+ on normalised earnings: Micron traded 4–6× forward EPS through the 2018–19 rollover. Across [[br_n]] documented NAND company-years the median operating margin is [[br_med]], the best three-year run [[br_best3]], and [[br_neg]] of [[br_n]] lost money (A2).</div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; align-items:start">
        <div class="figbox" style="height:130px"><img src="figures/kioxia_rv.png"></div>
        <div class="sm"><div class="h3 blue">Same fabs, different price</div>Kioxia co-owns Flash Ventures, is ~20% larger by revenue, makes no HBM either, and trades at 3.1× forward sales and 4.4× forward earnings vs SanDisk's 5.2× and 8.2×. <b>SanDisk at Kioxia's multiples is [[kx_lo]]–[[kx_hi]]</b> (−39% to −47%), a cycle-agnostic cross-check. The gap is a listing venue and an index flow, not a business.</div>
      </div>
      <div style="display:grid; grid-template-columns: 1fr 1.1fr; gap:8px; align-items:center; margin-top:6px">
        <div class="figbox" style="height:120px"><img src="figures/pb_peaks.png"></div>
        <div class="sm">Price-to-book <b>16.7×</b> vs 2.2–3.6× at every prior SanDisk and Micron cycle peak, each followed by a 40–59% drawdown within 6–12 months (A2). Book value is the one denominator that is not marked to spot.</div>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Sum-of-parts value by the one assumption that matters</div>
    <div class="pc" style="display:grid; grid-template-columns: 1.1fr 1fr; gap:8px">
      <div class="figbox"><img src="figures/value_vs_gm.png"></div>
      <div class="sm">
        <table style="margin-bottom:5px">
          <tr><th>Post-contract GM</th><th class=n>30%</th><th class=n>40%</th><th class=n>50%</th><th class=n>60%</th><th class=n>70%</th><th class=n>80%</th></tr>
          <tr><td>Value / share</td><td class=n>[[sop30]]</td><td class=n>[[sop40]]</td><td class=n>[[sop50]]</td><td class=n>[[sop60]]</td><td class=n>[[sop70]]</td><td class=n>[[sop80]]</td></tr>
        </table>
        <b>Method.</b> FY27–28 at consensus; FY29–31 NBM floor at 80% GM plus uncontracted bits at mid-cycle; FY32+ everything at mid-cycle. Cost base grows with bits (15%) less cost-per-bit declines (12%); WACC 11%; g 2%.<br>
        <b>Monte Carlo (20,000 paths).</b> Post-contract GM drawn N(45%, 15%), <i>above</i> every mid-cycle in NAND history; bit growth N(18%, 7%), above guidance; WACC 10–13%; consensus hit/miss ±12%; 20% chance floors are renegotiated. Result: p5–p95 [[mc_p5]]–[[mc_p95]], <b>P(value > price) = [[mc_pabove]]</b>. Re-centre GM at 60% and the price is still at the [[mc60_pct]]th percentile.<br>
        <b>Options.</b> Risk-neutral, not a forecast: P(above [[price]] in Jan) [[bl_pabove]]; P(reach $2,125) [[bl_ptarget]]; P(below $1,000) [[bl_p1000]]; 25Δ risk-reversal [[bl_rr]], calls are the expensive side.
      </div>
    </div>
  </div>"""),
    "Sources: analysis/sndk_contract_dcf.py (sum-of-parts, Monte Carlo, required margin); Breeden–Litzenberger density from CBOE Jan-27 quotes via Yahoo ([[asof]], [[bl_n]] OTM quotes, OI ≥ 50, own implied vols, spline in vol space); Kioxia (285A.T) multiples from Bloomberg consensus as reported; sell-side normalised EPS as reported (Morgan Stanley, Goldman, Bernstein).",
    "8"))

# ------------------------------------------------------------------ 9. scenarios, trade, event path
SLIDES.append(slide(
    "Scenarios, the trade, and the event path",
    "Base target [[tgt_base]] ([[ret_base]]) on a cut FY28 at a cyclical multiple; [[ev_ret]] expected return at [[rr]] : 1",
    ("grid-template-columns: 1.15fr 1fr; grid-template-rows: auto 1fr;", """
  <div class="panel" style="grid-column: 1 / -1;">
    <div class="ph red">Twelve-month scenarios: what the market pays once the terminal narrative breaks (multiple × FY28 EPS)</div>
    <div class="pc" style="display:grid; grid-template-columns: 1.55fr 1fr; gap:10px; align-items:start">
      <table>
        <tr><th>Scenario</th><th class=n>Weight</th><th class=n>FY28 revenue</th><th class=n>Op. margin</th><th class=n>FY28 EPS</th><th class=n>Multiple</th><th class=n>Target</th><th class=n>Short return</th><th>Why this multiple</th></tr>
        <tr class="hl"><td><b>Base</b>: contract prices flat by 1Q27, falling from 2Q27</td><td class=n>50%</td><td class=n>$38bn</td><td class=n>60%</td><td class=n>[[eps_base]]</td><td class=n>7×</td><td class=n><b>[[tgt_base]]</b></td><td class=n><b>[[sr_base]]</b></td><td>Consensus cut ~35%; floors cushion margin; 7× = Micron 2018–19 rollover range</td></tr>
        <tr><td><b>Deep bust</b>: bullwhip unwind + China supply; floors partly renegotiated</td><td class=n>20%</td><td class=n>$30bn</td><td class=n>45%</td><td class=n>[[eps_bust]]</td><td class=n>8×</td><td class=n>[[tgt_bust]]</td><td class=n>[[sr_bust]]</td><td>Revenue back to the FQ4-26 run-rate; higher multiple on trough EPS</td></tr>
        <tr><td><b>Against us</b>: prices rise through CY27; FY28 consensus holds</td><td class=n>30%</td><td class=n>[[fy28]]</td><td class=n>75%</td><td class=n>[[eps_bull]]</td><td class=n>9×</td><td class=n>[[tgt_bull]]</td><td class=n>[[sr_bull]]</td><td>Management's 75% OM on full consensus at Citi's "mature cyclical" 9×</td></tr>
        <tr><td colspan="6"><b>Probability-weighted short return [[ev_ret]] · reward/risk [[rr]] : 1.</b> The tail beyond the against-us case (June high $2,354; Bernstein $3,000) is handled by sizing and the stop.</td><td colspan="3" class="sm mut">Intrinsic value (slide 8) is below every target: targets are what the market <i>pays</i> at a rollover, not DCF value.</td></tr>
      </table>
      <div class="figbox" style="height:150px"><img src="figures/scenarios.png"></div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Event path: what pays inside the window, and what we test at each date</div>
    <div class="pc tight" style="display:grid; grid-template-rows: 1fr auto; gap:4px; padding:4px 8px 7px">
      <div class="figbox"><img src="figures/catalyst_timeline.png"></div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px" class="sm">
        <div><span class="pill red">confirms</span> wafer or client-SSD contract prices flat-to-down; SanDisk or hyperscaler inventory days rising; FQ2 gross-margin guide below FQ1; 2027 capex framed as "efficiency"; Micron FY27 capex step-up.</div>
        <div><span class="pill blue">refutes</span> blended contract prices +10% or more into 1Q27; inventory days falling while prices rise; floors re-set up at renewal; TrendForce pushes the crossover into 2028. Each has a kill criterion on slide 10.</div>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Trade construction</div>
    <div class="pc spread">
      <table class="tl">
        <tr><td>Size · borrow</td><td>[[idio]] idiosyncratic vol → ~2.5% of NAV notional per 1% of NAV at risk per quarter; 2.5–3% is full-conviction size. Borrow 0.28% GC, 2.1m shares available (IBKR, 9 Sep), no dividend.</td></tr>
        <tr><td>Entry</td><td>Half after the 21 Sep inclusion print and Micron on 30 Sep; second half on the first TrendForce print showing wafer / client-SSD contract prices flat-to-down (early Oct for 4Q26, or late Dec for 1Q27).</td></tr>
        <tr><td>Hedge</td><td>Half the SMH beta (β [[beta]], R² [[r2]]) ≈ $0.85 long SMH per $1 short. A full hedge buys back Micron and Samsung, which fall in the payoff state; no hedge leaves 43% of variance as sector beta.</td></tr>
        <tr><td>Stop / tail</td><td>Close above the June high <b>$2,354</b> = re-rating, not testing: cover half, reassess. No call protection: a rolled 3-month 25Δ call at [[bl_iv]] IV costs ~5% of notional per quarter, the entire expected return.</td></tr>
        <tr><td>Expected path</td><td><b>Down 10–20% into November.</b> The 6 Nov print will likely show 83–85% GM and top-of-range revenue. We hold because the print cannot change the post-2031 arithmetic.</td></tr>
        <tr><td>Exit</td><td>First two negative quarterly contract prints, which base rates put in 2Q–3Q27; the six-month minimum is met by construction. The pair a fund would run: short SNDK / long Kioxia (outside the mandate).</td></tr>
      </table>
      <table style="margin-top:6px">
        <tr><th>P&amp;L map, 2.5% of NAV short, half-beta hedged</th><th class=n>Bust (20%)</th><th class=n>Base (50%)</th><th class=n>Against (30%)</th><th class=n>Stop $2,354</th><th class=n>Expected</th></tr>
        <tr><td>NAV impact</td><td class=n>+1.6%</td><td class=n><b>+1.2%</b></td><td class=n>−0.7%</td><td class=n>−0.8%</td><td class=n><b>+0.7%</b></td></tr>
      </table>
    </div>
  </div>"""),
    "Sources: analysis/sndk_contract_dcf.py section F (scenario targets); factor regression vs SMH with Newey–West errors (analysis/sndk_exhibits.py); IBKR borrow desk (9 Sep 2026); event dates from company IR calendars, TrendForce release cadence, S&P Dow Jones Indices (4 Sep 2026); Micron 2018–19 multiples from Bloomberg.",
    "9"))

# ------------------------------------------------------------------ 10. risks and kill criteria
SLIDES.append(slide(
    "Risks and kill criteria",
    "What breaks the short, what we do about it, and the four pre-committed conditions under which we cover",
    ("grid-template-columns: 1.4fr 1fr;", """
  <div class="panel">
    <div class="ph red">The other side of the trade, and our mitigants</div>
    <div class="pc">
      <table>
        <tr><th style="width:27%">Risk</th><th style="width:34%">How it hurts</th><th>Mitigant / why it is already in the numbers</th></tr>
        <tr><td><b>1. Prices keep rising through CY27</b> (allocation "beyond 2027"; HBM diverts more wafers; hyperscaler capex > $1tn)</td><td>FY28 consensus holds or rises; stock re-rates on "structural"; we are down 28% in the against-us case, more in the tail</td><td>Weighted 30% at 9× full consensus. We pay consensus in full and the price <i>still</i> needs [[perp5]] forever. Staged entry; stop at $2,354; sized to a 1% NAV loss per quarter</td></tr>
        <tr><td><b>2. The floors hold and the market believes them</b></td><td>Trough earnings are cushioned; "8× a protected trough" persists</td><td>Floors on every bit = [[floor_all]]/yr, [[floor_vs28]] vs consensus; the base case already assumes 60% op margin in FY28. The price needs more than the floors</td></tr>
        <tr><td><b>3. Flows, momentum, buyback</b> (S&P 100 21 Sep; $15.5bn authorisation; 128 hedge funds)</td><td>The stock grinds higher on no news at 76% IV</td><td>Entry <i>after</i> inclusion; half position until the first flat print; the buyback retires ~6% of shares at ~$1,700; Micron bought back at the top in 2018 and 2022 and halved anyway</td></tr>
        <tr><td><b>4. Structural change: HBF, AI-storage TAM</b> (High-Bandwidth Flash; 16 TB NAND per GPU)</td><td>NAND becomes an AI bottleneck with pricing power that survives the cycle</td><td>HBF is pre-revenue until 2028 and excluded from every bull model; Vera Rubin demand is in the consensus we pay. Structural pricing power shows up as floors re-set <i>up</i> at renewal: kill criterion 3</td></tr>
        <tr><td><b>5. Squeeze / borrow</b></td><td>Short interest rises, borrow tightens</td><td>5.3% of float, ~1 day to cover, 0.28% GC, 2.1m shares available. The crowd is long, not short</td></tr>
        <tr><td><b>6. Timing wrong by two quarters</b></td><td>Crossover in 2028; carry is trivial, drawdown and opportunity cost are not</td><td>The stock leads the print by 1–2 quarters; the 6-month minimum is met; kill criterion 1 forces a re-underwrite by the 2Q27 print</td></tr>
        <tr><td><b>7. The contracts get longer</b> (new NBMs to FY33+)</td><td>The perpetuity starts to look contracted</td><td>Kill criterion 3 covers it: coverage above 80% of FY29 bits or floors stepping up → exit</td></tr>
      </table>
      <div class="sm mut" style="margin:6px 0 8px">Everything in the "How it hurts" column is a price path, not a change in the post-2031 arithmetic. Only the kill criteria describe changes in the arithmetic.</div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px">
        <div>
          <div class="h3">The asymmetry</div>
          <table>
            <tr><td>Probability-weighted 12-month short return</td><td class=n><b>[[ev_ret]]</b></td></tr>
            <tr><td>Reward / risk, against-us case at 30%</td><td class=n>[[rr]] : 1</td></tr>
            <tr><td>Share of 20,000 Monte Carlo paths reaching today's price</td><td class=n>[[mc_pabove]]</td></tr>
            <tr><td>Loss on a 2.5% position if the stop is hit</td><td class=n>−0.8% of NAV</td></tr>
            <tr><td>Carry (borrow, no dividend)</td><td class=n>0.28% p.a.</td></tr>
          </table>
        </div>
        <div>
          <div class="h3">Refreshed before the final</div>
          <table>
            <tr><th>Date</th><th>Input</th><th>Slides</th></tr>
            <tr><td>21 Sep</td><td>S&P 100 inclusion print</td><td>2, 9</td></tr>
            <tr><td>30 Sep</td><td>Micron FQ4: NAND ASP, FY27 capex</td><td>7, 9</td></tr>
            <tr><td>early Oct</td><td>TrendForce 4Q26 NAND contract forecast</td><td>7, 9, 10</td></tr>
            <tr><td>14 Oct</td><td>Engine re-run on refreshed prices, consensus, options</td><td>2, 5, 8, 9</td></tr>
          </table>
        </div>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Risk map and kill criteria</div>
    <div class="pc" style="display:grid; grid-template-rows: auto 1fr; gap:6px">
      <div class="figbox" style="height:270px"><img src="figures/risk_matrix.png"></div>
      <div>
        <ul class="kill" style="margin-bottom:8px">
          <li><span class="num ink">1</span><b>TrendForce 1Q27 and 2Q27 prints both show blended NAND contract prices still rising QoQ</b> → timing wrong; cover half. <span class="pill gold">late Dec 26 · late Mar 27</span></li>
          <li><span class="num ink">2</span><b>Hyperscaler 2027 capex guides accelerate above ~$1tn with storage-specific commitments</b>, and SanDisk FQ2 shows inventory days <i>falling</i> → cover half. <span class="pill gold">late Jan 27</span></li>
          <li><span class="num ink">3</span><b>SanDisk discloses floor prices ≥ 2Q26 ASP with guarantees stepping <i>up</i>, or new NBMs taking coverage above 80% of FY29 bits</b> → the terminal is being contracted; exit. <span class="pill gold">6 Nov 26 · Jan 27</span></li>
          <li><span class="num ink">4</span><b>Close above $2,354</b> → re-rating, not testing; cover half. <span class="pill gold">any day</span></li>
        </ul>
        <div class="callout ink"><b>What would make us wrong:</b> a structural, not cyclical, change in NAND pricing. Each version of it has a date above. Everything else, a strong FQ1, a rally into November, a higher June high, is priced, sized, or stopped.</div>
      </div>
    </div>
  </div>"""),
    "Sources: SanDisk FQ4 call and 10-K; S&P Dow Jones Indices; FINRA; IBKR; TrendForce; hyperscaler Q2-26 calls; Micron 2018 and 2022 buyback history from 10-Ks; analysis/sndk_contract_dcf.py for scenario weights and Monte Carlo.",
    "10"))

# ------------------------------------------------------------------ A1
SLIDES.append(slide(
    "A1 · Contract-aware DCF mechanics",
    "The engine behind slides 5 and 8: consensus paid directly, the floor paid directly, the residual solved for",
    ("grid-template-columns: 1.45fr 1fr;", """
  <div class="panel">
    <div class="ph">Cash-flow build, sum-of-parts case C at 40% post-contract gross margin ($bn, FY Jun)</div>
    <div class="pc">
      <table style="margin-bottom:6px">
        <tr><th>Year</th><th>Regime</th><th class=n>Revenue</th><th class=n>GM</th><th class=n>Cash COGS</th><th class=n>Opex</th><th class=n>NOPAT</th><th class=n>FCF</th></tr>
        [[dcf_rows]]
      </table>
      <div class="sm">Terminal value = FY36 NOPAT × 1.02 / (11% − 2%), discounted 10 years. Equity = EV − debt $0.2bn + cash $4.8bn over 146.4m shares → <b>[[val40]]</b> at 40% GM. FY29–31 revenue = floor $18.8bn plus uncontracted bits (1/3 of the cost base) at mid-cycle. Cash COGS starts at FY26's $5.8bn, grows with bits (+15%) less cost-per-bit (−12%); opex $2.12bn growing 5%; incremental capital 15% of revenue growth; tax 15%.</div>
      <div class="h3" style="margin-top:8px">Case A, step by step</div>
      <table style="margin-bottom:8px">
        <tr><th>Step</th><th class=n>$bn</th></tr>
        <tr><td>PV of FY27 consensus net income: [[ni27n]] / 1.11</td><td class=n>[[pvA27]]</td></tr>
        <tr><td>PV of FY28 consensus net income: [[ni28n]] / 1.11²</td><td class=n>[[pvA28]]</td></tr>
        <tr><td>Enterprise value [[evn]] less both</td><td class=n>[[resid2n]]</td></tr>
        <tr class="hl"><td>× 1.11² × (0.11 − 0.02) / 1.02 = perpetual NOPAT from FY29</td><td class=n>[[perp2n]]</td></tr>
      </table>
      <div class="h3">Verification tests (analysis/tests/test_engine.py, 17 passing)</div>
      <table>
        <tr><th>Group</th><th>What is asserted</th></tr>
        <tr><td>DCF engine (5)</td><td>Zero-growth EV = NOPAT/WACC; reverse solvers round-trip; terminal NOPAT round-trips; forecast period monotone</td></tr>
        <tr><td>Options (5)</td><td>Put–call parity; IV round-trips; sub-intrinsic quotes rejected; B–L recovers a lognormal; smile fit recovers flat vol</td></tr>
        <tr><td>Monte Carlo (3)</td><td>Degenerate draws match the deterministic value; correlation sign propagates; percentiles correct</td></tr>
        <tr class="hl"><td>Contract model (4)</td><td>Required NOPAT reproduces EV; required GM reproduces NOPAT; monotone in margin and growth; case-B closed form</td></tr>
      </table>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Residual algebra and assumptions</div>
    <div class="pc spread">
      <div class="h3">The required perpetual NOPAT</div>
      <div class="sm" style="margin-bottom:6px">Residual = EV − Σ PV(FCF<sub>t</sub>) for t ≤ T. If the post-T business earns constant NOPAT growing at inflation i with value-neutral reinvestment: Residual = NOPAT × (1+i) / (WACC − i) / (1+WACC)<sup>T</sup>, so <b>NOPAT<sub>req</sub> = Residual × (1+WACC)<sup>T</sup> × (WACC − i) / (1+i)</b>. Required gross margin: GM<sub>req</sub> = 1 − COGS<sub>32</sub> / (NOPAT<sub>req</sub>/(1−τ) + Opex<sub>32</sub> + COGS<sub>32</sub>).</div>
      <table style="margin-bottom:6px">
        <tr><th>Assumption</th><th class=n>Base</th><th>Provenance</th></tr>
        <tr><td>WACC</td><td class=n>11%</td><td>rf 4.8% + β 1.7–2.2 × ERP 4.5% → 11–13%; low end used</td></tr>
        <tr><td>Terminal growth</td><td class=n>2%</td><td>Inflation; bit growth is in the cost base, not the terminal</td></tr>
        <tr><td>Tax</td><td class=n>15%</td><td>Guided non-GAAP rate</td></tr>
        <tr><td>Consensus FY27 / FY28 NI</td><td class=n>[[ni27]] / [[ni28]]</td><td>EPS [[eps27]] / [[eps28]] × 146.4m shares (Yahoo/LSEG)</td></tr>
        <tr><td>NBM floor / yr · GM at floor</td><td class=n>$18.8bn · 80%</td><td>$93.9bn ÷ 5 years; FQ4 call</td></tr>
        <tr><td>Bit growth · cost/bit</td><td class=n>+15% · −12%</td><td>"Mid-teens" guide; nodal productivity</td></tr>
        <tr><td>Shares</td><td class=n>146.4m basic</td><td>Diluted ~157m would lower per-share values ~7%</td></tr>
      </table>
      <div class="h3">Required perpetual NOPAT across the WACC band (case A)</div>
      <table>
        <tr><th class=n>WACC</th><th class=n>10%</th><th class=n>11%</th><th class=n>12%</th><th class=n>13%</th></tr>
        <tr><td class=n>NOPAT/yr from FY29</td><td class=n>[[perp2_lo]]</td><td class=n>[[perp2]]</td><td class=n>${p12}bn</td><td class=n>[[perp2_hi]]</td></tr>
      </table>
      <div class="sm mut" style="margin:6px 0 8px">A lower discount rate makes the required perpetual profit smaller but still ~12× SanDisk's best pre-2026 year and about the whole industry's 2018 profit pool.</div>
      <div class="h3">Assumptions that favour the bull case</div>
      <ul class="tight sm">
        <li>Consensus FY27–28 net income is paid in full with no reinvestment charge beyond 15% of revenue growth; FY29–31 floor years use the 80% gross margin management quoted <i>at floor</i>.</li>
        <li>WACC 11% is the low end of a CAPM band for a 1.7–2.7 beta stock; cost per bit falls 12% a year in perpetuity; tax is the guided 15%, not the 21% statutory.</li>
        <li>Basic shares (146.4m) are used; the ~157m diluted count would cut every per-share value by ~7%.</li>
        <li>No value is deducted for the $6.6bn of JV commitments or the ¥5tn Japan plan.</li>
      </ul>
    </div>
  </div>""".replace("{p12}", f"{N['perp2_by_wacc']['0.12']:,.1f}")),
    "Source: analysis/sndk_contract_dcf.py and analysis/quant/dcf.py (Rappaport–Mauboussin FCFF engine); analysis/tests/test_engine.py.",
    "A1", app=True))

# ------------------------------------------------------------------ A2
SLIDES.append(slide(
    "A2 · Base rates",
    "[[br_n]] documented NAND company-years: median operating margin [[br_med]], best year [[br_best]], best three-year run [[br_best3]], [[br_neg]] loss-making years",
    ("grid-template-columns: 1.5fr 1fr; grid-template-rows: 1.1fr 1fr;", """
  <div class="panel">
    <div class="ph">Every documented company-year, ranked (GAAP operating margin)</div>
    <div class="pc tight"><div class="figbox"><img src="figures/base_rates.png"></div></div>
  </div>
  <div class="panel" style="grid-column: 2; grid-row: 1 / 3;">
    <div class="ph">Cycle table and the record after peaks</div>
    <div class="pc">
      <table style="margin-bottom:6px">
        <tr><th>Peak</th><th class=n>P/B at peak</th><th>What followed</th></tr>
        <tr><td>SanDisk, 2010</td><td class=n>2.6×</td><td>−45% within 12 months as MLC pricing fell</td></tr>
        <tr><td>SanDisk, 2014</td><td class=n>3.6×</td><td>−59% by 2015; sold to WDC 2016</td></tr>
        <tr><td>Micron, May 2018</td><td class=n>2.2×</td><td>−50% in 7 months; earnings peaked two quarters later</td></tr>
        <tr><td>Micron, Jan 2022</td><td class=n>2.6×</td><td>−45% by Sep 2022; loss-making by 2023</td></tr>
        <tr class="hl"><td>SanDisk, today</td><td class=n>16.7×</td><td>—</td></tr>
      </table>
      <div class="figbox" style="height:150px; margin-bottom:6px"><img src="figures/pb_peaks.png"></div>
      <table>
        <tr><th>Company</th><th>Operating margin by year, %</th></tr>
        [[br_rows]]
      </table>
      <div class="sm mut" style="margin-top:6px">Excluded as estimates or boom-affected: WDC Flash 2020–22 (~+4/+12/+20, est.) and Kioxia FY25 (+37, includes the 2026 spike). Kioxia FY2020 and Samsung / SK hynix NAND-only margins are not disclosed. Micron's NAND unit never exceeded 19% in thirteen disclosed years.</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Annual gross margin, SanDisk vs Micron: gross losses to 71% in three fiscal years</div>
    <div class="pc tight" style="display:grid; grid-template-columns: 1.3fr 1fr; gap:8px; padding:6px 9px">
      <div class="figbox"><img src="figures/margin_cycle.png"></div>
      <div class="sm">The industry's operating profit pool: ~$17–21bn in 2018 (all producers, estimated from segment disclosures), ~$12–15bn in 2021–22. SanDisk's FY26 operating income alone ($12.5bn) equals the whole industry's 2021–22 peak; the perpetual profit the price needs ([[perp5]]–[[nopat_req]]) equals or exceeds the whole industry's best year. The required permanent gross margin ([[gm_req]]) is above every number in the record except the current quarter.</div>
    </div>
  </div>"""),
    "Sources: SanDisk 10-Ks 2005–15; Western Digital segment reporting 2020–25; Micron 10-Ks (Storage / NAND business unit disclosures 2010–24); Kioxia securities reports 2018–25; StockAnalysis; price-to-book at peaks from Bloomberg / company filings; drawdowns from price history.",
    "A2", app=True))

# ------------------------------------------------------------------ A3
SLIDES.append(slide(
    "A3 · Monte Carlo and sensitivity",
    "Inputs centred above NAND history and above guidance, and the price still sits at the [[mc_pct]]th percentile",
    ("grid-template-columns: 1fr 1fr; grid-template-rows: auto 1fr;", """
  <div class="panel" style="grid-column: 1 / -1;">
    <div class="ph">Value per share across the two assumptions that matter (row: permanent post-contract gross margin); red below [[price]], blue above</div>
    <div class="pc" style="display:grid; grid-template-columns: 1.25fr 1fr 1fr; gap:12px">
      <table>
        <tr><th>GM ↓ · bit growth →</th>[[gbg_head]]</tr>
        [[gbg_rows]]
      </table>
      <table>
        <tr><th>GM ↓ · WACC →</th>[[gw_head]]</tr>
        [[gw_rows]]
      </table>
      <div class="sm">To reach [[price]] you need <b>either</b> a permanent 80% gross margin with 20%+ bit growth, <b>or</b> a 70% margin with 30% bit growth, every year after the contracts expire. No cell at 60% margin or below reaches the price at any WACC or growth rate. The consensus FY27–28 years and the FY29–31 floor are paid in full in every cell.</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Input distributions and what drives the spread</div>
    <div class="pc" style="display:grid; grid-template-rows: 1fr auto; gap:6px">
      <div class="figbox"><img src="figures/mc_tornado.png"></div>
      <div>
        <table style="margin-bottom:5px">
          <tr><th>Percentile</th><th class=n>p5</th><th class=n>p10</th><th class=n>p25</th><th class=n>p50</th><th class=n>p75</th><th class=n>p90</th><th class=n>p95</th></tr>
          <tr><td>Value / share</td>[[mc_pct_row]]</tr>
        </table>
        <div class="sm">Draws are independent except that busts hit price and margin together through the shared cost base. Terminal paths with WACC ≤ g are impossible by construction (WACC ≥ 10%). Rank correlations are Spearman against value/share over 20,000 paths.</div>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Provenance of every distribution</div>
    <div class="pc">
      <table style="margin-bottom:7px">
        <tr><th>Input</th><th>Distribution</th><th>Why it favours the bull case</th></tr>
        <tr><td>Post-contract GM</td><td>N(45%, 15%), clipped 5–85%</td><td>NAND mid-cycle history 25–40%; 2026 peak 85%; centre is above every non-boom year</td></tr>
        <tr><td>Bit growth</td><td>N(18%, 7%), clipped 0–40%</td><td>Company guides mid-teens; AI-storage bulls 25–30%</td></tr>
        <tr><td>Cost/bit decline</td><td>N(12%, 4%)</td><td>Nodal cadence; higher declines raise value</td></tr>
        <tr><td>WACC</td><td>Triangular 10 / 11.5 / 13%</td><td>CAPM band; mode below midpoint</td></tr>
        <tr><td>FY27–28 vs consensus</td><td>N(100%, 12%)</td><td>Symmetric hit/miss on the Street's boom</td></tr>
        <tr><td>Floor renegotiation</td><td>20% chance × U(60–90%) of floor revenue</td><td>Enforceability untested; 80% of paths keep the floors whole</td></tr>
      </table>
      <div class="h3">Sensitivity to the margin centre</div>
      <table style="margin-bottom:6px">
        <tr><th>Post-contract GM centre</th><th class=n>Median value</th><th class=n>Price percentile</th><th class=n>P(value > price)</th></tr>
        <tr><td>45% (base; above NAND history)</td><td class=n>[[mc_med]]</td><td class=n>[[mc_pct]]th</td><td class=n>[[mc_pabove]]</td></tr>
        <tr class="hl"><td>60% (5,000 paths, all else equal)</td><td class=n>[[mc60_med]]</td><td class=n>[[mc60_pct]]th</td><td class=n>[[mc60_pabove]]</td></tr>
      </table>
      <div class="sm mut">A 60% permanent gross margin is 13 points above the best year NAND had before 2026 and 30 points above its best three-year run; even then, roughly one path in eight reaches today's price. The distribution is not the argument; slide 5's arithmetic is. The distribution shows how much room the argument has.</div>
    </div>
  </div>"""),
    "Source: analysis/sndk_contract_dcf.py section D (Monte Carlo, seed 11, 20,000 paths) and section C grids; Damodaran, Probabilistic Approaches to Valuation, for the method.",
    "A3", app=True))

# ------------------------------------------------------------------ A4
SLIDES.append(slide(
    "A4 · Options, factor exposure, and positioning",
    "The option-implied density is what the market prices, not what we predict; the position is majority idiosyncratic; the crowd is long",
    ("grid-template-columns: 1.5fr 1fr; grid-template-rows: 1fr 1fr;", """
  <div class="panel">
    <div class="ph">Breeden–Litzenberger pipeline and validation (Jan-2027 expiry)</div>
    <div class="pc" style="display:grid; grid-template-columns: 1.6fr 1fr; gap:8px">
      <div class="figbox"><img src="figures/bl_vs_lognormal.png"></div>
      <div class="sm">
        <b>Pipeline.</b> Mid quotes, bid > 0, OI ≥ 50, OTM only ([[bl_n]] quotes) → our own Black–Scholes implied vols → smoothing spline in vol space vs log-moneyness → reprice calls on a 4,001-point grid → second difference → density ≥ 0, ∫ = 0.96 before renormalisation over the quoted strike range → tight call-spread digital check within 2 points.<br><br>
        <b>Risk-neutral, not real-world.</b> It embeds risk premia, which is why we use it as "what the market prices" and as a sizing input, never as a forecast. The smile sits within ~5 points of a flat lognormal at [[bl_iv]] IV, and its tails moved 15 points in a week of data.
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">What the market prices, Jan-27 and Mar-27</div>
    <div class="pc spread">
      <table style="margin-bottom:6px">
        <tr><th>Probability (risk-neutral)</th><th class=n>Jan-27</th><th class=n>Mar-27</th></tr>
        <tr><td>Above [[price]] (today's price)</td><td class=n>[[bl_pabove]]</td><td class=n>35%</td></tr>
        <tr><td>Above $2,125 (mean sell-side target)</td><td class=n>[[bl_ptarget]]</td><td class=n>22%</td></tr>
        <tr><td>Above $2,354 (June high; our stop)</td><td class=n>15%</td><td class=n>16%</td></tr>
        <tr><td>Below $1,200</td><td class=n>[[bl_p1200]]</td><td class=n>33%</td></tr>
        <tr><td>Below $1,000</td><td class=n>[[bl_p1000]]</td><td class=n>21%</td></tr>
        <tr><td>ATM implied vol · 25Δ risk-reversal</td><td class=n>[[bl_iv]] · [[bl_rr]]</td><td class=n>78% · +4.4%</td></tr>
      </table>
      <div class="sm">Calls are the rich side of the smile: the market is paying up for upside, not downside, consistent with a long-crowded, uncrowded-short register. Horizon mismatch: sell-side targets are 12-month; the density is 4–6 months. A week earlier the same pipeline priced P(below $1,000) at 31%; it is now [[bl_p1000]]. The density moves with the smile, which is why it sizes the trade and does not make the argument.</div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Factor exposure: what we are actually underwriting</div>
    <div class="pc" style="display:grid; grid-template-columns: 1fr 1.3fr; gap:8px">
      <div class="figbox"><img src="figures/beta_scatter.png"></div>
      <div class="sm">
        <table style="margin-bottom:6px">
          <tr><th>vs</th><th class=n>β</th><th class=n>R²</th><th class=n>Idio vol</th></tr>
          <tr><td>SMH (semis)</td><td class=n>[[beta]]</td><td class=n>[[r2]]</td><td class=n>[[idio]]</td></tr>
          <tr><td>QQQ</td><td class=n>2.67</td><td class=n>33%</td><td class=n>86%</td></tr>
        </table>
        Daily returns since Mar-25, OLS with Newey–West (6 lags) errors. 57% of variance is idiosyncratic: the trade is a NAND-pricing bet, not a semis bet. R² of 30–60% is normal for a single stock; we do not claim historical alpha. Half-beta hedge in SMH keeps the payoff-state exposure (Micron, Samsung fall with NAND) while removing the pure index leg.
        <div class="h3" style="margin-top:7px">The IV cone: why the position is 2.5% of NAV, not 10%</div>
        <table>
          <tr><th>Horizon at [[bl_iv]] ATM vol</th><th class=n>1 month</th><th class=n>3 months</th><th class=n>6 months</th></tr>
          <tr><td>One-standard-deviation move</td><td class=n>[[cone1]]</td><td class=n>[[cone3]]</td><td class=n>[[cone6]]</td></tr>
          <tr><td>Loss on 2.5% notional at 1σ against us</td><td class=n>0.5% NAV</td><td class=n>1.0% NAV</td><td class=n>1.4% NAV</td></tr>
        </table>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Positioning and the flow calendar</div>
    <div class="pc">
      <table>
        <tr><th>Item</th><th class=n>Value</th><th>Note</th></tr>
        <tr><td>Short interest (FINRA, 14 Aug settlement)</td><td class=n>7.68m sh · 5.3%</td><td>Yahoo's 8.2% is an artefact; ~1 day to cover</td></tr>
        <tr><td>Borrow · availability</td><td class=n>0.28% · 2.1m sh</td><td>General collateral; IBKR 9 Sep</td></tr>
        <tr><td>Institutional · hedge funds</td><td class=n>81% · 128 funds</td><td>$25.6bn at Q2; up from 114 funds</td></tr>
        <tr><td>Notable exits, Q2-26</td><td class=n>Duquesne, Appaloosa</td><td>the two most experienced macro holders</td></tr>
        <tr><td>MSCI inclusion</td><td class=n>31 Aug</td><td>done; visible in the 31 Aug volume</td></tr>
        <tr><td>S&P 100 inclusion</td><td class=n>21 Sep</td><td>announced 4 Sep (+12% that day); last mechanical bid</td></tr>
        <tr><td>Company buyback</td><td class=n>$4.5bn FQ4 · $15.5bn left</td><td>at ~24× trailing; a cycle-top signal (Micron 2018, 2022)</td></tr>
        <tr><td>Analyst ratings, 3 months ago → now</td><td class=n>3/15/3/1/0 → 4/16/3/0/1</td><td>Strong Buy / Buy / Hold / Sell / Strong Sell</td></tr>
        <tr><td>EPS-upgrade breadth</td><td class=n>92% → 77%</td><td>share of revisions that were upward, past 30 days</td></tr>
      </table>
      <div class="sm mut" style="margin-top:6px">Uncrowded on the short side, crowded on the long side. The risk to the position is flow and momentum, not a squeeze from other shorts, which is why entry waits for the last mechanical buyer.</div>
    </div>
  </div>"""),
    "Sources: CBOE option quotes via Yahoo ([[asof]]), analysis/quant/bl_density.py and analysis/sndk_exhibits.py; FINRA short interest; IBKR; 13F aggregates (WhaleWisdom) Q2-26; MSCI and S&P Dow Jones Indices announcements; SanDisk FQ4 release.",
    "A4", app=True))

# ------------------------------------------------------------------ A5
SLIDES.append(slide(
    "A5 · JV accounting, guarantees, and the long-term-agreement record",
    "SanDisk's obligations to Flash Ventures are unconditional; its customers' obligations to SanDisk are collateralised mostly off its balance sheet and untested",
    ("grid-template-columns: 1fr 1fr 1fr;", """
  <div class="panel">
    <div class="ph">Flash Ventures mechanics (FY26 10-K)</div>
    <div class="pc spread">
      <table style="margin-bottom:7px">
        <tr><th>Term</th><th>Disclosure</th></tr>
        <tr><td>Ownership</td><td>49.9% SanDisk / 50.1% Kioxia; three JV entities (Yokkaichi Fabs 2–7, Kitakami K1/K2)</td></tr>
        <tr><td>Wafer purchase</td><td>SanDisk buys ~50% of JV output at cost; <b>pays 50% of fixed costs regardless of output</b></td></tr>
        <tr><td>Commitments FY27–31</td><td><b>$6.6bn</b> purchase and funding commitments</td></tr>
        <tr><td>Lease guarantees</td><td>$923m of JV equipment leases guaranteed by SanDisk</td></tr>
        <tr><td>Payments to Kioxia</td><td>$1.2bn in FY26 for wafers, R&amp;D and fab services</td></tr>
        <tr><td>Own capex</td><td>~$0.2bn/yr on SanDisk's books; the capital intensity is in the JV, off the SanDisk P&amp;L until wafers are purchased</td></tr>
        <tr><td>Japan plan (27 Aug 2026)</td><td>¥5tn (~$31bn) with Kioxia; Kitakami Fab 3 output FY2029; SanDisk's share funded from peak cash flow</td></tr>
      </table>
      <div class="callout">In a downturn SanDisk's cash cost is fixed, its wafer intake is contracted, and its selling price is the only variable. That is why the record on A2 has ten loss-making years in thirty-three.</div>
      <table>
        <tr><th>Year</th><th>What happened to SanDisk / WDC Flash</th></tr>
        <tr><td>2008</td><td>Operating margin −59%; JV output cut, fixed costs still paid; $1.5bn+ impairments</td></tr>
        <tr><td>2019</td><td>WDC Flash margin turned negative; Kioxia (Toshiba Memory) lost ¥170bn; JV under-utilisation charges</td></tr>
        <tr><td>2023</td><td>Flash operating margin −22% ex-impairment; $1.8bn impairment at the spin; net loss $2.1bn</td></tr>
      </table>
    </div>
  </div>
  <div class="panel">
    <div class="ph">The NBM balances in the 10-K</div>
    <div class="pc" style="display:grid; grid-template-rows: auto auto 1fr; gap:6px">
      <table>
        <tr><th>Balance (30 Jun 2026)</th><th class=n>$bn</th></tr>
        <tr><td>Contract liabilities (customer prepayments)</td><td class=n>1.24</td></tr>
        <tr><td>Refundable customer deposits</td><td class=n>1.50</td></tr>
        <tr class="hl"><td>Cash-backed guarantees on balance sheet</td><td class=n>2.74</td></tr>
        <tr><td>Headline "financial guarantees" (call)</td><td class=n>16.5</td></tr>
        <tr><td>Off-balance-sheet portion (third-party collateral)</td><td class=n>13.8</td></tr>
        <tr><td>Inventory · days</td><td class=n>2.70 · ~178</td></tr>
        <tr><td>Cash · debt</td><td class=n>4.76 · 0.18</td></tr>
      </table>
      <div>
        <div class="h3">Inventory days are already rising</div>
        <div class="sm">~178 days at FY26 year-end vs ~135 a year earlier, while the company reports allocation. Rising inventory in a "sold out" market is the classic pre-rollover tell (Micron 2018: 143 → 165 days into the peak). We compute hyperscaler and SanDisk inventory days from every 10-Q on the event path.</div>
        <div class="sm mut" style="margin-top:5px">Open item: reconcile the ">50% FY27 / ~2/3 FY28" bit coverage (5 Aug call) with Citi's "50% by end-FY28" (8 Sep) against the replay.</div>
      </div>
      <div class="figbox"><img src="figures/cash_cycle.png"></div>
    </div>
  </div>
  <div class="panel">
    <div class="ph">Every 2026 memory long-term agreement we can find</div>
    <div class="pc spread">
      <table style="margin-bottom:7px">
        <tr><th>Supplier</th><th>Structure</th><th>Tested?</th></tr>
        <tr><td>SanDisk</td><td>10 NBMs, $93.9bn floors, $16.5bn guarantees, >4 yrs</td><td>No</td></tr>
        <tr><td>Micron</td><td>$100bn take-or-pay, $22bn customer prepayments</td><td>No</td></tr>
        <tr><td>Samsung</td><td>60–70% of capacity under 3-year-plus deals</td><td>No</td></tr>
        <tr><td>SK hynix</td><td>HBM sold out 2026–27; NAND LTAs with hyperscalers</td><td>No</td></tr>
        <tr><td>Kioxia</td><td>Multi-year eSSD supply agreements; volumes, not floors, disclosed</td><td>No</td></tr>
        <tr><td>Apple (buyer)</td><td>Multi-year NAND supply from Kioxia/YMTC reported</td><td>—</td></tr>
      </table>
      <div class="h3 red">What we say, and what we do not</div>
      <ul class="tight sm" style="margin-bottom:7px">
        <li>We say <b>"untested"</b>, not "always renegotiated." We found no primary documentation of 2019 or 2023 LTA renegotiations and do not claim any.</li>
        <li>Goldman on prior-generation agreements: "minimal enforceability — buyers could reduce volumes or breach with limited consequences."</li>
        <li>Two NBMs have already been re-opened in SanDisk's favour. Bilateral re-opening is evidence the terms are negotiable, in both directions.</li>
        <li>Our base case keeps the floors whole. Only the 20%-weighted bust case and 20% of Monte Carlo paths assume partial renegotiation.</li>
      </ul>
      <div class="h3">What a renegotiation would look like, mechanically</div>
      <table>
        <tr><th>Step</th><th>Consequence for SanDisk</th></tr>
        <tr><td>Customer defers volume under a shortfall clause</td><td>Revenue timing slips; JV fixed cost unchanged</td></tr>
        <tr><td>Bilateral re-price to "market plus" in exchange for extension</td><td>Floor economics fall; duration rises; the terminal is contracted <i>lower</i></td></tr>
        <tr><td>Draw on collateral</td><td>One-off cash; relationship and future volume at risk</td></tr>
        <tr><td>Litigation</td><td>Multi-year; no precedent in memory of a supplier enforcing a floor against a hyperscaler</td></tr>
      </table>
    </div>
  </div>"""),
    "Sources: SanDisk FY26 10-K (17 Aug 2026), Flash Ventures notes, commitments, contract liabilities, deposits, inventory; FQ4 call (5 Aug); Kioxia/SanDisk release (27 Aug); Micron FQ3 call (24 Jun); Samsung and SK hynix Q2-26 calls; Goldman memory note as reported; press reports on Apple supply agreements.",
    "A5", app=True))

html = "<!doctype html><html><head><meta charset='utf-8'><title>Short SanDisk — Oxford Alpha Fund Varsity Pitch 2026</title>" + CSS + "</head><body>" + "\n".join(SLIDES) + "</body></html>"
for k, v in T.items():
    html = html.replace(f"[[{k}]]", str(v))
leftover = sorted(set(__import__("re").findall(r"\[\[([a-z0-9_]+)\]\]", html)))
if leftover:
    raise SystemExit(f"unreplaced tokens: {leftover}")
out_html = DECK / "SNDK_short_deck.html"
out_html.write_text(html)
print("wrote", out_html)

out_pdf = DECK / "SNDK_short_deck.pdf"
cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-margins",
       f"--print-to-pdf={out_pdf}", f"file://{out_html}"]
subprocess.run(cmd, check=True, capture_output=True, timeout=180)
print("wrote", out_pdf)

# previews
import fitz  # pymupdf
doc = fitz.open(out_pdf)
prev = DECK / "preview"
prev.mkdir(exist_ok=True)
for f in prev.glob("*.png"):
    f.unlink()
for i, p in enumerate(doc):
    p.get_pixmap(dpi=110).save(prev / f"p{i+1:02d}.png")
print(f"{len(doc)} pages; previews in {prev}")
