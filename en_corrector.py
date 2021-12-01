import plotly.graph_objects as go
from error_handler import try_read
import numpy as np
from scipy.interpolate import interpolate, pchip_interpolate
from file_reader import *


@try_read
def en_correction(file_path, real_en, kth_num):

    file = read_dat_file(file_path,
                         kth_num=kth_num,
                         scan_type='en')
    if file is None: return

    file_new = smoothing(file)

    # file['derv'] = file.intensity.diff() / file.intensity.index.to_series().diff()
    # file['derv'] = file['derv'] / abs(file['derv'].mean()) * abs(file_new['derv'].mean())

    file_new['derv'] = file_new.intensity.diff() / file_new.intensity.index.to_series().diff()
    meas_en = file_new[file_new['derv'] == file_new['derv'].min()]['en'].values[0]

    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=file_new['en'], y=file_new['derv']))
    # fig.add_trace(go.Scatter(x=file['en'], y=file['derv']))
    # fig.show()

    return meas_en, real_en


def smoothing(df, n_scatters=400, window=17):  # Adding points and smoothing
    energies = np.linspace(min(df['en']), max(df['en']), n_scatters)
    intensity = interpolate.interp1d(df['en'], df['intensity'], kind='quadratic')
    step = df['en'][1] - df['en'][0]

    return pd.DataFrame(data={'en': energies + step / 2, 'intensity': intensity(energies)}).rolling(window).mean()
