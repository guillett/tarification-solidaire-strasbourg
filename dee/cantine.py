import sys

sys.path.append("../technique")
from utils import *

import numpy as np
import pandas as pd


def get(filename):
    return pd.read_excel(
        filename,
        usecols=["N° FAM", "QF", "N° PER", "REPAS", "MOIS", "NOMBRE"],
        dtype={
            "Activite": "category",
            "N° FAM": np.int64.__name__,
            "QF": np.int64.__name__,
            "N° PER": np.int64.__name__,
            "MOIS": np.datetime64.__name__,
            # "REPAS": 'category',
            "NOMBRE": np.int64.__name__,
        },
    )


def get_df():
    return (
        get_data(
            "/home/thomas/Nextcloud/CodeursEnLiberte/EMS/dee/Données cantines scolaires 2021.xlsx",
            get,
        )
        .groupby(["N° FAM", "QF", "N° PER", "REPAS"])
        .sum(numeric_only=True)
        .reset_index()
    )


def get_results(tbs):
    df = get_df()

    coef_sans_resa = 1
    raw_df = pd.pivot_table(
        df,
        index=["N° FAM", "N° PER", "QF"],
        columns="REPAS",
        values="NOMBRE",
        fill_value=0,
        aggfunc=np.sum,
    )
    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(len(raw_df))),
            "strasbourg_metropole_nombre_repas_cantine": (
                raw_df["Standard avec résa"]
                + raw_df["Halal avec résa"]
                + raw_df["Sans Porc avec résa"]
                + coef_sans_resa
                * (
                    raw_df["Standard sans résa"]
                    + raw_df["Halal sans résa"]
                    + raw_df["Sans Porc sans résa"]
                )
            ),
            "strasbourg_metropole_nombre_repas_cantine_vegetarien": (
                raw_df["Végétarien avec résa"]
                + coef_sans_resa * raw_df["Végétarien sans résa"]
            ),
            "strasbourg_metropole_nombre_repas_cantine_panier": (
                raw_df["Panier avec résa"]
                + coef_sans_resa
                * (raw_df["Panier sans résa"] if "Panier sans résa" in raw_df else 0)
            ),
        }
    )
    famille_df = pd.DataFrame(
        {
            "strasbourg_metropole_quotient_familial": [
                1.0 * q for (f, p, q) in raw_df.index
            ],
        }
    )
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

    var = {
        "Repas standard": {
            "cout": "strasbourg_metropole_cout_cantine_individu",
            "nombre": "strasbourg_metropole_nombre_repas_cantine",
        },
        "Repas végétarien": {
            "cout": "strasbourg_metropole_cout_cantine_individu_repas_vegetarien",
            "nombre": "strasbourg_metropole_nombre_repas_cantine_vegetarien",
        },
        "Repas panier": {
            "cout": "strasbourg_metropole_cout_cantine_individu_repas_panier",
            "nombre": "strasbourg_metropole_nombre_repas_cantine_panier",
        },
    }

    res_cout = pd.DataFrame(
        data={
            n: scenario.simulation.calculate(var[n]["cout"], base_period) for n in var
        }
    )

    res_nombre = pd.DataFrame(
        data={
            n: scenario.simulation.calculate(var[n]["nombre"], base_period) for n in var
        }
    )

    return pd.DataFrame(
        data={
            "Direction": "DEE",
            "Recettes": res_cout.sum(),
            "Quantité": res_nombre.sum(),
        }
    ).reset_index(names="Service")
