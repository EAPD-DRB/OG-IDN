"""
Tests of macro_params.py module
"""

import json
from importlib.resources import files

import pandas as pd
import pytest
import requests
from ogcore.parameters import Specifications

from ogidn import macro_params


class MockResponse:
    """
    Minimal mock response for requests.get().
    """

    def __init__(self, *, json_data=None, text="", status_code=200):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(
                f"HTTP {self.status_code} returned from mocked request"
            )


def _wb_payload(observations):
    return [
        {
            "page": 1,
            "pages": 1,
            "per_page": "10000",
            "total": len(observations),
        },
        [
            {
                "date": date,
                "value": value,
                "indicator": {"id": "mock-indicator"},
            }
            for date, value in observations
        ],
    ]


def _imf_payload(indicator_year_values, country="IDN"):
    years = sorted(
        {
            int(year)
            for observations in indicator_year_values.values()
            for year in observations.keys()
        }
    )
    indicators = list(indicator_year_values.keys())
    return {
        "meta": {},
        "data": {
            "dataSets": [
                {
                    "structure": 0,
                    "action": "Replace",
                    "series": {
                        f"0:0:0:{indicator_idx}:0:0": {
                            "attributes": [0, None, None],
                            "observations": {
                                str(years.index(int(year))): [str(value)]
                                for year, value in observations.items()
                            },
                        }
                        for indicator_idx, observations in enumerate(
                            indicator_year_values.values()
                        )
                    },
                }
            ],
            "structures": [
                {
                    "dimensions": {
                        "series": [
                            {"id": "COUNTRY", "values": [{"id": country}]},
                            {"id": "SECTOR", "values": [{"id": "S1311"}]},
                            {"id": "GFS_GRP", "values": [{"id": "G2M"}]},
                            {
                                "id": "INDICATOR",
                                "values": [
                                    {"id": indicator}
                                    for indicator in indicators
                                ],
                            },
                            {
                                "id": "TYPE_OF_TRANSFORMATION",
                                "values": [{"id": "POGDP_PT"}],
                            },
                            {
                                "id": "FREQUENCY",
                                "values": [{"id": "A"}],
                            },
                        ],
                        "observation": [
                            {
                                "id": "TIME_PERIOD",
                                "values": [
                                    {"value": str(year)} for year in years
                                ],
                            }
                        ],
                    },
                    "measures": {
                        "observation": [{"id": "OBS_VALUE", "roles": []}]
                    },
                    "attributes": {
                        "dimensionGroup": [],
                        "series": [],
                        "observation": [],
                    },
                    "annotations": [],
                }
            ],
        },
    }


def _default_wb_payloads():
    return {
        "NY.GDP.PCAP.KD": _wb_payload(
            [("2024", 100.0), ("2023", 80.0), ("2022", 64.0)]
        ),
        "DP.DOD.DECD.CR.PS.CD": _wb_payload(
            [("2024Q4", 60.0), ("2024Q3", 58.0), ("2024Q2", 57.0)]
        ),
        "DP.DOD.DECX.CR.PS.CD": _wb_payload(
            [("2024Q4", 40.0), ("2024Q3", 42.0), ("2024Q2", 43.0)]
        ),
        "DP.DOD.DECT.CR.GG.Z1": _wb_payload(
            [("2024Q4", 50.0), ("2024Q3", 49.0), ("2024Q2", 48.0)]
        ),
    }


def _mock_requests_get(
    monkeypatch, *, wb_payloads=None, ilo_text=None, imf_json=None
):
    payloads = _default_wb_payloads() if wb_payloads is None else wb_payloads

    def fake_get(url, params=None, headers=None, timeout=None):
        if "worldbank.org" in url:
            indicator_code = url.rstrip("/").split("/")[-1]
            return MockResponse(json_data=payloads[indicator_code])
        if "rplumber.ilo.org" in url:
            return MockResponse(
                text=ilo_text or "time,obs_value\n2024,40\n2023,39\n"
            )
        if "api.imf.org" in url:
            return MockResponse(
                json_data=imf_json
                or _imf_payload(
                    {
                        "G2_T": {2023: 14.0, 2024: 14.5},
                        "G24_T": {2023: 2.1, 2024: 2.2},
                        "G27_T": {2023: 0.8, 2024: 0.9},
                        "G271_T": {2023: 0.0, 2024: 0.1},
                    }
                )
            )
        raise AssertionError(f"Unexpected URL requested in test: {url}")

    monkeypatch.setattr(macro_params.requests, "get", fake_get)


def test_get_macro_params_update_from_api_false_returns_empty_dict():
    test_dict = macro_params.get_macro_params(update_from_api=False)

    assert isinstance(test_dict, dict)
    assert test_dict == {}


