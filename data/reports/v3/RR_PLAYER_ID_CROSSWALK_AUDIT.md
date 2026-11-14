# Rajasthan Royals Player Entity Crosswalk & ID Audit

**Document:** `data/reports/v3/RR_PLAYER_ID_CROSSWALK_AUDIT.md`  
**Associated Artifact:** `data/outputs/v3/RR_PLAYER_ID_CROSSWALK.csv`  
**Execution Date:** 14 November 2026  
**Status:** **AUDITED & VERIFIED (40 ENTITIES)**

---

## 1. Background & Problem Statement

During the initial ingestion of Rajasthan Royals reference files (`data/reference/rr_2026_user_brief.csv` and `data/reference/rr_2027_auction_assumptions.csv`), external identifier keys were provided that did not match the primary database keys in `competition_team_player_mapping_ipl_t20i.csv`, `playing_eleven_ipl_t20i.csv`, and `ball_by_ball_ipl_t20i.csv`.

Furthermore, in legacy scouting scripts, candidate IDs suffered from severe misattribution:
- **Prasidh Krishna** was assigned `6424` in legacy fit scripts, which in reality is the primary database ID of **Kuldeep Sen**!
- **Avesh Khan** was assigned `4707`, whereas his canonical database ID is `3653`.
- **Mukesh Kumar** was assigned `3182`, whereas his canonical database ID is `5041`.
- **Akash Deep** was assigned `7884`, whereas his canonical database ID is `7473`.
- **R Sai Kishore** was assigned `4709`, whereas his canonical database ID is `5577`.
- **Ashutosh Sharma** was assigned `7828`, whereas his canonical database ID is `8101`.

To prevent price misallocation, incorrect statistical joins, and corrupted squad modeling, a verified **Player Entity Crosswalk** (`data/outputs/v3/RR_PLAYER_ID_CROSSWALK.csv`) was constructed.

---

## 2. Complete Entity Crosswalk Table

