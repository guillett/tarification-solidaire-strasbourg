import numpy as np
import pandas as pd
from rules import get_values, dyn_rules, constant_value


def caf_fiscal(a):
    return np.maximum(0, a * 0.9 - 100).astype("int64")


qf_min = 0
qf_max = 1200

import os

fake_mapping_file = "fake_mapping_qf_caf_ems.pickle"
if os.path.exists(fake_mapping_file):
    qf_mapping = pd.read_pickle(fake_mapping_file)
else:
    qf_mapping = pd.read_pickle(os.path.join("..", fake_mapping_file))


def real_qf_df(mi, ma, s):
    items = qf_mapping[(qf_mapping.CAF >= mi) * (qf_mapping.CAF < ma)]
    if len(items):
        return items.sample(s, replace=True)
    else:
        return unif_qf_df(mi, ma, s)


def fake_formula(caf):
    np.maximum(
        0,
        np.random.normal(
            np.maximum(0, caf * 0.6 - 100), np.maximum(0, caf * 0.5 - 100)
        ),
    ).astype("int64")


def unif_qf_df(mi, ma, s):
    v = np.random.randint(mi, ma, s)
    return pd.DataFrame(data={"CAF": v, "EMS": fake_formula(v)})


real_qf = dyn_rules(real_qf_df, qf_min, qf_max)
unif_qf = dyn_rules(unif_qf_df, qf_min, qf_max)


# unif_qf = dyn_rules(lambda mi, ma, s: np.random.randint(10000, 100000, s), qf_min, qf_max)
def constant_qf_df(mi, ma, s):
    v = np.ones(s) * (mi + ma - 1) / 2
    return pd.DataFrame(data={"CAF": v, "EMS": v})


qfrules_constant = dyn_rules(lambda mi, ma, s: constant_qf_df, qf_min, qf_max)
qfrules = real_qf  # unif_qf#qfrules_constant

ruler = lambda value: constant_value(10 * value)


# ruler = lambda value: lambda v_min, v_max, size: np.random.randint(0, 10*value, size)
def override_ruler(constant):
    def fn(*args):
        v = ruler(constant)(*args)
        return pd.DataFrame(data={"CAF": v, "EMS": v})

    return fn


class LogAccessDict(dict):
    def __init__(self, arg={}):
        super(LogAccessDict, self).__init__(arg)
        self.accesses = {}

    def __getitem__(self, key):
        if key not in self.accesses:
            self.accesses[key] = 0
        self.accesses[key] = self.accesses[key] + 1
        return dict.__getitem__(self, key)


try:
    pass
except Exception as e:
    raise
else:
    pass
finally:
    pass

qftype_override = LogAccessDict(
    {
        # Mobilité
        "QF_AGE418": override_ruler(1000),
        "QF_AGE1925": override_ruler(1000),
        "QF_AGE2664": override_ruler(1000),
        "QF_AGE65P": override_ruler(1000),
        "QF_PMR": override_ruler(1000),
        "QF_EMERAUDE": override_ruler(300),
        # Piscine
        # via mapping QF CAF/EMS sur les données individuelles CTS
        "QF_HANDICAP": override_ruler(1000),
        "QF_CADA": override_ruler(0),
        # 0 pour QF EMS
        "QF_ASS": override_ruler(0),
        # Pas de nouvelles du CROUS/CNOUS
        "QF_ETU": override_ruler(300),
        # https://www.strasbourg.eu/sortir-bouger-cultiver
        # PA non imposable
        "QF_EVASION": override_ruler(300),
        # 0 pour QF EMS
        "QF_RSA": override_ruler(300),
        # QF important
        "QF_AGENT_CUS": override_ruler(1500),
        "QF_AGENT_EMS": override_ruler(1500),
        "QF_MINEUR": override_ruler(1500),
        "QF_CE": override_ruler(1500),
        "QF_CBW": override_ruler(0),
        # CCS
        # À voir avec Johanne ?
        "QF_CCS_TP": override_ruler(1000),
        "QF_CCS_RA": override_ruler(1000),
        "QF_CCS_RB": override_ruler(1000),
    }
)


def determine_qf(df):
    df["qf_caf"] = 0
    df["qf_fiscal"] = 0
    qf_groups = df.groupby(by=["qfrule"]).groups

    for key in qf_groups:
        indexes_in_group = qf_groups[key]
        v = qfrules(key, qftype_override)(len(indexes_in_group))
        df.loc[indexes_in_group, "qf_caf"] = v.CAF.values
        df.loc[indexes_in_group, "qf_fiscal"] = v.EMS.values
