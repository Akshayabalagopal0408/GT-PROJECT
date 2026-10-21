# Empirical Tax Benchmark Dataset Documentation

This documentation details the empirical dataset used to calibrate our Evolutionary Game-Theoretic Simulation Model (**The Gold Standard**).

---

## 1. Data Sources & Download URLs

| Dataset Name | Governing Body / Publisher | Official Download URL | Data Points Extracted |
| :--- | :--- | :--- | :--- |
| **OECD Tax Administration 2021 / 2023 (ISORA Series)** | OECD, CIAT, IOTA, and IMF | [OECD Tax Administration Series](https://www.oecd.org/tax/forum-on-tax-administration/database/) / [ISORA Data Portal](https://isoradata.org/) | Cost of collection ratio ($C$), statutory audit coverage ($p_I$), and tax-to-GDP / average rates ($\tau$) across OECD member states. |
| **World Bank Enterprise Surveys (Tax Administration Module)** | The World Bank Group | [World Bank Enterprise Survey Microdata](https://microdata.worldbank.org/index.php/catalog/enterprise_surveys) | Average percentage of annual sales declared for tax purposes ($\beta$), informal competition, and inspection frequency. |
| **IRS Tax Gap & National Research Program (NRP)** | United States Internal Revenue Service (IRS) | [IRS Tax Gap Estimates](https://www.irs.gov/statistics/irs-the-tax-gap) | Estimated true voluntary compliance rate ($85\%$), audit detection rate ($\alpha \approx 65\%$), and penalty structure. |
| **Income Tax Department Administration Statistics** | Central Board of Direct Taxes (CBDT), Ministry of Finance, India | [Incometaxindia.gov.in Statistics](https://incometaxindia.gov.in/) | Scrutiny assessment rates ($0.3\% - 0.5\%$), statutory penalty rates under Section 270A, and cost of collection ($0.57\%$). |

---

## 2. Parameter Mapping Methodology

To calibrate our game-theoretic and agent-based model to real economies, empirical variables are mapped to the model's parameters:

| Model Parameter | Economic Meaning | Empirical Proxy from Data | Typical Real-World Range |
| :---: | :--- | :--- | :---: |
| $\tau$ | Statutory / Effective Tax Rate | National statutory corporate / personal effective tax rate | $25\% - 34\%$ |
| $\beta$ | Declared Fraction of Income | Average percentage of revenue declared to authorities (World Bank Enterprise Survey question: *"percent of sales declared for taxes"*) | $69\% - 90\%$ |
| $(1 - \beta)$ | Evaded Fraction of Income | $1 - \beta$ (The estimated tax evasion / informal revenue share) | $10\% - 31\%$ |
| $p_I$ | Audit Coverage Rate | Total completed field/scrutiny audits divided by active taxpayer base (OECD ISORA Table 4.1) | $0.5\% - 2.8\%$ |
| $C$ | Cost of Collection Ratio | Total operating expenditures of the tax administration divided by total revenue collected (OECD ISORA) | $0.5\% - 1.4\%$ |
| $\phi$ | Penalty Multiplier on Evaded Tax | Statutory non-compliance fine penalty rate (e.g., 50% penalty = $0.50$, 100% penalty = $1.00$) | $0.75 - 1.20$ |
| $\alpha$ | Audit Detection Efficacy | Percentage of audits that successfully identify and recover unpaid liabilities (Audit hit/recovery rate) | $50\% - 75\%$ |

---

## 3. Country Case Studies Summary

1. **United States (USA):** High-deterrence, automated information-matching regime. High voluntary compliance ($85\%$), low collection cost ($0.5\%$).
2. **Germany (DEU):** Comprehensive European administrative system. Very high reported sales fraction ($88\%$), moderate audit cost ($1.3\%$).
3. **Italy (ITA):** Extensively analyzed in Italian public finance literature (including Fedeli & Costarelli, 2026). Prominent shadow economy ($23\%$ evasion gap) and active audit recovery programs.
4. **United Kingdom (GBR):** Digital Making Tax Digital framework. High declared share ($90\%$), low collection costs ($0.7\%$).
5. **India (IND):** Rapidly expanding direct tax base with a large informal cash sector. Declared fraction $\approx 72\%$, growing faceless scrutiny assessment framework.
6. **Brazil (BRA):** High tax complexity and substantial informal economic sector ($\beta = 69\%$).
7. **OECD 38 Average:** Baseline consolidated profile representing developed economies.
8. **Emerging Nations Average:** Baseline consolidated profile representing developing economies with high informality.

---

## 4. How to Use in Code
The calibrated profiles are loaded via `model/empirical_loader.py` and evaluated across all 5 audit policies using `experiments/empirical_country_comparison.py`.
