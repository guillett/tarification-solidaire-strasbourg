from dotenv import load_dotenv

load_dotenv()
import os
import sys

sys.path.append("../technique")
from utils import determine_age, determine_qf, StrasbourgSurveyScenario, base_period
from results import result_index, extract
import numpy as np
import pandas as pd


def get_df():
    # raw_df = pd.read_csv(
    #     f"{os.getenv("DATA_FOLDER")}culture/CCS_ELEVES_FULL.csv",
    #     delimiter=";",
    #     encoding="windows-1250",
    #     index_col=0,
    #     decimal=",",
    # )
    raw_df = pd.read_pickle(f"{os.getenv('DATA_FOLDER')}culture/CCS_ELEVES_anon.pickle")
    df_types = pd.read_excel(
        f"{os.getenv('DATA_FOLDER')}culture/CSS_Tarifs20230720.xlsx",
        names=["Nom complet", "Profil", "Cours", "Type", "Tarif", "Période", "Montant"],
        index_col=None,
    )
    df = raw_df.merge(df_types, how="left", left_on="LABEL", right_on="Nom complet")
    df["Montant.facturé"] = (
        df["Montant.facturé"]
        .str.extract("(\d*,\d*) €")[0]
        .str.replace(",", ".")
        .astype("float")
    )
    df["Cours complet"] = df.Profil + "_" + df.Cours + "_" + df.Type + "_" + df.Période
    df["qfrule"] = "QF_CCS_" + df.Tarif

    return df


fields = {
    "ENF_CP_EI_AN": "strasbourg_centre_choregraphique_eveil_prix",
    "ADU_xx_1C_TR": "strasbourg_centre_choregraphique_adulte_1_cours_trimestre_prix",
    "ADU_xx_1C_AN": "strasbourg_centre_choregraphique_adulte_1_cours_prix",
    "ADU_xx_2C_AN": "strasbourg_centre_choregraphique_adulte_2_cours_prix",
    "ADU_xx_3C_AN": "strasbourg_centre_choregraphique_adulte_3_cours_prix",
    "ADU_xx_4C_AN": "strasbourg_centre_choregraphique_adulte_4_cours_prix",
    "ENF_CL_1C_AN": "strasbourg_centre_choregraphique_enfant_1_cours_prix",
    "ENF_CL_2C_AN": "strasbourg_centre_choregraphique_enfant_2_cours_prix",
    "ENF_CL_3C_AN": "strasbourg_centre_choregraphique_enfant_3_cours_prix",
    "ENF_CL_4C_AN": "strasbourg_centre_choregraphique_enfant_4_cours_prix",
}


def build_data(df, categorie, sample_count=1):
    product_df = df[df["Cours complet"] == categorie]

    count = len(product_df)
    sample_ids = np.repeat(list(range(sample_count)), count)
    indiv_ids = np.tile(list(range(count)), sample_count)
    sample_qfrule = np.tile(product_df.qfrule, sample_count)

    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(count * sample_count)),
        }
    )

    famille_df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "qfrule": sample_qfrule,
            "strasbourg_centre_choregraphique_tarif": np.tile(
                product_df.Tarif, sample_count
            ),
        }
    )
    determine_qf(famille_df)

    menage_df = pd.DataFrame({})
    foyerfiscaux_df = pd.DataFrame({})

    individu_df["famille_role_index"] = 0
    individu_df["foyer_fiscal_id"] = individu_df.famille_id
    individu_df["foyer_fiscal_role_index"] = 0
    individu_df["menage_id"] = individu_df.famille_id
    individu_df["menage_role_index"] = 0

    base = pd.DataFrame(
        data={
            "sample_id": sample_ids,
            "individu_id": indiv_ids,
            "qf_caf": famille_df.qf_caf,
            "qf_fiscal": famille_df.qf_fiscal,
            "quantité": 1,
            "prix_input": np.tile(product_df["Montant.facturé"], sample_count),
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
        base,
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
    for v in fields:
        openfisca_output_variable = fields[v]

        (data, base) = build_data(df, v, sample_count)
        res = compute(tbs, data, base, openfisca_output_variable)
        row = ["Culture", v]
        count, value = extract(res, output_field)
        row.extend([count["mean"], count["count"]])
        row.extend(value)

        if reform:
            r_res = compute(reform, data, base, openfisca_output_variable, "_r")
            _, r_value = extract(r_res, output_field + "_r")
            row.extend(r_value)
        dfs.append((v, res))
        rows.append(row)

    return pd.DataFrame(rows, columns=result_index[0 : len(rows[0])]), dfs
