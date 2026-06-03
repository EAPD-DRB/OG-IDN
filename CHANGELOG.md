# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
