import sys

sys.path.append("../technique")
from utils import determine_qf, StrasbourgSurveyScenario, base_period, get_data

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


def build_data(df):
    individu_df = pd.DataFrame(
        {
            "famille_id": list(range(len(df))),
        }
    )
    famille_df = pd.DataFrame(
        {
            "qfrule": "QF==" + df.QF.astype("str"),
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


def get_results(tbs):
    df_apm_usage, df_al = get_dfs()

    data_apm = build_data(df_apm_usage)
    scenario_apm = StrasbourgSurveyScenario(tbs, data=data_apm)
    prix = scenario_apm.simulation.calculate(
        "strasbourg_periscolaire_maternelle_prix", base_period
    )
    total_apm = (prix * df_apm_usage.MOIS).sum()
    total_apm_count = (1 * df_apm_usage.MOIS).sum()

    data_al = build_data(df_al)
    scenario_al = StrasbourgSurveyScenario(tbs, data=data_al)
    res_al = pd.DataFrame(
        data={
            v: scenario_al.simulation.calculate(al_fields[v], base_period)
            for v in al_fields
        }
    )
    idx, cols = pd.factorize(df_al.SERVICE2)
    df_al["PRIX"] = res_al.reindex(cols, axis=1).to_numpy()[np.arange(len(res_al)), idx]
    df_al["Recettes"] = df_al.PRIX * df_al.NOMBRE
    df_al["Quantité"] = 1 * df_al.NOMBRE
    res = df_al[["Recettes", "Quantité", "SERVICE2"]].groupby("SERVICE2").sum()

    res.loc["APM"] = [total_apm, total_apm_count]
    res.index.name = "Service"

    res["Direction"] = "DEE"
    return res.sort_values("Recettes", ascending=False).reset_index()
