import numpy as np
from rules import get_values, dyn_rules, constant_value

qf_name = "strasbourg_metropole_quotient_familial"


def caf_fiscal(a):
    return np.maximum(0, a * 0.9 - 100).astype("int64")


qf_min = 0
qf_max = 1200

unif_qf = dyn_rules(np.random.randint, qf_min, qf_max)
qfrules_constant = dyn_rules(
    lambda mi, ma, s: (np.ones(s) * (mi + ma - 1) / 2).astype("int64"), qf_min, qf_max
)

qftype_override = {
    "QF_MINEUR": constant_value(700),
    "QF_AGE418": constant_value(1000),
    "QF_AGE1925": constant_value(1000),
    "QF_AGE2664": constant_value(1000),
    "QF_AGE65P": constant_value(1000),
    "QF_PMR": constant_value(1000),
    "QF_HANDICAP": constant_value(1000),
    "QF_CADA": constant_value(400),
    "QF_ASS": constant_value(100),
    "QF_ETU": constant_value(300),
    "QF_EMERAUDE": constant_value(300),
    # https://www.strasbourg.eu/sortir-bouger-cultiver
    # PA non imposable
    "QF_EVASION": constant_value(300),
    "QF_RSA": constant_value(300),
    "QF_AGENT_CUS": constant_value(800),
    "QF_AGENT_EMS": constant_value(800),
    "QF_CE": constant_value(800),
    "QF_CBW": constant_value(0),
    "QF_CCS_TP": constant_value(921),
    "QF_CCS_RA": constant_value(821),
    "QF_CCS_RB": constant_value(500),
}


def determine_qf(individu_df, qfrules, caf_to_fiscal=None):
    determine_qf_caf(individu_df, qfrules)
    if caf_to_fiscal:
        individu_df["qf_fiscal"] = caf_to_fiscal(individu_df["qf_caf"])
        individu_df[qf_name] = individu_df["qf_fiscal"]
    else:
        individu_df[qf_name] = individu_df["qf_caf"]


def determine_qf_caf(individu_df, qfrules):
    qf_groups = individu_df.groupby(by=["qfrule"]).groups

    for key in qf_groups:
        indexes_in_group = qf_groups[key]
        v = qfrules(key, qftype_override)(len(indexes_in_group))
        individu_df.loc[indexes_in_group, "qf_caf"] = v
