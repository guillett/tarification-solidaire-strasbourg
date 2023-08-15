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
qf_default_rule = qfrules_constant


class LogAccessDict(dict):
    def __init__(self, arg={}):
        super(LogAccessDict, self).__init__(arg)
        self.accesses = {}

    def __getitem__(self, key):
        if key not in self.accesses:
            self.accesses[key] = 0
        self.accesses[key] = self.accesses[key] + 1
        return dict.__getitem__(self, key)


ruler = lambda value: constant_value(10 * value)


# ruler = lambda value: lambda v_min, v_max, size: np.random.randint(0, 10*value, size)
def override_ruler(constant):
    return lambda *args: ruler(constant)(*args)


qftype_override = LogAccessDict(
    {
        "QF_MINEUR": override_ruler(700),
        "QF_AGE418": override_ruler(1000),
        "QF_AGE1925": override_ruler(1000),
        "QF_AGE2664": override_ruler(1000),
        "QF_AGE65P": override_ruler(1000),
        "QF_PMR": override_ruler(1000),
        "QF_HANDICAP": override_ruler(1000),
        "QF_CADA": override_ruler(400),
        "QF_ASS": override_ruler(100),
        "QF_ETU": override_ruler(300),
        "QF_EMERAUDE": override_ruler(300),
        # https://www.strasbourg.eu/sortir-bouger-cultiver
        # PA non imposable
        "QF_EVASION": override_ruler(300),
        "QF_RSA": override_ruler(300),
        "QF_AGENT_CUS": override_ruler(800),
        "QF_AGENT_EMS": override_ruler(800),
        "QF_CE": override_ruler(800),
        "QF_CBW": override_ruler(0),
        "QF_CCS_TP": override_ruler(1000),
        "QF_CCS_RA": override_ruler(1000),
        "QF_CCS_RB": override_ruler(1000),
    }
)

qfrules = qfrules_constant
caf_to_fiscal = None


def determine_qf(individu_df):
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
