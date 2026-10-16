# One-year cost estimate (build + running)

> **TEAM ESTIMATE — draft, inputs to be confirmed by the team; not a quote.**
> Every price below is a public price, either a list price or a merchant quote on a price-comparison site (S1, S3–S6). Each source was opened on **16 Oct 2026** when this sheet was drafted; the team still needs to check them. The source URL, the exact price seen and its currency are given for each one. Quantities are judgement inputs: each one is a parameter with a stated default, and each is marked *team to confirm*. A cost with no public price is listed as a parameter with no number, and it is left out of the totals. No supplier was contacted. Prices change, and a real purchase needs fresh quotes.

## Summary

All figures are in MOP. They are built from the parameters in section 1 and the prices in section 2. The arithmetic is in sections 3 to 5.

| | Low | High |
|---|---:|---:|
| **(a) Build, one-off** (phones, mounts, power banks, signs) | 31,445.90 | 78,497.24 |
| **(b) Running, per year: cash** (SIMs, cloud, Apple developer fee) | 2,939.90 | 22,598.72 |
| **(b) Running, per year: staff time** (field placement + 0.2 FTE upkeep) | 45,380.77 | 84,680.77 |
| **Year-1 total (a + b)** | **79,766.57** | **185,776.73** |
| Year-1 cash only, without staff time | 34,385.80 | 101,095.96 |

In round numbers, year one costs **about MOP 80,000 (low) to MOP 186,000 (high)**. About MOP 34,000 to 101,000 of that is cash. The rest is staff time, which an operator may already employ. The two largest lines are the phones (B1: MOP 27,810 low, 68,189 high) and the 0.2 FTE upkeep assumption (R5: MOP 43,200 low, 49,200 high).

---

## 1. Parameters (judgement inputs; team to confirm all)

| # | Parameter | Low | High | Where the default comes from | Status |
|---|---|---:|---:|---|---|
| P1 | Sensing positions (phones placed each day) | 9 | 9 | `shared/zones.json` → `sensors`: 9 positions in 7 zones (2 at the Ruins, 2 at Senado Square, 1 in each other zone) | team to confirm |
| P2 | Spare phones, % of P1 (rounded up) | 10% → 1 | 20% → 2 | Team judgement. Spares cover breakage, theft and flat batteries. | team to confirm |
| P3 | Kits bought = P1 + spares | 10 | 11 | P1 + P2 | follows P1, P2 |
| P4 | Peak deployment days per year | 7 | 40 | Low: Golden Week only (it ran 7 days in 2026; `docs/research/brief-evidence.md`, header). High: the team's earlier assumption in `docs/deployment.md` (commit 79595e9), which covered Golden Week, Chinese New Year, Grand Prix and festivals | team to confirm |
| P5 | Sensing hours per day | 7 | 12 | Low: 12:00–19:00, the hours of the police temporary pedestrian zones at Taipa Old Village and 關前後街, 1–6 Oct 2026 (`brief-evidence.md`, section 2). These are not the hours of the project's 7 zones; they are used only as a proxy. High: 10:00–22:00, a team assumption | team to confirm |
| P6 | Staff-hours per phone per deployment day (place, register in app, collect) | 0.4 | 1.0 | Low: the earlier `deployment.md` assumption (2 staff × 4 h ÷ 20 kits = 0.4). High: a team judgement that adds walking between 7 zones and a midday check | team to confirm by timing a dry run |
| P7 | Power banks per kit | 1 | 2 | Team judgement. No battery measurement exists in the repo: `docs/architecture.md`, "Performance", lists only timings measured on a Mac | team to confirm by a battery test |
| P8 | Phone life (years), used only for the annualised view | 3 | 3 | Earlier `deployment.md` assumption | team to confirm |
| P9 | Upkeep engineer (maintenance, retraining, support), FTE | 0.2 | 0.2 | Earlier `deployment.md` assumption | team to confirm |
| P10 | Months per year that the cloud runs | 12 | 12 | Team assumption: always on. Pausing between peak periods was not checked against the hosts' billing rules | team to confirm |
| P11 | Paid hours per month, used to turn monthly pay into an hourly rate | 208 | 208 | 48 h/week × 52 ÷ 12. 48 h is the weekly cap on normal working hours under the Labour Relations Law (source S16). A shorter week gives a higher hourly rate | team to confirm |
| P12 | Data per upload, including the TLS/TCP allowance | 2 KB | 2 KB | Measured on 16 Oct: about 0.97 KB per upload at the application layer (see section 6). Doubled as an allowance for the encryption and network overhead | team to measure on a phone |
| P13 | Apple grants the operator the developer fee waiver | yes → R3 = 0 | no → R3 = USD 99 | S14 says government entities can request a waiver. Whether the operator qualifies, and whether Apple grants it, is not known | team to confirm |
| P14 | Render accepts the operator's pilot on its Hobby workspace | yes → no workspace fee | no → Pro workspace, USD 25/month | S11 describes Hobby as "For individuals building personal projects and prototypes". If the low case cannot use Hobby, add MOP 2,424.87 a year (section 4, notes) | team to confirm with Render |
| P15 | Backend instance size | 0.5 CPU / 512 MB | 1 CPU / 2 GB | Short memory runs on a Mac only (section 6). If the low case needs 2 GB, low R2 rises by (25 − 7) × 12 × 8.0829 = MOP 1,745.91 | team to confirm by a sustained run on the host |
| P16 | Signs printed | 10 A2, single-sided, 128 g | 10 A2, double-sided, 157 g | One per position (P1 = 9) plus one spare; the paper and sides follow the two S7 price rows | team to confirm the design and count |
| P17 | Paid cloud accounts (high case) | — | 1 Vercel Pro developer seat; 1 Supabase Pro project on Micro compute | S13 prices Pro per "Developer seat" ("$20 / month"). S12's Pro plan includes the first project and enough compute credit for one Micro instance. More seats or a larger instance cost more | team to confirm |
| P18 | CTM Buddy still charged once the Social plan starts (high case) | — | no (assumed) | Neither CTM page says. S10 says an existing package plan "needs to be terminated" before a change of plan. If Buddy is still charged, add 11 × 13 × 10.00 = MOP 1,430.00 a year | team to confirm at a CTM shop |

