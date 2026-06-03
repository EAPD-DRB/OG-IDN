"""
Import smoke tests for installed package usage.
"""

import json
import importlib.resources


def test_import_smoke():
    import ogidn
    from ogidn import macro_params
    from ogidn.calibrate import Calibration

    assert ogidn is not None
    assert macro_params is not None
    assert Calibration is not None


def test_packaged_data_available():
    """Packaged data files load from the installed wheel."""
    from ogidn import input_output

    sam = input_output.read_SAM()
    assert sam is not None

    for name in (
        "ogidn_default_parameters.json",
        "ogidn_multisector_default_parameters.json",
    ):
        with importlib.resources.open_text("ogidn", name) as f:
            defaults = json.load(f)
        assert isinstance(defaults, dict)
