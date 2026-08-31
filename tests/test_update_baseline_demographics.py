"""
Tests of update_baseline_demographics.py module.

The tool regenerates only the demographic keys in the packaged JSON.
These tests stub ogcore's demographics and the earnings interpolation so
no network or model solve is involved.
"""

import json

import numpy as np

from ogidn import update_baseline_demographics as ubd


class FakePath:
    def __init__(self, path):
        self._path = path

    def joinpath(self, name):
        return self._path

    def read_text(self):
        return self._path.read_text()


class FakeSpecs:
    E, S, T, J = 20, 80, 320, 7
    start_year = 2025
    lambdas = np.array([[0.25], [0.25], [0.2], [0.1], [0.1], [0.09], [0.01]])

    def update_specifications(self, params):
        type(self).seen = params


def _fake_pop_objs(*args, **kwargs):
    assert np.array_equal(
        kwargs["income_percentiles"], FakeSpecs.lambdas.flatten()
    )
    return {
        "omega": np.full((4, 3, 2), 0.1),
        "omega_SS": np.full((3, 2), 0.2),
        "rho": np.full((4, 3, 2), 0.3),
        "imm_rates": np.full((4, 3, 2), 0.0),
        "g_n_ss": np.float64(0.01),
    }


def _patch_all(monkeypatch, tmp_path, packaged):
    path = tmp_path / "params.json"
    path.write_text(json.dumps(packaged))
    monkeypatch.setattr(ubd, "files", lambda pkg: FakePath(path))
    monkeypatch.setattr(ubd, "Specifications", FakeSpecs)
    monkeypatch.setattr(ubd.demographics, "get_pop_objs", _fake_pop_objs)
    monkeypatch.setattr(
        ubd.income,
        "get_e_interp",
        lambda E, S, J, lambdas, age_wgts: np.full((3, 2), 1.0),
    )
    return path


def test_regenerate_bootstraps_without_demographic_keys(monkeypatch, tmp_path):
    packaged = {
        "zeta_K": [0.42],
        "omega": [[9.0]],  # stale shape: must NOT reach Specifications
        "rho": [[9.0]],
        "e": [[9.0]],
    }
    _patch_all(monkeypatch, tmp_path, packaged)

    _, before, overlay = ubd.regenerate()

    spec_seen = FakeSpecs.seen
    assert "omega" not in spec_seen and "rho" not in spec_seen
    assert "e" not in spec_seen
    assert spec_seen["zeta_K"] == [0.42]
    # overlay is the regenerated demographics plus the derived e, jsonable
    assert set(overlay) == {
        "omega",
        "omega_SS",
        "rho",
        "imm_rates",
        "g_n_ss",
        "e",
    }
    assert overlay["omega"] == np.full((4, 3, 2), 0.1).tolist()
    assert overlay["g_n_ss"] == 0.01


def test_main_rewrites_only_demographic_keys(monkeypatch, tmp_path):
    packaged = {
        "zeta_K": [0.42],
        "alpha_G": [0.14],
        "omega": [[9.0]],
        "rho": [[9.0]],
        "e": [[9.0]],
    }
    path = _patch_all(monkeypatch, tmp_path, packaged)

    ubd.main()

    out = json.loads(path.read_text())
    # demographic keys replaced with the regenerated shapes
    assert out["omega"] == np.full((4, 3, 2), 0.1).tolist()
    assert out["e"] == np.full((3, 2), 1.0).tolist()
    # keys returned by get_pop_objs but absent before are added
    assert out["omega_SS"] == np.full((3, 2), 0.2).tolist()
    # non-demographic keys byte-identical
    assert out["zeta_K"] == [0.42]
    assert out["alpha_G"] == [0.14]
