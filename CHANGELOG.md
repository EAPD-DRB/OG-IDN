# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Fixed

- Brought all installation instructions in line with the uv workflow the project migrated to in 0.1.0, matching the same fix in OG-PHL and OG-ZAF. The README now documents two supported paths, each as per-platform copy-paste blocks verified end to end: the OG family's universal installer (`install.sh --repo og-idn`, from PSLmodels/OG-Core) and a manual install (install uv, clone, `uv run python examples/run_og_idn.py`). The PyPI install section is dropped: `pip install ogidn` on a Python older than 3.12, including the one that ships with macOS, silently installs an outdated release with an old OG-Core, and even on a supported Python the PyPI route does not pin the tested `ogcore` version. The contributor guide and the UN tutorial no longer instruct readers to build the deleted `ogidn-dev` conda environment (those steps failed outright: `environment.yml` was removed in 0.1.0); both now use `uv sync --extra dev` and `uv run`, the contributor guide's test command matches CI (`pytest -m "not local"`), and stale `master`-branch references now say `main`.

## [0.2.0] - 2026-07-03 12:00:00

### Changed

- Recalibrated the single-industry baseline to Indonesian data and stopped live API pulls from clobbering documented values. `ogidn/macro_params.py` now refreshes only `g_y_annual` from the World Bank (over a pre-pandemic **2000–2019** window, ≈4.0%, replacing the 2000–2024 window that folded in the COVID crash); every other macro parameter is a documented, point-in-time value held in `ogidn/ogidn_default_parameters.json`. Previously the connected run also pulled the debt ratios (World Bank QPSD), `gamma` (ILOSTAT), and `alpha_T`/`alpha_G` (IMF GFS) on every call, so the offline default and the connected run drifted apart.
- Recalibrated the open-economy block: `zeta_K` 0.9 → 0.42 (normalized Chinn-Ito capital-account-openness index for Indonesia, validated against the Bank Indonesia IIP foreign-capital share of ~20%), `world_int_rate_annual` 0.04 → 0.05 (global risk-free rate plus a ~100 bp Indonesian sovereign premium), and `debt_ratio_ss` 0.50 → 0.40 (IMF Article IV medium-term anchor / current stance; the 60% ceiling in Law 17/2003 is a constraint, not a target). `initial_debt_ratio` 0.390 → 0.402 (IMF WEO general-government gross debt, 2024).
- Enabled a **centered debt-elastic sovereign premium** `r_gov_DY2·(D/Y − 0.40)²` (`r_gov_DY2 = 0.04`, `r_gov_DY = -0.032`, `r_gov_shift` recentered -0.03377 → -0.04017). It prices debt overshoots along the transition without moving the steady state.
- Retuned the packaged steady-state initial guesses to the recalibrated equilibrium (`initial_guess_r_SS` 0.04 → 0.0613, `initial_guess_TR_SS` 0.042 → 0.0077, `initial_guess_factor_SS` 71707 → 500000), so the baseline steady state solves quickly instead of crawling OG-Core's guess sweep. (The true model→rupiah factor is ~1e8, above OG-Core's `initial_guess_factor_SS` schema maximum of 500000, so the guess is pinned at that maximum; the `r` and `TR` retunes carry the convergence speed-up.)
- Set `alpha_G` to the IMF WEO general-government expenditure basis (0.111 → 0.14) so government spending is on the same basis as revenue and the debt anchors. The previous value came from a narrower IMF GFS expense series, which understated spending and produced a spurious 2–4%-of-GDP primary surplus that drove the baseline debt-to-GDP ratio negative (to about −0.23) before the budget-closure rule engages at `tG1`. On the WEO basis the baseline debt path stays near Indonesia's ~40% (easing to ~0.31 by `tG1`, returning to the 0.40 steady state); the steady state itself is unchanged because steady-state `G` is set by the closure rule.
- The recalibrated steady state matches Indonesia far better: the foreign-owned capital share falls from ~44% to ~17% (Bank Indonesia IIP ≈ 20%), the private return rises from ~4.3% to ~6.3%, `K/Y` falls from 4.4 to 3.6, and consumption rises to ~53% of GDP.

### Added

- `ogidn/update_baseline.py` regenerates the packaged single-industry JSON from the live calibration (UN demographics, the earnings profile `e`, and World Bank `g_y_annual`), so an offline run reproduces the connected one. Run with `uv run python -m ogidn.update_baseline`.
- Tests for `update_baseline` and for the frozen-parameter / offline-safe behavior of `macro_params`.

## [0.1.0] - 2026-06-03 12:00:00

### Changed

- Migrated the project from conda to uv. Install with `uv sync --extra dev`; `pyproject.toml` is the single source of truth for dependencies and `uv.lock` pins exact versions.
- CI uses `astral-sh/setup-uv`, and ruff replaces black for formatting and linting (`check_format.yml` -> `check_ruff.yml`).
- Updated the README, `AGENTS.md`, and the Makefile to the uv workflow.
- Bumps `__version__` from `0.0.7` to `0.1.0`, syncing with the package version (the prior `__init__.py` was lagging behind `setup.py`).

### Removed

- `setup.py`, `environment.yml`, `pytest.ini`, and `MANIFEST.in` (their settings moved into `pyproject.toml`).

## [0.0.8] - 2025-08-15 21:00:00

### Added

- Updates for Python 3.13 compatibility
- Removes the deprecated `initial_guess_w_SS` parameter from the default parameters file

## [0.0.7] - 2025-04-28 12:00:00

### Added

- Updates `environment.yml` to pin to `marshmallow` version < 4.0.0
- Removes unused imports in example scripts

## [0.0.6] - 2025-03-17 12:30:00

### Added

- Updates `environment.yml` to allow Python 3.12

## [0.0.5] - 2025-03-14 10:30:00

### Added

- Updates `ogidn_multisector_default_parameters.json`
- Adds extended table of exogenous parameter values to documentation

## [0.0.4] - 2025-03-12 18:30:00

### Added

- Updates the baseline calibration in `ogidn_default_parameters.json`
- Adds a baseline calibration for a multisector model in `ogidn_multisector_default_parameters.json`
- Function to read SAM file in `input_output.py`


## [0.0.3] - 2024-08-07 12:00:00

### Added

- Updates the baseline calibration in `ogidn_default_parameters.json` and the example run script `run_og_idn.py`.


## [0.0.0] - 2024-06-20 12:00:00

### Added

- This version is a pre-release alpha. The example run script OG-IDN/examples/run_og_idn.py runs, but the model is not currently calibrated to represent the Indonesian economy and population.

[0.1.0]: https://github.com/EAPD-DRB/OG-IDN/compare/v0.0.8...v0.1.0
[0.0.8]: https://github.com/EAPD-DRB/OG-IDN/compare/v0.0.7...v0.0.8
[0.0.7]: https://github.com/EAPD-DRB/OG-IDN/compare/v0.0.6...v0.0.7
[0.0.6]: https://github.com/EAPD-DRB/OG-IDN/compare/v0.0.5...v0.0.6
[0.0.5]: https://github.com/EAPD-DRB/OG-IDN/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/EAPD-DRB/OG-IDN/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/EAPD-DRB/OG-IDN/compare/v0.0.0...v0.0.3
