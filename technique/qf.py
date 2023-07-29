import numpy as np
from rules import get_values

qf_name = 'eurometropole_strasbourg_tarification_solidaire_transport_quotient_familial'

def caf_fiscal(a):
    return np.maximum(0, a*0.9-100).astype('int64')

def dyn_qfrules(func):
    def rule(text, qftype_override = {}):
        def values(size):
            (v_min, v_max, qftype) = get_values(text)
            if qftype in qftype_override:
                return qftype_override[qftype](v_min, v_max, size)
            if v_min == None:
                v_min = 0
            if v_max == None:
                v_max = 1200
            return func(v_min, v_max, size)

        return values

    return rule

unif_qf = dyn_qfrules(np.random.randint)
qfrules_constant = dyn_qfrules(lambda mi, ma, s: (np.ones(s) * (mi+ma-1)/2).astype('int64'))

qr_recalc = lambda v_min, v_max, size: 1000 * np.ones(size)
qftype_override = {
    "QF_AGE65P": qr_recalc,
    "QF_AGE1925": qr_recalc,
    "QF_MINEUR": qr_recalc,
    "QF_AGE2664": qr_recalc,
    "QF_PMR": qr_recalc,
}

def determine_qf(individu_df, qfrules, caf_to_fiscal=None):
    determine_qf_caf(
        individu_df,
        qfrules
    )
    if caf_to_fiscal:
        individu_df['qf_fiscal'] = caf_to_fiscal(individu_df['qf_caf'])
        individu_df[qf_name] = individu_df['qf_fiscal']
    else:
        individu_df[qf_name] = individu_df['qf_caf']


def determine_qf_caf(individu_df, qfrules):
    qf_groups = individu_df.groupby(by=['qfrule']).groups

    for key in qf_groups:
        indexes_in_group = qf_groups[key]
        v = qfrules(key, qftype_override)(len(indexes_in_group))
        individu_df.loc[indexes_in_group, 'qf_caf'] = v

