(Chap_MacroCalib)=
# Calibration of Macroeconomic Parameters

## Economic Assumptions

As the default rate of labor augmenting technological change, $g_y$, we use a value of 3.8%.  The average annual growth rate in GDP per capita in Indonesia between 2007 and 2023 is 3.8% per year.

## Open Economy Parameters

### Foreign holding of government debt in the initial period

The path of foreign holding of domestic debt is endogenous, but the initial period stock of debt held by foreign investors is exogenous.  We set this parameter, `initial_foreign_debt_ratio` to 0.76, consistent with data from the Bank of Indonesia's Debt Statistics of Indonesia report.

### Foreign purchases of newly issued debt

We set $\zeta_D = 0.9$.  This is the average share of foreign purchases of newly issued government debt found from the World Bank WDI.

### Foreign holdings of excess capital

We set $\zeta_K = 0.9$. Note, this parameter is harder to pin down from the data as foreign purchases on "excess" capital demand is not typically directly measured or reported.  A value of 0.9 implies a high degree of openness to international capital flows.

## Government Debt, Spending and Transfers

### Government Debt

The path of government debt is endogenous.  But the initial value is exogenous.  To avoid converting between model units and dollars, we calibrate the initial debt to GDP ratio, rather than the dollar value of the debt.  This is the model parameter $\alpha_D$.  We compute this from the ratio of publicly held debt outstanding to GDP.  Based on 2023 values, this gives us a ratio of 0.398.

#### Interest rates on government debt

We assume that there is a wedge between the real rate of return on private capital and the real interest rate on government debt.  We model this wedge a scale and level shift.  Specifically, we assume that the real interest rate on government debt, $r_{gov,t}$, is related to the real rate of return on private capital, $r_{t}$, by the following equation:

```{math}
:label: eqn:r_gov
    r_{gov,t} = (1-\tau_{d,t})r_t + \mu_d
```

where $\tau_d$ is the scale parameter and $\mu_d$ is the level shift parameter.  We set the values of these two parameters to 0.24485 and -0.03377, respectively.  These are found by using the estimated relationship between corporate and sovereign yields in {cite}`LMW2023` (Table 8, Column 2) and simulating a series of corporate yields given a series of sovereign yields between 2% and 12%.  We then estimate the scale and level shift parameters that best fit these simulated data using ordinary least squares.

Because the inputs to this OLS are deterministic (a fixed quadratic over a fixed sovereign yield grid) and contain no Indonesia-specific data, the resulting values of `r_gov_scale` and `r_gov_shift` do not change across calibration runs.  Rather than refitting the same regression every time `get_macro_params(update_from_api=True)` is called, the packaged values in `ogidn/ogidn_default_parameters.json` (and `ogidn/ogidn_multisector_default_parameters.json`) are the authoritative source.  The snippet below reproduces them for reviewers and documents the methodology:

```python
import numpy as np
import statsmodels.api as sm

sov_y = np.arange(20, 120) / 10
corp_yhat = 8.199 - (2.975 * sov_y) + (0.478 * sov_y**2)
corp_yhat = sm.add_constant(corp_yhat)
res = sm.OLS(sov_y, corp_yhat).fit()

r_gov_shift = -res.params[0] / 100
r_gov_scale = res.params[1]

print(round(r_gov_shift, 5))  # -0.03377
print(round(r_gov_scale, 5))  # 0.24485
```

If {cite}`LMW2023` is ever superseded by a follow-up study with revised coefficients, re-run the snippet above and update the JSON values (see [OG-IDN](https://github.com/EAPD-DRB/OG-IDN)).

### Aggregate transfers

Aggregate (non-Social Security) transfers to households are set as a share of GDP with the parameter $\alpha_T$. We exclude Social Security from transfers since it is modeled specifically. With this definition, the share of transfers to GDP in 2015 is 1.3% according to [IMF data](https://data.imf.org/?sk=b052f0f0-c166-43b6-84fa-47cccae3e219&hide_uv=1).

### Government expenditures

Government spending on goods and services are also set as a share of GDP with the parameter $\alpha_G$. We define government spending as:
    <center>Government Spending = Total Outlays - Transfers - Net Interest on Debt - Social Security</center>
With this definition, the share of government expenditure to GDP is 13.2% based on [data from the IMF](https://data.imf.org/?sk=b052f0f0-c166-43b6-84fa-47cccae3e219&hide_uv=1).
