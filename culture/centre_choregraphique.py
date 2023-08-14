import sys

sys.path.append("../technique")
from utils import *
import pandas as pd


def get_df():
    raw_df = pd.read_csv(
        "/home/thomas/Nextcloud/CodeursEnLiberte/EMS/culture/CCS_ELEVES_FULL.csv",
        delimiter=";",
        encoding="windows-1250",
        index_col=0,
        decimal=",",
    )
    df_types = pd.read_excel(
        "/home/thomas/Nextcloud/CodeursEnLiberte/EMS/culture/CSS_Tarifs20230720.xlsx",
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


def compute(tbs, df, categorie):
    openfisca_output_variable = fields[categorie]
    product_df = df[df["Cours complet"] == categorie]
    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(len(product_df))),
        }
    )

    famille_df = pd.DataFrame(
        {
            "qfrule": product_df.qfrule,
        }
    )
    determine_qf(famille_df, qfrules_constant)

    menage_df = pd.DataFrame({})
    foyerfiscaux_df = pd.DataFrame({})

    individu_df["famille_role_index"] = 0
    individu_df["foyer_fiscal_id"] = individu_df.famille_id
    individu_df["foyer_fiscal_role_index"] = 0
    individu_df["menage_id"] = individu_df.famille_id
    individu_df["menage_role_index"] = 0

    data = dict(
        input_data_frame_by_entity=dict(
            individu=individu_df,
            famille=famille_df,
            menage=menage_df,
            foyer_fiscal=foyerfiscaux_df,
        )
    )

    scenario = StrasbourgSurveyScenario(tbs, data=data)

    prix = scenario.simulation.calculate(openfisca_output_variable, base_period)
    res_prix = pd.DataFrame(
        data={
            "qf_caf": famille_df.qf_caf,
            "res": (prix - product_df["Montant.facturé"]).abs() < 0.001,
            "prix_input": product_df["Montant.facturé"],
            "prix_output": prix,
        }
    )
    return res_prix


def get_results(tbs):
    df = get_df()

    results = [compute(tbs, df, v) for v in fields]
    return pd.DataFrame(
        data={
            "Direction": "Culture",
            "Service": [v for v in fields],
            "Recettes": [r.prix_output.sum() for r in results],
            "Quantité": [r.prix_output.count() for r in results],
        }
    )
