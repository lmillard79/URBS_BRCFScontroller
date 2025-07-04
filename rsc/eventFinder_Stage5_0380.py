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

# NOTE WHEN PROCESSING FAST MODEL RESULTS PLEASE MOD THE READ LOC NAMES FUNCTION IN BRIS UTLS to point at C:\Projects\Python\TUFLOW\LocNames.txt line 119.

import numpy as np
import bris_utilities as utl
import os
import eventFinder as evtFinder
import tcc_do as tcc
#import time
import process_LP_Functionised as lp
import process_LP_All_AEPs as lp_all
import plotData as pd
import matplotlib.pyplot as plt
import scipy.io as sio
import TUFLOW_results2015_BRFS

def bab_out(out_dir,out_file,table_type,max_arg,event_arg,level_arg,tol,aep_levels,loc_names,aep):
    # Output the Mark Babister style table and plots
    # There will be one chart per AEP
    # Open the output file

    # Get the Brief Accuracy Limits
    lims = utl.get_acc_limits()

    # Reorder the outputs
    # Lockyer and Bremer First then Brisbane. Upstream to Downstream
    site_order = [2,0,16,17,18,19,20,22,21,23,25,24,1,3,4,5,6,7,26,8,27,9,10,11,12,13,14,15]
    sites_reorder=[]
    data_reorder = np.zeros(level_arg.shape)
    aep_levels_reorder = np.zeros(aep_levels.shape)
    max_arg_reorder = np.zeros(max_arg.shape)
    tol_reorder = np.zeros(tol.shape)
    lims_reorder = np.zeros(tol.shape)

    # Reorder the sites.
    for i,ll in enumerate(loc_names):

        uind = site_order[i]
        sites_reorder.append(loc_names[uind])
        tol_reorder[i] = tol[uind]
        lims_reorder[i] = lims[uind]

        data_reorder[i] = level_arg[uind]
        aep_levels_reorder[i] = aep_levels[uind]
        max_arg_reorder[i] = max_arg[uind]

##        # If aep 10 year or less, interpolate Woogaroo based on adjacent sites Moggill and Jindalee
##        if (aep == '2' or aep == '5' or aep == '10' or aep == '20') and uind == 26:    # Was previously required for Woogaroo resutls. With 0360 series is ok to remove.
##
##            data_reorder[i] = (level_arg[7]+level_arg[8])/ 2
##            aep_levels_reorder[i] = (aep_levels[7] + aep_levels[8]) /2
##            max_arg_reorder[i] = max_arg[7] + max_arg[8] / 2
##
##        else:
##            data_reorder[i] = level_arg[uind]
##            aep_levels_reorder[i] = aep_levels[uind]
##            max_arg_reorder[i] = max_arg[uind]


    full_path = os.path.join(out_dir,out_file)
    with open(full_path,'w') as f:

    # Output the header
        f.write('Location,')
        if table_type == 'Level':
            f.write('1 in ' + aep + ' Year AEP Level (mAHD),' 'Tolerance (mAHD),' 'Maximum (mAHD),')
            for i,ens in enumerate(event_arg):
                f.write('%(event)s (mAHD),' % {"event" : evtFinder.index_to_dur_event(ens)})
                if i == len(event_arg)-1:
                    f.write('\n')
            tol = tol + aep_levels

        elif table_type == 'Diff':
            f.write('1 in ' + aep + ' Year AEP Level (m),' 'Tolerance (m),' 'Maximum (m),')
            for i,ens in enumerate(event_arg):
                f.write('%(event)s (m),' % {"event" : evtFinder.index_to_dur_event(ens)})
                if i == len(event_arg)-1:
                    f.write('\n')
            aep_levels = np.zeros(aep_levels.shape)

        else:
            print 'table type needs to be either ''Level'' of ''Diff'''
            return

    # Output the data
        for i,ll in enumerate(sites_reorder):
            # Write the aep and tolerance
            f.write(ll + ','+ str(aep_levels_reorder[i]) +','+ str(tol_reorder[i]) +',')

            # Write out the maximum
            f.write(str(max_arg_reorder[i]) +',')

            # Write the data for each event
            for j,ens in enumerate(event_arg):
                f.write('%(level)4.2f,' % { 'level' : data_reorder[i,j]})
                if j == len(event_arg)-1:
                    f.write('\n')

    return data_reorder, max_arg_reorder, tol_reorder, lims_reorder, sites_reorder

def strictly_increasing(L):
    return all(x<y for x, y in zip(L, L[1:]))


