from dotenv import load_dotenv

load_dotenv()
import os
import sys

sys.path.append("../technique")
from utils import (
    StrasbourgSurveyScenario,
    base_period,
    get_data,
    determine_qf_avec_enfants,
)

from scenario import build_reform

from openfisca_france import CountryTaxBenefitSystem

from results import result_index, extract


import cantine
import activite
import pandas as pd


import datetime


def get_results(tbs, sample_count=2, reform=None, source="caf"):
    if source != "caf":
        raise Exception("TODO")
    (crecap, cdfs) = cantine.get_results(tbs, sample_count, reform)
    (arecap, adfs) = activite.get_results(tbs, sample_count, reform)

    return pd.concat([crecap, arecap]), [*cdfs, *adfs]


of_v = pd.DataFrame(
    {
        "LIB_SERVICE": [
            "AL Vacances scolaires - Présence demi journée",
            "Halal avec résa",
            "Standard avec résa",
            "AL Vacances scolaires - Séquence méridienne (Repas)",
            "Végétarien sans résa",
            "APM - Présence soir",
            "Sans Porc avec résa",
            "Standard sans résa",
            "AL Mercredi - Séquence méridienne (Repas)",
            "Alerte Météo",
            "Sans Porc sans résa",
            "AL Mercredi - Présence demi journée",
            "Végétarien avec résa",
            "AL Vacances scolaires  - Présence journée",
            "Halal sans résa",
            "APM - Présence matin",
            "AL Mercredi - Pique-nique",
            "Panier avec résa",
            "AL Vacances scolaires - Pique-nique",
            "AL Mercredi  - Présence journée",
            "Panier sans résa",
        ],
        "openfisca": [
            "strasbourg_periscolaire_loisirs_demi_journee_prix",
            "strasbourg_metropole_cout_cantine_individu",
            "strasbourg_metropole_cout_cantine_individu",
            "strasbourg_periscolaire_loisirs_repas_cout",
            "strasbourg_metropole_cout_cantine_individu_repas_vegetarien",
            "strasbourg_periscolaire_maternelle_cout",
            "strasbourg_metropole_cout_cantine_individu",
            "strasbourg_metropole_cout_cantine_individu",
            "strasbourg_periscolaire_loisirs_repas_cout",
            "TODO",  # Alerte Météo
            "strasbourg_metropole_cout_cantine_individu",
            "strasbourg_periscolaire_loisirs_demi_journee_prix",
            "strasbourg_metropole_cout_cantine_individu_repas_vegetarien",
            "strasbourg_periscolaire_loisirs_journee_cout",
            "strasbourg_metropole_cout_cantine_individu",
            "strasbourg_periscolaire_maternelle_matin_ou_soir_cout",
            "strasbourg_periscolaire_loisirs_panier_cout",
            "strasbourg_metropole_cout_cantine_individu_repas_panier",
            "strasbourg_periscolaire_loisirs_panier_cout",
            "strasbourg_periscolaire_loisirs_journee_cout",
            "strasbourg_metropole_cout_cantine_individu_repas_panier",
        ],
    }
)


def get_df():
    raw_df = pd.read_csv(
        #        f"{os.getenv('DATA_FOLDER')}dee/DEE_v3_20231003_QFCAFQFEMS.csv",
        f"{os.getenv('DATA_FOLDER')}dee/DEE_calcul_anonym_decode_V2.csv",
        delimiter=";",
        encoding="windows-1250",
        index_col=0,
        decimal=",",
    )
    df = raw_df.merge(of_v, on="LIB_SERVICE", how="left")
    assert not df.openfisca.isna().any()
    df[df.openfisca == "strasbourg_periscolaire_maternelle_cout"].NB = 1
    return df


