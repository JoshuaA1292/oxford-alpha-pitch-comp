# Variant Perception Playbook

**Oxford Alpha Fund · Varsity Pitch Competition 2026 · Strategy Memo**

A research-backed plan for finding the stock, building the analytics, and winning the final — engineered around what the judges at Point72, Fidelity, and Citadel actually pay for. Compiled 27 Aug 2026 from a 7-agent research sweep. The stock selection this playbook drove is documented in [CASE_SANDISK_SHORT.md](CASE_SANDISK_SHORT.md).

| | |
|---|---|
| Finals | **15 Oct 2026 · Chamberlain Hotel, London** |
| Format | 10 slides + ≤5 appendix · 10 min pitch · 10 min Q&A |
| Judged on | (a) Originality of idea/thesis · (b) Technical competency in valuation/data analytics · (c) Presentation & Q&A |

---

## 1. The brief, decoded

The mandate: one **long or short** on a US or UK-listed equity, **$2bn+ market cap**, no ADRs, fundamentals-based, minimum **6-month holding period**. Deliverables: a 10-slide deck (plus ≤5 appendix slides), a SumZero-style one-page write-up (required but unassessed), and an optional financial model. 75 teams entered last year; 15 reach online semis; 5 pitch live to PM-level judges.

The guidelines hand us the marking scheme in prose: strong pitches demonstrate *competitive/industry dynamics, what is currently priced in, a contrarian view, a sensible set of scenarios, and a clear event path*. "What's priced in" appearing verbatim in the rules is a gift — it is a precise, quantifiable question, and almost no student team answers it with actual mathematics. We answer it three independent ways (§4).

> **Open item:** the submission deadline for the deck + SumZero write-up is earlier than finals and wasn't public — confirm via varsitypitchcompetition2026@gmail.com.

## 2. What has actually won here

| Year | Winner | Runner-up |
|---|---|---|
| 2022 | **Short** CommScope (COMM) | Long B&M |
| 2023 | **Short** Hayward (HAYW) | Long Churchill Downs |
| 2024 | **Long** KLA Corp (KLAC) | Short Roku |
| 2025 | **Short** Boot Barn (BOOT) | Long James Hardie (JHX) |

Shorts won 3 of 4 years. Every winner was an idiosyncratic, *uncrowded* mid-cap — never a mega-cap consensus name.

The winning decks aren't published, but two 2025 **finalist** decks are, and both were extracted in full during research:

- **Team Upside — Long Global Payments (GPN):** probability-weighted 3-scenario DCF (25/50/25 weights, per-scenario assumption tables), WACC × terminal-growth sensitivity grid, full comps table, per-slide source citations (CapIQ, FRED, Nilson, McKinsey), explicit "Street is bearish, here's why they're wrong" framing.
- **Burry Capital — Short Altria (MO):** the more instructive one. An "uncrowded short" (2% short interest, Hold consensus), a **reverse DCF showing the market prices in implausible assumptions**, NBER price-elasticity econometrics, alternative data (social engagement ratios, CDC surveys, retailer shelf margins, insider-selling tables), a short-return calc netting dividends and borrow cost, and a dated event path with entry and exit catalysts.

**The implication:** a reverse DCF and a scenario-weighted valuation are no longer differentiators at this competition — a finalist did both last year. They are the *entry ticket*. To win on the technical axis we need the next tier: distributions instead of point estimates, market-implied probabilities extracted from options, regression-disciplined comps, and alternative data we collected ourselves (§4). To win on originality we need an uncrowded name with a falsifiable variant view (§5).

## 3. The core strategy: quantify the expectations gap

Every framework used at the judges' firms is a version of the same idea. Michael Steinhardt called it **variant perception**: a well-founded view meaningfully different from consensus, plus a trigger that forces the market to recognise the gap. Fundamental Edge (which trains Citadel/Point72 pod analysts) formalises it as *Market view → Internal view → Convergence*. Mauboussin and Rappaport's *Expectations Investing* makes it mathematical: read the expectations embedded in the price, then argue about whether *those* are plausible — you never have to defend your own crystal ball, only the market's.

The pitch is structured as four claims, each with quantitative evidence:

1. **What the market believes** — measured, not asserted: reverse-DCF implied drivers, consensus estimates and dispersion, options-implied probability density, short interest and positioning.
2. **What we believe, and why** — 2–3 thesis points grounded in a driver-based model and alternative data we gathered ourselves.
3. **Why the gap closes** — a dated event path of hard catalysts (earnings prints, guidance, regulatory decisions) inside 6–12 months.
4. **What it's worth if we're right — and wrong** — a full distribution of outcomes, not a point target, with an explicit expected value and asymmetry.

