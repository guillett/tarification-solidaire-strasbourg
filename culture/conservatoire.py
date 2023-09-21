from dotenv import load_dotenv

load_dotenv()
import os
import sys

sys.path.append("../technique")
from utils import StrasbourgSurveyScenario, base_period
from results import result_index, extract
import numpy as np
import pandas as pd


def get_df():
    df = pd.read_excel(f"{os.getenv('DATA_FOLDER')}minimales/conservatoire.xlsx")

    df.agent.fillna(0, inplace=True)
    df["habitant EMS"].fillna(0, inplace=True)
    # df['hors EMS'].fillna(0, inplace=True)
    # df["Enfant de la fratrie"].fillna(1, inplace=True)
    # df["Cycle"].fillna(0, inplace=True)
    # df.Dominante.fillna(1, inplace=True)
    df["prix_input"] = df.MontantFactureSurEleve

    tdf = pd.DataFrame(
        {"t": [1, 2, 3, 4, 5, np.nan], "v": [0, 16714, 21707, 29007, 36114, 36114]}
    )

    df["ressources"] = df.merge(tdf, left_on="Tranche", right_on="t", how="left")[
        ["index", "Tranche", "v"]
    ].v

    return df


def build_data(df, sample_count=1):
    count = len(df)
    sample_count = 1
    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(count * sample_count)),
        }
    )
    sample_ids = np.repeat(list(range(sample_count)), count)
    indiv_ids = np.tile(list(range(count)), sample_count)
    # sample_qfrule = np.tile(product_df.qfrule, sample_count)
    df["sample_id"] = sample_ids

    famille_df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "strasbourg_conservatoire_base_ressources": np.tile(
                df["ressources"], sample_count
            ),
            "strasbourg_conservatoire_nombre_cycles": np.tile(
                df["Cycle.1"], sample_count
            ),
            "strasbourg_conservatoire_qf_bourse": np.tile(df.qf, sample_count),
            "agent_ems": np.tile(df.agent, sample_count),
            "habitant_ems": np.tile(df["habitant EMS"], sample_count),
        }
    )

    menage_df = pd.DataFrame({})
    foyerfiscaux_df = pd.DataFrame({})

    individu_df["famille_role_index"] = 0
    individu_df["foyer_fiscal_id"] = individu_df.famille_id
    individu_df["foyer_fiscal_role_index"] = 0
    individu_df["menage_id"] = individu_df.famille_id
    individu_df["menage_role_index"] = 0

    return dict(
        input_data_frame_by_entity=dict(
            individu=individu_df,
            famille=famille_df,
            menage=menage_df,
            foyer_fiscal=foyerfiscaux_df,
        )
    )


def compute(tbs, data, base, openfisca_output_variable, suffix=""):
    scenario = StrasbourgSurveyScenario(tbs, data=data)
    prix = scenario.simulation.calculate(openfisca_output_variable, base_period)

    base["prix" + suffix] = prix
    base["res" + suffix] = (base.prix - base.prix_input).abs() < 0.001
    return base


def get_results(tbs, sample_count=1, reform=None):
    df = get_df()

    results = []
    rows = []
    output_field = "prix"
    dfs = []
    for n, gdf in df.groupby("produit"):
        openfisca_output_variable = f"strasbourg_conservatoire_{n}"

        data = build_data(gdf, sample_count)
        res = compute(tbs, data, gdf, openfisca_output_variable)
        row = ["Culture", n]
        count, value = extract(res, output_field)
        row.extend([count["mean"], count["count"]])
        row.extend(value)

        if reform:
            r_res = compute(reform, data, gdf, openfisca_output_variable, "_r")
            _, r_value = extract(r_res, output_field + "_r")
            row.extend(r_value)
        dfs.append((n, res))
        rows.append(row)

    return pd.DataFrame(rows, columns=result_index[0 : len(rows[0])]), dfs
