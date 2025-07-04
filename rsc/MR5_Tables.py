#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Mitchell.Smith
#
# Created:     01/06/2016
# Copyright:   (c) Mitchell.Smith 2016
# Licence:     <your licence>

#

#-------------------------------------------------------------------------------
import TUFLOW_results2016
import os
import glob
import numpy as np
import bris_utilities as utl
import pickle

def open_res(tpc_file):
    """
    Open the TUFLOW result object set.
    """
    #initialise and load results
    res = TUFLOW_results2016.ResData()
    error, message = res.Load(tpc_file)
    if error:
        print message
    return res

def get_RL_TS(res):
    """
    Gets peak flow and water level lists for a given run.
    """
    return res.Data_RL.Q_L.Values[:,1:], res.Data_RL.H_P.Values[:,1:]

def get_RL_Max(res):
    """
    Gets peak flow and water level lists for a given run.
    """
    return res.Data_RL.L_Max.QMax, res.Data_RL.P_Max.HMax


def get_RL_QH(res_files,ensemble):
    """
    Combines all ensemble results for a given event and extracts the max max for both flow and water level.
    Also gets a matrix of the timeseries data.
    """
    # Get some info on the required array sizes
    res = open_res(res_files[1]) # Open a Res object just to get the right sizes for the array storage.
    t,m = res.Data_RL.Q_L.Values[:,1:].shape
    t,n = res.Data_RL.H_P.Values[:,1:].shape

    # Prepare a numpy array to hold the maximum datasets
    res_q = np.zeros((m-1,len(res_files)),dtype=float)   # Space to later save maximum vector
    res_h = np.zeros((n-1,len(res_files)),dtype=float)
    res_q_ts = np.zeros((m,len(res_files),t),dtype=float)  # hardcoded, will only work with DM design events 0.25 hr output over 240 hrs = 961
    res_h_ts = np.zeros((n,len(res_files),t),dtype=float)  # hardcoded, will only work with DM design events 0.25 hr output over 240 hrs = 961


    # Loop through each of the tpc files and add the results to the
    for i,tpc in enumerate(res_files):
        res = open_res(tpc) # Open Res object

        Qts,Hts = get_RL_TS(res)
        res_q_ts[:,i,:] = np.transpose(np.array(Qts))
        res_h_ts[:,i,:] = np.transpose(np.array(Hts))

        Qm,Hm = get_RL_Max(res)
        res_q[:,i] = np.array(Qm)
        res_h[:,i] = np.array(Hm)

        if ensemble:
            # Extract the ensemble max and return

            # Get the sign of all flow values and ensure the absolute max is output
            res_q_max = np.amax(res_q,axis=1) # axis = 1 takes the maximum of events at a given location
            res_q_min= np.amin(res_q,axis=1) # axis = 1 takes the maximum of events at a given location
            mask = np.absolute(res_q_max) < np.absolute(res_q_min)
            res_q_max[mask] = res_q_min[mask]

			# This assumes maximum water level is above 0.
            res_h_max = np.amax(res_h,axis=1)

        else:
            res_q_max = res_q
            res_h_max = res_h

    return res_q_max, res_h_max, res_q_ts,  res_h_ts


def MR5_res_walker(res_loc):
    """
    Returns a numpy array of maxes containing all AEPs for a given input directory.
    Also returns a list of timeseries outputs
    """
    h_list = []
    q_list = []
    hts_list = []
    qts_list = []
    all_res_files = []

    # Extract data from each of the tpc files
    for dirpath, dirnames, files in os.walk(res_loc):
        for d in dirnames:
            if d =="plot":
                res_files = glob.glob(dirpath + '\\' + d + '\\*.tpc')
                all_res_files.append(res_files)

                # Grab the maximum from the ensemble or the relevant dam and no-dam cases for cal.
                if os.path.split(res_loc)[1] == 'cal':
                    q_tmp,h_tmp,qts_tmp,hts_tmp = get_RL_QH(res_files,False)  # Don't take the max max if calibration.
                    qnd = q_tmp[:,0]
                    qwd = q_tmp[:,1]
                    q_list.append(qnd)
                    q_list.append(qwd)
                    hnd = h_tmp[:,0]
                    hwd = h_tmp[:,1]
                    h_list.append(hnd)
                    h_list.append(hwd)
                    hts_list.append(hts_tmp)
                    qts_list.append(qts_tmp)


                else:
                    # Calc the ensemble maximum.
                    q_tmp,h_tmp,qts_tmp,hts_tmp = get_RL_QH(res_files,True)
                    q_list.append(q_tmp)
                    h_list.append(h_tmp)
                    hts_list.append(hts_tmp)
                    qts_list.append(qts_tmp)


    return np.vstack(q_list),np.vstack(h_list),qts_list,hts_list,all_res_files


