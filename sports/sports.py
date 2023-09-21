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
    return pd.read_excel(
        f"{os.getenv('DATA_FOLDER')}sports/extractions_denombrement.ods"
    )


fields = {
    "entrée unitaire": {
        "categorie": "entrée unitaire",
        "champ_pu": "Pu entrée unitaire",
        "openfisca_input_variable": "strasbourg_piscine_entree_unitaire",
        "openfisca_output_variable": "strasbourg_piscine_entree_unitaire_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine.entree_unitaire.bareme_qf,
    },
    "10 entrées": {
        "categorie": "10 entrées",
        "champ_pu": "Pu 10 entrées",
        "openfisca_input_variable": "strasbourg_piscine_10_entrees",
        "openfisca_output_variable": "strasbourg_piscine_10_entrees_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine._10_entrees.bareme_qf,
    },
    "abonnement annuel": {
        "categorie": "abonnement annuel",
        "champ_pu": "pu abonnement annuel",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_annuel",
        "openfisca_output_variable": "strasbourg_piscine_abonnement_annuel_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine.abonnement_annuel.bareme,
    },
    # "abo_annuel_été": {
    #     "categorie": "abo_annuel_été",
    #     "champ_pu": "pu abo_annuel",
    #     "openfisca_input_variable": "strasbourg_piscine_abonnement_annuel",
    #     "openfisca_output_variable": "strasbourg_piscine_abonnement_ete_prix",
    #     "bareme": lambda p: p.communes.strasbourg.piscine.abonnement_ete,
    # },
    "abonnement annuel CE": {
        "categorie": "abonnement annuel CE",
        "champ_pu": "pu abonnement annuel CE",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_abonnement_ce_prix",
        "bareme": None,
    },
    "5 entrées CE": {
        "categorie": "5 entrées CE",
        "champ_pu": "pu 5 entrées CE",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_5_entrees_ce_prix",
        "bareme": None,
    },
    "cycle": {
        "categorie": "cycle",
        "champ_pu": "pu cycle",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_cycle_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine.cycle.bareme,
    },
    "cycle2": {
        "categorie": "cycle2",
        "champ_pu": "pu cycle2",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_cycle2_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine.cycle.bareme,
    },
    "stage été": {
        "categorie": "stage été",
        "champ_pu": "pu stage été",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_stage_ete_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine.stage_ete.bareme,
    },
    "stage vacances": {
        "categorie": "stage vacances",
        "champ_pu": "pu stage vacances",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_stage_vacances_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine.stage_vacances.bareme,
    },
    "stage 5 séances": {
        "categorie": "stage 5 séances",
        "champ_pu": "pu stage 5 séances",
        "openfisca_input_variable": "strasbourg_piscine_abonnement_ce",
        "openfisca_output_variable": "strasbourg_piscine_stage_5_seances_prix",
        "bareme": lambda p: p.communes.strasbourg.piscine.stage_5_seances.bareme,
    },
    "patinoire entrée unitaire": {
        "categorie": "patinoire entrée unitaire",
        "champ_pu": "pu patinoire entrée unitaire",
        "openfisca_input_variable": "strasbourg_patinoire_entree_unitaire",
        "openfisca_output_variable": "strasbourg_patinoire_entree_unitaire_prix",
        "bareme": lambda p: p.communes.strasbourg.patinoire.entree_unitaire.bareme_qf,
    },
    "patinoire 10 entrées": {
        "categorie": "patinoire 10 entrées",
        "champ_pu": "pu patinoire 10 entrées",
        "openfisca_input_variable": "strasbourg_patinoire_10_entrees",
        "openfisca_output_variable": "strasbourg_patinoire_10_entrees_prix",
        "bareme": lambda p: p.communes.strasbourg.patinoire._10_entrees.bareme_qf,
    },
    "patinoire 5 entrées CE": {
        "categorie": "patinoire 5 entrées CE",
        "champ_pu": "pu patinoire 5 entrées CE",
        "openfisca_input_variable": "strasbourg_patinoire_5_entrees_ce",
        "openfisca_output_variable": "strasbourg_patinoire_5_entrees_ce_prix",
        "bareme": None,
    },
}


def build_data(df, categorie, sample_count=1):
    champ_pu = fields[categorie]["champ_pu"]
    openfisca_input_variable = fields[categorie]["openfisca_input_variable"]

    product_df = df[~df[categorie].isna()]
    sample_ids = np.repeat(list(range(sample_count)), product_df.quantité.sum())
    inc = lambda s: np.tile(np.repeat(s, product_df.quantité), sample_count)
    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(product_df.quantité.sum() * sample_count)),
            "agerule": inc(product_df.age),
            "taux_incapacite": inc(
                np.where(product_df.qfrule.str.contains("HANDICAP"), 0.8, 0)
            ),
            "ass": inc(product_df.qfrule.str.contains("ASS")),
            "evasion": inc(product_df.qfrule.str.contains("EVASION")),
            "cada": inc(product_df.qfrule.str.contains("CADA")),
            "etudiant": inc(product_df.qfrule.str.contains("ETU")),
            openfisca_input_variable: inc(product_df.quantité),
        }
    )
    determine_age(individu_df)

    famille_df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "qfrule": inc(product_df.qfrule),
            "rsa": inc(product_df.qfrule.str.contains("RSA")),
            "agent_ems": inc(
                product_df.qfrule.str.contains("CUS")
                + product_df.qfrule.str.contains("EMS")
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

    res = pd.DataFrame(
        data={
            "sample_id": sample_ids,
            "individu_id": individu_df.famille_id,
            "prestation": inc(product_df.prestation),
            "qfrule": inc(product_df.qfrule),
            "qf_caf": famille_df.qf_caf,
            "qf_fiscal": famille_df.qf_fiscal,
            "agent_ems": famille_df.agent_ems,
            "age": individu_df.age,
            "prix_input": inc(product_df[champ_pu]),
            "quantité": 1,
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
        res,
    )


def compute(tbs, data, res, openfisca_output_variable, suffix=""):
    scenario = StrasbourgSurveyScenario(tbs, data=data)
    prix = scenario.simulation.calculate(openfisca_output_variable, base_period)
    prix_field = "prix" + suffix
    res[prix_field] = prix
    res["res" + suffix] = (res[prix_field] - res.prix_input).abs() < 0.001
    return res


def get_results(tbs, sample_count=1, reform=None, single=None):
    df = get_df()

    get_total = lambda r: sum(r.prix * r.quantité)
    rows = []
    dfs = []
    for v in fields:
        if single and v != single:
            continue
        data, res = build_data(df, v, sample_count)
        openfisca_output_variable = fields[v]["openfisca_output_variable"]
        compute(tbs, data, res, openfisca_output_variable)

        count, value = extract(res, "prix")
        row = ["Sport", v]
        row.extend([count["mean"], count["count"]])
        row.extend(value)
        if reform:
            compute(reform, data, res, openfisca_output_variable, "_r")
            _, value = extract(res, "prix_r")
            row.extend(value)
        rows.append(row)
        dfs.append((v, res))

    return pd.DataFrame(rows, columns=result_index[0 : len(rows[0])]), dfs
