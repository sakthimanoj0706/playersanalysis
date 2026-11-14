# Academic & Professional Cricket Analytics Research Review
**Project:** SupeRR Intelligence — Rajasthan Royals SupeRR Selector Season 2  
**Author:** Independent Multidisciplinary Research Team  
**Focus:** Context-Aware Modeling, Match Leverage, Win Probability, and Bayesian Player Evaluation  
**Directory:** `D:\rrhackthon\research\analysis_only\`  
**Date:** November 12, 2026  

---

## 1. Executive Research Overview

Traditional cricket metrics—batting average, strike rate, bowling average, and economy rate—were formulated in the 19th and 20th centuries for multi-day, unconstrained Test cricket. In Twenty20 cricket, these aggregate statistics suffer from profound structural biases:
1. **Context Blindness:** A boundary hit when needing 8 off 2 balls in the 20th over is treated as identical to a boundary hit when needing 140 off 80 balls.
2. **Resource Asymmetry:** A wicket taken in the 19th over when 6 runs are needed has vastly different game value than a wicket taken in the 2nd over.
3. **Survivor Bias:** Batting averages inflate red-ink finishers who remain not out in short innings.
4. **Volume Conflation:** Players facing low-quality bowling in dead rubbers accumulate nominal volume that masks clutch deficiencies.

To solve the official Rajasthan Royals hackathon objective—**measuring performance in high-pressure situations relative to usual performance**—this research review examines the foundational academic and sports analytics literature across five research directions.

---

## 2. Research Direction A: Context-Aware Cricket Performance

### 2.1 CAMP: A Context-Aware Metric of Player Performance
- **Authors:** Muhammad Sohaib Ayub, Naimat Ullah, Sarwan Ali, Imdad Ullah Khan, Mian Muhammad Awais, Muhammad Asad Khan, Safiullah Faizullah.
- **Year:** 2021 (Published in *Journal of Sports Analytics* / arXiv:2104.05387).
- **Core Concept:** CAMP replaces aggregate box-score counts with a fine-grained, ball-by-ball feature-vector framework. It models each player action as a function of the exact game state:
  - Phase of innings (Powerplay, Middle, Death).
  - Wickets fallen and wickets in hand.
  - Current scoring rate relative to required or par rate.
  - Opposition bowling/batting strength weighting.
- **Key Empirical Finding:** Top players ranked by CAMP matched official "Player of the Match" expert committee awards in **83% of evaluated limited-overs matches** (2001–2019), outperforming traditional metrics derived from Duckworth-Lewis-Stern (DLS).
- **Relevance to SupeRR Intelligence:** Demonstrates that player evaluation must operate on context-binned expectation baselines rather than global player averages.

### 2.2 Expected Run Differential (ERD) & The T20 Match Simulator
- **Authors:** Jack Davis, Harsha Perera, Tim B. Swartz.
- **Year:** 2015 (*A Simulator for Twenty20 Cricket*, *Australian & New Zealand Journal of Statistics*, Vol. 57, No. 1, pp. 55–71; *Player Evaluation in Twenty20 Cricket*, *Journal of Sports Analytics*, Vol. 1, No. 1, pp. 19–27).
- **Core Concept:** A stochastic dynamic programming simulator that models the discrete delivery outcome (dot, 1, 2, 3, 4, 6, wicket, extra) conditioned on:
  $$S_t = (\text{balls remaining}, \text{wickets in hand}, \text{innings})$$
  The Expected Run Differential (ERD) evaluates each delivery:
  $$\Delta_{\text{ERD}} = R_{\text{actual}} - \mathbb{E}[R \mid S_t]$$
  Elite T20 players contribute an additional **$+8$ to $+10$ runs per match** above a theoretical average player facing the identical match contexts.
- **Relevance to SupeRR Intelligence:** Provides the rigorous mathematical foundation for replacing raw strike rate with **Runs Above Expected (RAE)**.

---

## 3. Research Direction B: Match-State Pressure & Leverage Index

### 3.1 Leverage Index (LI) in Limited-Overs Cricket
- **Foundational Theory:** Keith Woolner (2002) and Tom Tango, Mitchel Lichtman, Andrew Dolphin (*The Book: Playing the Percentages in Baseball*, 2006).
- **Cricket Formulation:** Adapted for T20 cricket by White Ball Analytics and Cricmetric (2018–2023).
- **Mathematical Definition:**
  Let $W(S_t)$ be the Win Probability of the batting team at match state $S_t = (b, w, r, T)$, where $b$ is balls remaining, $w$ is wickets in hand, $r$ is current score, and $T$ is target.
  The delivery outcome random variable $X \in \{\text{dot}, 1, 2, 3, 4, 6, \text{wicket}\}$ transitions state $S_t \to S_{t+1}(X)$.
  The **Leverage Index** of state $S_t$ is defined as the standard deviation of win probability swings across all possible delivery outcomes, normalized by the mean game leverage:
  $$\text{LI}(S_t) = \frac{\sqrt{\sum_{x} P(X=x \mid S_t) \cdot \left[ W(S_{t+1}(x)) - \bar{W}(S_t) \right]^2}}{\mathbb{E}[\sigma_W]}$$
  Where $\mathbb{E}[\sigma_W]$ is the average swing across all match states in the historical database, setting the baseline average state to $\text{LI} = 1.0$.

- **Pressure Categorization via Leverage Index:**
  - **Low Leverage ($\text{LI} < 0.85$):** Blowout chases (e.g. needing 15 off 36 balls with 8 wickets in hand, or needing 90 off 18 balls with 2 wickets in hand). Unconstrained "garbage time".
  - **Medium Leverage ($0.85 \le \text{LI} < 1.75$):** Standard competitive match play.
  - **High Leverage ($1.75 \le \text{LI} < 3.0$):** High-tension situations where each ball swings win odds by $5\text{--}12\%$.
  - **Extreme Leverage ($\text{LI} \ge 3.0$):** Critical death overs, tight chases (needing 12 off the final over), and Super Overs.

- **Fundamental Breakthrough for SupeRR Intelligence:**
  Unlike batting-order collapse proxies, **Leverage Index applies symmetrically to BOTH the batter and the bowler on the very same delivery**.
  When $\text{LI} = 3.2$, the batter is under extreme pressure to score, and the bowler is under extreme pressure to prevent boundaries. There is zero position bias.

### 3.2 Win Probability Added (WPA)
- **Mathematical Definition:**
  $$\text{WPA}_{\text{batter}} = W(S_{t+1}) - W(S_t)$$
  $$\text{WPA}_{\text{bowler}} = -\text{WPA}_{\text{batter}} = W(S_t) - W(S_{t+1})$$
- **Properties:**
  1. **Zero-Sum per Delivery:** The batter's gain is the bowler's loss. Double-counting is mathematically impossible.
  2. **Context-Sensitive:** Hitting a six when win probability is 50% yields $+25\%$ WPA; hitting a six when win probability is already 99% yields $+0.8\%$ WPA.
  3. **Zero Target Leakage:** $W(S_t)$ is computed strictly before the delivery outcome occurs.

### 3.3 WASP: Winning and Score Predictor
- **Authors:** Dr. Scott Brooker and Dr. Seamus Hogan (University of Canterbury, 2012/2015).
- **Methodology:** Dynamic programming backward induction applied to uninterrupted historical matches.
  - First Innings: $V(b, w)$ = expected total score given $b$ balls remaining and $w$ wickets in hand.
  - Second Innings: $P(b, w, r)$ = probability of chasing target $T$ given $b$ balls, $w$ wickets, and $r$ runs scored.
  - Backward recursion:
    $$P(b, w, r) = \sum_{k} p_k(b, w) \cdot P(b-1, w - \mathbb{I}_{\text{wkt}}, r + \text{runs}_k)$$

---

## 4. Research Direction C: Statistical Player Evaluation & Empirical Bayes Shrinkage

### 4.1 Shrinkage of Differences ($\Delta_i$) vs Isolated Rates
- **Foundational Theory:** Bradley Efron & Carl Morris (1975, 1977, *Stein's Paradox in Statistics*, *Journal of the American Statistical Association*).
- **Core Flaw in Existing SupeRR Implementation:**
  The existing code shrinks `crisis_sr` toward $\mu_{\text{pop}}$ and leaves `norm_sr` unshrunk, then takes their ratio:
  $$M_i = \frac{\text{Crisis SR}_i}{\text{Normal SR}_i}$$
  Because the ratio of two random variables has high variance (approximating a Cauchy-like heavy-tailed distribution when the denominator is noisy), small-sample ratios explode.
- **Academic Solution: Empirical Bayes Shrinkage on the Performance Differential:**
  Define each player's **Clutch Differential**:
  $$\Delta_i = Y_{i, \text{pressure}} - Y_{i, \text{normal}}$$
  Under the hierarchical Normal-Normal model:
  $$\Delta_i \mid \delta_i, \sigma_i^2 \sim N(\delta_i, \sigma_i^2)$$
  $$\delta_i \sim N(\mu_\Delta, \tau^2_\Delta)$$
  Where:
  - $\sigma_i^2 = \text{Var}(Y_{i, \text{pressure}}) / n_{i, \text{pressure}} + \text{Var}(Y_{i, \text{normal}}) / n_{i, \text{normal}}$ is the player's specific within-sample sampling variance.
  - $\tau^2_\Delta = \max\left(0, \frac{1}{J-1} \sum_{j=1}^J (\hat{\Delta}_j - \bar{\Delta})^2 - \frac{1}{J} \sum_{j=1}^J \sigma_j^2\right)$ is the between-player variance of true clutch ability.
  - The posterior mean estimate is:
    $$\hat{\delta}_i^{\text{EB}} = B_i \mu_\Delta + (1 - B_i) \hat{\Delta}_i, \quad B_i = \frac{\sigma_i^2}{\sigma_i^2 + \tau^2_\Delta}$$
- **Statistical Property:**
  If a player has only 40 balls in pressure, $\sigma_i^2$ is large, $B_i \to 1$, and their estimated clutch differential is shrunk heavily toward the population mean $\mu_\Delta \approx 0$.
  If a player has 500 balls in pressure, $\sigma_i^2 \to 0$, $B_i \to 0$, and their observed clutch superiority is preserved.
  **This eliminates the need for arbitrary hard exclusions of tailenders or provisional players.**

---

## 5. Research Direction D: Reliability, Consistency & Uncertainty Quantification

### 5.1 Split-Half Reliability & Cronbach's Alpha in Sports
- In psychometrics and quantitative sports analytics, a metric is defined as reliable only if performance in partition A correlates with partition B for the same individuals:
  $$r_{\text{split-half}} = \text{Corr}(Y_{i, \text{odd matches}}, Y_{i, \text{even matches}})$$
  Applying the Spearman-Brown prophecy formula:
  $$\rho = \frac{2 r_{\text{split-half}}}{1 + r_{\text{split-half}}}$$
- If $r_{\text{split-half}} < 0.30$, the metric is dominated by noise and cannot be used for player ranking.

### 5.2 Bootstrap Credible Intervals & Rank Uncertainty
- Ranking players strictly by point estimates ($\hat{\theta}_1 > \hat{\theta}_2$) creates an illusion of certainty.
- By resampling deliveries clustered at the match level ($B = 1,000$ cluster bootstrap iterations), we compute:
  1. $95\%$ Confidence / Credible Intervals for each player's PRI.
  2. **Top-10 Selection Probability:** The percentage of bootstrap resamples in which the player finishes in the Top 10.
  3. Players with genuine clutch reliability maintain $> 80\%$ Top-10 selection frequency; small-sample flukes drop below $20\%$.

---

## 6. Research Direction E: IPL and T20I Comparability

### 6.1 The Competition Dilemma
The dataset merges **IPL franchise matches** with **Men's T20 International matches** across full members and associate nations:
- IPL attacks feature 5 international-quality bowlers in every team.
- Certain T20I matches feature top-ranked teams playing lower-tier associate nations where scoring baselines are inflated or bowling resistance is weak.
- A raw strike rate of 160 in an IPL death over against Jasprit Bumrah is qualitatively different from 160 in a bilateral match against a developing associate nation.

### 6.2 Evaluated Methodologies:
1. **Separate Models:** Stratifies IPL and T20I into separate pipelines.
   - *Limitation:* Drastically reduces sample sizes for international players with limited IPL exposure.
2. **Competition Z-Score Standardization:** Normalizes performance relative to competition-specific mean and standard deviation:
   $$Z_{ijk} = \frac{X_{ijk} - \mu_{\text{comp}}}{\sigma_{\text{comp}}}$$
3. **Opposition-Quality Bayesian Adjustment (Hierarchical Partial Pooling):**
   Models delivery expectation as a function of the opposition bowler's/batter's career rating:
   $$\mathbb{E}[R_{ij}] = \alpha + \beta_{\text{batter}, i} - \gamma_{\text{bowler}, j} + \delta_{\text{phase}}$$
   Where $\beta_i \sim N(0, \sigma^2_\beta)$ and $\gamma_j \sim N(0, \sigma^2_\gamma)$.

---

## 7. Comparative Academic Literature Matrix

| Paper / Framework | Authors & Year | Venue / Citation | Primary Metric | Inputs Required | Suitability for RR Dataset |
|---|---|---|---|---|:---:|
| **CAMP** | Ayub et al. (2021) | *J. Sports Analytics*, arXiv:2104.05387 | Context-Aware Vector Score | Ball-by-ball, phase, wickets, target | **Directly Implementable** |
| **T20 Simulator & ERD** | Davis, Perera, Swartz (2015) | *ANZJS*, Vol. 57, No. 1, pp. 55–71 | Expected Run Differential (ERD) | Delivery logs, phase, wickets remaining | **Directly Implementable** |
| **WASP** | Brooker & Hogan (2015) | Univ. of Canterbury Research | Dynamic Win Probability / Par Score | Target, balls left, wickets in hand | **Conditionally Implementable** (requires approximate target) |
| **Leverage Index & WPA** | Tango, Lichtman, Dolphin (2006); adapted White Ball Analytics (2020) | *The Book: Playing Percentages*; Cricmetric | Win Probability Added (WPA) & Leverage Index | Win probability model, state transitions | **Directly Implementable** (via empirical match-state grid) |
| **Empirical Bayes Shrinkage** | Efron & Morris (1975, 1977) | *JASA*, Vol. 70, pp. 311–319 | Posterior Mean $\hat{\delta}^{\text{EB}}$ | Observed rates, within-player variance | **Directly Implementable** |
| **Hierarchical Sports Models** | Gelman et al. (2013) | *Bayesian Data Analysis*, 3rd Ed., CRC Press | Random Effects Partial Pooling | Clustered player-match deliveries | **Directly Implementable** |

---

## 8. Summary of Research Recommendations

1. **Abandon Wicket-Count Depletion as Primary Pressure:** Replace it with an **Empirical Leverage Index (LI)** based on pre-delivery match tension (balls remaining, wickets in hand, and approximate required scoring rate).
2. **Apply Symmetric Pressure to Both Disciplines:** High leverage must indicate high pressure for both batter and bowler on the same ball.
3. **Shrink the Differential ($\Delta$), Not Just the Raw Rate:** Apply conjugate Empirical Bayes shrinkage to $\Delta_i = \text{Pressure Rate}_i - \text{Normal Rate}_i$.
4. **Report Rank Confidence Intervals:** Present Top 10 rankings alongside bootstrap credible intervals and selection frequencies to reflect statistical honesty.
