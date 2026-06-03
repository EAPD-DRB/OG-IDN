(Chap_MacroCalib)=
# Calibration of Macroeconomic Parameters

## Economic Assumptions

As the default rate of labor augmenting technological change, $g_y$, we use a value of 3.71%. This is the average annual growth rate in GDP per capita in Indonesia over the 2000 to 2024 calibration window using the World Bank series employed in the baseline refresh. The 2000 start year is a structural-break boundary: it excludes the 1997-98 Asian Financial Crisis and the post-Suharto Reformasi transition, so the mean reflects Indonesia's modern macroeconomic regime rather than the one-off crisis contraction. The start year is exposed as the module-level constant `GDP_GROWTH_START_YEAR` in `ogidn/macro_params.py` and is passed directly to the World Bank WDI API as the lower bound of the request window.

### Calibration vintage

The packaged values in `ogidn/ogidn_default_parameters.json` are a snapshot of a refresh run. Each parameter uses the latest value available from its source at the time of that run:

| Parameter | Source | Vintage |
|---|---|---|
| `g_y_annual` | World Bank WDI (GDP per capita, constant 2015 US$) | 2000–2024 mean |
| `gamma` | ILOSTAT capital share | 2024 |
| `initial_debt_ratio` | World Bank QPSD | 2024Q4 |
| `initial_foreign_debt_ratio` | World Bank QPSD | 2024Q4 |
| `zeta_D` | World Bank QPSD (same as above) | 2024Q4 |
| `alpha_T` | IMF Government Finance Statistics | 2023 |
| `alpha_G` | IMF Government Finance Statistics | 2023 |

To refresh against newer source data, run `get_macro_params(update_from_api=True)` and commit the updated JSON.

## Open Economy Parameters

### Foreign holding of government debt in the initial period

The path of foreign holding of domestic debt is endogenous, but the initial period stock of debt held by foreign investors is exogenous. We set this parameter, `initial_foreign_debt_ratio`, to 0.262 based on the World Bank Quarterly Public Sector Debt (QPSD) series for gross public sector debt held by domestic and external creditors in Indonesia in 2024Q4.

### Foreign purchases of newly issued debt

We set $\zeta_D = 0.262$. In the current baseline calibration, this is aligned with the same World Bank QPSD-based foreign debt share used for `initial_foreign_debt_ratio`.

### Foreign holdings of excess capital

We set $\zeta_K = 0.9$. Note, this parameter is harder to pin down from the data as foreign purchases on "excess" capital demand is not typically directly measured or reported.  A value of 0.9 implies a high degree of openness to international capital flows.

## Government Debt, Spending and Transfers

### Government Debt

The path of government debt is endogenous. But the initial value is exogenous. To avoid converting between model units and dollars, we calibrate the initial debt to GDP ratio, rather than the dollar value of the debt. This is the model parameter $\alpha_D$. We compute this from the World Bank QPSD general government debt-to-GDP series for Indonesia. Using 2024Q4 values gives an initial ratio of 0.390.

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

OG-Core's operational formula is $r_{gov,t} = \max\!\big(\texttt{r\_gov\_scale}\cdot r_t - \texttt{r\_gov\_shift},\; 0\big)$, so the JSON stores `r_gov_scale = 1-τ_d = 0.24485` and `r_gov_shift = -μ_d = -0.03377`.  The negative sign on `r_gov_shift` reflects the subtraction in the OG-Core rule, not a negative level shift in the theoretical equation.

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

### Aggregate transfers

Aggregate (non-Social Security) transfers to households are set as a share of GDP with the parameter $\alpha_T$. We exclude Social Security from transfers since it is modeled specifically. In the current baseline, `alpha_T = 0.00776`, computed from IMF Government Finance Statistics Statement of Operations data as total social benefits less social security benefits, expressed as a share of GDP. For the default target year of 2024, the latest complete IMF year available is 2023, so the baseline uses that year.

### Government expenditures

Government spending on goods and services are also set as a share of GDP with the parameter $\alpha_G$. We define government spending as:
    <center>Government Spending = Total Outlays - Transfers - Net Interest on Debt - Social Security</center>
With this definition, the share of government expenditure to GDP is 11.13% in the current baseline, based on IMF Government Finance Statistics Statement of Operations data. As with `alpha_T`, the default target year is 2024, but the baseline uses the latest complete IMF year available at or before that year, which is currently 2023.
