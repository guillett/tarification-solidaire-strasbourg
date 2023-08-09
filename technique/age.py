import numpy as np
from rules import get_values, dyn_rules, constant_value

age_rules = dyn_rules(
    lambda mi, ma, s: (np.ones(s) * (mi + ma - 1) / 2).astype("int64"), 0, 99
)

age_override = {
    #    "4-18": constant_value(17),
    #    "19-25": constant_value(20),
    #    "26-64": constant_value(30),
    #    "+65": constant_value(70),
    "AGE_PMR": constant_value(30),
    "AGE_EMERAUDE": constant_value(75),
    "AGE_CADA": constant_value(25),
    "AGE_ASS": constant_value(30),
    "AGE_ETU": constant_value(20),
    "AGE_EVASION": constant_value(80),
    "AGE_HANDICAP": constant_value(30),
    "AGE_QF0": constant_value(30),
    "AGE_QF800": constant_value(30),
    "AGE_RSA": constant_value(30),
    "AGE_AGENT_CUS": constant_value(40),
    "AGE_CE": constant_value(40),
    "AGE_AGENT_EMS": constant_value(40),
}


def determine_age(individu_df):
    qf_groups = individu_df.groupby(by=["agerule"]).groups
    for key in qf_groups:
        indexes_in_group = qf_groups[key]
        v = age_rules(key, age_override)(len(indexes_in_group))
        individu_df.loc[indexes_in_group, "age"] = v
