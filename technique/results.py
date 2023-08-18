import pandas as pd

distrib_items = [
    "Moyenne",
    "Écart-type",
    "Min",
    # "25%",
    "Médiane",
    # "50%",
    # "75%",
    "Max",
]

result_index = pd.MultiIndex.from_tuples(
    [
        ("Direction", ""),
        ("Service", ""),
        ("Quantité", ""),
        ("Nb éch.", ""),
        *[("Recettes base", i) for i in distrib_items],
        *[("Recettes réforme", i) for i in distrib_items],
    ]
)


def extract(r, field, count_field=None):
    describe = (
        lambda r: r.groupby(["sample_id"])[field].sum().describe()[[1, 2, 3, 5, 7]]
    )
    if count_field:
        count = r.groupby(["sample_id"])[count_field].sum().describe()
    else:
        count = r.groupby(["sample_id"])[field].count().describe()
    assert pd.isna(count["std"]) or count["std"] == 0
    value = describe(r)
    return count, value