meta = {
    "strasbourg_metropole_cout_cantine_individu": (
        "Repas standard",
        "strasbourg_metropole_nombre_repas_cantine",
        "strasbourg_metropole_tarification_cantine",
    ),
    "strasbourg_periscolaire_maternelle_cout": (
        "APM",
        "strasbourg_periscolaire_maternelle_nombre",
        "strasbourg_periscolaire_maternelle_prix",
    ),
    "strasbourg_metropole_cout_cantine_individu_repas_vegetarien": (
        "Repas végétarien",
        "strasbourg_metropole_nombre_repas_cantine_vegetarien",
        "strasbourg_metropole_tarification_cantine_vegetarien",
    ),
    "strasbourg_periscolaire_loisirs_journee_cout": (
        "AL_J",
        "strasbourg_periscolaire_loisirs_journee_nombre",
        "strasbourg_periscolaire_loisirs_journee_prix",
    ),
    "strasbourg_periscolaire_loisirs_repas_cout": (
        "AL_R",
        "strasbourg_periscolaire_loisirs_repas_nombre",
        "strasbourg_periscolaire_loisirs_repas_prix",
    ),
    "strasbourg_metropole_cout_cantine_individu_repas_panier": (
        "Repas panier",
        "strasbourg_metropole_nombre_repas_cantine_panier",
        "strasbourg_metropole_tarification_cantine_panier",
    ),
    "strasbourg_periscolaire_loisirs_panier_cout": (
        "AL_P",
        "strasbourg_periscolaire_loisirs_panier_nombre",
        "strasbourg_periscolaire_loisirs_panier_prix",
    ),
    "strasbourg_periscolaire_loisirs_demi_journee_prix": (
        "AL_1/2J",
        "strasbourg_periscolaire_loisirs_demi_journee_nombre",
        "strasbourg_periscolaire_loisirs_demi_journee_prix",
    ),
    "strasbourg_periscolaire_maternelle_matin_ou_soir_cout": (
        "APM_1/2",
        "strasbourg_periscolaire_maternelle_matin_ou_soir_nombre",
        "strasbourg_periscolaire_maternelle_matin_ou_soir_prix",
    ),
}


def build_data(openfisca_quantite_field, df):
    qf_caf_field = "MONTANT.QF.CNAF"
    qf_fiscal_field = "QFEMS"
    quantite_field = "NB"

    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(len(df))),
            openfisca_quantite_field: df[quantite_field],
        }
    )
    famille_df = pd.DataFrame(
        {
            "qf_caf": df[qf_caf_field],
            "qf_fiscal": df[qf_fiscal_field],
            "sample_id": 0,
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


def get_results11(tbs, sample_count=1, reform=None):
    df = get_df()
    rows = []
    dfs = []

    for field_cout, gdf in df.groupby("openfisca"):
        if field_cout == "TODO" or "maternelle" in field_cout:
            continue
        (name, nb_field, prix_field) = meta[field_cout]
        data = build_data(nb_field, gdf)
        scenario = StrasbourgSurveyScenario(tbs, data=data)
        cout = scenario.simulation.calculate(field_cout, base_period)
        prix = scenario.simulation.calculate(prix_field, base_period)
        nb = scenario.simulation.calculate(nb_field, base_period)

        res = pd.DataFrame(
            {
                "sample_id": data["input_data_frame_by_entity"]["famille"][
                    "sample_id"
                ].values,
                "qf_caf": data["input_data_frame_by_entity"]["famille"][
                    "qf_caf"
                ].values,
                "qf_fiscal": data["input_data_frame_by_entity"]["famille"][
                    "qf_fiscal"
                ].values,
                "prix_unitaire": prix,
                "prix": cout,
                "nb": nb,
            }
        )

        nbt = nb.sum()
        ct = cout.sum()
        row = ["DEE", name, nbt, 1, ct, 0, ct, ct, ct]
        if reform:
            scenario = StrasbourgSurveyScenario(reform, data=data)
            cout = scenario.simulation.calculate(field_cout, base_period)
            prix = scenario.simulation.calculate(prix_field, base_period)
            nb = scenario.simulation.calculate(nb_field, base_period)
            res["prix_unitaire_r"] = prix
            res["prix_r"] = cout
            res["nb_r"] = nb
            nbt = nb.sum()
            ct = cout.sum()
            row.extend([ct, 0, ct, ct, ct])

        rows.append(row)
        dfs.append((name, res))

    return pd.DataFrame(rows, columns=result_index[0 : len(rows[0])]), dfs