def run_long_bat(comm,run_dir):

    print('Running Long Section Bat File')
    from subprocess import Popen
    p = Popen(comm, cwd=run_dir)
    stdout, stderr = p.communicate()
    print stdout

def write_wll_condor(ensemble,file_out):

   for i,ev in enumerate(ensemble):
    ev_str = evtFinder.index_to_dur_event(ev)
    durs = ev_str[0:3]
    events = ev_str[4:]
    utl.htcondor_out(file_out,durs,events)

def write_lp_bat(ensemble,base_mc_dir,t2gis,mif):

    mid = mif.replace('mif','mid')
    mif_local = os.path.split(mif)[1]
    mif_local = mif_local.replace('"','')

    for i,ev in enumerate(ensemble):
        ev_str = evtFinder.index_to_dur_event(ev)
        durs = ev_str[0:3]
        events = ev_str[4:]

        # Setup the bat file in the correct directory
        res_dir = base_mc_dir + '\\' + durs
        bat_file = os.path.join(res_dir + '\\long_section.bat')

        # Copy the mif file into the correct directory
        print tcc.tcc_do('copy','/z',mif, '', '"'+res_dir+'"')
        print tcc.tcc_do('copy','/z',mid, '', '"'+res_dir+'"')

        with open(bat_file,'w') as f:
            f.write('Setlocal\n')

            # Write the duration Loop
            f.write('set A=')
            f.write("%(dur)s\n" % {"dur": durs})

           # if durs == '036':
            #    print('debug')

            print(ev_str)
            # Write the event loop
            f.write('set B=')
            f.write("%(ev)s\n" % {"ev": events})
            f.write('FOR %%a in (%A%) do (\n')
            f.write('   FOR %%b in (%B%) do (\n')
            f.write('       %(t2gis)s -b -lp %(mif)s -typeH -t99999 BR_F_%%%%a_%%%%b_MC_0360_MC.xmdf\n' % \
                {'t2gis':t2gis,'mif': mif_local})   # Filenames are hardcoded be careful.
            f.write('   )\n')
            f.write(')\n')

        run_long_bat(bat_file,res_dir)  # Extract the long section

def main():

    # Load in the previously processed datasets
    data = np.load("Event_Selection_0360.npz")
    aep_list = ['2','5','10','20','50','100','200','500','2000','10000','100000']
    out_dir = 'C:\\Projects\\Python\\TUFLOW\\Event_Selection\\'
    out_plot = r'C:\Projects\Python\TUFLOW\ReportPlots'
    out_file = 'Stage5_Summary_3_Groups_380.csv'
    bab_out_lev = 'Babister_Output_Lev_'
    bab_out_diff = 'Babister_Output_Diff_'
    out_np_res =  'Final_Selection_380.npz'

    # For Long Section Extraction
    t2gis = r'"C:\Projects\BRFS\Long_Sections\TUFLOW_to_GIS\w64\TUFLOW_to_GIS_w64.exe"'
    base_mc_dir = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\TUFLOW\F\results\360\360'
    lsect_mif = r'"C:\Projects\BRFS\Long_Sections\LP_003.mif"'

    # For amended tailwaters
    #tw_resim_path = r'C:\Projects\BRFS\TUFLOW\F\results\360'

