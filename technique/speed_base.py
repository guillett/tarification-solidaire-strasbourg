import numpy as np
import pandas as pd

import cProfile

import tempfile

profile = cProfile.Profile()
profile.enable()

print(__file__)

df = pd.read_excel(
    "/home/thomas/Nextcloud/CodeursEnLiberte/EMS/sports/extractions_denombrement.ods"
)

entree_unitaire = df[df["entrée unitaire"] == "x"]

from openfisca_survey_manager.scenarios import AbstractSurveyScenario
from openfisca_france import CountryTaxBenefitSystem
from openfisca_france.model.base import Famille, FoyerFiscal, Menage
from openfisca_core import periods

base_year = "2023"

count = sum(entree_unitaire.quantité)
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


sample_count = 1

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

tf = tempfile.NamedTemporaryFile(
    delete=False, prefix="speed_base_", suffix=f"_{sample_count}.profile", dir="."
)
profile.dump_stats(tf.name)
print(tf.name)
