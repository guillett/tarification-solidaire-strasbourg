import numpy as np

agerules = {
    "4-18": lambda s=1: 17*np.ones(s),
    "19-25": lambda s=1: 20*np.ones(s),
    "26-64": lambda s=1: 30*np.ones(s),
    "+65": lambda s=1: 70*np.ones(s),
    "AGE_PMR": lambda s=1: 30*np.ones(s),
    "AGE_EMERAUDE": lambda s=1: 75*np.ones(s)
}

def determine_age(individu_df):
    qf_groups = individu_df.groupby(by=['agerule']).groups
    for key in qf_groups:
        indexes_in_group = qf_groups[key]
        v = agerules[key](len(indexes_in_group))
        individu_df.loc[indexes_in_group, 'age'] = v
