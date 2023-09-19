import numpy as np
from rules import dyn_rules

age_rules = dyn_rules(
    lambda mi, ma, s: (np.ones(s) * (mi + ma - 1) / 2).astype("int64"), 0, 99
)

age_override = {
    "AGE_PMR": "18<=AGE<=60",
    "AGE_EMERAUDE": "AGE>=75",
    "AGE_CADA": "18<=AGE<=40",
    "AGE_ASS": "20<=AGE<=40",
    "AGE_ETU": "18<=AGE<=26",
    "AGE_EVASION": "AGE>=70",
    "AGE_HANDICAP": "18<=AGE<=60",
    "AGE_QF0": "18<=AGE<=50",
    "AGE_QF800": "18<=AGE<=50",
    "AGE_RSA": "15<AGE<=60",
    "AGE_AGENT_CUS": "22<=AGE<=60",
    "AGE_CE": "22<=AGE<=60",
    "AGE_AGENT_EMS": "22<=AGE<=60",
}


def determine_age(individu_df):
    qf_groups = individu_df.groupby(by=["agerule"]).groups
    for key in qf_groups:
        try:
            indexes_in_group = qf_groups[key]
            rule = key if key not in age_override else age_override[key]
            v = age_rules(rule)(len(indexes_in_group))
            individu_df.loc[indexes_in_group, "age"] = v
        except Exception as e:
            raise Exception(key, e)