## 2. Prices seen on 16 Oct 2026

Currency conversion uses the Monetary Authority of Macao (AMCM) interbank midpoint for 16 Oct 2026, **HKD 1 = MOP 1.0300** and **USD 1 = MOP 8.0829** (S17). MOP figures are rounded to 2 decimals.

| ID | Item | Exact price seen (currency) | MOP | Source (accessed 16 Oct 2026) |
|---|---|---|---:|---|
| S1 | **Phone, low:** Apple iPhone SE (3rd generation) 64GB, Hong Kong merchant quotes in the local-warranty (行貨) column of price.com.hk's price listing. The model is not in Apple Macau's current line-up (https://www.apple.com/mo/iphone/), so confirm new or used condition and the warranty with the merchant | "HK$2,700-2,850" (lowest local-warranty quote HK$2,700, from several merchants updated 15–16 Oct; parallel-import quotes of HK$2,100–2,700 not used) | 2,781.00 | https://www.price.com.hk/product.php?p=536208 |
| S2 | **Phone, high:** Apple iPhone 17e, new, from Apple's Macau site | "MOP$6,199 起" (from) | 6,199.00 | https://www.apple.com/mo/iphone-17e/ |
| S3 | **Mount, low:** Multipro tablet & phone tripod 2 m (4089), height 70–200 cm | "HK$148" (3 quotes, updated 9–14 Oct) | 152.44 | https://www.price.com.hk/product.php?p=544764 |
| S4 | **Mount, high:** Ugreen LP585 phone/tablet tripod stand, aluminium, 174.1 cm | "HK$198" | 203.94 | https://www.price.com.hk/product.php?p=688798 |
| S5 | **Power bank, low:** Xiaomi Power Bank 3 fast-charge 20000mAh PLM18ZM, 2 USB-A ports and 1 USB-C port, 18 W | "HK$160" | 164.80 | https://www.price.com.hk/product.php?p=639461 |
| S6 | **Power bank, high:** Anker 30W Power Bank 20000mAh A1384 | "HK$320-349" (21 quotes; the lowest, HK$320, is used) | 329.60 | https://www.price.com.hk/product.php?p=630517 |
| S7 | **Signs:** e-print A2 posters (420 × 594 mm), 10 pieces. Low: 128 g gloss, single-sided. High: 157 g gloss, double-sided | price table, 10 pcs: "$450" (low), "$790" (high); the site's order panel prices in HK$ | 463.50 / 813.70 | https://www.e-print.com.hk/en_products_poster_printing |
| S8 | **SIM, low:** CTM Chill Card prepaid SIM, valid 180 days from activation (a reload extends it). It auto-subscribes "CTM Buddy" at "$10 / 30 Days" from the balance | "Face Value Amounts (MOP): $100 and $200" | 100.00 | https://www.ctm.net/en-US/fiveG/T31-010010010120090/202511/b7b0b9b76d0e4e49b8fb49cdd32347f3.html |
| S9 | **Data, low:** CTM "Data Usage without Expiry Date Plan for 3 Destinations", valid until the prepaid card expires, paid from the card balance | "$38/5GB" (offer plan, MOP) | 38.00 | https://www.ctm.net/en-US/fiveG/T31-010010010090050/20264/a87329b1d8e3483386268aa878d5bf79.html |
| S10 | **Data, high:** CTM "5.5G Social Unlimited Data Plan", renewed every 30 days from a prepaid balance; full speed for 12 GB | "$88/ 30 days" (MOP) | 88.00 | https://www.ctm.net/en-US/fiveG/T31-010010010090060/20267/251bb9a6787b4ba0b687fc2f63d35554.html |
| S11 | **Cloud, Render:** Hobby workspace "$0/mo + compute" ("For individuals building personal projects and prototypes"); Pro workspace "$25/mo + compute"; web service 0.5 CPU / 512 MB "$7/month"; web service 1 CPU / 2 GB "$25/month"; Postgres 0.1 CPU / 256 MB "$6/month" with "1 GB SSD storage included" and "Expandable storage ($0.30/GB)" (the page does not say on that line whether this is per month) | as quoted (USD) | 7 USD = 56.58 | https://render.com/pricing |
| S12 | **Database, Supabase Pro:** "$25/month". "Paid plans include $10/mo in compute credits, enough to cover one Micro instance." (Free projects "are paused after 1 week of inactivity".) | "$25/month" (USD) | 202.07 | https://supabase.com/pricing |
| S13 | **Dashboard, Vercel Pro:** "$20 /mo."; the Team Seats table prices a Pro "Developer seat" at "$20 / month". The Hobby plan "is for personal, non-commercial use" | "$20 /mo." (USD), for 1 developer seat | 161.66 | https://vercel.com/pricing |
| S14 | **iOS app signing:** Apple Developer Program "$99 annual membership". Government entities can request a fee waiver. Without a membership, a free personal team can register 3 devices, with profiles that expire after 7 days | "$99" (USD per year) | 800.21 | https://developer.apple.com/programs/ ; https://developer.apple.com/help/account/membership/fee-waivers/ ; https://developer.apple.com/support/compare-memberships/ |
| S15 | **Wage:** DSEC Employment Survey, Apr–Jun 2026: "Median monthly employment earnings of employed residents and the employed population in the second quarter of 2026 were MOP20,500 and MOP18,000 respectively." | MOP 18,000 (low) / MOP 20,500 (high) per month | 18,000 / 20,500 | https://www.gcs.gov.mo/news/detail/en/N26GenaKjt (GCS, 31 Jul 2026) |
| S16 | **Working week:** Labour Affairs Bureau (DSAL) reply to the Legislative Assembly, signed 27 Jun 2025. Under the Labour Relations Law, normal working hours "每周不得超過48小時" (may not exceed 48 hours a week) | 48 h/week | — | https://al.gov.mo/uploads/attachment/2025-07/182906875b863ed3c1.pdf |
| S17 | **Exchange rates:** AMCM interbank midpoint, date field 2026-10-16 | HKD 1 = 1.0300; USD 1 = 8.0829 | — | https://www.amcm.gov.mo/zh-hant/financial-information/interbank-midpoint |

**Why these phones.** The app targets **iOS 17.0** (`ios/CrowdPulseSensor/project.yml`, `deploymentTarget`). Apple lists iOS 17 support for the iPhone XR, XS and later, and for the iPhone SE (2nd and 3rd generation) (https://support.apple.com/zh-tw/guide/iphone/iphe3fa5df43/17.0/ios/17.0). Both phones chosen here are also on Apple's list for the current iOS 27, so they still get security updates (https://support.apple.com/zh-tw/guide/iphone/iphe3fa5df43/ios). The app is iOS-only, so an Android phone would first need an Android port. That port is not costed. A used phone may be cheaper, but listings on second-hand boards are single offers, not list prices or merchant quotes, so none was used. The iPhone SE (3rd gen) charges through Lightning and the iPhone 17e through USB-C. Each one uses the cable in its box with the power bank's USB port (team to confirm the box contents).

## 3. (a) BUILD — one-off

| Line | Low: arithmetic | Low (MOP) | High: arithmetic | High (MOP) |
|---|---|---:|---|---:|
| B1 Phones | 10 kits × 2,781.00 (S1) | 27,810.00 | 11 kits × 6,199.00 (S2) | 68,189.00 |
| B2 Tripods | 10 × 152.44 (S3) | 1,524.40 | 11 × 203.94 (S4) | 2,243.34 |
| B3 Power banks | 10 × 1 × 164.80 (S5) | 1,648.00 | 11 × 2 × 329.60 (S6) | 7,251.20 |
| B4 Trilingual signs, one per position (10 printed for 9 positions) | 1 × 463.50 (S7, single-sided; P16) | 463.50 | 1 × 813.70 (S7, double-sided; P16) | 813.70 |
| **Build total** | | **31,445.90** | | **78,497.24** |

## 4. (b) RUNNING — per year

| Line | Low: arithmetic | Low (MOP) | High: arithmetic | High (MOP) |
|---|---|---:|---|---:|
| R1 Mobile data, one SIM per kit | 10 × 100.00 (S8). The MOP 100 balance pays the 5 GB pack (S9, 38.00) plus 6 × 10.00 CTM Buddy = 98.00 over the card's 180 days. 5 GB is more than the 0.12 GB a phone needs in this case (section 6) | 1,000.00 | 11 × 13 × 88.00 (S10). 13 periods of 30 days cover 365 days. The fee is taken every 30 days from each SIM's prepaid balance (S10), so each SIM needs 13 × 88.00 = MOP 1,144.00 of balance over the year. A card's face value is MOP 100 or 200 (S8), so each SIM must be reloaded several times. S8 allows reloads up to "a maximum value of $50,000"; reload channels and any fees were not checked | 12,584.00 |
| R2 Cloud backend + database + dashboard | (7 backend + 6 Postgres + 7 dashboard, all on Render, Hobby workspace 0; P14, P15) = USD 20/month × 12 = USD 240 × 8.0829 (S11) | 1,939.90 | (25 Render Pro workspace + 25 backend 1 CPU/2 GB + 25 Supabase Pro, 1 project on Micro + 20 Vercel Pro, 1 developer seat; P17) = USD 95/month × 12 = USD 1,140 × 8.0829 (S11–S13) | 9,214.51 |
| R3 Apple Developer Program (needed to install the app on 10–11 phones for longer than 7 days) | 0, if Apple grants the government-entity fee waiver (S14, P13) | 0.00 | USD 99 × 8.0829 (S14) | 800.21 |
| R4 Field staff time (place, register, collect) | 9 positions × 0.4 h × 7 days × (18,000 ÷ 208 = 86.54/h) (S15, P11) | 2,180.77 | 9 × 1.0 h × 40 days × (20,500 ÷ 208 = 98.56/h) | 35,480.77 |
| R5 Upkeep engineer | 0.2 FTE × 12 months × 18,000 (S15) | 43,200.00 | 0.2 × 12 × 20,500 | 49,200.00 |
| **Running total** | | **48,320.67** | | **107,279.49** |

Notes on R1–R3:
- R1: the CTM pages say plan fees are taken from the prepaid balance. Whether the card's face value is all usable balance should be confirmed at a CTM shop. The Chill Card page also caps prepaid registrations at "up to 25" for each institutional customer "(excluding public entities)". That covers 10–11 SIMs for a private operator. The page states no limit or process for public entities, so if the operator is one (for example PSP or MGTO), confirm at a CTM shop.
- R1, high: neither CTM page says whether the auto-applied CTM Buddy (MOP 10 per 30 days, S8) keeps charging once the Social plan starts (P18). If it does, add MOP 1,430.00 a year.
- R2, low: the Hobby workspace is described as "For individuals building personal projects and prototypes" (P14). If Render does not accept an operator's pilot on Hobby, add the Pro workspace fee: USD 25 × 12 × 8.0829 = MOP 2,424.87 a year. A Vercel Hobby dashboard is not used in either case, because Vercel limits Hobby to personal, non-commercial use (S13).
- R3: the free alternative (a personal team) allows only 3 devices, with profiles that expire every 7 days (S14), so it cannot run 10–11 phones.

R4 and R5 use the overall median monthly earnings, as no occupation-level figure for engineers was opened. An engineer's real pay is probably higher, so R5 is likely an underestimate. Both lines cost staff time. If the operator's own staff do this work, the lines are an opportunity cost, not new cash. Employer on-costs (for example social security contributions) are not included.

## 5. Totals

| | Low | High |
|---|---:|---:|
| (a) Build | 31,445.90 | 78,497.24 |
| (b) Running, cash (R1 + R2 + R3) | 1,000.00 + 1,939.90 + 0.00 = 2,939.90 | 12,584.00 + 9,214.51 + 800.21 = 22,598.72 |
| (b) Running, staff (R4 + R5) | 2,180.77 + 43,200.00 = 45,380.77 | 35,480.77 + 49,200.00 = 84,680.77 |
| **Year 1 = (a) + (b)** | 31,445.90 + 48,320.67 = **79,766.57** | 78,497.24 + 107,279.49 = **185,776.73** |
| Year-1 cash only = (a) + running cash | 31,445.90 + 2,939.90 = 34,385.80 | 78,497.24 + 22,598.72 = 101,095.96 |
| Annualised: hardware (B1 + B2 + B3) ÷ 3 years + signs + running | 30,982.40 ÷ 3 + 463.50 + 48,320.67 = 59,111.64 | 77,683.54 ÷ 3 + 813.70 + 107,279.49 = 133,987.70 |

## 6. Repo facts and measurements behind the quantities

- **Positions:** 9 sensor positions in 7 zones (`shared/zones.json`). Kit contents (phone, tripod or clamp, battery pack, laminated instructions), with morning placement and evening collection, come from `docs/deployment.md`, "Operational model". The mount height of 1.5–2.5 m comes from `docs/experiment-protocol.md`.
- **Upload rate:** the app sends one upload every 3 s by default, adjustable from 1 to 5 s (`ios/CrowdPulseSensor/Sources/Services/SensorSettings.swift`). That is 3,600 ÷ 3 = 1,200 uploads per hour.
- **Upload size, measured 16 Oct 2026** against the local backend with one valid observation: request body 419 B, request headers ≈ 273 B, response body 141 B, response headers 132 B, so ≈ 965 B per upload. The sheet allows 2 KB per upload (P12).
- **Data per phone:** 1,200 × 7 h × 2 KB = 16.8 MB a day, × 7 days = 0.12 GB a year (low). 1,200 × 12 h × 2 KB = 28.8 MB a day, × 40 days = 1.15 GB a year (high). Both fit inside CTM's 5 GB pack (S9).
- **Backend memory, short runs on a Mac only (16 Oct 2026):** the FastAPI backend (`backend/`, with the scikit-learn models in `ml/models/`, 89 MB on disk) ran the built-in 9-phone Golden Week simulation on a scratch SQLite database on an Apple-silicon Mac. Its resident memory (RSS), sampled every 10 s, was 300–346 MiB in a 3-minute run. In a 20-minute run (covering the simulated scenario) it peaked at 343 MiB during start-up, then stayed at or below 285 MiB (median 261 MiB), with no upward trend. These are short runs, not a sustained measurement. macOS leaves compressed memory out of RSS, so the cloud host's Linux may show more; it has not been measured there. That leaves little headroom on a 512 MB instance (low), which is why the high case uses 2 GB (P15). The dashboard's memory has not been measured. To rerun from the repo root:
  `CROWDPULSE_DATABASE_URL=sqlite:////tmp/cp_mem.db .venv/bin/python -m uvicorn backend.app.main:app --port 8771 & PID=$!; while kill -0 $PID 2>/dev/null; do ps -o rss= -p $PID; sleep 10; done` (RSS in KiB; stop with `kill $PID`). The simulation starts by default (`shared/config.json`, `live_simulation`) and runs 120 simulated minutes at 6× speed, about 20 real minutes.
- **Database size, projected from the 20-minute run (SQLite only):** raw observations and predictions are pruned after 48 h (`docs/privacy.md`, `CROWDPULSE_RETENTION_HOURS`). Predictions, not observations, take most of the space. The run stored 12,969 observations at about 335 B each and 8,967 predictions at about 2,174 B each (table plus its indexes, from SQLite's `dbstat`). The backend writes 21 predictions (7 zones × 3 horizons) on each refresh while data arrives: about 26,900 an hour in this run, and 37,800 an hour if every 2 s refresh (the configured interval) runs on time. Dashboard reads right after an upload can trigger extra refreshes; that was not measured. A 48 h window holds 2 sensing days:
  - Low (7 h a day, 14 h): 151,200 observations (0.05 GB) + 376,600–529,200 predictions (0.82–1.15 GB) ≈ **0.87–1.20 GB**. This may exceed the 1 GB included with Render's Postgres (S11). Render lists "Expandable storage ($0.30/GB)"; if that is per month, 1 GB more costs USD 0.30 × 12 × 8.0829 = MOP 29.10 a year. This is not in the totals.
  - High (12 h a day, 24 h): 259,200 observations (0.09 GB) + 645,600–907,200 predictions (1.40–1.97 GB) ≈ **1.5–2.1 GB**, inside Supabase Pro's 8 GB (S12).
  - Zone states (one row per zone per minute, about 336 B each) are not pruned: about 0.07 GB a year in the high case.
  - Postgres stores rows differently and was not measured, so these sizes are a guide only.

## 7. Lines with no public price (parameters only; not in the totals)

| Line | Why there is no number |
|---|---|
| Weatherproofing for signs (lamination or a clear sleeve) | e-print lists lamination as an available process but shows no price for it |
| Laminated staff instruction card in each kit | Not priced. It could be printed in-house |
| Calibration at installation: hand-count 20 frames per position (`experiments/results/mall/summary.md`) | Staff time not yet measured. Time it in the school test |
| Operations-room monitoring of the dashboard | Assumed to be done by the operator's existing control-room staff. Team to confirm |
| Delivery from Hong Kong to Macau; card or e-payment surcharges | Merchants list these separately or on request |
| Lock or tether per kit; loss beyond the spares | No product chosen |
| Insurance; legal and privacy review; permission to place devices at heritage sites | No price looked up. The legal points are open questions in `docs/research/brief-evidence.md`, section 8 |
| Hosting inside Macau, if the operator requires local hosting | No price looked up |
| China Telecom Macau data plans | The operator's site (redirecting to 1888.com.mo) did not render on 16 Oct. CTM prices are used instead. 3 Macau was not used, because its notice says its mobile service ends after 30 Nov 2026 (https://www.three.com.mo/stop_service.html) |
| A fixed counting camera, for comparison | No published price was found (`docs/research/brief-evidence.md`, section 8). No comparison is made |
| Electricity for charging | Not costed |

## 8. How to update this sheet

1. Change a parameter in section 1. Then redo only the lines that cite it, in sections 3–5.
2. Before a real purchase, reopen every source in section 2. Record the new price, its currency and the access date, and replace the row.
3. Keep the label at the top until the team has confirmed every *team to confirm* input.
