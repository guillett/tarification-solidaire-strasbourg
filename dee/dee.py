import cantine
import activite
import pandas as pd


def get_results(tbs, sample_count=2, reform=None):
    (crecap, cdfs) = cantine.get_results(tbs, sample_count, reform)
    (arecap, adfs) = activite.get_results(tbs, sample_count, reform)

    return pd.concat([crecap, arecap]), [*cdfs, *adfs]
