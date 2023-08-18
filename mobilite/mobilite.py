import sys

sys.path.append("../technique")

from dotenv import load_dotenv
import numpy as np
import os
import pandas as pd
from results import result_index, extract

load_dotenv()
from utils import determine_age, determine_qf, StrasbourgSurveyScenario, base_period


def add_compensation(df):
    max_prix = df[["reduit", "pu_calc"]].groupby(by="reduit").max().pu_calc
    max_prix_grille = np.where(df.reduit, max_prix[1], max_prix[0])
    df["tp"] = df.pu_calc == max_prix_grille
    df["compensation"] = np.where(
        df["tp"], (max_prix_grille / max(max_prix_grille)).round(1), 0
    )


def get_df():
    full_df = pd.read_excel(
        os.getenv("DATA_FOLDER")
        + "mobilite/extrait-Tableau_de_Bord_CTS_Valeurs 012023_ajout_qf_age.xlsx",
        sheet_name="QRD - Quantités",
    )
    full_df["ajustement_mensuel_num"] = full_df.ajustement_mensuel.astype("str").apply(
        lambda x: eval(str(x)) if x != "nan" else 1
    )
    compens_df = full_df[~full_df.Exclu.isna() * ~full_df.ajustement_mensuel.isna()][
        ["Titres", "quantité", "ajustement_mensuel_num"]
    ]
    compens_constant = sum(compens_df.quantité * compens_df.ajustement_mensuel_num)
    compens_constant

    df = full_df[full_df.Exclu.isna()]

    return df, compens_constant


def build_data(df, res_df, sample_count=1):
    count = int(sum(df.quantité))
    sample_ids = np.repeat(list(range(sample_count)), count)
    indiv_ids = np.tile(list(range(count)), sample_count)
    sample_qfrule = np.tile(np.repeat(df.QF, df.quantité), sample_count)
    titre_fichier = np.tile(np.repeat(df.Titres, df.quantité), sample_count)
    ajustement_mensuel_num = np.tile(
        np.repeat(df.ajustement_mensuel_num, df.quantité), sample_count
    )

    sample_individu_df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "famille_id": list(range(count * sample_count)),
            "agerule": np.tile(np.repeat(df.AGE, df.quantité), sample_count),
            "taux_incapacite": np.tile(
                np.repeat(np.where(df.Titres.str.contains("PMR"), 0.8, 0), df.quantité),
                sample_count,
            ),
            "eurometropole_strasbourg_tarification_solidaire_transport_quotient_familial_etudiant": 10000,
            "emeraude": np.tile(
                np.repeat(df.Titres == "Emeraude", df.quantité), sample_count
            ),
        }
    )
    determine_age(sample_individu_df)

    sample_famille_df = pd.DataFrame(
        {
            "qfrule": sample_qfrule,
        }
    )
    determine_qf(sample_famille_df)

    sample_menage_df = pd.DataFrame(
        {
            "eurometropole_strasbourg_tarification_solidaire_transport_eligibilite_geographique": np.ones(
                len(sample_individu_df)
            ),
        }
    )
    sample_foyerfiscaux_df = pd.DataFrame({})

    sample_individu_df["famille_role_index"] = 0
    sample_individu_df["foyer_fiscal_id"] = sample_individu_df.famille_id
    sample_individu_df["foyer_fiscal_role_index"] = 0
    sample_individu_df["menage_id"] = sample_individu_df.famille_id
    sample_individu_df["menage_role_index"] = 0

    sample_data = dict(
        input_data_frame_by_entity=dict(
            individu=sample_individu_df,
            famille=sample_famille_df,
            menage=sample_menage_df,
            foyer_fiscal=sample_foyerfiscaux_df,
        )
    )
    complement_df = pd.DataFrame(
        data={
            "sample_id": sample_ids,
            "individu_id": indiv_ids,
            "ajustement_mensuel_num": ajustement_mensuel_num,
            "titre_fichier": titre_fichier,
            "idx": np.tile(np.repeat(df.idx, df.quantité), sample_count),
            "pu_fichier": np.tile(
                np.repeat(res_df.pu_fichier, df.quantité), sample_count
            ),
            "pu_calc_base": np.tile(
                np.repeat(res_df.pu_calc, df.quantité), sample_count
            ),
            "tp_base": np.tile(np.repeat(res_df.tp, df.quantité), sample_count),
        }
    )

    return sample_data, complement_df


def compute_result(scenario, complement_df, recette_base, compens_constant):
    sample_calc = scenario.simulation.calculate(
        "eurometropole_strasbourg_tarification_transport", base_period
    )
    sample_reduit = scenario.simulation.calculate(
        "eurometropole_strasbourg_tarification_solidaire_transport_eligible_tarif_reduit",
        base_period,
    )

    sample_res = pd.DataFrame(
        data={
            "sample_id": complement_df.sample_id,
            "individu_id": complement_df.individu_id,
            "titre_fichier": complement_df.titre_fichier,
            "recettes": sample_calc / 1.1 * complement_df.ajustement_mensuel_num,
            "pu_calc": sample_calc,
            "pu_calc_ht": sample_calc / 1.1 * complement_df.ajustement_mensuel_num,
            "reduit": sample_reduit,
            "idx": complement_df.idx,
            "pu_fichier": complement_df.pu_fichier,
            "pu_calc_base": complement_df.pu_calc_base,
            "tp_base": complement_df.tp_base,
            "quantité": 12,
        }
    )
    sample_res["ecart"] = sample_res.pu_calc_ht - sample_res.pu_fichier
    sample_res["ok"] = sample_res.ecart.abs() < 1
    add_compensation(sample_res)

    sample_recette = sample_res[["sample_id", "recettes"]].groupby(by="sample_id").sum()
    sample_recette["equiv_tp"] = (
        sample_res[["sample_id", "compensation"]].groupby(by="sample_id").sum()
    )
    sample_recette["tp"] = sample_res[["sample_id", "tp"]].groupby(by="sample_id").sum()
    sample_recette["pertes"] = sample_recette.recettes - recette_base
    sample_recette["compens"] = -sample_recette.pertes / (
        sample_recette.equiv_tp + compens_constant
    )
    return (sample_res, sample_recette)


def get_results(tbs, sample_count=1, reform=None):
    df, compens_constant = get_df()
    rdf = pd.DataFrame(
        data={
            "pu_fichier": df.PU,
            "pu_calc": df.PU * 0,
            "tp": df.PU * 0,
        }
    )
    data, complement_df = build_data(df, rdf, sample_count)
    scenario = StrasbourgSurveyScenario(tbs, data=data)
    (res, recettes) = compute_result(scenario, complement_df, 0, compens_constant)
    field = "cout"
    res[field] = res.pu_calc_ht * 12
    count, value = extract(res, field, "quantité")

    row = ["Mobilité", "Transports en commun", count["mean"], count["count"], *value]

    if reform:
        reform_scenario = StrasbourgSurveyScenario(reform, data=data)
        (r_res, r_recettes) = compute_result(
            reform_scenario, complement_df, 0, compens_constant
        )
        r_res[field] = r_res.pu_calc_ht * 12
        r_count, r_value = extract(r_res, field, "quantité")
        row.extend(r_value)

    return pd.DataFrame([row], columns=result_index[0 : len(row)])
