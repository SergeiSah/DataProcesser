import numpy as np
from scipy.interpolate import interpolate, pchip_interpolate
import pandas as pd
from error_handler import try_read


def read_excel_log(excel_filepath):
    return pd.read_excel(io=excel_filepath,
                         usecols="A:C,K,L,S,U,V,Y:BA",
                         header=1)


@try_read
def en_correction(file_path, real_en, kth_num):

    file = read_dat_file(file_path,
                         kth_num=kth_num,
                         scan_type='en')
    if file is None: return

    file_new = _smoothing(file)

    # file['derv'] = file.intensity.diff() / file.intensity.index.to_series().diff()
    # file['derv'] = file['derv'] / abs(file['derv'].mean()) * abs(file_new['derv'].mean())

    file_new['derv'] = file_new.intensity.diff() / file_new.intensity.index.to_series().diff()
    meas_en = file_new[file_new['derv'] == file_new['derv'].min()]['en'].values[0]

    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=file_new['en'], y=file_new['derv']))
    # fig.add_trace(go.Scatter(x=file['en'], y=file['derv']))
    # fig.show()

    return meas_en, real_en


def _smoothing(df, n_scatters=400, window=17):  # Adding points and smoothing
    energies = np.linspace(min(df['en']), max(df['en']), n_scatters)
    intensity = interpolate.interp1d(df['en'], df['intensity'], kind='quadratic')
    step = df['en'][1] - df['en'][0]

    return pd.DataFrame(data={'en': energies + step / 2, 'intensity': intensity(energies)}).rolling(window).mean()


@try_read
def read_dat_file(dat_filepath: str, kth_num: int, scan_type: str) -> pd.DataFrame:
    df = pd.read_csv(dat_filepath, skiprows=85, sep='\s+')
    kth = f'kth{kth_num}'
    new_df = pd.concat([df[df.columns[0]], df[kth] / df['ringc']], axis=1)

    return new_df.rename(columns={0: 'intensity', df.columns[0]: scan_type})

