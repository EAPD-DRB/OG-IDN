"""
This module uses data from World Bank WDI, World Bank Quarterly Public
Sector Debt (QPSD) database, the IMF, and UN ILO to find values for
parameters for the OG-IDN model that rely on macro data for calibration.
"""

# imports
import pandas as pd
import numpy as np
import requests
import datetime
from io import StringIO
from pathlib import Path

# Post-Asian-Financial-Crisis / post-Reformasi regime boundary.
# Used as the start year for the g_y_annual GDP-per-capita growth window
# so the mean reflects Indonesia's modern regime, not the 1997-98 crash.
GDP_GROWTH_START_YEAR = 2000


def _fetch_wb_data(indicators, country_iso, start_year, end_year, source):
    """
    Fetch a set of World Bank indicators from the v2 API.

    Args:
        indicators (dict): mapping of label to indicator code
        country_iso (str): ISO alpha-3 country code
        start_year (int): first year to request
        end_year (int): last year to request
        source (int): World Bank source ID

    Returns:
        pandas.DataFrame: DataFrame indexed by year/quarter label
    """
    if source == 2:
        date_range = f"{start_year}:{end_year}"
    elif source == 20:
        date_range = f"{start_year}Q1:{end_year}Q4"
    else:
        raise ValueError(f"Unsupported World Bank source: {source}")

    data_frames = []
    for label, indicator_code in indicators.items():
        response = requests.get(
            (
                "https://api.worldbank.org/v2/country/"
                f"{country_iso}/indicator/{indicator_code}"
            ),
            params={
                "date": date_range,
                "source": source,
                "format": "json",
                "per_page": 10000,
            },
            timeout=30,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError(
                f"Malformed World Bank response for {indicator_code}"
            ) from exc

        if (
            not isinstance(payload, list)
            or len(payload) < 2
            or not isinstance(payload[1], list)
        ):
            raise ValueError(
                f"Empty or malformed World Bank response for {indicator_code}"
            )

        series_data = {}
        for row in payload[1]:
            date = row.get("date")
            if date is None:
                continue
            series_data[date] = row.get("value")

        series = pd.Series(series_data, name=label)
        series = pd.to_numeric(series, errors="coerce")
        data_frames.append(series.to_frame())

    data = pd.concat(data_frames, axis=1)
    data.index.name = "year"
    return data.sort_index(ascending=False)


def _get_imf_macro_params(country_iso, target_year, data_path=None):
    """
    Fetch IMF GFS data and compute alpha_T and alpha_G.

    IMF GFS publishes with a lag. If target_year is not yet available, the
    function falls back to the latest complete year and logs it. See the
    "Calibration vintage" table in docs/book/content/calibration/macro.md.

    Args:
        country_iso (str): ISO alpha-3 country code
        target_year (int): preferred calibration year
        data_path (str | Path | None): optional path to save IMF CSV data

    Returns:
        dict: IMF-derived macro parameters
    """
    required_indicators = {"G2_T", "G24_T", "G27_T", "G271_T"}
    data_path = Path(data_path) if data_path is not None else None
    response = requests.get(
        (
            "https://api.imf.org/external/sdmx/3.0/data/dataflow/"
            f"IMF.STA/GFS_SOO/12.0.0/"
            f"{country_iso.upper()}.S1311.G2M.*.POGDP_PT.A"
        ),
        timeout=30,
    )
    response.raise_for_status()
    try:
        payload = response.json()
        data = payload["data"]
        structure = data["structures"][0]
        data_set = data["dataSets"][0]
        series_dimensions = structure["dimensions"]["series"]
        observation_years = [
            value.get("id", value.get("value"))
            for value in structure["dimensions"]["observation"][0]["values"]
        ]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            "Empty or malformed IMF response for GFS_SOO"
        ) from exc

    records = []
    for series_key, series in data_set["series"].items():
        dimension_indexes = [int(idx) for idx in series_key.split(":")]
        labels = {
            dim["id"]: dim["values"][idx]["id"]
            for dim, idx in zip(series_dimensions, dimension_indexes)
        }
        indicator = labels.get("INDICATOR")
        if indicator not in required_indicators:
            continue
        for observation_key, observation in series.get(
            "observations", {}
        ).items():
            value = observation[0]
            if value is None:
                continue
            records.append(
                {
                    "year": observation_years[int(observation_key)],
                    "indicator": indicator,
                    "value": float(value),
                    "country_iso": country_iso.upper(),
                    "sector": "S1311",
                    "dataset": "IMF.STA:GFS_SOO(12.0.0)",
                }
            )

    imf_data = pd.DataFrame(records)
    if imf_data.empty:
        raise ValueError("Empty or malformed IMF response for GFS_SOO")

    if data_path is not None:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        imf_data.sort_values(["indicator", "year"]).to_csv(
            data_path, index=False
        )
        print(f"IMF data saved to {data_path}")

    imf_data["year"] = pd.to_numeric(imf_data["year"], errors="coerce")
    imf_data["value"] = pd.to_numeric(imf_data["value"], errors="coerce")
    imf_data = imf_data.dropna(subset=["year", "value"])

    available = (
        imf_data.pivot_table(
            index="year",
            columns="indicator",
            values="value",
            aggfunc="first",
        )
        .sort_index()
        .dropna(subset=sorted(required_indicators))
    )
    available = available.loc[available.index <= int(target_year)]

    if available.empty:
        raise ValueError(
            f"No complete IMF data available for {country_iso.upper()} up to "
            f"{target_year}"
        )

    selected_year = (
        int(target_year)
        if int(target_year) in available.index
        else int(available.index.max())
    )
    if selected_year != int(target_year):
        print(
            f"Warning: No IMF data for {target_year}. Using last available "
            f"year: {selected_year}"
        )

    values = available.loc[selected_year]
    return {
        "alpha_T": [(values["G27_T"] - values["G271_T"]) / 100],
        "alpha_G": [
            (values["G2_T"] - values["G24_T"] - values["G27_T"]) / 100
        ],
    }


