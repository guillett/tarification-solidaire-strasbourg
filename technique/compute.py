from dotenv import load_dotenv

load_dotenv()
import os
import pandas as pd
import numpy as np

from openfisca_core import periods, parameters
from openfisca_core.model_api import Reform
from openfisca_survey_manager.scenarios import AbstractSurveyScenario
from openfisca_france import CountryTaxBenefitSystem

from grist import api
from scenario import StrasbourgSurveyScenario, base_period
from utils import *


class mobiliteGristSimulationReform(Reform):
    name = "Fusionne les trois premières tranches"

    def __init__(self, tbs, steps):
        self.steps = steps
        super().__init__(tbs)

    def apply(self):
        def modify_parameters_grist(local_parameters):
            period = base_period
            reduit = []
            classique = []

            for tranche in self.steps:
                (qf, r, c) = tranche
                reduit.append(
                    parameters.ParameterScaleBracket(
                        data={
                            "threshold": {period: {"value": qf}},
                            "amount": {period: {"value": r}},
                        }
                    )
                )
                classique.append(
                    parameters.ParameterScaleBracket(
                        data={
                            "threshold": {period: {"value": qf}},
                            "amount": {period: {"value": c}},
                        }
                    )
                )
            local_parameters.metropoles.strasbourg.tarification_solidaire.bareme_reduit.brackets = (
                reduit
            )
            local_parameters.metropoles.strasbourg.tarification_solidaire.bareme.brackets = (
                classique
            )
            return local_parameters

        self.modify_parameters(modifier_function=modify_parameters_grist)


full_df = pd.read_excel(
    os.getenv("DATA_FOLDER")
    + "mobilite/extrait-Tableau_de_Bord_CTS_Valeurs 012023_ajout_qf_age.xlsx",
    sheet_name="QRD - Quantités",
)
df = full_df[~full_df.Exclu.notna()]

base = CountryTaxBenefitSystem()
base.load_extension("openfisca_france_local")


def compute(scenario, qf):
    scale_data = api.fetch_table("Baremes_transports")
    scale_data.sort(key=lambda i: i.QF)
    has_reduit = None
    try:
        getattr(scale_data[0], f"{scenario}_reduit")
        has_reduit = True
    except AttributeError as e:
        has_reduit = False

    steps = []
    for s in scale_data:
        if getattr(s, scenario):
            steps.append(
                [
                    s.QF - 1,
                    getattr(s, f"{scenario}_reduit")
                    if has_reduit
                    else getattr(s, scenario),
                    getattr(s, scenario),
                ]
            )

    r = mobiliteGristSimulationReform(base, steps)

    count = int(sum(df.quantité))
    sample_count = 40
    sample_ids = np.repeat(list(range(sample_count)), count)
    sample_qfrule = np.tile(np.repeat(df.QF, df.quantité), sample_count)
    sample_individu_df = pd.DataFrame(
        {
            "famille_id": list(range(count * sample_count)),
            "agerule": np.tile(np.repeat(df.AGE, df.quantité), sample_count),
            "taux_incapacite": np.tile(
                np.repeat(np.where(df.Titres.str.contains("PMR"), 0.8, 0), df.quantité),
                sample_count,
            ),
            # Évite le calcul de cette branche inutilisée dans notre contexte
            # Sans cela, étant donnée la taille importante du vecteur, le serveur timeout.
            "eurometropole_strasbourg_tarification_solidaire_transport_quotient_familial_etudiant": 10000,
        }
    )
    determine_age(sample_individu_df)

    sample_famille_df = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "qfrule": sample_qfrule,
        }
    )
    determine_qf(sample_famille_df)

    sample_menage_df = pd.DataFrame(
        {
            "eurometropole_strasbourg_tarification_solidaire_transport_eligibilite_geographique": np.ones(
                count * sample_count
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

    reform_scenario = StrasbourgSurveyScenario(r, data=sample_data)
    df_reform = pd.DataFrame(
        data={
            "sample_id": sample_ids,
            "qf": reform_scenario.simulation.calculate(
                "eurometropole_strasbourg_tarification_solidaire_transport_quotient_familial",
                base_period,
            ),
            "recettes": reform_scenario.simulation.calculate(
                "eurometropole_strasbourg_tarification_transport", base_period
            ),
            "prix": reform_scenario.simulation.calculate(
                "eurometropole_strasbourg_tarification_transport", base_period
            ),
        }
    )
    recettes = (
        df_reform[["sample_id", "recettes"]].groupby(by="sample_id").sum().describe()
    )
    return (recettes, steps)
