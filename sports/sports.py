import sys

sys.path.append("../technique")
from utils import *
import numpy as np
import pandas as pd


def get_df():
    return pd.read_excel(
        "/home/thomas/Nextcloud/CodeursEnLiberte/EMS/sports/extractions_denombrement.ods"
    )


fields = {
    "entrée unitaire": {
        "categorie": "entrée unitaire",
        "champ_pu": "Pu entrée unitaire",
        "openfisca_input_variable": "strasbourg_piscine_entree_unitaire",
        "openfisca_output_variable": "strasbourg_piscine_entree_unitaire_prix",
    },
    "10 entrées": {
        "categorie": "10 entrées",
        "champ_pu": "Pu 10 entrées",
        "openfisca_input_variable": "strasbourg_piscine_10_entrees",
        "openfisca_output_variable": "strasbourg_piscine_10_entrees_prix",
    },
    "abo_annuel": {
        "categorie": "abo_annuel",
        "champ_pu": "pu abo_annuel",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_annuel",
        "openfisca_output_variable": "strasbourg_piscine_abonnement_annuel_prix",
    },
    "abo_annuel_ce": {
        "categorie": "abo_annuel_ce",
        "champ_pu": "pu abo_annuel_ce",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_abonnement_ce_prix",
    },
    "5 entrées ce": {
        "categorie": "5 entrées ce",
        "champ_pu": "pu 5 entrées ce",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_5_entrees_ce_prix",
    },
    "cycle": {
        "categorie": "cycle",
        "champ_pu": "pu cycle",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_cycle_prix",
    },
    "stage été": {
        "categorie": "stage été",
        "champ_pu": "pu stage été",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_stage_ete_prix",
    },
    "stage vacances": {
        "categorie": "stage vacances",
        "champ_pu": "pu stage vacances",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_stage_vacances_prix",
    },
    "stage 5 séances": {
        "categorie": "stage 5 séances",
        "champ_pu": "pu stage 5 séances",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_stage_5_seances_prix",
    },
    "patinoire entree unitaire": {
        "categorie": "patinoire entree unitaire",
        "champ_pu": "pu patinoire entree unitaire",
        "openfisca_input_variable": "strasbourg_patinoire_entree_unitaire",
        "openfisca_output_variable": "strasbourg_patinoire_entree_unitaire_prix",
    },
    "patinoire 10 entrees": {
        "categorie": "patinoire 10 entrees",
        "champ_pu": "pu patinoire 10 entrees",
        "openfisca_input_variable": "strasbourg_patinoire_10_entrees",
        "openfisca_output_variable": "strasbourg_patinoire_10_entrees_prix",
    },
    "patinoire 5 entrees ce": {
        "categorie": "patinoire 5 entrees ce",
        "champ_pu": "pu patinoire 5 entrees ce",
        "openfisca_input_variable": "strasbourg_patinoire_5_entrees_ce",
        "openfisca_output_variable": "strasbourg_patinoire_5_entrees_ce_prix",
    },
}


def compute(tbs, df, categorie):
    champ_pu = fields[categorie]["champ_pu"]
    openfisca_input_variable = fields[categorie]["openfisca_input_variable"]
    openfisca_output_variable = fields[categorie]["openfisca_output_variable"]

    product_df = df[~df[categorie].isna()]
    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(len(product_df))),
            "agerule": product_df.age,
            "taux_incapacite": np.where(
                product_df.qfrule.str.contains("HANDICAP"), 0.8, 0
            ),
            "ass": product_df.qfrule.str.contains("ASS"),
            "evasion": product_df.qfrule.str.contains("EVASION"),
            "cada": product_df.qfrule.str.contains("CADA"),
            "etudiant": product_df.qfrule.str.contains("ETU"),
            openfisca_input_variable: product_df.quantité,
        }
    )
    determine_age(individu_df)

    famille_df = pd.DataFrame(
        {
            "qfrule": product_df.qfrule,
            "rsa": product_df.qfrule.str.contains("RSA"),
            "agent_ems": product_df.qfrule.str.contains("CUS")
            + product_df.qfrule.str.contains("EMS"),
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
            "prestation": product_df.prestation,
            "qfrule": product_df.qfrule,
            "qf_caf": famille_df.qf_caf,
            "age": individu_df.age,
            "res": (prix - product_df[champ_pu]).abs() < 0.001,
            "prix_input": product_df[champ_pu],
            "prix_output": prix,
            "quantité": product_df.quantité,
        }
    )
    return res_prix


def get_results(tbs):
    df = get_df()

    get_total = lambda r: sum(r.prix_output * r.quantité)
    results = [compute(tbs, df, v) for v in fields]

    return pd.DataFrame(
        data={
            "Direction": "Sport",
            "Service": [v for v in fields],
            "Recettes": [get_total(r) for r in results],
            "Quantité": [r.quantité.sum() for r in results],
        }
    )
