import sys
from age import determine_age
from qf import determine_qf, determine_qf_avec_enfants, unif_qf
from scenario import (
    StrasbourgSurveyScenario,
    base_period,
    gristSimulationReform,
    QfFiscalReform,
    StatutReform,
)
from storage import get_data

import pickle


class LimitContainer(object):
    file = "limits.pickle"

    @classmethod
    def get(cls, name):
        with open("limits.pickle", "rb") as f:
            vv = pickle.load(f)
            if name in vv:
                return vv[name]
            else:
                return []

    @classmethod
    def set(cls, name, value):
        with open("limits.pickle", "rb+") as f:
            vv = pickle.load(f)
            if name not in vv:
                vv[name] = []
            vv[name].append(value)
            f.seek(0)
            pickle.dump(vv, f)

    @classmethod
    def raw(cls):
        with open("limits.pickle", "rb") as f:
            return pickle.load(f)

    @classmethod
    def reset(cls):
        with open("limits.pickle", "wb") as f:
            return pickle.dump({}, f)