def MR5_res_saver(base_dir,dir_list):
    """
    Loops through each of the result directory and saves off a numpy array to disk for each folder with the max maxes stacked by aep.
    """

    # Loop through the result directories.
    for dd in dir_list:
        try:

            # Save off the maximums to a numpy array.
            dpath = os.path.join(base_dir,dd)
            max_q,max_h,q_ts,h_ts,all_res_files = MR5_res_walker(dpath)
            np.savez('DM_' + dd , max_q=max_q,max_h=max_h)

            # Dump the timeseries list as a pickle.
            data = {'qts': q_ts, 'hts': h_ts,'all_res_files':all_res_files}
            #data = {'qts': q_ts, 'hts': h_ts}
            output = open('DM_' + dd + 'ts.pkl', 'wb')
            pickle.dump(data, output)
            output.close()

        except ValueError:
            print('Issue with run in folder: ' + dd)
            continue

def table_baseline(q,wl,rl,aep_list,out_table):
    """
    Only purpose is to output the baseline tables for MR5
    """

    with open(out_table,'w+') as f:

        # Write header H
        f.write('Location,')
        for aa,aep in enumerate(aep_list):
            f.write('1 in ' + aep + ' Level (mAHD),')
        # Write remaining Header Q
        for aa,aep in enumerate(aep_list):
            f.write('1 in ' + aep + ' Flow (m^3/s),')
            if aa == len(aep_list)-1:
                f.write('\n')

        # Write out the data
        for i,ll in enumerate(rl):
            f.write(ll + ',')
            for j in range(len(aep_list)):                  # H
                f.write('%(level)4.2f,' % {"level": wl[j,i]})
            for j in range(len(aep_list)):                  # Q
                f.write('%(flow)6.2f,' % {"flow": q[j,i]})
                if j == len(aep_list)-1:
                    f.write('\n')

def table_sens(q_new, wl_new, q_old, wl_old, rl,aep_list,out_table):

    # Calc the diff.
    q_diff = q_new - q_old
    h_diff = wl_new - wl_old

    with open(out_table,'w+') as f:
        # Write header H
        f.write('Location,')
        for aa,aep in enumerate(aep_list):
            f.write('1 in ' + aep + ' Level (mAHD), dH (m),')
        # Write remaining Header Q
        for aa,aep in enumerate(aep_list):
            f.write('1 in ' + aep + ' Flow (m^3/s), dQ (%),')
            if aa == len(aep_list)-1:
                f.write('\n')

        # Write out the data
        for i,ll in enumerate(rl):
            f.write(ll + ',')
            for j in range(len(aep_list)):                                  # H
                f.write('%(level)4.2f,%(dh)4.2f,' % {"level": wl_new[j,i],"dh": h_diff[j,i]})
                #f.write('%(level)4.2f,%(dh)4.2f,' % {"level": wl_old[j,i],"dh": h_diff[j,i]})   # no dams 6/10/2016
            for j in range(len(aep_list)):                                  # Q

                if abs(q_diff[j,i]/q_old[j,i]*100) > 0.1:
                    f.write('%(flow)6.2f,%(dq)4.1f,' % {"flow": q_new[j,i],"dq": (q_diff[j,i]/q_old[j,i]*100)})
                    #f.write('%(flow)6.2f,%(dq)4.1f,' % {"flow": q_old[j,i],"dq": (q_diff[j,i]/q_old[j,i]*100)})    # no dams 6/10/2016
                elif abs(q_diff[j,i]/q_old[j,i]*100) <= 0.1:
                    #f.write('%(flow)6.2f,<0.1,' % {"flow": q_old[j,i]})    # no dams 6/10/2016
                    f.write('%(flow)6.2f,<0.1,' % {"flow": q_new[j,i]})    #
                else:
                    print('Unexpected value when calculating difference outputs')
                if j == len(aep_list)-1:
                    f.write('\n')

