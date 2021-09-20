import pandas as pd


def read_excel_log(excel_filepath):
    return pd.read_excel(io=excel_filepath,
                         usecols="A:C,K,L,S,U,V,Y:BA",
                         header=1)


def read_dat_file(dat_filepath, kth_num, scan_type):
    df = pd.read_csv(dat_filepath, skiprows=85, sep='\s+')
    kth = 'kth' + str(kth_num)
    new_df = pd.concat([df[df.columns[0]], df[kth] / df['ringc']], axis=1)
    return new_df.rename(columns={0: 'intensity', df.columns[0]: scan_type})