#===============================================================================
    # Load WL
    level_diff_aep = data['level_diff_aep'] # First row is the closest set of n events. 2nd row 2nd, etc.
    event_list_aep = data['event_list_aep'] # First row is the closest set of n events.
    level_list_aep = data['level_list_aep'] # First row is the closest set of n events.
    event_list = data['event_list']
    level_diff = data['level_diff']
    level_list = data['level_list']
    tol_all_aep = data['tol_all_aep']

    # Load Volume info
  #  allResVol = data['allResVol']

    URBS_Vols = sio.loadmat(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\MC_Boundary_Processing\netCDF\test_2\URBS_Vol.mat')
    URBS_Vols= URBS_Vols['URBS_Vol']

# ==============================================================================
    # Series of switche
    get_wll = False          # Output a condor file to allow resimulation with WLLs reduced. This needs to be run and all selected MC runs re-simed before lp_process. NOT REQUIRED FOR 0360 series as they had WLL added from the getgo
    lp_process = False     # Process long sections using TUFLOW to GIS
    ts_plot_out = False   # Output timeseries plots of the event selection.
    long_plot_out = True     # Output the long sections
    out_bab = False
    out_dmbat = False   # Output batch files to copy ts1 files and run the detailed model.

    if out_dmbat:

        dm_tcf = 'BR_D_~s1~_~s2~_~s3~_~e1~_545_BCS.tcf'
        dm_exe = r'C:\TUFLOW\Releases\2015-XX\w64\2015-09-AE\TUFLOW_iSP_w64.exe'
        timeout_period = '60'
        out_dmbat_file = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_D_Design_Events\Tuflow\runs\Run_546_30m_MC_001.bat'
        ts1_bat = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\TUFLOW\bc_dbase\Extract_Production_TS1.bat'
        src = r'"B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_D_Design_Events\Tuflow\bc_dbase\MC\"'
        dest = r'"B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\Delivery\TUFLOW\bc_dbase\MC\"'

        ff = True

        # Delete any existing bat file as we will need to append to the newly created on later.
        try:
            os.remove(out_dmbat_file)
            os.remove(ts1_bat)

        except:
            pass
# ==============================================================================
    # Prepare datasets
    ensemble_set =[]
    m,n,o = level_diff_aep.shape
    ens_max_ld = np.zeros([m,o])
    ens_max_lev = np.zeros([m,o])
    ens_size = np.zeros(m)
    ens_total = np.zeros(1)
    ev_max = np.zeros([m,o])

   #get a list of events that need to be removed from selection
    e4r = []
    e4rs = ['096_0378','168_0587','024_0808','024_0616','072_0916']
    for eee in e4rs:
        e4r.append(utl.index_to_dur_event(eee))

    e4r = set(e4r)
    event_for_removal = set([5183,10113,4294,660,5807,9526,5990,4719,4460])     #048_0143 168_0033 036_0514 012_0660 048_0767 120_0706 048_0950 036_0939 036_0680
    event_for_removal = event_for_removal | e4r
    ## MJS 24/03/16 event_for_removal
    ## The variable event_for_removal was added following the MR4 workshop to remove events that were essentially doubling up.
    ## please refer to B:\B20702 BRCFS Hydraulics\80_Workshops\160225 W4A Fast Model Results II\Presentations\B20702_W4A_2016.02.25.002.pptx
    ## for further details. At this time, the code has been modified to not output time series, babister or long sections from these events.

    for aa,aep in enumerate(aep_list):
        plot_figs = utl.get_plot_figs(aep,'ts')
        aep_levels = np.array(utl.get_aep(aep))
        aep_levels_zip = zip(range(1,29),aep_levels)
        ensemble_set =[]

        # Manual fix for wivenhoe, savages, lowood and the two mt crosby stations 5 year only  # This was all required due to non-monotonic events in the detailed model.
        if aep == '5':
            event_list_aep[aa,0,1] = event_list_aep[aa,1,1]  # Select second best at wivenhoe RL002
            event_list_aep[aa,0,3] = event_list_aep[aa,1,3]  # Select second best at lowood RL004
            event_list_aep[aa,0,4] = event_list_aep[aa,1,4]  # Select second best at savages RL005
            event_list_aep[aa,0,5] = event_list_aep[aa,1,5]  # Select second best at upper crosby RL006
            event_list_aep[aa,0,6] = event_list_aep[aa,1,6]  # Select second best at upper crosby RL007

        # Update the water level array if a tailwater boundary has been modified
        updated_tw_set = set(['072_0054','012_0381','096_0261','168_0086','120_0625','096_0774','096_0889','018_0789'])

        # Get the number of events in each row
        best_events = set(event_list_aep[aa,0,:].flatten())  # Events closest to AEP level + tolerance (so might not be the closest to the AEP level overall)
        event_keepers = best_events  - (best_events & event_for_removal)  # Remove events that are within the removal list. Refer event_for_removal comments above MJS 24/03/16
        ensemble_set.append(event_keepers)

        # Get the values of each ensemble
        for i, ens in enumerate(ensemble_set): # Give me each set.
            # Find the water levels of each event in the set at each location
            ld = np.zeros([len(ens),o])
            lev = np.zeros([len(ens),o])
            event_temp = np.zeros([len(ens)])

            # Extract a longsection for each event for processing later. Do all of them even though only the maximum ones are requried.
            if get_wll:
                write_wll_condor(ens,r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\TUFLOW\F\runs\WLL_Sub.sub')
            if lp_process:
                write_lp_bat(ens,base_mc_dir,t2gis,lsect_mif)

            # Loop through and find the event levels and differences for each event
            for j, ev in enumerate(ens):  # Give me each event in the set

                # Now loop along each location and find the index for that location
                #print ev
                event_temp[j] = ev

                # For each site
                for k in range(o): # o is the number of sites
                    ev_ind = event_list[:,k] == ev     # Returns a mask of all events for a given site

                    # Check if the event has been modded by tw  # REQUIRED DUE TO NON MONOTONIC DETAILED MODEL 28/04/16
                    tmp = utl.index_to_dur_event(float(ev))
                    ev_max_tw_check = set([tmp])

                    if set.intersection(ev_max_tw_check,updated_tw_set):
                        # Return the duration and event name from the index
                        dur,ee = list(ev_max_tw_check)[0].split('_')
                        #res_dir = tw_resim_path +'\\' + dur + '\\plot\\'  # this was done before Mitch had copied the results onto the B drive.
                        res_dir = base_mc_dir +'\\' + dur + '\\plot\\'
                        res_file = res_dir + 'BR_F_' + dur + '_' + ee + '_MC_0380_MC.tpc'

                        # Load the data
                        res = TUFLOW_results2015_BRFS.ResData()
                        error, message = res.Load(res_file)
                        tmp_data = res.Data_RL.P_Max.HMax[k]

                        # Now update ens_max_ld and ens_max_lev based on new data
                        level_list[:,k][ev_ind] = tmp_data

                    # Add levels to the level array
                    lev[j,k] = level_list[:,k][ev_ind]  # Return the RL level for that event and location

                ld[j,:]= lev[j,:] - aep_levels

            ind_ld_max = np.argmax(ld,axis=0)   # This is the event index that gives the maximum water level diff etc. [28 x 1]

            # For each ari and location add the maximum level and difference to the max array
            # This reduces the number of events to only include the maximum event levels
            for i in range(o):
                ens_max_ld[aa,i] = ld[ind_ld_max[i],i]
                ens_max_lev[aa,i] = lev[ind_ld_max[i],i]

            # Get the maximum level events and count them.
            ev_max[aa,:] = event_temp[ind_ld_max]
            ens_size[aa] = len(set(ev_max[aa,:]))
            ens_total +=ens_size[aa]

            if ts_plot_out:
                pd.plot_events(list(set(ev_max[aa,:])),base_mc_dir,out_plot,aep,aep_levels_zip,plot_figs,updated_tw_set)

    print ens_total

    # Check: Is there anywhere where the AEPs are not monotonically increasing?
    for i in range(o):
        test = strictly_increasing(ens_max_lev[:,i])
        print test

    #Print the outputs to file
    loc_names = utl.get_loc_names()
    short_loc_names = utl.get_short_loc_names()

    # Get the data in a better format to output
    ens_max_ld = np.transpose(ens_max_ld)
    ens_max_lev = np.transpose(ens_max_lev)
    ev_max = np.transpose(ev_max)       # Has the event for each ARI and Location that gives the highest level. [28,11]

    # Save off events, water levels and differences
    np.savez(out_np_res, ev_max=ev_max,ens_max_ld=ens_max_ld,ens_max_lev=ens_max_lev)

    # Open the output file
    full_path = os.path.join(out_dir,out_file)
    with open(full_path,'w') as f:

    # Output the header
        f.write('Location,')
        for aa,aep in enumerate(aep_list):
            f.write(aep + ' Year AEP - Ensemble Length ' + str(ens_size[aa]) + ' Event Name,'+ aep + ' Year AEP - Ensemble Length ' + str(ens_size[aa]) + ' Max,'+ aep + ' Year AEP - Ensemble Length ' + str(ens_size[aa]) + ' Level,')
            if aa == m-1:
                f.write('\n')
    # Output the data
        for i,ll in enumerate(loc_names):
            f.write(ll + ',')
            for j in range(len(aep_list)):
                f.write('%(event)s,%(diff)4.2f,%(level)4.2f,' % {"event": evtFinder.index_to_dur_event(ev_max[i,j]),"diff": ens_max_ld[i,j],"level": ens_max_lev[i,j]})
                if j == len(aep_list)-1:
                    f.write('\n')

    # Output babister style plots or detailed model batch files to disk.
    if out_bab or out_dmbat:
        data_reorder =[]
        max_reorder =[]
        tol_reorder =[]
        ev_set_all =[]

        # Open the batch file for writing
        if out_dmbat:
            dmbf = open(out_dmbat_file,'a')
            ts1f = open(ts1_bat,'a')

        for aa,aep in enumerate(aep_list):
            # Output the level tables
            aep_levels = np.array(utl.get_aep(aep))

            # For the given aep, get an array of levels for each event in the maximum event set.
            ev_max = np.transpose(ev_max) # Make the data easier to handle again. back to [11,28] [Aeps,sites]

            # Get the set of events for this aep
            ev_max_set = list(set(ev_max[aa,:]))

            # Setup some empty arrays to pass to the output text function
            ld = np.zeros([len(ev_max_set),o])      # This gives space for x number of events for each locations
            lev = np.zeros([len(ev_max_set),o])

            if out_dmbat:

                # Print Which ARI
                if ff:
                    dmbf.write(':: Block of runs for the %s Year ARI\n' % (aep))
                    ts1f.write('set dest=%s\n' % (dest))
                    ts1f.write('set src=%s\n\n' % (src))

                    ff = False
                else:
                    dmbf.write('\n:: Block of runs for the %s Year ARI\n' % (aep))
                dmbf.write('::##############\n')

                for enm in ev_max_set:
                    tmp = evtFinder.index_to_dur_event(enm)
                    ddd,eee = tmp.split('_')

                    if aep == '10000':
                        dmbf.write('start "TUFLOW" %s -s1 D010k -s2 %s -s3 %s -e1 MC %s\n'  % (dm_exe,ddd,eee,dm_tcf))
                    elif aep == '100000':
                        dmbf.write('start "TUFLOW" %s -s1 D100k -s2 %s -s3 %s -e1 MC %s\n'  % (dm_exe,ddd,eee,dm_tcf))
                    else:
                        dmbf.write('start "TUFLOW" %s -s1 D%04d -s2 %s -s3 %s -e1 MC %s\n'  % (dm_exe,int(aep),ddd,eee,dm_tcf))

                    dmbf.write('timeout %s\n' % (timeout_period))

                    # write ts1 info
                    ts1f.write('copy %%src%%Brisbane_%s.ts1 %%dest%%\n' % (tmp))

                print('debug')
                pass

            # For each member of the set, extract the water level at each location
            for ee,ev in enumerate(ev_max_set):

                # Now loop along each location and find the index for that location
                for k in range(o):
                    ev_ind = event_list[:,k] == ev     # Get the index of the event
                    lev[ee,k] = level_list[:,k][ev_ind]  # Return the RL level for that event and location
                ld[ee,:]= lev[ee,:] - aep_levels    # Calc the differences

            # Restore the data to original form for later processing.
            ev_max = np.transpose(ev_max) # Back to [28,11]
            lev = np.transpose(lev)
            ld = np.transpose(ld)

            # Output the Babbister Plots as requried.
            if out_bab:
                bab_out(out_dir,bab_out_lev + aep + '.csv','Level',ens_max_lev[:,aa],ev_max_set,lev,tol_all_aep[aa],aep_levels,short_loc_names,aep)

            # Output the differential tables 10/06 Commented out as not required. Should still work if un-commented.
            dtmp, mtmp, ttmp, lims_reorder, sites_reorder = bab_out(out_dir,bab_out_diff + aep + '.csv','Diff',ens_max_ld[:,aa],ev_max_set,ld,tol_all_aep[aa],aep_levels,short_loc_names,aep)
            data_reorder.append(dtmp)
            max_reorder.append(mtmp)
            tol_reorder.append(ttmp)
            ev_set_all.append(ev_max_set)

        if out_bab:
            # Output the AEP diff plots
            plot_figs = ['Plot 37 - AEP Level Difference between Ensemble and Monte Carlo Analysis - Sheet 1 of 3','Plot 38 - AEP Level Difference between Ensemble and Monte Carlo Analysis - Sheet 2 of 3','Plot 39 - AEP Level Difference between Ensemble and Monte Carlo Analysis - Sheet 3 of 3']
            pd.plot_A3_Bab(ev_set_all,data_reorder, max_reorder, tol_reorder, lims_reorder, 'AEP Level Difference (m)',sites_reorder, out_plot,plot_figs,aep_list)

        # Close the batch file as needed.
        if out_dmbat:
            dmbf.close()
            ts1f.close()

    if long_plot_out:
        # Output Long Sections per AEP
        ev_max = np.transpose(ev_max)
##        for i, ens in enumerate(ev_max):
##            lp.long_section('Bris',list(set(ens)),utl.get_plot_figs(aep_list[i],'ls')[0],False,aep_list[i],updated_tw_set)
##            lp.long_section('BremLock',list(set(ens)),utl.get_plot_figs(aep_list[i],'ls')[1],False,aep_list[i],updated_tw_set)

        # Output Long Sections all AEP
        lp_all.long_section('Bris',ev_max, 'Plot 51 - Brisbane River Longitudinal Profiles Maximums - All AEPs',False,aep_list,updated_tw_set)
        lp_all.long_section('BremLock',ev_max,'Plot 63 - Bremer/Lockyer Longitudinal Profiles Maximums - All AEPs',False,aep_list,updated_tw_set)


if __name__ == '__main__':
    main()
   # pd.main() # Output all required non-time, babbister or longseries plots for MR4 Reporting
