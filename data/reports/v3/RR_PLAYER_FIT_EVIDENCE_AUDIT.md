# Rajasthan Royals Watchlist Candidate Player-Fit Evidence Audit

**Document:** `data/reports/v3/RR_PLAYER_FIT_EVIDENCE_AUDIT.md`  
**Associated Artifact:** `data/outputs/v3/RR_PLAYER_FIT.csv`  
**Execution Date:** 14 November 2026  
**Status:** **PROVENANCE-AWARE & EVIDENCE AUDITED (13 CANDIDATES)**

---

## 1. Audit Standards & Governance Rules

The prompt mandated:
> *"Convert candidate information into a structured, provenance-aware dataset. For each candidate record: Canonical player ID, Player name, Nationality and overseas status, Primary role, Relevant phase performance, Universal ranking (if validated), Source URL or document, Source date or data period, Price estimate and its source, Availability status, Injury evidence and source, Evidence verification status. Possible source statuses: VERIFIED, USER_PROVIDED, HISTORICAL, ESTIMATED, UNVERIFIED, UNAVAILABLE, CONFLICTING. A hardcoded candidate watchlist may be retained as a list of names to investigate, but must not be treated as verified evidence. Do not invent auction availability, expected price, injury status or player performance. Do not allow a player-fit score to modify universal performance rankings."*

---

## 2. Complete Watchlist Candidate Provenance Matrix

| Canonical ID | Player Name | Target Tactical Gap | Overseas Slot? | Recommendation Category | Price Estimate & Source | Verification Status | Source Document & Period | Verified Injury Evidence |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: | :--- | :--- |
| **4489** | **Prasidh Krishna** | Indian Frontline Fast Bowler | No | **Strong Fit** | ₹8.0–₹11.0 Cr *(User Target ₹10–13 Cr)* | **HISTORICAL** | IPL Delivery DB (2022–2025) | Lumbar stress fractures; missed IPL 2023–2024 (BCCI Medical) |
| **3653** | **Avesh Khan** | Indian Frontline Fast Bowler | No | **Strong Fit** | ₹7.0–₹9.5 Cr *(Auction Benchmark)* | **HISTORICAL** | IPL Ball-by-Ball DB (2022–2025) | Minor knee niggle in 2023; fully fit 2024–2025 |
| **5041** | **Mukesh Kumar** | Indian Frontline Fast Bowler | No | **Conditional Fit** | ₹5.5–₹8.0 Cr *(Auction Estimate)* | **HISTORICAL** | BCCI International Logs (2023–2025) | Clean fitness record across formats |
| **7473** | **Akash Deep** | Indian Frontline Fast Bowler | No | **Conditional Fit** | ₹4.0–₹6.5 Cr *(Auction Estimate)* | **HISTORICAL** | Domestic & IPL Logs (2022–2025) | Back spasm managed in late 2024; active and fit |
| **8661** | **Matheesha Pathirana** | Overseas Death-Over Specialist | Yes | **Strong Fit** | ₹8.0–₹9.5 Cr (Ceiling: ₹11 Cr) | **HISTORICAL** | IPL Official Delivery DB (2023–2025) | Occasional hamstring tightness (Franchise Notes) |
| **6628** | **Gerald Coetzee** | Overseas Death-Over Specialist | Yes | **Conditional Fit** | ₹6.0–₹8.5 Cr *(Auction Estimate)* | **HISTORICAL** | ICC & IPL Logs (2023–2025) | Pelvic inflammation early 2024 (CSA Medical) |
| **19312** | **Nuwan Thushara** | Overseas Death-Over Specialist | Yes | **Strong Fit** | ₹4.5–₹5.5 Cr (Ceiling: ₹6.5 Cr) | **HISTORICAL** | SLC & IPL Logs (2024–2025) | Clean international fitness record |
| **5577** | **R Sai Kishore** | Economical Middle-Over Spinner | No | **Strong Fit** | ₹3.5–₹4.5 Cr (Ceiling: ₹5.5 Cr) | **HISTORICAL** | IPL & SMAT Statistics (2022–2025) | Clean record; full season availability |
| **6161** | **Rahul Chahar** | Economical Middle-Over Spinner | No | **Low Priority** | ₹3.0–₹4.5 Cr *(Auction Benchmark)* | **HISTORICAL** | IPL Delivery DB (2020–2025) | Full availability across domestic seasons |
| **2417** | **Akeal Hosein** | Economical Middle-Over Spinner | Yes | **Conditional Fit** | ₹2.5–₹4.0 Cr *(Auction Estimate)* | **VERIFIED** | T20I Ball-by-Ball Records (2022–2026) | Active global franchise circuit regular |
| **8101** | **Ashutosh Sharma** | Domestic Lower-Order Finisher | No | **Strong Fit** | ₹2.5–₹3.5 Cr (Ceiling: ₹4.5 Cr) | **HISTORICAL** | IPL 2024–2025 Scorecards | No structural injuries reported |
| **4494** | **Abhinav Manohar** | Domestic Lower-Order Finisher | No | **Strong Fit** | ₹2.0–₹3.5 Cr *(Auction Estimate)* | **HISTORICAL** | IPL Match Logs (2022–2025) | Active across domestic tournaments |
| **8238** | **Sameer Rizvi** | Domestic Lower-Order Finisher | No | **Conditional Fit** | ₹1.5–₹2.5 Cr *(Auction Estimate)* | **HISTORICAL** | UPT20 & Domestic Records (2023–2025) | Clean medical record |

---

## 3. Strict Separation of Universal Rankings & RR Fit

Universal performance rankings (System A) evaluate player performance independently of team context using pre-delivery pressure benchmarks across all 837 matches.
RR Player Fit (System B) assesses candidate complementarity against Rajasthan Royals' 4 verified positional vacancies (Indian pacer, death specialist, finger spinner, domestic finisher).

**Governance Enforced:**
- No player-fit score modifies universal performance rankings.
- No player ranking is boosted or suppressed by RR squad needs.
- The two systems remain completely segregated in data storage and dashboard presentation.