def test_get_macro_params_update_from_api_true(monkeypatch):
    _mock_requests_get(monkeypatch)

    test_dict = macro_params.get_macro_params(update_from_api=True)

    assert sorted(test_dict.keys()) == sorted(
        [
            "alpha_T",
            "alpha_G",
            "initial_debt_ratio",
            "g_y_annual",
            "gamma",
            "zeta_D",
            "initial_foreign_debt_ratio",
        ]
    )
    assert test_dict["initial_debt_ratio"] == 0.5
    assert test_dict["initial_foreign_debt_ratio"] == 0.4
    assert test_dict["zeta_D"] == [0.4]
    assert test_dict["g_y_annual"] == pytest.approx(0.25)
    assert test_dict["gamma"] == [0.6]
    assert test_dict["alpha_T"] == [pytest.approx(0.008)]
    assert test_dict["alpha_G"] == [pytest.approx(0.114)]


def test_world_bank_partial_data_does_not_collapse(monkeypatch):
    _mock_requests_get(
        monkeypatch,
        wb_payloads={
            "NY.GDP.PCAP.KD": _wb_payload(
                [("2024", None), ("2023", None), ("2022", None)]
            ),
            "DP.DOD.DECD.CR.PS.CD": _wb_payload([]),
            "DP.DOD.DECX.CR.PS.CD": _wb_payload([]),
            "DP.DOD.DECT.CR.GG.Z1": _wb_payload(
                [("2024Q4", None), ("2024Q3", 50.0), ("2024Q2", 48.0)]
            ),
        },
    )
    test_dict = macro_params.get_macro_params(update_from_api=True)

    assert test_dict["initial_debt_ratio"] == 0.5
    assert "initial_foreign_debt_ratio" not in test_dict
    assert "zeta_D" not in test_dict
    assert "g_y_annual" not in test_dict


