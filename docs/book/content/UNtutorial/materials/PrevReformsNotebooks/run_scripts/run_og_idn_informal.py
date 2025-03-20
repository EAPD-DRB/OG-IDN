# Need to fix references to Calculator, reform json, and substitute new tax
# function call
import multiprocessing
from distributed import Client
import os
import json
import time
import copy
import numpy as np
from importlib.resources import files
import matplotlib.pyplot as plt
import ogcore
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle
from ogidn.calibrate import Calibration
from ogidn.utils import is_connected

# Use a custom matplotlib style file for plots
plt.style.use("ogcore.OGcorePlots")


def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    save_dir = os.path.join(CUR_DIR, "OG-IDN-Informal")
    base_dir = os.path.join(save_dir, "OUTPUT_BASELINE")
    reform_dir = os.path.join(save_dir, "OUTPUT_REFORM")

    """
    ---------------------------------------------------------------------------
    Run baseline policy
    ---------------------------------------------------------------------------
    """
    # Set up baseline parameterization
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=base_dir,
        output_base=base_dir,
    )
    # Update parameters for baseline from default json file
    with (
        files("ogidn")
        .joinpath("ogidn_default_parameters.json")
        .open("r") as file
    ):
        defaults = json.load(file)
    p.update_specifications(defaults)
    # further update for 2 sectors: formal and informal
    informal_spec = {
        "M": 2,
        "I": 2,
        "gamma_g": [
            0.0,
            0.0,
        ],  # need to set production function params to for two industries
        "epsilon": [1.0, 1.0],
        "gamma": [
            0.1,
            0.41,
        ],  # assumption (first sector is informal): informal has lower capital labor ratio
        "cit_rate": [[0.0], [0.22]],  # no CIT for informal
        "tau_c": [[0.0], [0.11]],  # no VAT for informal
        "alpha_c": [
            0.36,
            0.64,
        ],  # 36\% of GDP on average https://documents1.worldbank.org/curated/en/099435011152325553/pdf/IDU025ef01630fdd504ae5085e90437dc8b1c171.pdf
        "io_matrix": np.eye(2),
    }
    p.update_specifications(informal_spec)

    # Run model
    start_time = time.time()
    runner(p, time_path=True, client=client)
    print("run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    Run reform policy
    ---------------------------------------------------------------------------
    """

    # create new Specifications object for reform simulation
    p2 = copy.deepcopy(p)
    p2.baseline = False
    p2.output_base = reform_dir

    # Parameter change for the reform run
    formalize_spec = {
        "gamma": [0.3, 0.41],  # capital deepening in the informal sector
        "cit_rate": [[0.22], [0.22]],  # informal sector now pays CIT
        "tau_c": [[0.11], [0.11]],  # informal now pays VAT
        "alpha_c": [
            0.25,
            0.75,
        ],  # Consumption shifts away from informal since now compete with established formal sector
        "io_matrix": np.eye(2),
    }
    p2.update_specifications(formalize_spec)

    # Run model
    start_time = time.time()
    runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ---------------------------------------------------------------------------
    Save some results of simulations
    ---------------------------------------------------------------------------
    """
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    reform_tpi = safe_read_pickle(
        os.path.join(reform_dir, "TPI", "TPI_vars.pkl")
    )
    reform_params = safe_read_pickle(
        os.path.join(reform_dir, "model_params.pkl")
    )
    ans = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi,
        reform_params=reform_params,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir, reform_dir, os.path.join(save_dir, "OG-IDN_Informal_plots")
    )

    print("Percentage changes in aggregates:", ans)
    # save percentage change output to csv file
    ans.to_csv(os.path.join(save_dir, "OG-IDN_Informal_output.csv"))


if __name__ == "__main__":
    # execute only if run as a script
    main()
