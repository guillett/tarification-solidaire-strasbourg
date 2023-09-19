import sys

sys.path.append("../technique")
from utils import determine_qf, StrasbourgSurveyScenario, base_period, get_data
from results import result_index, extract

import numpy as np
from openfisca_france import CountryTaxBenefitSystem
import pandas as pd


def get(file):
    sheet_name = "2022-2023"
    return pd.read_excel(
        file,
        sheet_name=sheet_name,
    )


def get_dfs():
    df = get_data(
        "/home/thomas/Nextcloud/CodeursEnLiberte/EMS/dee/DEE_20230719_Données activités QF.xlsx",
        get,
    )
    df["SERVICE"] = df.Activite + "_" + df.UNITE
    df["SERVICE2"] = df.Activite.str.replace("AL .*", "AL", regex=True) + "_" + df.UNITE

    # Il semblerait que les données soient de la fréquentation et donc
    # qu'il faille faire le lien avec les services/tarifications
    df_apm = df[df.Activite == "APM"].pivot(
        index=["N° FAM", "QF", "N° PER", "MOIS"], columns="UNITE", values="NOMBRE"
    )
    df_apm_base = df_apm.reset_index()
    df_apm_base["USE"] = True
    df_apm_mensuel = (
        df_apm_base[["N° FAM", "QF", "N° PER", "MOIS", "USE"]]
        .groupby(["N° FAM", "QF", "N° PER", "MOIS"])
        .count()
    )
    df_apm_usage = (
        df_apm_mensuel.reset_index()[["N° FAM", "QF", "N° PER", "MOIS"]]
        .groupby(["N° FAM", "QF", "N° PER"])
        .count()
        .reset_index()
    )

    df_al = (
        df[df.SERVICE2.str.contains("AL_")][
            ["N° FAM", "QF", "N° PER", "SERVICE2", "NOMBRE"]
        ]
        .groupby(["N° FAM", "QF", "N° PER", "SERVICE2"])
        .sum()
        .reset_index()
    )

    return df_apm_usage, df_al


def build_data(df, sample_count):
    sample_ids = np.repeat(list(range(sample_count)), len(df))
    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(len(df) * sample_count)),
        }
    )
    famille_df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "qfrule": "QF==" + np.tile(df.QF.astype("str"), sample_count),
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

    return dict(
        input_data_frame_by_entity=dict(
            individu=individu_df,
            famille=famille_df,
            menage=menage_df,
            foyer_fiscal=foyerfiscaux_df,
        )
    )


al_fields = {
    "AL_J": "strasbourg_periscolaire_loisirs_journee_prix",
    "AL_1/2J": "strasbourg_periscolaire_loisirs_demi_journee_prix",
    "AL_R": "strasbourg_periscolaire_loisirs_repas_prix",
    "AL_P": "strasbourg_periscolaire_loisirs_panier_prix",
}


def get_results(tbs, sample_count=1, reform=None):
    df_apm_usage, df_al = get_dfs()
    rows = []
    dfs = []

    data_apm = build_data(df_apm_usage, sample_count)
    apm_sample_ids = np.repeat(list(range(sample_count)), len(df_apm_usage))
    scenario_apm = StrasbourgSurveyScenario(tbs, data=data_apm)
    res_apm = pd.DataFrame(
        {
            "sample_id": data_apm["input_data_frame_by_entity"]["famille"].sample_id,
            "qf_caf": data_apm["input_data_frame_by_entity"]["famille"].qf_caf,
            "qf_fiscal": data_apm["input_data_frame_by_entity"]["famille"].qf_fiscal,
            "quantité": np.tile(df_apm_usage.MOIS, sample_count),
        }
    )
    dfs.append(("APM", res_apm))

    def compute_apm(s, res, field):
        prix = s.simulation.calculate(
            "strasbourg_periscolaire_maternelle_prix", base_period
        )
        res[field] = prix
        res["cout"] = res[field] * res.quantité

    compute_apm(scenario_apm, res_apm, "prix")

    row = ["DEE", "APM"]
    apm_count, apm_value = extract(res_apm, "cout", "quantité")
    row.extend([apm_count["mean"], apm_count["count"]])
    row.extend(apm_value)
    if reform:
        r_scenario_apm = StrasbourgSurveyScenario(reform, data=data_apm)
        compute_apm(r_scenario_apm, res_apm, "prix_r")
        _, r_apm_value = extract(res_apm, "cout", "quantité")
        row.extend(r_apm_value)

    rows.append(row)

    data_al = build_data(df_al, sample_count)
    scenario_al = StrasbourgSurveyScenario(tbs, data=data_al)
    res_al = pd.DataFrame(
        data={
            "sample_id": data_al["input_data_frame_by_entity"]["famille"].sample_id,
            "quantité": np.tile(df_al.NOMBRE, sample_count),
            "service": np.tile(df_al.SERVICE2, sample_count),
        }
    )
    for v in al_fields:
        res_al[v] = scenario_al.simulation.calculate(al_fields[v], base_period)
    idx, cols = pd.factorize(res_al.service)
    res_al["prix"] = res_al.reindex(cols, axis=1).to_numpy()[
        np.arange(len(res_al)), idx
    ]
    res_al["cout"] = res_al.prix * res_al.quantité
    if reform:
        r_scenario_al = StrasbourgSurveyScenario(reform, data=data_al)
        for v in al_fields:
            res_al[v + "_r"] = r_scenario_al.simulation.calculate(
                al_fields[v], base_period
            )
            r_idx, r_cols = pd.factorize(res_al.service + "_r")
            res_al["prix_r"] = res_al.reindex(r_cols, axis=1).to_numpy()[
                np.arange(len(res_al)), r_idx
            ]
            res_al["cout_r"] = res_al.prix_r * res_al.quantité

    for n, df in res_al.groupby("service"):
        row = ["DEE", n]
        count, value = extract(df, "cout", "quantité")
        row.extend([count["mean"], count["count"]])
        row.extend(value)
        if reform:
            _, r_value = extract(df, "cout_r", "quantité")
            row.extend(r_value)
        rows.append(row)

    return pd.DataFrame(rows, columns=result_index[0 : len(rows[0])]), dfs