def test_wb_annual_fetch_failure_preserves_quarterly(monkeypatch):
    """Annual WB source=2 down; quarterly source=20 still succeeds."""
    payloads = _default_wb_payloads()

    def fake_get(url, params=None, headers=None, timeout=None):
        if "worldbank.org" in url:
            if params and params.get("source") == 2:
                raise requests.ConnectionError("annual source down")
            indicator_code = url.rstrip("/").split("/")[-1]
            return MockResponse(json_data=payloads[indicator_code])
        if "rplumber.ilo.org" in url:
            return MockResponse(text="time,obs_value\n2024,40\n2023,39\n")
        if "api.imf.org" in url:
            return MockResponse(
                json_data=_imf_payload(
                    {
                        "G2_T": {2023: 14.0, 2024: 14.5},
                        "G24_T": {2023: 2.1, 2024: 2.2},
                        "G27_T": {2023: 0.8, 2024: 0.9},
                        "G271_T": {2023: 0.0, 2024: 0.1},
                    }
                )
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(macro_params.requests, "get", fake_get)

    test_dict = macro_params.get_macro_params(update_from_api=True)

    assert "g_y_annual" not in test_dict
    assert test_dict["initial_debt_ratio"] == 0.5
    assert test_dict["initial_foreign_debt_ratio"] == 0.4
    assert test_dict["zeta_D"] == [0.4]


def test_wb_quarterly_fetch_failure_preserves_annual(monkeypatch):
    """Quarterly WB source=20 down; annual source=2 still succeeds."""
    payloads = _default_wb_payloads()

    def fake_get(url, params=None, headers=None, timeout=None):
        if "worldbank.org" in url:
            if params and params.get("source") == 20:
                raise requests.ConnectionError("quarterly source down")
            indicator_code = url.rstrip("/").split("/")[-1]
            return MockResponse(json_data=payloads[indicator_code])
        if "rplumber.ilo.org" in url:
            return MockResponse(text="time,obs_value\n2024,40\n2023,39\n")
        if "api.imf.org" in url:
            return MockResponse(
                json_data=_imf_payload(
                    {
                        "G2_T": {2023: 14.0, 2024: 14.5},
                        "G24_T": {2023: 2.1, 2024: 2.2},
                        "G27_T": {2023: 0.8, 2024: 0.9},
                        "G271_T": {2023: 0.0, 2024: 0.1},
                    }
                )
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(macro_params.requests, "get", fake_get)

    test_dict = macro_params.get_macro_params(update_from_api=True)

    assert test_dict["g_y_annual"] == pytest.approx(0.25)
    assert "initial_debt_ratio" not in test_dict
    assert "initial_foreign_debt_ratio" not in test_dict
    assert "zeta_D" not in test_dict


def test_get_macro_params_uses_last_valid_quarter(monkeypatch):
    _mock_requests_get(
        monkeypatch,
        wb_payloads={
            "NY.GDP.PCAP.KD": _wb_payload(
                [("2024", 100.0), ("2023", 80.0), ("2022", 64.0)]
            ),
            "DP.DOD.DECD.CR.PS.CD": _wb_payload(
                [("2024Q4", None), ("2024Q3", 60.0), ("2024Q2", None)]
            ),
            "DP.DOD.DECX.CR.PS.CD": _wb_payload(
                [("2024Q4", None), ("2024Q3", 40.0), ("2024Q2", None)]
            ),
            "DP.DOD.DECT.CR.GG.Z1": _wb_payload(
                [("2024Q4", None), ("2024Q3", 50.0), ("2024Q2", None)]
            ),
        },
    )
    test_dict = macro_params.get_macro_params(update_from_api=True)

    assert test_dict["initial_debt_ratio"] == 0.5
    assert test_dict["initial_foreign_debt_ratio"] == 0.4
    assert test_dict["zeta_D"] == [0.4]


def test_get_macro_params_uses_imf_year_override(monkeypatch):
    _mock_requests_get(
        monkeypatch,
        imf_json=_imf_payload(
            {
                "G2_T": {2023: 14.0, 2024: 18.0},
                "G24_T": {2023: 2.1, 2024: 3.0},
                "G27_T": {2023: 0.8, 2024: 1.5},
                "G271_T": {2023: 0.0, 2024: 0.2},
            }
        ),
    )
    test_dict = macro_params.get_macro_params(
        update_from_api=True, imf_data_year=2023
    )

    assert test_dict["alpha_T"] == [pytest.approx(0.008)]
    assert test_dict["alpha_G"] == [pytest.approx(0.111)]


def test_get_imf_macro_params_overwrites_saved_file(monkeypatch, tmp_path):
    _mock_requests_get(
        monkeypatch,
        imf_json=_imf_payload(
            {
                "G2_T": {2023: 14.0, 2024: 14.5},
                "G24_T": {2023: 2.1, 2024: 2.2},
                "G27_T": {2023: 0.8, 2024: 0.9},
                "G271_T": {2023: 0.0, 2024: 0.1},
            }
        ),
    )

    data_file = tmp_path / "imf_gfs_soo_idn_s1311_g2m_pogdp_pt_a.csv"
    result = macro_params._get_imf_macro_params(
        "IDN", 2024, data_path=data_file
    )

    assert result["alpha_T"] == [pytest.approx(0.008)]
    assert result["alpha_G"] == [pytest.approx(0.114)]
    assert data_file.exists()

    _mock_requests_get(
        monkeypatch,
        imf_json=_imf_payload(
            {
                "G2_T": {2023: 14.0, 2024: 15.0},
                "G24_T": {2023: 2.1, 2024: 2.4},
                "G27_T": {2023: 0.8, 2024: 1.0},
                "G271_T": {2023: 0.0, 2024: 0.2},
            }
        ),
    )

    refreshed = macro_params._get_imf_macro_params(
        "IDN", 2024, data_path=data_file
    )

    assert refreshed != result
    saved_data = pd.read_csv(data_file)
    saved_2024 = saved_data[saved_data["year"] == 2024].set_index("indicator")
    assert saved_2024.loc["G27_T", "value"] == pytest.approx(1.0)
    assert saved_2024.loc["G271_T", "value"] == pytest.approx(0.2)


def test_get_imf_macro_params_falls_back_to_last_available_year(monkeypatch):
    _mock_requests_get(
        monkeypatch,
        imf_json=_imf_payload(
            {
                "G2_T": {2023: 14.0},
                "G24_T": {2023: 2.1},
                "G27_T": {2023: 0.8},
                "G271_T": {2023: 0.0},
            }
        ),
    )

    result = macro_params._get_imf_macro_params("IDN", 2024)

    assert result["alpha_T"] == [pytest.approx(0.008)]
    assert result["alpha_G"] == [pytest.approx(0.111)]


def test_get_macro_params_ilo_request_uses_timeout(monkeypatch):
    seen_timeouts = []

    def fake_get(url, params=None, headers=None, timeout=None):
        if "worldbank.org" in url:
            indicator_code = url.rstrip("/").split("/")[-1]
            return MockResponse(
                json_data=_default_wb_payloads()[indicator_code]
            )
        if "rplumber.ilo.org" in url:
            seen_timeouts.append(timeout)
            return MockResponse(
                text="time,obs_value\n2024,40\n2023,39\n", status_code=200
            )
        if "api.imf.org" in url:
            return MockResponse(
                json_data=_imf_payload(
                    {
                        "G2_T": {2023: 14.0, 2024: 14.5},
                        "G24_T": {2023: 2.1, 2024: 2.2},
                        "G27_T": {2023: 0.8, 2024: 0.9},
                        "G271_T": {2023: 0.0, 2024: 0.1},
                    }
                )
            )
        raise AssertionError(f"Unexpected URL requested in test: {url}")

    monkeypatch.setattr(macro_params.requests, "get", fake_get)

    macro_params.get_macro_params(update_from_api=True)

    assert seen_timeouts == [30]


@pytest.mark.parametrize(
    "defaults_file",
    [
        "ogidn_default_parameters.json",
        "ogidn_multisector_default_parameters.json",
    ],
)
def test_packaged_defaults_load_into_specifications(defaults_file):
    p = Specifications()
    with files("ogidn").joinpath(defaults_file).open("r") as file:
        defaults = json.load(file)

    p.update_specifications(defaults)
