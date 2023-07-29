import pandas as pd
from openfisca_survey_manager.scenarios import AbstractSurveyScenario

base_period = "2023-01"

class StrasbourgSurveyScenario(AbstractSurveyScenario):
    def __init__(self, tbs, data = None):
        super(StrasbourgSurveyScenario, self).__init__()

        self.year = base_period
        self.non_neutralizable_variables = ['qf_caf', 'qf_fiscal']

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