#===============================================================================
#===============================================================================
if __name__ == "__main__":

## ============================USER INPUT DATA==================================
    aep_list = ['2','5','10','20','50','100','200','500','2000','10000','100000']
    cc_bl_aep_list = ['5','20','100','10000']
    ff_aep_list = ['100','200','500','10000']
    cal_list = ['1974','1996','1999','2011','2013']
    dir_list = ['B15','BL1', 'BL2', 'cal', 'CC1', 'CC2', 'CC3', 'CC4', 'FF1']
    #dir_list = ['cal']
    #dir_list = [ 'CC1', 'CC2', 'CC3', 'CC4']
    #dir_list = ['CC1']
    base_dir = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\600_D_Design_Events\TUFLOW\D\results\605'
    process_res = False
    all_res_files = []

## ============================ EXTRACT THE DATA ===============================
    # Extract the peak flows and levels and save them to disk as needed.
    if process_res:
        MR5_res_saver(base_dir,dir_list)

## =========================COMPLETE THE TABLES=================================
    # Baseline Table
    rl = utl.get_loc_names()
    data = np.load(r"C:\Projects\Python\TUFLOW\DM_B15.npz")
    b15_q = data['max_q']
    b15_h= data['max_h']
    table_baseline(b15_q,b15_h,rl,aep_list,'MR5_Baseline.csv')

    # CC and BL
    sss = ['CC1', 'CC2', 'CC3', 'CC4','BL1','BL2']
    for c in sss:
        data = np.load(r"C:\Projects\Python\TUFLOW\DM_" + c + ".npz")
        cc_q = data['max_q']
        cc_h = data['max_h']
        table_sens(cc_q, cc_h, b15_q[[1,3,5,9],:], b15_h[[1,3,5,9],:], rl, cc_bl_aep_list, 'MR5_' + c + '.csv')

    # FF
    data = np.load(r"C:\Projects\Python\TUFLOW\DM_FF1.npz")
    cc_q = data['max_q']
    cc_h = data['max_h']
    table_sens(cc_q, cc_h, b15_q[[5,6,7,9],:], b15_h[[5,6,7,9],:], rl, ff_aep_list, 'MR5_FF1.csv')

    # Dams
    data = np.load(r"C:\Projects\Python\TUFLOW\DM_cal.npz")
    cal_q = data['max_q']
    cal_h= data['max_h']

    cal_hwd = cal_h[[1,2,4,6,8],:]           # wl with dams  # note 1974 (first two columns) switched 0 and 1 indices as doing without dams - dams
    cal_hnd = cal_h[[0,3,5,7,9],:]          # wl no dams    # note 1974 (first two columns) switched 0 and 1 indices as doing without dams - dams
    cal_qwd = cal_q[[1,2,4,6,8],:]          # flow with dams # note 1974 (first two columns) switched 0 and 1 indices as doing without dams - dams
    cal_qnd = cal_q[[0,3,5,7,9],:]           # flow no dams # note 1974 (first two columns) switched 0 and 1 indices as doing without dams - dams

    #table_sens(cal_qnd, cal_hnd, cal_qwd, cal_hwd, rl, cal_list, 'MR5_Cal.csv')
    table_sens(cal_qwd, cal_hwd, cal_qnd, cal_hnd, rl, cal_list, 'MR5_Cal.csv')    # 6/10/2016  do dam outputs modded for final MR5 reporting. Dams - No Dams to show benefit. Levels shown as no dams.
