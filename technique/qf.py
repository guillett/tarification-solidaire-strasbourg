import numpy as np
import pandas as pd
from rules import get_values, dyn_rules, constant_value
import warnings


def caf_fiscal(a):
    return np.maximum(0, a * 0.9 - 100).astype("int64")


qf_min = 0
qf_max = 4000

import os

mapping_file = "fake_mapping_qf_caf_ems.pickle"
mapping_file = "mapping_qf_caf_ems.pickle"
if os.path.exists(mapping_file):
    qf_mapping = pd.read_pickle(mapping_file)
else:
    qf_mapping = pd.read_pickle(os.path.join("..", mapping_file))


def real_qf_df(mi, ma, s):
    lims = [0]
    for l in lims:
        items = qf_mapping[(qf_mapping.CAF >= mi - l) * (qf_mapping.CAF < ma + l)]
        n = len(items)
        if n:
            if l != 0:
                warnings.warn(f"Enlarged interval [{mi}-{l}, {ma}+{l}[…")
            if s > n:
                pass
                # TODO
                # warnings.warn(f"Concentring data… n={n} but s={s}")
            # TODO
            # Explicit replacement
            return items.sample(s, replace=True)
    raise Exception("What a mess!")


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
        "QF_AGE418": "QF",
        "QF_AGE1925": "QF",
        "QF_AGE2664": "QF",
        "QF_AGE65P": "QF<=3000",
        "QF_PMR": "QF<=2000",
        "QF_EMERAUDE": "QF<=2000",
        # Piscine
        # via mapping QF CAF/EMS sur les données individuelles CTS
        "QF_HANDICAP": "QF",
        "QF_CADA": "QF<=2000",
        # 0 pour QF EMS
        "QF_ASS": "QF<=200",
        # Pas de nouvelles du CROUS/CNOUS
        "QF_ETU": "QF",
        # https://www.strasbourg.eu/sortir-bouger-cultiver
        # PA non imposable
        "QF_EVASION": "QF<=1000",
        # 0 pour QF EMS
        "QF_RSA": "QF<=500",
        # QF important
        "QF_AGENT_CUS": "1000<=QF<=3000",
        "QF_AGENT_EMS": "1000<=QF<=3000",
        "QF_MINEUR": "QF",
        "QF_CE": "1500<=QF<=3000",
        "QF_CBW": "QF<=300",
        # CCS
        # À voir avec la CAF
        "QF_CCS_TP": "QF",
        "QF_CCS_RA": "QF<=3000",
        "QF_CCS_RB": "QF<=2000",
    }
)


def determine_qf(df):
    df["qf_caf"] = 0
    df["qf_fiscal"] = 0
    qf_groups = df.groupby(by=["sample_id", "qfrule"]).groups
    for sample, key in qf_groups:
        try:
            indexes_in_group = qf_groups[(sample, key)]
            rule = key if key not in qftype_override else qftype_override[key]
            n = len(indexes_in_group)
            v = qfrules(rule)(n)
        except Exception as e:
            warnings.warn(f"Bogus rule {rule} for {n} items.")
            v = unif_qf(rule)(n)
        finally:
            df.loc[indexes_in_group, "qf_caf"] = v.CAF.values
            df.loc[indexes_in_group, "qf_fiscal"] = v.EMS.values
