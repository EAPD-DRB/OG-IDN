"""Regenerate ONLY the demographic parameters in the packaged base
``ogidn_default_parameters.json`` under the installed ogcore.

Regeneration is a rare event: run this after bumping ogcore across a
demographics-convention change (e.g. ogcore 0.18.0 / PSLmodels/OG-Core#1165,
which stores the demographic arrays by age and lifetime income group). It
calls the same ``get_pop_objs`` that ``ogidn.calibrate`` uses (UN data, with
the cached GitHub-mirror fallback, so no API token is required) and writes
back ONLY the demographic keys plus the demographics-derived earnings
profile ``e``.

Everything else in the JSON -- the documented macro constants, tax
parameters, the open-economy block -- is left byte-for-byte unchanged: a
clobber guard aborts the write if any non-demographic key would differ.
Macro parameters are documented constants (see ``ogidn.macro_params`` and
the calibration docs), NOT pulled from live APIs, so they are deliberately
not touched here. For a full refresh of the API-sourced overlay (including
``g_y_annual``) use ``ogidn.update_baseline`` instead.

    python -m ogidn.update_baseline_demographics
"""

import json

from importlib.resources import files

from ogcore import demographics
from ogcore.parameters import Specifications

from ogidn import income
from ogidn.calibrate import UN_COUNTRY_CODE

# Demographic keys returned by get_pop_objs, plus the derived earnings profile.
# Only these are rewritten; anything else is a clobber and blocks the write.
_DERIVED = "e"


def regenerate():
    """Return the demographic overlay {key: jsonable} regenerated under the
    installed ogcore, matching ogidn.calibrate's get_pop_objs calls."""
    json_path = files("ogidn").joinpath("ogidn_default_parameters.json")
    before = json.loads(json_path.read_text())

    # Bootstrap: across an ogcore demographics-convention change the packaged
    # arrays still have the PREVIOUS ogcore's shapes, which the installed
    # schema rejects -- and they are exactly the keys being regenerated.
    # Load the base without them; the tool only needs the non-demographic
    # scalars (E, S, T, J, lambdas, start_year) to drive the regeneration.
    demog_keys = {
        "omega",
        "omega_SS",
        "omega_S_preTP",
        "rho",
        "rho_preTP",
        "imm_rates",
        "imm_rates_preTP",
        "g_n",
        "g_n_ss",
        "g_n_preTP",
        _DERIVED,
    }
    p = Specifications()
    p.update_specifications(
        {k: v for k, v in before.items() if k not in demog_keys}
    )  # single-sector base (M=1, I=1)

    pop = demographics.get_pop_objs(
        p.E,
        p.S,
        p.T,
        0,
        99,
        country_id=UN_COUNTRY_CODE,
        initial_data_year=p.start_year - 1,
        final_data_year=p.start_year + 1,
        income_percentiles=p.lambdas.flatten(),
        GraphDiag=False,
    )
    demog80 = demographics.get_pop_objs(
        20,
        80,
        p.T,
        0,
        99,
        country_id=UN_COUNTRY_CODE,
        initial_data_year=p.start_year - 1,
        final_data_year=p.start_year + 1,
        income_percentiles=p.lambdas.flatten(),
        GraphDiag=False,
    )
    e = income.get_e_interp(p.E, p.S, p.J, p.lambdas, demog80["omega_SS"])

    def _jsonable(v):
        return v.tolist() if hasattr(v, "tolist") else v

    overlay = {k: _jsonable(v) for k, v in pop.items()}
    overlay[_DERIVED] = _jsonable(e)
    return json_path, before, overlay


def main():
    json_path, before, overlay = regenerate()
    after = dict(before)
    after.update(overlay)

    overlay_keys = set(overlay)
    clobbered = [
        k
        for k in before
        if k not in overlay_keys and after.get(k) != before.get(k)
    ]
    added = sorted(set(after) - set(before))
    print(f"demographic keys written: {sorted(overlay_keys)}")
    print(f"new keys added: {added}")
    print(f"non-demographic keys clobbered (must be []): {clobbered}")
    assert not clobbered, "clobber guard tripped -- refusing to write"

    json_path.write_text(json.dumps(after, indent=4) + "\n")
    print(f"wrote {json_path}")


if __name__ == "__main__":
    main()
