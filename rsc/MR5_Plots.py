#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Mitchell.Smith
#
# Created:     08/07/2015
# Copyright:   (c) Mitchell.Smith 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import numpy as np
import bris_utilities as utl
import os
import process_LP_Functionised_DM as lp
import process_LP_ALL_AEPs_DM as lp_all
import plotData as pd
import pickle



def out_ts(aep_list,data_file,out_plot,runtype):
    # Plot the timeseries outputs

    # Knock over the design event timeseries
    pkl_file = open(data_file, 'rb')
    ts_data = pickle.load(pkl_file)
    pkl_file.close()

    qts = ts_data['qts']
    hts = ts_data['hts']
    res_files = ts_data['all_res_files']


    for aa,aep in enumerate(aep_list):
        event_ll = []

        if runtype == 'Design' or runtype == 'Sens':
            for rr in res_files[aa]:
                event_ll.append(rr[-16:][:-8])  # tmp
                    # Just get the time array.
            t = qts[0]
            t = t[0,0,:]

        if runtype == 'Sens':
            aa = 2  # The 100 y sits in the third column.
            #aa = 0  # The 100 y sits in the third column. MJS, was only when Barry hadn't run all events.

        elif runtype == 'Cal':
            aa = 3
            t = qts[aa]
            t = t[0,0,:]

        plot_figs = utl.get_plot_figs(aep,'dm_ts')
        dur = '012'
        loc_names = utl.get_loc_names()

        QQ = qts[aa]
        print QQ.shape
        QQ =  QQ[1:,:,:] # remove time column
        print QQ.shape
        QQ = np.swapaxes(np.swapaxes(QQ,1,2),0,2) # swap the axis to be compatible with the timeseris output
        QQ[QQ==-99999]=np.nan   # Set -99999 values to Nan for plotting.
        print QQ.shape
        HH = hts[aa]
        HH =  HH[1:,:,:] # remove time column
        HH = np.swapaxes(np.swapaxes(HH,1,2),0,2)
        HH[HH==-99999]=np.nan
        m = len(loc_names)

        if runtype == 'Cal':
            # Just grab the no dams run
            event_ll = ['2011_WithDams','2011_NoDams']
            pd.plot_A3_RL(t,QQ,HH,[90,350],'Time (hrs)','Water Level (mAHD)','EV_TS_out'+str(aep),loc_names,dur,out_plot,'time_series_dm',False,event_ll,plot_figs)
        else:
            ## Need to ensure that event number is output to file
            pd.plot_A3_RL(t,QQ,HH,[0,240],'Time (hrs)','Water Level (mAHD)','EV_TS_out'+str(aep),loc_names,dur,out_plot,'time_series_dm',False,event_ll,plot_figs)

def main():

    # Load in the previously processed datasets
    aep_list = ['2','5','10','20','50','100','200','500','2000','10000','100000']
    dm_ts_out = ['CC1','CC2','CC3','CC4','ND']
    data_loc = r'C:\Projects\Python\TUFLOW'
    out_plot = r'C:\Projects\Python\TUFLOW\ReportPlots'

# ==============================================================================
    # Series of switche
    ts_plot_out = False  # Output timeseries plots of the event selection.
    long_plot_out = True    # Output the long sections

 # ==============================================================================
    if ts_plot_out:
        sout_ts(aep_list,os.path.join(data_loc,'DM_B15ts.pkl'),out_plot,'Design')
        out_ts(['CC1'],os.path.join(data_loc,'DM_CC1ts.pkl'),out_plot,'Sens')
        out_ts(['CC2'],os.path.join(data_loc,'DM_CC2ts.pkl'),out_plot,'Sens')
        out_ts(['CC3'],os.path.join(data_loc,'DM_CC3ts.pkl'),out_plot,'Sens')
        out_ts(['CC4'],os.path.join(data_loc,'DM_CC4ts.pkl'),out_plot,'Sens')
        out_ts(['ND'],os.path.join(data_loc,'DM_calts.pkl'),out_plot,'Cal')

    if long_plot_out:

          # Knock over the design event timeseries
        pkl_file = open(os.path.join(data_loc,'DM_B15ts.pkl'), 'rb')
        ts_data = pickle.load(pkl_file)
        pkl_file.close()
        res_files = ts_data['all_res_files']

        # Output Long Sections per AEP
        for i, ens in enumerate(res_files):
            lp.long_section('Bris',ens,utl.get_plot_figs(aep_list[i],'ls_dm')[0],False,aep_list[i])
            lp.long_section('BremLock',ens,utl.get_plot_figs(aep_list[i],'ls_dm')[1],False,aep_list[i])

        # Output Long Sections all AEP
        lp_all.long_section('Bris',res_files, 'Plot 45 - Brisbane River Longitudinal Profiles Maximums - All AEPs',False,aep_list)
        lp_all.long_section('BremLock',res_files,'Plot 57 - Bremer/Lockyer Longitudinal Profiles Maximums - All AEPs',False,aep_list)


if __name__ == '__main__':
    main()
   # pd.main() # Output all required non-time, babbister or longseries plots for MR4 Reporting
