import pandas as pd
import numpy as np
from en_corrector import *
from reader import *


def add_to_corrector(corrector, correction):
    # correction: (Measured_energy, Energy_correction)

    to_append = [correction[0], real_energy, correction[1], 0, 0]
    a_series = pd.Series(to_append, index=corrector.columns)

    if real_energy in corrector.En_real.values:
        corrector_ind = corrector[corrector.En_real == real_energy].index[0]

        corrector.loc[[corrector_ind], :] = to_append

        if corrector_ind == 0:    # We cannot calculate coefficients for line zero in the corrector
            return corrector

        for i in range(corrector_ind, corrector_ind + 2):
            corrector.loc[[corrector_ind], ['Slope']] = calculate(slope, corrector, corrector_ind)
            corrector.loc[[corrector_ind], ['Intercept']] = calculate(intercept, corrector, corrector_ind)

    else:
        corrector = corrector.append(a_series, ignore_index=True)
        last_ind = corrector.shape[0] - 1
        start_ind = last_ind

        if corrector.shape[0] > 1:

            if corrector.loc[[last_ind], ['En_meas']].values[0] < corrector.loc[[last_ind - 1], ['En_meas']].values[0]:
                corrector.sort_values(by=['En_meas'], inplace=True)
                start_ind = 1

            for i in range(start_ind, last_ind + 1):
                corrector.loc[[i], ['Slope']] = calculate(slope, corrector, last_ind)
                corrector.loc[[i], ['Intercept']] = calculate(intercept, corrector, last_ind)

    return corrector


def calculate(function, corrector, index):
    y1 = corrector.loc[[index], ['Corr']].values[0]
    y2 = corrector.loc[[index - 1], ['Corr']].values[0]
    x1 = corrector.loc[[index], ['En_meas']].values[0]
    x2 = corrector.loc[[index - 1], ['En_meas']].values[0]
    return function(x1, y1, x2, y2)


def slope(x1, y1, x2, y2):
    return (y1 - y2) / (x1 - x2)


def intercept(x1, y1, x2, y2):
    return (y1 * x2 - y2 * x1) / (x2 - x1)


en_corrector = pd.DataFrame(columns=['En_meas', 'En_real', 'Corr', 'Slope', 'Intercept'])

date = "2021.02"

path_dat_files = f"../{date}/Файлы/"
path_processed_dat_files = path_dat_files + 'Обработанные/'
path_test_log = f"../{date}/For_fast_processing.xlsx"

df = read_excel_log(path_test_log)

for ind in df.index:
    line = df[df.index == ind]

    Io_file_num = line['Io file #'].values[0]  # str type
    Ir_file_num = line['file #'].values[0]  # str type

    kth = 3

    # Processing of the files with data measured from the filters for energy correction
    if 'edge' in str(line['Sample info'].values[0]) and 'order' in str(line['Sample info'].values[0]):

        real_energy = line['Sample short name'].values[0]
        file_name = line['First part of file name'].values[0] + str(int(Ir_file_num)) + '.dat'

        corr = en_correction(file_path=path_dat_files + file_name,
                             real_en=real_energy,
                             kth_num=kth)

        # Add data to en_corrector Data Frame
        en_corrector = add_to_corrector(en_corrector, corr)

    elif not pd.isna(Io_file_num):
        Io_filename = line['First part of file name'].values[0] + str(int(Io_file_num)) + '.dat'
        Ir_filename = line['First part of file name'].values[0] + str(int(Ir_file_num)) + '.dat'
        new_filename = str(int(line['file #'].values[0])) + '.dat'

        scan_type = line['Scan m. 1'].values[0]

        Io_data = read_dat_file(path_dat_files + Io_filename, kth, scan_type)
        Ir_data = read_dat_file(path_dat_files + Ir_filename, kth, scan_type)

        Ir_Io = Ir_data

        if scan_type == 'en':
            Ir_Io.intensity = Ir_data.intensity / Io_data.intensity * 100

            # Energy correction
            for corr_ind in en_corrector.index:

                # Find required range
                if Ir_Io.en.mean() < en_corrector.loc[[corr_ind], 'En_meas'].values[0]:
                    Ir_Io.en = Ir_Io.en + Ir_Io.en * en_corrector.loc[[corr_ind], 'Slope'].values[0] + \
                               en_corrector.loc[[corr_ind], 'Intercept'].values[0]
                    break

        elif scan_type == 'tha':
            Ir_Io.intensity = Ir_data.intensity / Io_data.intensity.mean() * 100

        Ir_Io.to_csv(path_processed_dat_files + new_filename, sep='\t', index=False, float_format="%.10f")

# TODO: Добавить обработку NEXAFS
# TODO: Автоматически определять kithley (по возможности)
