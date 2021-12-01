import pandas as pd
from scipy.interpolate import interpolate
import plotly.graph_objects as go
from file_reader import *


DATE = "2021.11"


class LinearCorrector:

    def __init__(self, param_1: str, param_2: str):
        self.corr_df = pd.DataFrame(columns=[param_1, param_2, 'Corr', 'Slope', 'Intercept'])

    # TODO: Попробовать решить через interpolate или scikit-learn
    def add_to_corrector(self, meas_real: tuple) -> None:

        measured_en = meas_real[0]
        real_en = meas_real[1]
        correction = meas_real[1] - meas_real[0]

        to_add_in_corrector = [measured_en, real_en, correction, 0, 0]
        a_series = pd.Series(to_add_in_corrector, index=self.corr_df.columns)

        if real_en in self.corr_df.En_real.values:
            corrector_ind = self.corr_df[self.corr_df.En_real == real_en].index[0]
            self.corr_df.loc[[corrector_ind], :] = to_add_in_corrector

            if corrector_ind != 0:    # We cannot calculate coefficients for line with zero index in the corrector
                for i in range(corrector_ind, corrector_ind + 2):
                    self.corr_df.loc[[corrector_ind], ['Slope']] = self.calc_coefficient(self.slope, corrector_ind)
                    self.corr_df.loc[[corrector_ind], ['Intercept']] = self.calc_coefficient(self.intercept, corrector_ind)

        else:
            self.corr_df = self.corr_df.append(a_series, ignore_index=True)
            last_ind = self.corr_df.shape[0] - 1
            start_ind = last_ind

            if self.corr_df.shape[0] > 1:

                if self.corr_df.loc[[last_ind], ['En_meas']].values[0] < self.corr_df.loc[[last_ind - 1], ['En_meas']].values[0]:
                    self.corr_df.sort_values(by=['En_meas'], inplace=True)
                    start_ind = 1

                for i in range(start_ind, last_ind + 1):
                    self.corr_df.loc[[i], ['Slope']] = self.calc_coefficient(self.slope, last_ind)
                    self.corr_df.loc[[i], ['Intercept']] = self.calc_coefficient(self.intercept, last_ind)

    def calc_coefficient(self, line_func_coefficient, index):

        y1 = self.corr_df.loc[[index], ['Corr']].values[0]
        y2 = self.corr_df.loc[[index - 1], ['Corr']].values[0]
        x1 = self.corr_df.loc[[index], ['En_meas']].values[0]
        x2 = self.corr_df.loc[[index - 1], ['En_meas']].values[0]

        return line_func_coefficient(x1, y1, x2, y2)

    @staticmethod
    def slope(x1: float, y1: float, x2: float, y2: float) -> float:
        return (y1 - y2) / (x1 - x2)

    @staticmethod
    def intercept(x1: float, y1: float, x2: float, y2: float) -> float:
        return (y1 * x2 - y2 * x1) / (x2 - x1)


def adjust_region(df_to_adjust: pd.DataFrame, df_main: pd.DataFrame) -> pd.DataFrame:
    cols = df_main.columns
    interp_func = interpolate.interp1d(df_to_adjust.iloc[:, 0], df_to_adjust.iloc[:, 1],
                                       kind='quadratic',
                                       fill_value='extrapolate')

    return pd.DataFrame(data={cols[0]: df_main.iloc[:, 0], cols[1]: interp_func(df_main.iloc[:, 0])})


en_corrector = LinearCorrector('En_meas', 'En_real')


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
        en_corrector.add_to_corrector(corr)

    elif not pd.isna(Io_file_num):
        Io_filename = line['First part of file name'].values[0] + str(int(Io_file_num)) + '.dat'
        Ir_filename = line['First part of file name'].values[0] + str(int(Ir_file_num)) + '.dat'
        new_filename = str(int(line['file #'].values[0])) + '.dat'

        scan_type = line['Scan m. 1'].values[0]

        Io_data = read_dat_file(path_dat_files + Io_filename, kth_Io, scan_type)
        Ir_data = read_dat_file(path_dat_files + Ir_filename, kth_Ir, scan_type)

        if (Ir_data is None) or (Io_data is None):
            continue

        Ir_Io = Ir_data

        if scan_type == 'en':
            corr_df = en_corrector.corr_df

            if Ir_data.shape != Io_data.shape:
                Io_data = adjust_region(Io_data, Ir_data)

            Ir_Io.intensity = Ir_data.intensity / Io_data.intensity * 100

            # Energy correction
            for corr_ind in corr_df.index:

                # Find required range
                if Ir_Io.en.mean() < corr_df.loc[[corr_ind], 'En_meas'].values[0]:
                    Ir_Io.en = Ir_Io.en + Ir_Io.en * corr_df.loc[[corr_ind], 'Slope'].values[0] + \
                               corr_df.loc[[corr_ind], 'Intercept'].values[0]
                    break

        elif scan_type == 'tha':
            Ir_Io.intensity = Ir_data.intensity / Io_data.intensity.mean() * 100

        Ir_Io.to_csv(path_processed_dat_files + new_filename, sep='\t', index=False, float_format="%.10f")

# TODO: Добавить обработку NEXAFS
# TODO: Автоматически определять kithley (по возможности)
