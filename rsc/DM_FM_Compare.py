import os
import numpy as np
import matplotlib.pyplot as plt
import glob
import TUFLOW_results2015

# Read the events and tailwater data into memory
#eif = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\ResultProcessing\TUFLOW_0360\Python\TUFLOW\Event_Selection\Events_Summary_0360_61.csv'


# Get the list of events
eif = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\ResultProcessing\TUFLOW_0360\Python\TUFLOW\Event_Selection\test.csv'
events  = np.genfromtxt(eif, delimiter=",",skip_header=1,usecols=(0,1),dtype=[('event','S8'),('ari','i8 ')])
ev=events['event']
aep=events['ari']
all_dur = ['012','018','024','036','048','072','096','120','168']
#all_res_path = 'B:\\B20702 BRCFS Hydraulics\\50_Hydraulic_Models\\500_MCA\\TUFLOW\\F\\results\\360\\360\\'
out_summary = r'C:\Projects\Python\DM_FM_Compare.csv'


# Load the fast model results
data = np.load("Final_Selection.npz")  # Saved by eventFinder_Stage5_0360
fm_event = data['ev_max']
#fm_aep_diff= data['ens_max_ld']  # Not required at this stage. Could be useful for backing out AEP levels if needed.
fm_level=data['ens_max_lev']


print('debug')

### Load all the fast model results
##
##
##
##
### Open the fast model results for each run. Check whether the peak level exceeds the GHD
### storm tide level for that aep. If so, append it to the naughty list.
### Also, create a plot of downstream boundary, gateway, hawthorne and city gauge.
### Create a table Event, AEP, Downstream peak level, GHD ST, Difference (DS - GHD)
##
##ds_max = []    # Node BR80_12070.2  >> Col 435 refer res.Data_1D.H.ID
##gate_max = []
##haw_max = []
##city_max = []
##
### Return a list of Storm Tide levels based on the contents of ARI
##st_levs = np.interp(aep,tw_data[:,0],tw_data[:,1],left=tw_data[-1,1],right=tw_data[-1,1])
##
### Loop through the events
##for ii,ee in enumerate(ev):
##
##    try:
##        # Get the duration
##        dur = ee.split('_')[0]
##        res_dir = all_res_path + dur + '\\plot\\'
##        res_file = res_dir + 'BR_F_' + ee + '_MC_0360_MC.tpc'
##
##    # Intilise and open the data structure
##        res = TUFLOW_results2015.ResData()
##        error, message = res.Load(res_file)
##
##        # Add the peak water level to some lists
##        ds_max.append(res.Data_1D.Node_Max.HMax[435])
##        gate_max.append(res.Data_RL.P_Max.HMax[15])
##        haw_max.append(res.Data_RL.P_Max.HMax[14])
##        city_max.append(res.Data_RL.P_Max.HMax[13])
##
##    except:
##        print('Issue opening ' + ee + ' moving on...')
##
### Now we have max levels at key points. Setup the table
##ds_max = np.array(ds_max)
##gate_max = np.array(gate_max)
##haw_max = np.array(haw_max)
##city_max = np.array(city_max)
##st_diff = ds_max - st_levs
##
##
### open a file for output
##with open(out_summary, 'w') as f:
##    # Write header
##    f.write('Event,AEP,Peak Level Downstream Boundary (mAHD),GHD Stormtide AEP Level(mAHD),Difference (BMT WBM - GHD), Peak Level Downstream Gateway (mAHD),Peak Level Hawthorne (mAHD),Peak Level City (mAHD)\n')
##
##    for ii, row in enumerate(ev):
##        f.write('%s,%u,%f,%f,%f,%f,%f,%f\n'  % (ev[ii],aep[ii],ds_max[ii],st_levs[ii],st_diff[ii],gate_max[ii],haw_max[ii],city_max[ii]))
##
##print('dd')