| Canonical ID | Canonical Player Name | Reference ID | Reference Name in Brief | Entity Group | Resolution Method | Verification Status | Audit Notes |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **50284** | Vaibhav Sooryavanshi | 281699 | Vaibhav Sooryavanshi | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 281699 mapped to canonical dataset ID 50284 |
| **7260** | Dhruv Jurel | 7825 | Dhruv Jurel | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 7825 mapped to canonical dataset ID 7260 |
| **6819** | Yashasvi Jaiswal | 6948 | Yashasvi Jaiswal | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 6948 mapped to canonical dataset ID 6819 |
| **8182** | Donovan Ferreira | 8182 | Donovan Ferreira | RR Squad | EXACT_NAME_MATCH | VERIFIED | Canonical ID matches brief ID |
| **6423** | Riyan Parag | 6423 | Riyan Parag | RR Squad | EXACT_NAME_MATCH | VERIFIED | Canonical ID matches brief ID |
| **152** | Ravindra Jadeja | 152 | Ravindra Jadeja | RR Squad | EXACT_NAME_MATCH | VERIFIED | Canonical ID matches brief ID |
| **25139** | Shubham Dubey | 7826 | Shubham Dubey | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 7826 mapped to canonical dataset ID 25139 |
| **3297** | Shimron Hetmyer | 3249 | Shimron Hetmyer | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 3249 mapped to canonical dataset ID 3297 |
| **2436** | Dasun Shanaka | 2386 | Dasun Shanaka | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 2386 mapped to canonical dataset ID 2436 |
| **3298** | Jofra Archer | 3262 | Jofra Archer | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 3262 mapped to canonical dataset ID 3298 |
| **7312** | Nandre Burger | 7883 | Nandre Burger | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 7883 mapped to canonical dataset ID 7312 |
| **67036** | Brijesh Sharma | 281700 | Brijesh Sharma | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 281700 mapped to canonical dataset ID 67036 |
| **7503** | Ravi Bishnoi | 7503 | Ravi Bishnoi | RR Squad | EXACT_NAME_MATCH | VERIFIED | Canonical ID matches brief ID |
| **2411** | Sandeep Sharma | 1602 | Sandeep Sharma | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 1602 mapped to canonical dataset ID 2411 |
| **6806** | Tushar Deshpande | 2524 | Tushar Deshpande | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 2524 mapped to canonical dataset ID 6806 |
| **1487** | Adam Milne | 1629 | Adam Milne | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 1629 mapped to canonical dataset ID 1487 |
| **7545** | Kuldeep Sen | 6424 | Kuldeep Sen | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 6424 mapped to canonical dataset ID 7545 (corrected collision with Prasidh) |
| **26663** | Kwena Maphaka | 8662 | Kwena Maphaka | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 8662 mapped to canonical dataset ID 26663 |
| **43798** | Lhuan Pretorius | 281701 | Lhuan-dre Pretorius | RR Squad | NAME_VARIANT_MATCH | VERIFIED | Brief ID 281701 mapped to canonical dataset ID 43798 |
| **8580** | Yudhvir Singh | 7827 | Yudhvir Singh | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 7827 mapped to canonical dataset ID 8580 |
| **48557** | Vignesh Puthur | 281702 | Vignesh Puthur | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 281702 mapped to canonical dataset ID 48557 |
| **47523** | Aman Rao Perala | 281703 | Aman Rao | RR Squad | NAME_VARIANT_MATCH | VERIFIED | Brief ID 281703 mapped to canonical dataset ID 47523 |
| **41503** | Yash Punja | 281704 | Yash Punja | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 281704 mapped to canonical dataset ID 41503 |
| **7269** | Sushant Mishra | 7487 | Sushant Mishra | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 7487 mapped to canonical dataset ID 7269 |
| **43965** | Emanjot Singh Chahal | 281705 | Emanjot Chahal | RR Squad | NAME_VARIANT_MATCH | VERIFIED | Brief ID 281705 mapped to canonical dataset ID 43965 |
| **4409** | Sam Curran | 1918 | Sam Curran | RR Squad | EXACT_NAME_MATCH | VERIFIED | Brief ID 1918 mapped to canonical dataset ID 4409 (Injured, replaced by Shanaka) |
| **60700** | Ravi Singh | *None* | *Omitted from Brief* | RR Squad | ROSTER_RECORD | VERIFIED | Present in RR 2026 squad roster (1 app, 4 runs) |
| **4489** | Prasidh Krishna | 6424 | Prasidh Krishna | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 4489; legacy script had 6424 (Kuldeep Sen) |
| **3653** | Avesh Khan | 4707 | Avesh Khan | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 3653; legacy script had 4707 |
| **5041** | Mukesh Kumar | 3182 | Mukesh Kumar | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 5041; legacy script had 3182 |
| **7473** | Akash Deep | 7884 | Akash Deep | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 7473; legacy script had 7884 |
| **8661** | Matheesha Pathirana | 8661 | Matheesha Pathirana | Watchlist | EXACT_MATCH | VERIFIED | Canonical ID matches reference ID 8661 |
| **6628** | Gerald Coetzee | 6863 | Gerald Coetzee | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 6628; legacy script had 6863 |
| **19312** | Nuwan Thushara | 8663 | Nuwan Thushara | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 19312; legacy script had 8663 |
| **5577** | Sai Kishore | 4709 | R Sai Kishore | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 5577; legacy script had 4709 |
| **6161** | Rahul Chahar | 6161 | Rahul Chahar | Watchlist | EXACT_MATCH | VERIFIED | Canonical ID matches reference ID 6161 |
| **2417** | Akeal Hosein | 2417 | Akeal Hosein | Watchlist | EXACT_MATCH | VERIFIED | Canonical ID matches reference ID 2417 |
| **8101** | Ashutosh Sharma | 7828 | Ashutosh Sharma | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 8101; legacy script had 7828 |
| **4494** | Abhinav Manohar | 6820 | Abhinav Manohar | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 4494; legacy script had 6820 |
| **8238** | Sameer Rizvi | 7829 | Sameer Rizvi | Watchlist | CORRECTED_MISATTRIBUTION | VERIFIED | Corrected canonical ID 8238; legacy script had 7829 |

---

## 3. Governance Rules Enforced

1. **Primary Key Guarantee:** All model pipelines (`src/models/`, `src/cricket_engine/`, `src/scouting_engine/`) must join data strictly on `canonical_player_id`.
2. **Contract Protection:** Contract prices in `rr_2026_player_contribution.csv` are joined exclusively through this crosswalk.
3. **No Blind Imputation:** Any unmapped player ID is flagged as `UNRESOLVED` and quarantined.
