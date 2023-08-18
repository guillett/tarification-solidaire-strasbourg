import sys

sys.path.append("../technique")
from utils import StrasbourgSurveyScenario, base_period, get_data, determine_qf
from results import result_index, extract

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


fields = {
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


def build_data(df, sample_count):
    coef_sans_resa = 1
    raw_df = pd.pivot_table(
        df,
        index=["N° FAM", "N° PER", "QF"],
        columns="REPAS",
        values="NOMBRE",
        fill_value=0,
        aggfunc=np.sum,
    )
    raw_df["strasbourg_metropole_nombre_repas_cantine"] = (
        raw_df["Standard avec résa"]
        + raw_df["Halal avec résa"]
        + raw_df["Sans Porc avec résa"]
        + coef_sans_resa
        * (
            raw_df["Standard sans résa"]
            + raw_df["Halal sans résa"]
            + raw_df["Sans Porc sans résa"]
        )
    )
    raw_df["strasbourg_metropole_nombre_repas_cantine_vegetarien"] = (
        raw_df["Végétarien avec résa"] + coef_sans_resa * raw_df["Végétarien sans résa"]
    )
    raw_df["strasbourg_metropole_nombre_repas_cantine_panier"] = raw_df[
        "Panier avec résa"
    ] + coef_sans_resa * (
        raw_df["Panier sans résa"] if "Panier sans résa" in raw_df else 0
    )
    raw_df["qfrule"] = ["QF==" + str(q) for (f, p, q) in raw_df.index]

    np.tile(df.QF.astype("str"), sample_count)

    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(len(raw_df) * sample_count)),
        }
    )
    for f in fields:
        fn = fields[f]["nombre"]
        individu_df[fn] = np.tile(raw_df[fn], sample_count)

    famille_df = pd.DataFrame(
        {
            "qfrule": np.tile(raw_df.qfrule, sample_count),
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

    sample_ids = np.repeat(list(range(sample_count)), len(raw_df))

    data = dict(
        input_data_frame_by_entity=dict(
            individu=individu_df,
            famille=famille_df,
            menage=menage_df,
            foyer_fiscal=foyerfiscaux_df,
        )
    )
    return data, sample_ids


def get_results(tbs, sample_count=2, reform=None):
    df = get_df()
    data, sample_ids = build_data(df, sample_count)
    rows = []

    scenario = StrasbourgSurveyScenario(tbs, data=data)
    if reform:
        r_scenario = StrasbourgSurveyScenario(reform, data=data)
    res = pd.DataFrame({"sample_id": sample_ids})
    for n in fields:
        row = ["DEE", n]
        prix_field = "prix_" + n
        nombre_field = "nombre_" + n
        res[prix_field] = scenario.simulation.calculate(fields[n]["cout"], base_period)
        res[nombre_field] = scenario.simulation.calculate(
            fields[n]["nombre"], base_period
        )
        count, value = extract(res, prix_field, nombre_field)
        row.extend([count["mean"], count["count"]])
        row.extend(value)

        if reform:
            prix_field = "r_prix_" + n
            nombre_field = "r_nombre_" + n
            res[prix_field] = r_scenario.simulation.calculate(
                fields[n]["cout"], base_period
            )
            res[nombre_field] = r_scenario.simulation.calculate(
                fields[n]["nombre"], base_period
            )
            count, value = extract(res, prix_field, nombre_field)
            row.extend(value)

        rows.append(row)

    return pd.DataFrame(rows, columns=result_index[0 : len(rows[0])])
