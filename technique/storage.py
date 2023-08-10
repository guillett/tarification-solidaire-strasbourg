import pandas as pd
import os


def get_data(filename, processor):
    pickle_filename = filename + ".pickle"
    if os.path.isfile(pickle_filename):
        return pd.read_pickle(pickle_filename)
    else:
        df = processor(filename)
        df.to_pickle(pickle_filename)
        return df
