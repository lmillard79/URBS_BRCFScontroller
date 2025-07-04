import process_LP_ALL_AEPs_DMFM_Compare as lp_all
import pickle
import numpy as np
import os

# Some varibables for processing.
aep_list = ['2','5','10','20','50','100','200','500','2000','10000','100000']
updated_tw_set = set(['072_0054','012_0381','096_0261','168_0086','120_0625','096_0774','096_0889','018_0789'])  # Taken from eventFinder_Stage5_0380.py

# Open up the pre-processed detailed model long sections
data_loc = r'C:\Projects\Python\TUFLOW'
pkl_file = open(os.path.join(data_loc,'DM_B15ts.pkl'), 'rb')
ts_data = pickle.load(pkl_file)
pkl_file.close()
res_files = ts_data['all_res_files']

# Load the fast model results
data = np.load(r"C:\Projects\Python\TUFLOW\Final_Selection_380.npz")
ev_max = data['ev_max']
ev_max = np.transpose(ev_max)

# Output Long Sections all AEP
lp_all.long_section('Bris',res_files,ev_max, 'Plot 999 - Brisbane River Longitudinal Profiles Maximums - All AEPs',False,aep_list,updated_tw_set)
