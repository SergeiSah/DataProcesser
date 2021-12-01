import plotly.graph_objects as go
from file_reader import *
import pandas as pd
import numpy as np

MEAS_DATE = "2021.11"
PATH_LOG = f"../{MEAS_DATE}/For_fast_processing.xlsx"
PATH_PROCESSED_FILES = f"../{MEAS_DATE}/Файлы/Обработанные/"

# files_to_plot = ['6019', '6021', '6023']  # VP-454-0 R(tha)

# files_to_plot = ['5808', '5810', '5812', '5814', '5816', '5818']  # VP-495-300 R(tha)
# files_to_plot = ['5868', '5873', '5876', '5879', '5882', '5885']  # VP-497-300 R(tha)
# files_to_plot = ['5867', '5872', '5875', '5878', '5881', '5884']  # VP-498-300 R(tha)

# files_to_plot = ['5887', '5889', '5891', '5893']  # VP-454-300 R(tha)
# files_to_plot = ['5986', '5990', '5993', '5996']  # VP-465-300 R(tha)
# files_to_plot = ['5988', '5991', '5994', '5997']  # VP-467-300 R(tha)

# files_to_plot = ['5856', '5865', '5962', '5969', '5963', '5970']  # VP-454,465,467-300 R(E)
# files_to_plot = ['5802', '5806', '5850', '5862', '5851', '5863']  # VP-495,497,498-300 R(E)

# files_to_plot = ['6078', '6081', '6084', '6087', '6090', '6093']  # VP-495-450 R(tha)
# files_to_plot = ['5974', '5976', '5978', '5980', '5982', '5984']  # VP-497-450 R(tha)
# files_to_plot = ['6079', '6082', '6085', '6088', '6091', '6094']  # VP-498-450 R(tha)
# files_to_plot = ['6062', '6070', '5965', '5972', '6063', '6071']  # VP-495,497,498-450 R(E)

# files_to_plot = ['6105', '6107', '6109', '6115']  # VP-454-450 R(tha)
# files_to_plot = ['6096', '6099', '6102', '6111']  # VP-465-450 R(tha)
# files_to_plot = ['6097', '6100', '6103', '6113']  # VP-467-450 R(tha)
# files_to_plot = ['6068', '6076', '6065', '6073', '6066', '6074']  # VP-454,465,467-450 R(E)

# files_to_plot = ['7694', '7696', '7698', '7700', '7702']    # PR-467
# files_to_plot = ['7704', '7706', '7708']    # PR-457
# files_to_plot = ['7710', '7712', '7714']    # RM-322
# files_to_plot = ['7740', '7739', '7735', '7736']    # ScL + NK: RM-454, RM-455, RM-456, RM-458
# files_to_plot = ['7745', '7744', '7742', '7743', '7758', '7777', '7759']    # OK: RM-454, RM-455, RM-456, RM-458, RM-469, RM-468
# files_to_plot = ['7752', '7755', '7753', '7754', '7764', '7785']    # ScL + NK_short: RM-454(2), RM-455, RM-458, RM-469, RM-468
# files_to_plot = ['7762', '7793', '7795', '7794']    # CrL: PR-414, RM-462, RM-460, RM-468
files_to_plot = ['7788', '7789', '7790', '7791']    # NK:


log = read_excel_log(PATH_LOG)
log.dropna(subset=['file #'], inplace=True)
log['file #'] = log['file #'].astype(int).astype(str)

fig = go.Figure()

peaks = np.array([[], []])

# TODO: Автоматически определять тип построения R(tha), R(E)
# TODO: Добавить тип построения TEY
for file_num in files_to_plot:
    file = pd.read_csv(PATH_PROCESSED_FILES + file_num + '.dat', sep="\t")
    info = log[log['file #'] == file_num]

    peaks = np.append(peaks, file[file.intensity == file.intensity.max()].values.reshape(2, 1), axis=1)

    line_name = info['Sample info'].values[0]
    if file.columns[0] == 'tha':
        line_name += ' [' + str(round(info['en'].values[0], 1)) + 'eV]'
    elif file.columns[0] == 'en':
        line_name += ' [' + str(info['tha'].values[0]) + '°]'

    fig.add_trace(go.Scatter(x=file.iloc[:, 0], y=file.iloc[:, 1],
                             mode='lines',
                             name=line_name))

peaks = np.around(peaks[:, peaks[0, :].argsort()], decimals=2)
fig.add_trace(go.Scatter(x=peaks[0], y=peaks[1],
                         mode='text+markers',
                         text=peaks[1],
                         textposition='top center',
                         showlegend=False))

fig.show()