**The centerpiece exhibit:** one chart, on one price axis — our **Monte Carlo intrinsic-value distribution** (what we think it's worth, with honest uncertainty) overlaid on the **option-market-implied distribution** (what the market literally prices in), with scenario markers and the current price as a vertical line. No student team will have this; every judge will understand it instantly.

*Framing note:* Citadel (the hedge fund) and Point72 are multi-manager fundamental shops — this playbook speaks their language directly. Jane Street is a market-maker; it doesn't pitch stocks, but its worldview (price = probability-weighted expectation; find where the market's quote is wrong) is exactly the expected-value framing in §4.

## 4. The analytics stack

Six layers, one shared engine. All buildable in Python with free data (yfinance, SEC EDGAR, FRED, Kenneth French library, FINRA), ranked by wow-per-effort with the Q&A traps pre-identified.

### Layer 1 — The spine: driver-based model + reverse DCF *(2–3 days)*
A quarterly, driver-based 3-statement model (units × price, not top-down %), plus the Rappaport–Mauboussin 7-driver reverse DCF: hold consensus drivers fixed and solve for the **market-implied forecast period**, then fix the horizon and solve (scipy `brentq`) for the implied sales CAGR and implied margin. Headline slide: "to justify today's price you must believe X% growth for Y years."
**Trap:** implied growth is joint with margin/WACC assumptions — present it as a locus ("12% CAGR at flat margins, or 8% with 300bps expansion"), never a single number.

### Layer 2 — Distributional valuation: Monte Carlo DCF + scenarios *(1–2 days on top of L1)*
Same DCF function, three uses: point estimate; bear/base/bull scenarios as coherent narratives (probability-weighted EV); and a 10,000+-path Monte Carlo with **correlated** input draws (growth↔margin via Cholesky), citing Damodaran's *Probabilistic Approaches* — "a DCF that gives you a single estimate of value is a flawed model." Output: P(value > price), the price's percentile, and a tornado chart of which assumption drives the spread.
**Trap:** independent draws of growth and margin, or terminal g ≥ WACC paths, will be spotted by any PM. Truncate, correlate, and say so on the slide.

### Layer 3 — Market-implied expectations: options-derived density *(2–3 days · the differentiator)*
**Breeden–Litzenberger:** the risk-neutral probability density is the second derivative of the call-price curve. Pull a liquid 3–12 month option chain, compute our own IVs from mid prices, fit a smoothing spline in vol space, reprice on a dense grid, second-difference. Result: "the options market assigns a Z% probability the stock is above our target by January." Also yields the 25-delta skew for positioning. Plus the cheap layer: consensus EPS revisions and dispersion — is the name in a beat-and-raise or miss-and-lower regime?
**Trap:** a judge will ask "risk-neutral or real-world?" Rehearsed answer: risk-neutral — it embeds risk premia, which is exactly why we use it as *what the market prices*, not what we predict. Validate density ≥ 0 and ∫ ≈ 1 before showing it.