def get_macro_params(
    data_start_date=datetime.datetime(1947, 1, 1),
    data_end_date=datetime.datetime(2024, 12, 31),
    country_iso="IDN",
    update_from_api=False,
    imf_data_year=None,
    imf_data_path=None,
):
    """
    Compute values of parameters that are derived from macro data

    Args:
        data_start_date (datetime): start date for data
        data_end_date (datetime): end date for data
        country_iso (str): ISO code for country
        update_from_api (bool): Set True if you want to pull updated
            macro data from World Bank and UN APIs
        imf_data_year (int | None): IMF target year override. Defaults to
            data_end_date.year when None.
        imf_data_path (str | Path | None): optional path to save IMF CSV data

    Returns:
        macro_parameters (dict): dictionary of parameter values
    """
    # initialize a dictionary of parameters
    macro_parameters = {}
    # baseline date formatted for World Bank data
    baseline_YYYYQ = (
        str(data_end_date.year)
        + "Q"
        + str(pd.Timestamp(data_end_date).quarter)
    )

    """
    Retrieve data from the World Bank World Development Indicators.
    """
    # Dictionaries of variables and their corresponding World Bank codes
    # Annual data
    wb_a_variable_dict = {
        "GDP per capita (constant 2015 US$)": "NY.GDP.PCAP.KD",
    }
    # Quarterly data
    wb_q_variable_dict = {
        "Gross PSD USD - domestic creditors": "DP.DOD.DECD.CR.PS.CD",
        "Gross PSD USD - external creditors": "DP.DOD.DECX.CR.PS.CD",
        "Gross PSD Gen Gov - percentage of GDP": "DP.DOD.DECT.CR.GG.Z1",
    }
    # Packaged baseline values for g_y_annual, initial_debt_ratio,
    # initial_foreign_debt_ratio, and zeta_D are sourced from these World
    # Bank WDI and QPSD series for Indonesia. g_y_annual uses a
    # GDP_GROWTH_START_YEAR-onward window (post-AFC / post-Reformasi).

    # Function to get the latest valid data if baseline_YYYYQ is missing or NaN
    def get_valid_data(series, baseline_YYYYQ):
        value = series.get(baseline_YYYYQ, None)

        if pd.isna(value):
            latest_non_nan = series.dropna().first_valid_index()

            if latest_non_nan is not None:
                print(
                    f"Warning: No data for {baseline_YYYYQ}. "
                    f"Using last available quarter: {latest_non_nan}"
                )
                value = series.get(latest_non_nan, None)
            else:
                print(
                    "Warning: No historical data available. Skipping update."
                )
                value = None

        return value

    if update_from_api:
        # Annual WB fetch (source=2) — drives g_y_annual only.
        try:
            wb_data_a = _fetch_wb_data(
                wb_a_variable_dict,
                country_iso,
                GDP_GROWTH_START_YEAR,
                data_end_date.year,
                source=2,
            )

            # Compute annual GDP growth safely
            if "GDP per capita (constant 2015 US$)" in wb_data_a.columns:
                g_y_series = wb_data_a[
                    "GDP per capita (constant 2015 US$)"
                ].pct_change(-1, fill_method=None)

                # If all values are NaN, return None
                g_y_annual = (
                    g_y_series.mean() if not g_y_series.isna().all() else None
                )
                if g_y_annual is not None:
                    macro_parameters["g_y_annual"] = g_y_annual
            else:
                print(
                    "Warning: Missing GDP per capita data in World Bank "
                    "data. Skipping update for g_y_annual."
                )

            if "g_y_annual" in macro_parameters:
                print(
                    "g_y_annual updated from World Bank API: "
                    f"{macro_parameters['g_y_annual']}"
                )
            else:
                print("Warning: Skipping update for g_y_annual.")
        except Exception:
            print("Failed to retrieve annual data from World Bank")
            print("Will not update g_y_annual")

        # Quarterly WB fetch (source=20) — drives initial_debt_ratio,
        # initial_foreign_debt_ratio, zeta_D. Independent of annual fetch so
        # one outage does not suppress both.
        try:
            wb_data_q = _fetch_wb_data(
                wb_q_variable_dict,
                country_iso,
                data_start_date.year,
                data_end_date.year,
                source=20,
            )

            # Compute macro parameters from WB data
            initial_debt_ratio = get_valid_data(
                pd.Series(wb_data_q["Gross PSD Gen Gov - percentage of GDP"])
                / 100,
                baseline_YYYYQ,
            )
            if initial_debt_ratio is not None:
                macro_parameters["initial_debt_ratio"] = initial_debt_ratio
                print(
                    "initial_debt_ratio updated from World Bank API: "
                    f"{macro_parameters['initial_debt_ratio']}"
                )
            else:
                print("Warning: Skipping update for initial_debt_ratio.")
            # Compute initial_foreign_debt_ratio safely
            if (
                "Gross PSD USD - external creditors" in wb_data_q.columns
                and "Gross PSD USD - domestic creditors" in wb_data_q.columns
            ):
                total_debt = (
                    wb_data_q["Gross PSD USD - domestic creditors"]
                    + wb_data_q["Gross PSD USD - external creditors"]
                )

                # Avoid division by zero
                wb_data_q["foreign_debt_ratio"] = wb_data_q[
                    "Gross PSD USD - external creditors"
                ] / total_debt.replace(0, np.nan)

                initial_foreign_debt_ratio = get_valid_data(
                    wb_data_q["foreign_debt_ratio"], baseline_YYYYQ
                )
                if initial_foreign_debt_ratio is not None:
                    macro_parameters["initial_foreign_debt_ratio"] = (
                        initial_foreign_debt_ratio
                    )
            else:
                print(
                    "Warning: Missing debt variables in World Bank data."
                    " Skipping update for initial_foreign_debt_ratio."
                )

            if "initial_foreign_debt_ratio" in macro_parameters:
                print(
                    "initial_foreign_debt_ratio updated from World Bank "
                    "API: "
                    f"{macro_parameters['initial_foreign_debt_ratio']}"
                )

                # Since it's the same formula, use the same calculated value
                macro_parameters["zeta_D"] = [
                    macro_parameters["initial_foreign_debt_ratio"]
                ]
                print(
                    "zeta_D updated from World Bank API: "
                    f"{macro_parameters['zeta_D']}"
                )
            else:
                print(
                    "Warning: Skipping update for "
                    "initial_foreign_debt_ratio and zeta_D."
                )
        except Exception:
            print("Failed to retrieve quarterly data from World Bank")
            print(
                "Will not update [initial_debt_ratio, "
                "initial_foreign_debt_ratio, zeta_D]"
            )
    else:
        print("Not updating from World Bank API")

    """
    Retrieve labour share data from the United Nations ILOSTAT Data API
    (see https://rshiny.ilo.org/dataexplorer9/?lang=en)
    The series code is SDG_1041_NOC_RT_A (capital share)
    Labor share (gamma) = 1 - capital share
    If this fails we will not update gamma in 'default_parameters.json'
    """
    # The packaged baseline gamma value is sourced from ILOSTAT series
    # SDG_1041_NOC_RT_A for Indonesia.
    if update_from_api:
        try:
            target = (
                "https://rplumber.ilo.org/data/indicator/"
                + "?id=SDG_1041_NOC_RT_A"
                + "&ref_area="
                + str(country_iso)
                + "&timefrom="
                + str(data_start_date.year)
                + "&timeto="
                + str(data_end_date.year)
                + "&type=both&format=.csv"
            )
            # Add headers
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }

            print("Attempting to update gamma from ILOSTAT")
            response = requests.get(target, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
            else:
                print("Request successful.")
            csv_content = StringIO(response.text)
            df_temp = pd.read_csv(csv_content)
            ilo_data = df_temp[["time", "obs_value"]]
            # find gamma, capital's share of income
            macro_parameters["gamma"] = [
                1
                - (
                    (
                        ilo_data.loc[
                            ilo_data["time"] == data_end_date.year, "obs_value"
                        ].squeeze()
                    )
                    / 100
                )
            ]
            print(
                f"gamma updated from ILOSTAT API: {macro_parameters['gamma']}"
            )
        except Exception:
            print("Failed to retrieve data from ILOSTAT")
            print("Will not update gamma")
    else:
        print("Not updating from ILOSTAT API")

    """
    Calibrate parameters from IMF data
    """
    if update_from_api:
        try:
            imf_year = (
                data_end_date.year if imf_data_year is None else imf_data_year
            )
            macro_parameters.update(
                _get_imf_macro_params(
                    country_iso,
                    imf_year,
                    data_path=imf_data_path,
                )
            )
            print(
                f"alpha_T updated from IMF data: {macro_parameters['alpha_T']}"
            )
            print(
                f"alpha_G updated from IMF data: {macro_parameters['alpha_G']}"
            )
        except Exception:
            print("Failed to retrieve data from IMF")
            print("Will not update alpha_T, alpha_G")
    else:
        print("Not updating alpha_T, alpha_G")

    return macro_parameters
