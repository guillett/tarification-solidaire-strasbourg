from dotenv import load_dotenv
import numpy as np
from openfisca_survey_manager.scenarios import AbstractSurveyScenario
import os
import pandas as pd

load_dotenv()

base_period = "2023-01"

qfrules_constant = {
    "QF1": lambda s=1: 300*np.ones(s),
    "QF2": lambda s=1: 500*np.ones(s),
    "QF3": lambda s=1: 700*np.ones(s),
    "TP": lambda s=1: 1000*np.ones(s),
}

def caf_fiscal(a):
    return np.maximum(0, a*0.9-100).astype('int64')

qfrules_alea = {
    "QF1": lambda s=1: np.random.randint(0, 371, size=s),
    "QF2": lambda s=1: np.random.randint(371, 583, size=s),
    "QF3": lambda s=1: np.random.randint(583, 796, size=s),
    "TP": lambda s=1: np.random.randint(796, 1200, size=s),
}

def determine_qf(individu_df, qfrules=qfrules_constant, caf_to_fiscal=caf_fiscal):
    qf_groups = individu_df.groupby(by=['qfrule']).groups

    for key in qf_groups:
        indexes_in_group = qf_groups[key]
        v = qfrules[key](len(indexes_in_group))
        individu_df.loc[indexes_in_group, 'qf_caf'] = v
        individu_df.loc[indexes_in_group, 'eurometropole_strasbourg_tarification_solidaire_transport_quotient_familial'] = caf_to_fiscal(v)

agerules = {
    "4-18": lambda s=1: 17*np.ones(s),
    "19-25": lambda s=1: 20*np.ones(s),
    "26-64": lambda s=1: 30*np.ones(s),
    "+65": lambda s=1: 70*np.ones(s),
    "AGE_PMR": lambda s=1: 30*np.ones(s),
}

def determine_age(individu_df):
    qf_groups = individu_df.groupby(by=['agerule']).groups
    for key in qf_groups:
        indexes_in_group = qf_groups[key]
        v = agerules[key](len(indexes_in_group))
        individu_df.loc[indexes_in_group, 'age'] = v

class StrasbourgSurveyScenario(AbstractSurveyScenario):
    def __init__(self, tbs, data = None):
        super(StrasbourgSurveyScenario, self).__init__()

        self.year = base_period

        if 'input_data_frame_by_entity' in data:
            dataframe_variables = set()
            for entity_dataframe in data['input_data_frame_by_entity'].values():
                if not isinstance(entity_dataframe, pd.DataFrame):
                    continue
                dataframe_variables = dataframe_variables.union(set(entity_dataframe.columns))
            self.used_as_input_variables = list(
                set(tbs.variables.keys()).intersection(dataframe_variables)
                )

        self.set_tax_benefit_systems(tbs)
        self.init_from_data(data = data)
