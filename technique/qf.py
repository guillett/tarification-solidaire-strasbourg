import numpy as np
import pandas as pd
from rules import dyn_rules
import warnings

import os

mapping_file = "fake_mapping_qf_caf_ems.pickle"
mapping_file = "mapping_qf_caf_ems_V2.pickle"
if os.path.exists(mapping_file):
    qf_mapping = pd.read_pickle(mapping_file)
else:
    qf_mapping = pd.read_pickle(os.path.join("..", mapping_file))

qf_min = 0
qf_max = 4000

# coef = np.select(
#     [
#         qf_mapping.TYPOLOGIE == "Isolé(s) sans enfant",
#         qf_mapping.TYPOLOGIE == "Famille monoparentale",
#     ],
#     [2/1.5, 2.5 / 2],
#     default=1,
# )

# qf_mapping['EMS'] = qf_mapping.EMS / coef


def gen_real_qf_df(data):
    def real_qf_df(mi, ma, s):
        lims = [0]
        for l in lims:
            items = data[(data.CAF >= mi - l) * (data.CAF < ma + l)]
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

    return real_qf_df


def fake_formula(caf):
    return np.maximum(
        0,
        np.random.normal(
            np.maximum(0, caf * 0.6 - 100), np.maximum(0, caf * 0.5 - 100)
        ),
    ).astype("int64")


def unif_qf_df(mi, ma, s):
    v = np.random.randint(mi, ma, s)
    return pd.DataFrame(
        data={"CAF": v, "EMS": v, "TYPOLOGIE": "Couple avec enfant(s)"}
    )  # fake_formula(v)})


def constant_qf_df(_, mi, ma, s):
    v = np.ones(s) * (mi + ma - 1) / 2
    return pd.DataFrame(data={"CAF": v, "EMS": v, "TYPOLOGIE": "Couple avec enfant(s)"})


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
        "QF_AGE65P": "QF",
        "QF_PMR": "QF<=2000",
        "QF_EMERAUDE": "QF<=2000",
        # Piscine
        # via mapping QF CAF/EMS sur les données individuelles CTS
        "QF_HANDICAP": "QF",
        "QF_CADA": "QF<=100",
        # 0 pour QF EMS
        "QF_ASS": "QF<=500",
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
        "QF_CBW": "QF==0",
        # CCS
        # À voir avec la CAF
        "QF_CCS_TP": "QF",
        "QF_CCS_RA": "QF<=3000",
        "QF_CCS_RB": "QF<=2000",
        "QF_CCS_RC": "QF<=3000",
    }
)

unif_qf = dyn_rules(unif_qf_df, qf_min, qf_max)
qfrules_constant = dyn_rules(lambda mi, ma, s: constant_qf_df, qf_min, qf_max)


def determine_qf_avec_enfants(df):
    data = qf_mapping[
        qf_mapping.TYPOLOGIE.isin(["Couple avec enfant(s)", "Famille monoparentale"])
    ]
    determine_qf(df, data)


def determine_qf(df, data=qf_mapping):
    df["qf_caf"] = 0
    df["qf_fiscal"] = 0
    df["TYPOLOGIE"] = ""
    qf_groups = df.groupby(by=["qfrule"]).groups

    real_qf_df = gen_real_qf_df(data)
    qfrules = dyn_rules(real_qf_df, qf_min, qf_max)
    bogus = []
    for key in qf_groups:
        try:
            indexes_in_group = qf_groups[key]
            rule = key if key not in qftype_override else qftype_override[key]
            n = len(indexes_in_group)
            v = qfrules(rule)(n)
        except Exception as e:
            bogus.append((rule, n))
            try:
                v = unif_qf(rule)(n)
            except Exception as e:
                print((rule, n))
                raise e
        finally:
            df.loc[indexes_in_group, "qf_caf"] = v.CAF.values
            df.loc[indexes_in_group, "qf_fiscal"] = v.EMS.values
            df.loc[indexes_in_group, "TYPOLOGIE"] = v.TYPOLOGIE.values
    if bogus:
        r = "\n".join([f"{r} ({n})" for r, n in bogus])
        warnings.warn(f"Bogus rules:\n{r}")


# La séparation par sample_id ralentit trop les estimations pour la DEE.
# L'imprécision générée n'est pas très grande.
def determine_qf_by_sample(df, data=qf_mapping):
    df["qf_caf"] = 0
    df["qf_fiscal"] = 0
    df["TYPOLOGIE"] = ""
    qf_groups = df.groupby(by=["sample_id", "qfrule"]).groups

    real_qf_df = gen_real_qf_df(data)
    qfrules = dyn_rules(real_qf_df, qf_min, qf_max)
    bogus = []
    for sample, key in qf_groups:
        try:
            indexes_in_group = qf_groups[(sample, key)]
            rule = key if key not in qftype_override else qftype_override[key]
            n = len(indexes_in_group)
            v = qfrules(rule)(n)
        except Exception as e:
            bogus.append((rule, n))
            try:
                v = unif_qf(rule)(n)
            except Exception as e:
                print((rule, n))
                raise e
        finally:
            df.loc[indexes_in_group, "qf_caf"] = v.CAF.values
            df.loc[indexes_in_group, "qf_fiscal"] = v.EMS.values
            df.loc[indexes_in_group, "TYPOLOGIE"] = v.TYPOLOGIE.values
    if bogus:
        r = "\n".join([f"{r} ({n})" for r, n in bogus])
        warnings.warn(f"Bogus rules:\n{r}")