### Layer 4 — Cross-sectional discipline: regression comps + factor decomposition *(1.5 days)*
Replace the naive comp table: regress EV/EBITDA on forward growth, margin, and ROIC across 15–40 comps (Damodaran's published method) — "controlling for quality, fundamentals predict 16×; the stock trades at 12×, two standard errors below the line." Separately, a Fama-French + sector-ETF factor regression (Newey-West errors) decomposing the stock's variance: "X% of this is a sector bet; here is the idiosyncratic part we're actually underwriting."
**Trap:** R² of 30–60% is normal — disclose it. Never claim the historical alpha t-stat supports the thesis; frame as risk decomposition.

### Layer 5 — Proprietary evidence: alternative data *(continuous, start day 1)*
Two or three "we measured it ourselves" exhibits, chosen to fit the name: Google Trends vs. reported revenue; app-rank or Similarweb traffic vs. user growth; ImportYeti customs shipments vs. inventory; job-postings mix from careers-page Wayback snapshots; Glassdoor outlook trend (JFE-validated); Loughran-McDonald uncertainty-word counts across 8 quarters of earnings-call Q&A; Amazon/G2 review velocity as a unit proxy. UK edge: Companies House iXBRL accounts of *private* competitors — data no rival team will have.
**Trap:** label panel-based estimates as estimates and triangulate with a second signal — judges reward the caveat.

### Layer 6 — Forecast discipline: base rates + TAM triangulation *(0.5 day)*
Every growth number — ours and the market's implied one — gets a percentile against Mauboussin's *Base Rate Book* reference class (sales-size decile × horizon). If the price implies growth/margins that ~0% of comparable companies have ever achieved, that's the whole thesis in one sentence. TAM claims get the population × conversion × price funnel plus a Bass-diffusion sanity check. ROIC vs. WACC panel connects growth to value creation.
**Trap:** none — this layer exists to defuse traps.

**If forced to cut:** cut from Layer 4 down — but keep the Breeden–Litzenberger density. It is the single exhibit no other team will have, and it lands directly on the "what's priced in" judging criterion.

## 5. Finding the stock

### Selection criteria (priority order)

1. **Measurable expectations gap** — we can show, with numbers, that the price implies something implausible (or misses something provable).
2. **Uncrowded** — low short interest for a short, light hedge-fund ownership for a long. Every past winner was idiosyncratic.
3. **Hard catalysts inside 6–12 months** — dated events. "Cheap forever" loses.
4. **Alt-data traction** — the business throws off signals we can actually collect.
5. **Options liquidity** — Layer 3 needs a liquid chain.
6. **Q&A survivability** — a business simple enough to know cold in six weeks.

### Hunting grounds screened (late Aug 2026 market context)

Sentiment extremely bullish; most crowded trades: long semiconductors, long Magnificent 7, short yen; hyperscaler AI capex ~$775–800bn; widest dispersion in energy, materials, tech, AI-adjacent.

| Theme | Direction | Candidates | Outcome of screen |
|---|---|---|---|
| AI memory supercycle euphoria | Short | SNDK · WDC · MU | **Selected: SNDK** (see case doc) |
| Spirits priced for terminal decline | Long | DGE.L · BF.B · STZ | Killed — reverse DCF shows market already prices recovery, not decline |
| Healthcare at relative lows | Long | HUM · ELV · GSK.L | Killed — HUM already +145% off lows, window closed |
| Sports betting massacre | Long | FLUT · DKNG · ENT.L | Passed over — Burry made it famous; originality penalty |
| UK housebuilders at P/B lows | Long | PSN.L · BTRW.L | Backup — ordinary analytics surface, no options |
| Post-SaaSpocalypse laggards | Long | TEAM · WDAY · HUBS | Passed over — loud, well-covered battleground |
| UK takeover-wave value | Long | TATE.L · ITRK.L | Passed over — "takeover hope" is a weak primary thesis |
| Speculative froth | Short | IONQ · OKLO · RDDT | Passed over — extreme borrow/squeeze risk |

## 6. The deliverables

- **10-slide deck** (slide-by-slide skeleton now instantiated with real numbers in [CASE_SANDISK_SHORT.md](CASE_SANDISK_SHORT.md) §7).
- **SumZero one-pager**, pod-analyst format: business in one line → variant view in two → consensus vs. our numbers → dated catalysts → bear/base/bull table with probabilities and R/R → risks and kill criteria. Every sentence under ~25 words.
- **Financial model** (optional — we submit it): Excel workbook mirroring the Python engine number-for-number. "Optional" is where the technical-competency criterion is quietly graded.

## 7. Workplan — to finals (15 Oct)

| When | Milestone |
|---|---|
| Week 1 | Screen & commit ✅ (done — SNDK selected 2 Sep, engine built and tested) |
| Weeks 2–3 | Build out remaining exhibits, Excel mirror, primary research (10-K, Kioxia, NAND price series, channel checks) |
| Week 4 | Thesis lock & internal red-team; freeze pillars and event path |
| Week 5 | Deck, one-pager, model — submit ahead of deadline |
| Weeks 6–7 | Rehearse: full run-throughs to stopwatch; mock Q&A drills; refresh all data the week of finals |

**Team roles (3–4):** Modeler (Python engine + Excel mirror, L1–2, 4) · Quant/data (B-L pipeline + alt-data, L3, 5) · Analyst (industry, filings, primary research, write-up) · Storyteller (deck design, narrative, rehearsal discipline).

## 8. How teams lose — our guardrails

| Failure mode | Our guardrail |
|---|---|
| Pitching consensus — "great company, growing market" | The pitch is *built* on a measured expectations gap; no gap, no pitch |
| DCF false precision — five slides of unquestioned model | One valuation slide, distributions not points; detail in appendix |
| No catalyst — "cheap can stay cheap forever" | Hard, dated catalysts are a selection criterion |
| Crowded/obvious name judges know better than us | Uncrowded requirement; positioning data on the slide |
| Quant theatre — techniques the team can't defend | Every exhibit ships with its pre-written trap answer; nothing goes in the deck the presenter can't derive on a whiteboard |
| Hedged 15% target that "reads as average" | Conviction with asymmetry: meaningful base-case return, quantified max-loss, explicit kill criteria |
| Unable to answer "why does this mispricing exist?" | Named answer on the what's-priced-in slide |
| Dying in Q&A | Q&A is 50% of stage time: two weeks of mock-Q&A, appendix built question-first |

---

*Sources: oxfordalphafund.com (2025 finalist decks, guidelines, feedback); Rappaport & Mauboussin, Expectations Investing; Mauboussin, The Base Rate Book / Probabilities & Payoffs (Counterpoint Global); Damodaran, Probabilistic Approaches to Valuation; Steinhardt; Fundamental Edge pod-analyst training material; Valentine, Best Practices for Equity Research Analysts; SumZero quality guidelines; CFA Research Challenge rubric; Sohn Idea Contest winners; BofA Global Fund Manager Survey (Aug 2026).*
