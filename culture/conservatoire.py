from dotenv import load_dotenv

load_dotenv()
import os
import sys

sys.path.append("../technique")
from utils import StrasbourgSurveyScenario, base_period, determine_qf, adjust_df
from results import result_index, extract
import numpy as np
import pandas as pd


def get_df(source):
    if source == "caf":
        df = pd.read_excel(
            f"{os.getenv('DATA_FOLDER')}minimales/conservatoire_base_v7.xlsx"
        )
    else:
        df = pd.read_excel(
            f"{os.getenv('DATA_FOLDER')}minimales/conservatoire_insee_v7.xlsx"
        )

    df.agent.fillna(0, inplace=True)
    df["habitant.EMS"].fillna(0, inplace=True)
    # df['hors EMS'].fillna(0, inplace=True)
    # df["Enfant de la fratrie"].fillna(1, inplace=True)
    # df["Cycle"].fillna(0, inplace=True)
    # df.Dominante.fillna(1, inplace=True)
    df["prix_input"] = df.MontantFactureSurEleve

    tdf = pd.DataFrame(
        {
            "t": [1, 2, 3, 4, 5],
            "v": [0, 16714, 21707, 29007, 36114],
        }
    )
    tdf["b"] = tdf.v / 12 / 2.5
    tdf["n"] = tdf.b.shift(-1, fill_value=4000)
    tdf["qfrule"] = (
        tdf.b.round().astype("int").astype("str")
        + "<=QF<"
        + tdf.n.round().astype("int").astype("str")
    )
    df["ressources"] = df.merge(tdf, left_on="Tranche", right_on="t", how="left")[
        ["index", "Tranche", "v"]
    ].v

    df["ressources"].fillna(tdf.v.iloc[-1], inplace=True)
    df["qfrule"] = df.merge(tdf, left_on="Tranche", right_on="t", how="left")[
        ["index", "Tranche", "qfrule"]
    ].qfrule
    df["qfrule"].fillna(tdf.qfrule.iloc[-1], inplace=True)
    # df["qfrule"].fillna("0<=QF<=4000", inplace=True)

    df["individu_id"] = [*range(len(df))]

    return df


def build_data(df, sample_count=1, adjustment="v1"):
    count = len(df)
    if type(sample_count) == str:
        sample_field, qf_field = sample_count.split("#")
        sample_ids = df[sample_field]
        sample_count = 1
    else:
        sample_field, qf_field = None, None
        sample_ids = np.repeat(list(range(sample_count)), count)

    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(count * sample_count)),
        }
    )
    sample_qfrule = np.tile(df.qfrule, sample_count)

    famille_df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "strasbourg_conservatoire_base_ressources_historique": np.tile(
                df["ressources"], sample_count
            ),
            "strasbourg_conservatoire_nombre_cycles": np.tile(
                df["Cycle.1"], sample_count
            ),
            "qfrule": np.tile(df.qfrule, sample_count),
            "strasbourg_conservatoire_bourse_historique": np.tile(
                df.strasbourg_conservatoire_bourse_historique, sample_count
            ),
            "agent_ems": np.tile(df.agent, sample_count),
            "habitant_ems": np.tile(
                df["habitant.EMS"],
                sample_count,
            ),
            # "strasbourg_conservatoire_enfant_dans_la_fratrie": np.tile(df["Enfant de la fratrie"], sample_count),
        }
    )
    determine_qf(famille_df)
    if qf_field:
        famille_df["qf_fiscal"] = df[qf_field]
    adjust_df(famille_df, adjustment)

    menage_df = pd.DataFrame({})
    foyerfiscaux_df = pd.DataFrame({})

    individu_df["famille_role_index"] = 0
    individu_df["foyer_fiscal_id"] = individu_df.famille_id
    individu_df["foyer_fiscal_role_index"] = 0
    individu_df["menage_id"] = individu_df.famille_id
    individu_df["menage_role_index"] = 0

    extra = pd.DataFrame(
        {
            "individu_id": np.tile(df.individu_id, sample_count),
            "sample_id": sample_ids,
            "qfrule": np.tile(df.qfrule, sample_count),
            "qf_caf": famille_df.qf_caf,
            "qf_fiscal": famille_df.qf_fiscal,
            "prix_input": np.tile(df.MontantFactureSurEleve, sample_count),
            "bourse": famille_df.strasbourg_conservatoire_bourse_historique,
        }
    )

    return (
        dict(
            input_data_frame_by_entity=dict(
                individu=individu_df,
                famille=famille_df,
                menage=menage_df,
                foyer_fiscal=foyerfiscaux_df,
            )
        ),
        extra,
    )


def compute(tbs, data, base, openfisca_output_variable, suffix=""):
    scenario = StrasbourgSurveyScenario(tbs, data=data)
    prix = scenario.simulation.calculate(openfisca_output_variable, base_period)

    base["prix" + suffix] = prix
    base["res" + suffix] = (base.prix - base.prix_input).abs() < 0.001


def get_results(tbs, sample_count=1, reform=None, source="caf", adjustment="v1"):
    df = get_df(source)

    results = []
    rows = []
    output_field = "prix"
    dfs = []
    for n, gdf in df.groupby("service"):
        openfisca_output_variable = f"strasbourg_conservatoire_{n}"

        data, out_df = build_data(gdf, sample_count)
        compute(tbs, data, out_df, openfisca_output_variable)
        row = ["Culture", n]
        count, value = extract(out_df, output_field)
        row.extend([count["mean"], count["count"]])
        row.extend(value)

        if reform:
            compute(reform, data, out_df, openfisca_output_variable, "_r")
            _, r_value = extract(out_df, output_field + "_r")
            row.extend(r_value)
        dfs.append((n, out_df))
        rows.append(row)

    return pd.DataFrame(rows, columns=result_index[0 : len(rows[0])]), dfs
