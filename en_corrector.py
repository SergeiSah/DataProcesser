import plotly.express as px
import numpy as np
from reader import *


# path_dat_files = "../2021.09/Файлы/"
# path_excel = "../2021.09/! Measurement_PM1 AS-2021-09-03 (SHORT).xlsx"


def en_correction(file_path, real_en, kth_num):

    file = read_dat_file(file_path,
                         kth_num=kth_num,
                         scan_type='en')

    file['derv'] = file.intensity.diff() / file.intensity.index.to_series().diff()
    meas_en = file[file['derv'] == file['derv'].min()]['en'].values[0]
    # fig = px.line(file, x='en', y=['intensity', 'derv'])
    # fig.show()
    return meas_en, real_en - meas_en


# print(en_correction(path_dat_files + 'AS_obl_2021_5771.dat', 932.12, 3))
