import numpy as np
import pandas as pd

import cProfile

import time
import tempfile

profile = cProfile.Profile()
profile.enable()


df = pd.read_excel(
    "/home/thomas/Nextcloud/CodeursEnLiberte/EMS/sports/extractions_denombrement.ods"
)

entree_unitaire = df[df["entrée unitaire"] == "x"]

from openfisca_survey_manager.scenarios import AbstractSurveyScenario
from openfisca_france import CountryTaxBenefitSystem
from openfisca_france.model.base import Famille, FoyerFiscal, Menage
from openfisca_core import periods

base_year = "2023"

base = CountryTaxBenefitSystem()
base.load_extension("openfisca_france_local")


class StrasbourgSurveyScenario(AbstractSurveyScenario):
    def __init__(
        self,
        data=None,
    ):
        super(StrasbourgSurveyScenario, self).__init__()

        self.year = base_year

        if "input_data_frame_by_entity" in data:
            period = periods.period(self.year)
            dataframe_variables = set()
            for entity_dataframe in data["input_data_frame_by_entity"].values():
                if not isinstance(entity_dataframe, pd.DataFrame):
                    continue
                dataframe_variables = dataframe_variables.union(
                    set(entity_dataframe.columns)
                )
            self.used_as_input_variables = list(
                set(base.variables.keys()).intersection(dataframe_variables)
            )

        self.set_tax_benefit_systems(base)
        self.init_from_data(data=data)


count = int(sum(entree_unitaire.quantité))
details_individu_df = pd.DataFrame(
    {
        "famille_id": list(range(count)),
        "strasbourg_piscine_quotient_familial": np.repeat(
            entree_unitaire.qf, entree_unitaire.quantité
        ),
        "age": np.repeat(entree_unitaire.age, entree_unitaire.quantité),
        "strasbourg_piscine_entree_unitaire": np.ones(count),
    }
)
# details_individu_df


sample_count = 5

sample_ids = np.repeat(list(range(sample_count)), len(details_individu_df))
sample_individu_df = pd.DataFrame(
    {
        "sample_id": sample_ids,
        "famille_id": list(range(len(details_individu_df) * sample_count)),
        "strasbourg_piscine_quotient_familial": np.tile(
            details_individu_df.strasbourg_piscine_quotient_familial, sample_count
        ),
        "age": np.tile(details_individu_df.age, sample_count),
        "strasbourg_piscine_entree_unitaire": np.tile(
            details_individu_df.strasbourg_piscine_entree_unitaire, sample_count
        ),
    }
)

sample_famille_df = pd.DataFrame({})
sample_menage_df = pd.DataFrame({})
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

sample_scenario = StrasbourgSurveyScenario(data=sample_data)

sample_prix = sample_scenario.simulation.calculate(
    "strasbourg_piscine_prix_entree_unitaire", base_year
)
sample_res_df = pd.DataFrame(data={"sample_id": sample_ids, "prix": sample_prix})

sample_sum = sample_res_df.groupby(["sample_id"]).sum()

tf = tempfile.NamedTemporaryFile(
    delete=False, suffix=f"_{sample_count}.profile", dir="."
)
profile.dump_stats(tf.name)
print(tf.name)
