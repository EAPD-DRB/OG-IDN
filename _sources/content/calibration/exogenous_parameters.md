---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: '1.4.1'
kernelspec:
  display_name: Python 3
  language: python
  name: ogidn-dev
---

(Chap_Exog)=
# Exogenous Parameters


  The JSON file [`ogidn_default_parameters.json`](https://github.com/EAPD-DRB/OG-IDN/blob/master/ogidn/ogidn_default_parameters.json) provides values for all the model parameters used as defaults for `OG-IDN`. Below, we provide a table highlighting some of the parameters describing the scale of the model (number of periods, aged, productivity types) and some parameters of the solution method (dampening parameter for TPI). The table below provides a list of the exogenous parameters and their baseline calibration values.

  <!-- +++
  ```{code-cell} ogidn-dev
  :tags: [hide-cell]
  from myst_nb import glue
  import ogcore.parameter_tables as pt
  from ogcore import Specifications
  p = Specifications()
  table = pt.param_table(p, table_format=None, path=None)
  glue("param_table", table, display=False)
  ```
  -->

  ```{list-table} **List of exogenous parameters and baseline calibration values.**
  :header-rows: 1
  :name: TabExogVars
  * - **Symbol**
    - **Description**
    - **Value**
  * - $S$
    - Maximum periods in economically active household life
    - 80
  * - $E$
    - Number of periods of youth economically outside the model
    - $\text{round} \frac{S}{4}$=20
  * - $T_1$
    - Number of periods to steady state for initial time path guesses
    - 160
  * - $T_2$
    - Maximum number of periods to steady state for nonsteady-state equilibrium
    - 160
  * - $\nu$
    - Dampening parameter for TPI
    - 0.4
  ```
