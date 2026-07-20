(Chap_MacroCalib)=
# Calibration of Macroeconomic Parameters

## Economic Assumptions

As the default rate of labor augmenting technological change, $g_y$, we use the average annual growth rate in GDP per capita in Indonesia over the **2000–2019** window (World Bank series `NY.GDP.PCAP.KD`, GDP per capita in constant 2015 US$). The 2000 start year is a structural-break boundary: it excludes the 1997-98 Asian Financial Crisis and the post-Suharto Reformasi transition, so the mean reflects Indonesia's modern macroeconomic regime rather than the one-off crisis contraction. The 2019 end year is pre-pandemic: it keeps the 2020 COVID contraction and its mechanical rebound out of a *long-run* productivity target. The window bounds are the module-level constants `GDP_GROWTH_START_YEAR` and `GDP_GROWTH_END_YEAR` in `ogidn/macro_params.py`. Over this window the packaged value is `g_y_annual` ≈ 0.040 (about 4.0% per year), up from the 3.71% implied by the earlier 2000–2024 window that folded in the COVID crash.

### Calibration vintage and refresh policy

`g_y_annual` is the **only** macro parameter refreshed from a live API when the calibration is run with `update_from_api=True`; every other macro parameter is a documented, point-in-time Indonesian value held directly in `ogidn/ogidn_default_parameters.json`. Previously the connected run also pulled the debt ratios (World Bank QPSD), `gamma` (ILOSTAT), and `alpha_T`/`alpha_G` (IMF GFS) on every call, overwriting the documented baseline with whatever those series happened to return — so the offline default and the connected run drifted apart. Freezing them keeps a live update from clobbering a value we source deliberately, and lets the offline default reproduce the connected run (see [`ogidn/update_baseline.py`](https://github.com/EAPD-DRB/OG-IDN/blob/main/ogidn/update_baseline.py)). Demographics and the earnings profile `e` remain live (UN data) and are baked in by `update_baseline`.

| Parameter | Packaged value | Source | Live-refreshed? |
|---|---|---|---|
| `g_y_annual` | ≈ 0.040 | World Bank WDI (GDP per capita, constant 2015 US$), 2000–2019 mean | **Yes** |
| `gamma` | 0.41859 | ILOSTAT capital share of income | No (frozen) |
| `initial_debt_ratio` | 0.402 | IMF WEO general-government gross debt, 2024 | No (frozen) |
| `initial_foreign_debt_ratio` | 0.262 | World Bank QPSD external creditors, 2024Q4 | No (frozen) |
| `zeta_D` | 0.262 | = `initial_foreign_debt_ratio` | No (frozen) |
| `alpha_T` | 0.00776 | IMF Government Finance Statistics, 2023 | No (frozen) |
| `alpha_G` | 0.14 | IMF WEO general-government expenditure basis, 2023–24 | No (frozen) |
| `zeta_K` | 0.42 | Normalized Chinn-Ito index (2023), validated against the BI IIP | No (frozen) |
| `world_int_rate_annual` | 0.05 | Global risk-free rate + Indonesian sovereign premium | No (frozen) |
| `debt_ratio_ss` | 0.40 | IMF Article IV medium-term debt anchor | No (frozen) |

To refresh `g_y_annual` (and the demographic overlay) against newer source data, run `uv run python -m ogidn.update_baseline` and commit the updated JSON.

## Open Economy Parameters

### Foreign holding of government debt in the initial period

The path of foreign holding of domestic debt is endogenous, but the initial period stock of debt held by foreign investors is exogenous. We set this parameter, `initial_foreign_debt_ratio`, to 0.262 based on the World Bank Quarterly Public Sector Debt (QPSD) series for gross public sector debt held by domestic and external creditors in Indonesia in 2024Q4.

### Foreign purchases of newly issued debt

We set $\zeta_D = 0.262$. In the current baseline calibration, this is aligned with the same World Bank QPSD-based foreign debt share used for `initial_foreign_debt_ratio`.

### Foreign holdings of excess capital

We set $\zeta_K = 0.42$. This parameter governs the share of the gap between domestically-supplied capital and the capital demanded at the world interest rate that foreign investors fill, so it is effectively the degree of openness of the capital account. It is harder to pin down from the data than the debt parameters, because purchases of "excess" capital demand are not directly measured. We anchor the value to the normalized Chinn-Ito capital-account openness index for Indonesia, which sits at **0.418** in the latest (2023) vintage and has been flat at that level since 2011, after Bank Indonesia introduced capital-flow-management measures around 2010–11 ([Chinn-Ito index](https://web.pdx.edu/~ito/Chinn-Ito_website.htm)). Indonesia is therefore a *partially* open economy, not the near-fully-open one the earlier placeholder of 0.9 implied.

The decisive discipline on the value is empirical: it is chosen so the model's steady-state foreign-owned share of the capital stock lands near Indonesia's actual position. Bank Indonesia's International Investment Position and UNCTAD's inward FDI stock put foreign-owned capital at roughly **20% of the stock** (FDI stock ≈ US$286bn against GDP ≈ US$1.37tn in 2023), far below the ~44% the placeholder of 0.9 produced in the single-industry steady state. At $\zeta_K = 0.42$ — together with the lower steady-state debt anchor and the higher world rate below, which both free up domestic capital — the model's foreign-owned capital share falls back into that empirical range. Note that $\zeta_K$ is a marginal-flow parameter (the fill share of *excess* demand) rather than a literal legal-openness index; the Chinn-Ito value is the anchor and the IIP share is the target the calibration is validated against.

### World interest rate

The small-open-economy block prices foreign capital and foreign debt at an exogenous world interest rate, `world_int_rate_annual`. We set it to **5%** — a global risk-free rate of about 4% plus an Indonesian country-risk premium of roughly 100 basis points. Indonesia is an investment-grade sovereign (Moody's Baa2, S&P and Fitch BBB), and its EMBI/CDS spreads over U.S. Treasuries have run near 80–150 bps in 2024–25, so ~100 bps is a representative premium. The previous 4% placeholder omitted this premium, understating the supply price of foreign capital and so overstating foreign ownership of the capital stock.

## Government Debt, Spending and Transfers

### Government Debt

The path of government debt is endogenous. But the initial value is exogenous. To avoid converting between model units and dollars, we calibrate the initial debt to GDP ratio, rather than the dollar value of the debt. This is the model parameter $\alpha_D$. We set `initial_debt_ratio` to **0.402**, the IMF World Economic Outlook general-government gross-debt-to-GDP figure for Indonesia in 2024 (the Kemenkeu/DJPPR central-government series runs about 1 pp lower and rounds to the same ~40%).

We also set the long-run (steady-state) debt-to-GDP target, `debt_ratio_ss`, to **0.40**, replacing the 0.50 placeholder. This anchors to the IMF 2025 Article IV consultation, which projects "stable public debt of just above 40 percent of GDP over the medium term," and to Indonesia's realized stance — central-government debt has sat in a 38–40% band (39.9% as of mid-2025, Kemenkeu). We deliberately do **not** use the 60% ceiling from Law No. 17/2003 on State Finances: that is a never-breach statutory limit (alongside the 3%-of-GDP deficit cap), not a target the authorities steer toward, and no official projection approaches it. Setting the steady-state target at 0.40 — essentially the current stance — keeps the fiscal closure consistent with Indonesia's debt position at both ends of the transition, and frees household saving that a US-style placeholder would have absorbed into government debt, easing the crowding-out that had inflated the foreign-owned capital share.

#### Interest rates on government debt

We assume a wedge between the real rate of return on private capital and the real interest rate on government debt, modeled as a scale and level shift.  The real interest rate on government debt, $r_{gov,t}$, relates to the real rate of return on private capital, $r_t$, by

```{math}
:label: eqn:r_gov
    r_{gov,t} = (1-\tau_{d,t}) r_t + \mu_d
```

where $(1-\tau_d)$ is the pass-through coefficient and $\mu_d$ is the level shift.  For Indonesia we use $1-\tau_d = 0.24485$ (so $\tau_d = 0.75515$) and $\mu_d = 0.03377$.

These values come from {cite}`LMW2023`, who estimate the long-run pass-through of sovereign yields to corporate yields across 46 emerging economies using corporate yields from IHS Markit and sovereign yields from Bloomberg (predominantly U.S.-dollar secondary-market yields).  They are therefore a cross-country emerging-market relationship rather than Indonesia-specific bond data.  Their preferred specification (Table 8, Column 2) fits a quadratic of the corporate yield on the sovereign yield of the same country:

```{math}
:label: eqn:lmw_quadratic
    y_{corp} = 8.199 - 2.975\, y_{sov} + 0.478\, y_{sov}^2
```

with both yields in percentage points.  The quadratic captures the empirical fact that pass-through rises with the level of sovereign risk, consistent with the credit-risk and liquidity-premium channels the paper identifies.  The paper is freely available as an IMF Working Paper, [Li, Magud, and Werner (2021)](https://www.imf.org/en/Publications/WP/Issues/2021/06/04/The-Long-Run-Impact-of-Sovereign-Yields-on-Corporate-Yields-in-Emerging-Markets-50224), and was later published in the *Journal of International Money and Finance* {cite}`LMW2023`.

OG-Core models the wedge in the opposite direction — it takes $r_t$ as an input and produces $r_{gov,t}$ — so we invert the LMW relationship.  We evaluate their quadratic on a grid of sovereign yields from 2% to 12% (approximately the emerging-market range in the LMW sample), compute the implied corporate yields, and then regress sovereign yields linearly on those corporate yields.  Calling the resulting slope $b$ and intercept $a$ (both in percentage points), we identify $1-\tau_d = b$ and $\mu_d = a/100$.

OG-Core's operational formula also carries a debt-elastic term (see the debt-elastic premium below):

```{math}
:label: eqn:r_gov_op
    r_{gov,t} = \max\!\big(\texttt{r\_gov\_scale}\cdot r_t - \texttt{r\_gov\_shift} + \texttt{r\_gov\_DY}\cdot\tfrac{D_t}{Y_t} + \texttt{r\_gov\_DY2}\cdot\big(\tfrac{D_t}{Y_t}\big)^2,\; 0\big)
```

The level wedge stores `r_gov_scale = 1-τ_d = 0.24485` and a base `r_gov_shift = -μ_d = -0.03377` (the negative sign reflects the subtraction in the OG-Core rule, not a negative level shift in the theoretical equation). Enabling the debt-elastic premium recenters the stored `r_gov_shift` to **-0.04017** (see below).

Because the inputs to this inversion are deterministic and contain no Indonesia-specific data, the resulting values do not change across calibration runs.  The packaged values in `ogidn/ogidn_default_parameters.json` and `ogidn/ogidn_multisector_default_parameters.json` are the authoritative source.  The snippet below reproduces them for transparency:

```python
import numpy as np
import statsmodels.api as sm

# LMW (2023) Table 8, Column 2: corp = 8.199 - 2.975 sov + 0.478 sov^2  (pct pts)
sov_y = np.arange(20, 120) / 10
corp_yhat = 8.199 - (2.975 * sov_y) + (0.478 * sov_y**2)

# Invert: regress sov on corp → linear pass-through
X = sm.add_constant(corp_yhat)
res = sm.OLS(sov_y, X).fit()

r_gov_shift = -res.params[0] / 100  # -0.03377  (= -μ_d in the theoretical equation)
r_gov_scale = res.params[1]         #  0.24485  (= 1-τ_d in the theoretical equation)
```

If the LMW estimates are superseded, re-run the inversion above with the new coefficients and update the JSON values.

For background on how this calibration was first derived, the slope/intercept mapping worked out, and the OG-Core specification refined, see the OG-ZAF discussion in issue [#22](https://github.com/EAPD-DRB/OG-ZAF/issues/22) and PRs [#24](https://github.com/EAPD-DRB/OG-ZAF/pull/24) (initial implementation) and [#30](https://github.com/EAPD-DRB/OG-ZAF/pull/30) (conversion of `r_gov` parameters to lists), together with OG-Core issue [#841](https://github.com/PSLmodels/OG-Core/issues/841) and PR [#844](https://github.com/PSLmodels/OG-Core/pull/844).

#### Debt-elastic sovereign premium

The `r_gov_DY` and `r_gov_DY2` terms let the sovereign rate rise with the debt ratio — the crowding-out-via-risk channel that OG-Core and the sister country models leave off by default (otherwise a debt-financed reform raises debt with no feedback to borrowing cost). It is the [Schmitt-Grohé and Uribe (2003)](https://www.nber.org/system/files/working_papers/w9270/w9270.pdf) debt-elastic premium in convex (quadratic) form, in the spirit of the fiscal-limits literature (Bi 2012; Ghosh et al. 2013). OG-IDN uses a *centered* form, $\texttt{r\_gov\_DY2}\,(D_t/Y_t - 0.40)^2$ — flat at the 0.40 steady-state debt target and steepening only as debt rises away from it — matching Indonesia's stable spreads around its current ~40% debt level and stress only well above it.

We set $\texttt{r\_gov\_DY2} = 0.04$. Expanding the centered quadratic $0.04\,(D/Y - 0.40)^2$ into OG-Core's $\texttt{r\_gov\_DY}\cdot(D/Y) + \texttt{r\_gov\_DY2}\cdot(D/Y)^2$ form gives $\texttt{r\_gov\_DY} = -2\cdot0.04\cdot0.40 = -0.032$, and folds the constant $0.04\cdot0.40^2 = 0.0064$ into the level shift, recentering `r_gov_shift` from $-0.03377$ to $-0.03377 - 0.0064 = -0.04017$. By construction the premium is zero at the 0.40 target, so it holds the steady state fixed; away from the target it adds about **36 bp at $D/Y = 0.70$** and **144 bp at $D/Y = 1.0$**, within the emerging-market spread-to-debt range. Centering is what makes the premium usable along the transition: a premium that bit at the target (vertex at zero debt) would compound any debt overshoot into a runaway debt-service feedback. It is enabled by default; a more conservative $\texttt{r\_gov\_DY2} = 0.02$ is a reasonable alternative.

### Aggregate transfers

Aggregate (non-Social Security) transfers to households are set as a share of GDP with the parameter $\alpha_T$. We exclude Social Security from transfers since it is modeled specifically. In the current baseline, `alpha_T = 0.00776`, computed from IMF Government Finance Statistics Statement of Operations data as total social benefits less social security benefits, expressed as a share of GDP. For the default target year of 2024, the latest complete IMF year available is 2023, so the baseline uses that year.

### Government expenditures

Government spending on goods and services is set as a share of GDP with the parameter $\alpha_G$. Conceptually it is government spending net of transfers, net interest, and social security:
    <center>Government Spending = Total Outlays - Transfers - Net Interest on Debt - Social Security</center>

We set `alpha_G = 0.14`. The value is built on the **IMF World Economic Outlook general-government basis** — the same basis used for revenue and for the debt anchors — so that the government's books are internally consistent. Indonesia's general-government expenditure is about 16.7% of GDP (WEO, 2023–24); netting out interest (~2%) and the transfers captured by $\alpha_T$ (0.78%) leaves roughly 14% for goods and services.

An earlier value of 11.13% came from a narrower IMF Government Finance Statistics expense series (total expense ≈ 14.0% of GDP), which understates general-government spending relative to the WEO revenue and debt figures the rest of the calibration uses. That inconsistency produced a spurious primary surplus: with revenue near 15% and spending near 12%, the government ran a 2–4%-of-GDP surplus every period, and because the budget-closure rule does not engage until $t_{G1}$ (period 20), the baseline debt-to-GDP ratio drifted all the way from 0.40 down through zero to about −0.23 before the closure pulled it back — a government that is implausibly a net creditor mid-transition. Putting $\alpha_G$ on the WEO basis matches Indonesia's actual fiscal stance (a small primary surplus — 2023 was Indonesia's first in over a decade — and an overall deficit near 2% of GDP), so the baseline debt path now stays near Indonesia's ~40% level (it eases to about 0.31 by $t_{G1}$ and returns to the 0.40 steady state) instead of going negative. Because steady-state $G$ is set by the closure rule rather than by $\alpha_G$, this change leaves the steady state unchanged; it only corrects the transition.

## Steady-state validation

Most of the parameters above are only weakly identified from the data on their own, so the real test of the calibration is whether the *steady state they jointly produce* resembles the Indonesian economy. The table below compares the packaged baseline steady state (single-industry, offline solve) against recent Indonesian data. The recalibration of the open-economy block and the debt anchor moves every ratio toward its empirical counterpart; the "prior baseline" column is the steady state under the earlier placeholders ($\zeta_K = 0.9$, `world_int_rate_annual` $= 0.04$, `debt_ratio_ss` $= 0.50$).

| Steady-state ratio | Prior baseline | **Recalibrated** | Indonesia (data) | Source |
|---|---|---|---|---|
| Foreign-owned capital, $K_f/K$ | 0.44 | **0.17** | ~0.20 | BI IIP / UNCTAD FDI stock (US$286bn) over GDP, 2023 |
| Real return on capital, $r$ | 0.043 | **0.063** | 0.05–0.08 | World Bank real interest rate; real MPK |
| Capital-output ratio, $K/Y$ | 4.44 | **3.64** | ~3.0–3.5 | flow-consistent $(I/Y)/(g+\delta)$ |
| Private consumption, $C/Y$ | 0.49 | **0.53** | 0.53–0.58 | World Bank `NE.CON.PRVT.ZS`, 2023–24 |
| Investment, $I/Y$ | 0.38 | **0.33** | 0.29–0.32 | World Bank `NE.GDI.FTOT.ZS`, 2023–24 |
| Government debt, $D/Y$ | 0.50 | **0.40** | ~0.40 | IMF WEO general-government gross debt, 2024 |
| Tax revenue, $REV/Y$ | 0.14 | **0.15** | 0.145–0.15 | IMF general-government revenue, 2023–24 |

The largest correction is the foreign-owned capital share, which falls from an implausible 44% to about 17%, in line with the ~20% implied by Bank Indonesia's International Investment Position. The domestic real return rises from 4.3% — pinned near the old 4% world rate — to a more realistic 6.3%, the capital-output ratio falls into the flow-consistent range, and consumption and investment shares move into their observed bands. The negative-domestic-capital ($K_d < 0$) condition that bound under the placeholder calibration no longer occurs. The packaged steady state solves offline in under a minute, and the full example (baseline plus a corporate-income-tax-cut reform, steady states and transition paths) runs end to end with transition-path residuals well inside tolerance.
