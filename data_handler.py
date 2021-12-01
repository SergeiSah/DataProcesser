import pandas as pd
from scipy.interpolate import interpolate
from en_corrector import *
from file_reader import *


DATE = "2021.11"


def add_to_corrector(corrector: pd.DataFrame, meas_real: tuple) -> pd.DataFrame:

    measured_en = meas_real[0]
    real_en = meas_real[1]
    correction = meas_real[1] - meas_real[0]

    to_add_in_corrector = [measured_en, real_en, correction, 0, 0]
    a_series = pd.Series(to_add_in_corrector, index=corrector.columns)

    if real_en in corrector.En_real.values:
        corrector_ind = corrector[corrector.En_real == real_en].index[0]
        corrector.loc[[corrector_ind], :] = to_add_in_corrector

        if corrector_ind == 0:    # We cannot calculate coefficients for line with zero index in the corrector
            return corrector

        for i in range(corrector_ind, corrector_ind + 2):
            corrector.loc[[corrector_ind], ['Slope']] = calc_coefficient(slope, corrector, corrector_ind)
            corrector.loc[[corrector_ind], ['Intercept']] = calc_coefficient(intercept, corrector, corrector_ind)

    else:
        corrector = corrector.append(a_series, ignore_index=True)
        last_ind = corrector.shape[0] - 1
        start_ind = last_ind

        if corrector.shape[0] > 1:

            if corrector.loc[[last_ind], ['En_meas']].values[0] < corrector.loc[[last_ind - 1], ['En_meas']].values[0]:
                corrector.sort_values(by=['En_meas'], inplace=True)
                start_ind = 1

            for i in range(start_ind, last_ind + 1):
                corrector.loc[[i], ['Slope']] = calc_coefficient(slope, corrector, last_ind)
                corrector.loc[[i], ['Intercept']] = calc_coefficient(intercept, corrector, last_ind)

    return corrector


def calc_coefficient(line_func_coefficient, corrector, index):

    y1 = corrector.loc[[index], ['Corr']].values[0]
    y2 = corrector.loc[[index - 1], ['Corr']].values[0]
    x1 = corrector.loc[[index], ['En_meas']].values[0]
    x2 = corrector.loc[[index - 1], ['En_meas']].values[0]

    return line_func_coefficient(x1, y1, x2, y2)


def slope(x1: float, y1: float, x2: float, y2: float) -> float:
    return (y1 - y2) / (x1 - x2)


def intercept(x1: float, y1: float, x2: float, y2: float) -> float:
    return (y1 * x2 - y2 * x1) / (x2 - x1)


def adjust_region(df_to_adjust: pd.DataFrame, df_main: pd.DataFrame) -> pd.DataFrame:
    cols = df_main.columns
    interp_func = interpolate.interp1d(df_to_adjust.iloc[:, 0], df_to_adjust.iloc[:, 1],
                                       kind='quadratic',
                                       fill_value='extrapolate')

    return pd.DataFrame(data={cols[0]: df_main.iloc[:, 0], cols[1]: interp_func(df_main.iloc[:, 0])})


en_corrector = pd.DataFrame(columns=['En_meas', 'En_real', 'Corr', 'Slope', 'Intercept'])


path_dat_files = f"../{DATE}/Файлы/"
path_processed_dat_files = path_dat_files + 'Обработанные/'
path_test_log = f"../{DATE}/For_fast_processing.xlsx"

df = read_excel_log(path_test_log)

# TODO: Wrap in function
# TODO: determine kth automatically
for ind in df.index:
    line = df[df.index == ind]

    Io_file_num = line['Io file #'].values[0]  # str type
    Ir_file_num = line['file #'].values[0]  # str type

    kth_Io = 3
    kth_Ir = 3

    # Processing of the files with data measured from the filters for energy correction
    if 'edge' in str(line['Sample info'].values[0]) and 'order' in str(line['Sample info'].values[0]):

        real_energy = line['Sample short name'].values[0]
        file_name = line['First part of file name'].values[0] + str(int(Ir_file_num)) + '.dat'

        corr = en_correction(file_path=path_dat_files + file_name, real_en=real_energy, kth_num=kth_Io)
        if corr is None:
            continue

        # Add data to en_corrector Data Frame
        en_corrector = add_to_corrector(en_corrector, corr)

    elif not pd.isna(Io_file_num):
        Io_filename = line['First part of file name'].values[0] + str(int(Io_file_num)) + '.dat'
        Ir_filename = line['First part of file name'].values[0] + str(int(Ir_file_num)) + '.dat'
        new_filename = str(int(line['file #'].values[0])) + '.dat'

        scan_type = line['Scan m. 1'].values[0]

        # TODO: Interpolate I0 data for x values from Ir data
        Io_data = read_dat_file(path_dat_files + Io_filename, kth_Io, scan_type)
        Ir_data = read_dat_file(path_dat_files + Ir_filename, kth_Ir, scan_type)

        if (Ir_data is None) or (Io_data is None):
            continue

        Ir_Io = Ir_data

        if scan_type == 'en':

            if Ir_data.shape != Io_data.shape:
                Io_data = adjust_region(Io_data, Ir_data)

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
