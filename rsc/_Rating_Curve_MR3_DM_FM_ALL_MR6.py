# Version 0003 uses multiple plots in one figure as subaxis - see: http://matplotlib.org/users/gridspec.html

#required python libraries
#required python libraries
import os
import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
import matplotlib.gridspec as gridspec
from matplotlib.font_manager import FontProperties
import bris_utilities as utl
import pickle

import TUFLOW_results2014
import Rating_Input_003
import math
from MR5_Tables import open_res


def get_data(indir,res_list,line_index):

    #LOAD INPUT
    infile = os.path.join(indir,'Rating_Index_zoom.csv')
    locs = Rating_Input_003.Rating_Index(infile)

    #load info for each gauge
    ext = []
    mod = []
    for name in locs.ShortName:
        ext_file = os.path.join(indir,(name+'_External_002.csv'))
        print 'loading '+ext_file
        ext.append(Rating_Input_003.Rating_Data(ext_file))
        mod_file = os.path.join(indir,'DM',(name+'_DM.csv'))
        print 'loading '+mod_file
        mod.append(Rating_Input_003.Modelled_Info(mod_file))
        event_levels = []
        event_flows = []

    for k, res_file in enumerate(res_list):

        res = TUFLOW_results2014.ResData(res_file)
        #res = open_res(res_file)
        print 'Data loaded - extracting required data'
        z = line_index

        #level data
        levels = []
        for i in range(len(mod)):
            found, hdata = res.getYData(mod[i].HID[z],mod[i].HDom[z],mod[i].HRestype[z],mod[i].HGeom[z])
            if found:
                levels.append(hdata)
            else:
                print 'Unable to find data for node: '+mod[i].HID[z]
                exit()
        event_levels.append(levels)

        #flow data
        flows = []
        for i in range(len(mod)):
            if (mod[i].QID[z].find('|')>-1):
                print 'multiple ID specified adding results'
                ID = mod[i].QID[z].split('|')
                DOM = mod[i].QDom[z].split('|')
                RESTYPE = mod[i].QRestype[z].split('|')
                GEOM = mod[i].QGeom[z].split('|')
                for j in range(len(ID)):
                    id = ID[j].strip()
                    if len(DOM)==1:
                        dom = DOM[0].strip()
                    else:
                        dom = DOM[j].strip()
                    if len(RESTYPE)==1:
                        restype = RESTYPE[0].strip()
                    else:
                        restype = RESTYPE[j].strip()
                    if len(GEOM)==1:
                        geom = GEOM[0].strip()
                    else:
                        geom = GEOM[j].strip()
                    if j==0:
                        found, qdata = res.getYData(id,dom,restype,geom)
                        if not found:
                            print 'Error loading Q data for id:'+id
                            exit()
                    else:
                        found, qdata2 = res.getYData(id,dom,restype,geom)
                        if not found:
                            print 'Error loading Q data for id:'+id
                            exit()
                        qdata = qdata + qdata2
            else:
                found, qdata = res.getYData(mod[i].QID[z],mod[i].QDom[z],mod[i].QRestype[z],mod[i].QGeom[z])
            if found:
                flows.append(qdata)
            else:
    #            print 'For event '+events[i]+' and location '+locs.ShortName[i]+' unable to get flow data'
                print 'Unable to find data for channel: '+mod[i].QID[z]
                exit()
        event_flows.append(flows)

        del res

    return stack_res(event_levels),stack_res(event_flows)

def rating_curve_out(out_fpath,fig_name,report_label,foot_note,nRow,nCol,data_ind, mc_fm_q, mc_fm_h, mc_dm_q, mc_dm_h,cal_fm_q,cal_fm_h,cal_dm_q,cal_dm_h,loc_file,del_axes):

    # Get the loc file
    locs = Rating_Input_003.Rating_Index(loc_file)
    mod = []
    ext = []
    fontP = FontProperties()
    fontP.set_size(12)
    for name in locs.ShortName:

        ext_file = os.path.join(indir,(name+'_External_002.csv'))
        print 'loading '+ext_file
        ext.append(Rating_Input_003.Rating_Data(ext_file))
        mod_file = os.path.join(indir,'DM',(name+'_DM.csv'))
        print 'loading '+mod_file
        mod.append(Rating_Input_003.Modelled_Info(mod_file))

    # Setup the figure
    fig = plt.figure(figsize=(paper_width,paper_height))
    axes1 = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # main axes
    gs = gridspec.GridSpec(nRow, nCol)
    ax=[]
    labels = []
    nplt = 0

    for i in range(nRow-1,-1,-1):   #reversed to start from bottom
        for j in range(nCol-1,-1,-1):     #right to left
            nplt = nplt + 1
            if nplt > len(locs.ShortName):
                break
            else:
                ax.append(plt.subplot(gs[i, j]))
            if j == 0:
                ax[nplt-1].set_ylabel('Level (mAHD)', fontsize="18")
            if i == nRow-1:
                ax[nplt-1].set_xlabel('Flow (cumecs)', fontsize="18")

    numpoints_count = []

    # Remove the bottom two axes as required.
    if del_axes:
        data_ind = data_ind[2:]

    for i,ind in enumerate(data_ind):

        if del_axes:
            i += 2

        #add modelled data
        ax[i].scatter(mc_fm_q[ind,:],mc_fm_h[ind,:],c='darkorchid',alpha=0.7,label='FM Design', rasterized=True,lw = 0)
        ax[i].scatter(mc_dm_q[ind,:],mc_dm_h[ind,:],c='grey',alpha=0.5,label='DM Design', rasterized=True,lw = 0)
        ax[i].scatter(cal_fm_q[ind,:],cal_fm_h[ind,:],c='lime',alpha=0.5,label='FM Calibration', rasterized=True,lw = 0)
        ax[i].scatter(cal_dm_q[ind,:],cal_dm_h[ind,:],c='crimson',alpha=0.3,label='DM Calibration', rasterized=True,lw = 0)
        numpoints_count.append(4)

        #add other curves
        for j in range(len(ext[ind].Source)):
            print 'loading csv file: '+ext[ind].Source[j]
            rfile = os.path.join(indir,ext[ind].Source[j])
            data = np.genfromtxt(rfile, delimiter=",", skip_header=1)
            if (ext[ind].line[j].upper() == 'F') or (ext[ind].line[j].upper() == 'N'):
                ax[i].plot(data[:,1],data[:,0]+ext[ind].datum_shift[j], color=ext[ind].colour[j],marker='o',linestyle='None',markersize=ext[ind].markersize[j],label=ext[ind].Name[j])
            else:
                ax[i].plot(data[:,1],data[:,0]+ext[ind].datum_shift[j], color=ext[ind].colour[j],marker='o',markersize=ext[ind].markersize[j],label=ext[ind].Name[j])
            numpoints_count.append(1)

        # Pretty up the plot
        ax[i].grid(True)
        if(len(locs.legend_loc[ind])>0):
            handles, labels = ax[i].get_legend_handles_labels()
            ax[i].legend(loc=locs.legend_loc[ind],prop=fontP, numpoints=4)
        else:
            ax[i].legend(loc=4,prop=fontP,numpoints=4)
        ax[i].set_title(locs.LongName[ind],fontsize="20")
        ax[i].set_xlim(locs.xmin[ind],locs.xmax[ind])
        ax[i].set_ylim(locs.ymin[ind],locs.ymax[ind])

    if del_axes:
        ax[0].axis("off")
        ax[1].axis("off")


    # Add some figure text to the bottom of the page.
    #fig.text(0.6,0.006,'Note: 1974 hydrology on the Bremer River adopts 50/50 Aurecon/ SEQwater losses', fontsize = "16")
    fig.text(0.02,0.006,foot_note ,fontsize="16")
    fig.text(0.5,0.02,report_label,fontsize="28")
    plt.tight_layout(pad=10.0, w_pad=7.0, h_pad=2.0)

    # Save the figure
    fig_file = os.path.join(out_fpath,(fig_name+'.png'))
    print 'saving file '+fig_file
    fig.savefig(fig_file, dpi=(300))
    #fig_file = os.path.join(out_fpath,(fig_name+'.pdf'))
    #print 'saving file '+fig_file
    #fig.savefig(fig_file, dpi=(300))
    plt.close(fig)


def stack_res(data):
    #rearrange data into numpy arrays to make it easier to plot. MJS 05/06 ****
    #list of events containing numpy arrays for each gauge location
    first = True
    for x in data:
        if first:
            dd = np.vstack(x)
            first = False

        dd = np.concatenate((dd,np.vstack(x)),axis=1)  # Keep adding data to the 'time' axis

    return dd

##==============================================================================
"""
==========================Script starts here.===================================
"""
##==============================================================================

#CONFIG DATA
out_fpath = r'C:\Projects\Python\TUFLOW\ReportPlots\Ratings'
indir = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\000_General\000_Scripts\PostProcessing\DM2\Rating'
res_fpath = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results'
process_data = True

## IF NOT PROCESSED GO GRAB THE DATA. THIS WILL SAVE OFF A PICKLE FOR THE FM, DM design and cal timeseries results.
if process_data:

    Cal_FM_RES_FILE = []
    Cal_DM_RES_FILE = []
    MC_FM_RES_FILE = []
    MC_DM_RES_FILE = []

    ## ========================CALIBRATION EVENTS===================================
    # FM Calibration Results
    Cal_FM_RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C1974\plot\BR_F_C1974_0285_ST09.tpc')
    Cal_FM_RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C1996\plot\BR_F_C1996_0285.tpc')
    Cal_FM_RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C1999\plot\BR_F_C1999_0285.tpc')
    Cal_FM_RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C2011\plot\BR_F_C2011_0285.tpc')
    Cal_FM_RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C2013\plot\BR_F_C2013_0285.tpc')

    # DM Calibration Results
    Cal_DM_RES_FILE.append(r"B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\600_D_Design_Events\TUFLOW\D\results\605\Cal\1974\plot\BR_D_C1974_605_ST09.tpc")
    Cal_DM_RES_FILE.append(r"B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\600_D_Design_Events\TUFLOW\D\results\605\Cal\1996\plot\BR_D_C1996_605.tpc")
    Cal_DM_RES_FILE.append(r"B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\600_D_Design_Events\TUFLOW\D\results\605\Cal\1999\plot\BR_D_C1999_605.tpc")
    Cal_DM_RES_FILE.append(r"B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\600_D_Design_Events\TUFLOW\D\results\605\Cal\2011\plot\BR_D_C2011_605.tpc")
    Cal_DM_RES_FILE.append(r"B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\600_D_Design_Events\TUFLOW\D\results\605\Cal\2013\plot\BR_D_C2013_605.tpc")

    ## ========================FM MONTE CARLO EVENTS================================
    # Load up Fast model event result locations
    data = np.load('Final_Selection_380.npz')
    event_ind = data['ev_max']
    base_mc_dir = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\TUFLOW\F\results\360\360'

    # Update the water level array if a tailwater boundary has been modified
    tw_resim_path = r'C:\Projects\BRFS\TUFLOW\F\results\360'
    updated_tw_set = set(['072_0054','012_0381','096_0261','168_0086','120_0625','096_0774','096_0889','018_0789'])

    fm_mc_events = []
    for x in np.unique(event_ind.flatten()):
        fm_mc_events.append(utl.index_to_dur_event(float(x)))

    for event in fm_mc_events:
        dur,ee = event.split('_')

        if set.intersection(set(event),updated_tw_set):
            # Return the duration and event name from the index
            res_dir = tw_resim_path +'\\' + dur + '\\plot\\'
            MC_FM_RES_FILE.append(res_dir + 'BR_F_' + dur + '_' + ee + '_MC_0380_MC.tpc')

        else:
            res_dir = base_mc_dir +'\\' + dur + '\\plot\\'
            MC_FM_RES_FILE.append(res_dir + 'BR_F_' + dur + '_' + ee + '_MC_0360_MC.tpc')

    # Load up the Detailed model MC Event result locations
    pkl_file = open('DM_B15ts.pkl', 'rb')
    ts_data = pickle.load(pkl_file)
    pkl_file.close()
    res_files = ts_data['all_res_files']
    MC_DM_RES_FILE = [item for sublist in res_files for item in sublist]

    #load data
    cal_fm_h,cal_fm_q = get_data(indir,Cal_FM_RES_FILE,0)
    cal_dm_h,cal_dm_q = get_data(indir,Cal_DM_RES_FILE,1)
    mc_fm_h,mc_fm_q = get_data(indir,MC_FM_RES_FILE,0)
    mc_dm_h,mc_dm_q = get_data(indir,MC_DM_RES_FILE,1)

    # Save to disk to save time
    # Cal
    gdata = {'cal_fm_h': cal_fm_h, 'cal_fm_q' : cal_fm_q ,'cal_dm_h' : cal_dm_h, 'cal_dm_q' : cal_dm_q}
    #data = {'qts': q_ts, 'hts': h_ts}
    output = open('Cal_Gauge_Data.pkl', 'wb')
    pickle.dump(gdata, output)
    output.close()

    # MC
    gdata = {'mc_fm_h': mc_fm_h, 'mc_fm_q' : mc_fm_q ,'mc_dm_h' : mc_dm_h, 'mc_dm_q' : mc_dm_q}
    #data = {'qts': q_ts, 'hts': h_ts}
    output = open('MC_Gauge_Data.pkl', 'wb')
    pickle.dump(gdata, output)
    output.close()

else:
    # Load the previously saved data
    pkl_file = open('MC_Gauge_Data.pkl', 'rb')
    ts_data = pickle.load(pkl_file)
    pkl_file.close()
    mc_fm_h = ts_data['mc_fm_h']
    mc_fm_q = ts_data['mc_fm_q']
    mc_dm_h = ts_data['mc_dm_h']
    mc_dm_q = ts_data['mc_dm_q']
    pkl_file.close()

    pkl_file = open('Cal_Gauge_Data.pkl', 'rb')
    ts_data = pickle.load(pkl_file)
    pkl_file.close()
    cal_fm_h = ts_data['cal_fm_h']
    cal_fm_q = ts_data['cal_fm_q']
    cal_dm_h = ts_data['cal_dm_h']
    cal_dm_q = ts_data['cal_dm_q']
    pkl_file.close()

## ==================OUTPUT THE CURVES======================================
# define figure layout
nRow = [2,2,2,2,2,2]
nCol = [2,2,2,2,2,2]
paper_width = 29.7
paper_height = 21.0
l_file = os.path.join(indir,'Rating_Index_zoom.csv')
ex_l_file = os.path.join(indir,'Rating_Index_Extreme_zoom_dm.csv')

report_label = ['Sheet 45 Rating Curves Sheet 1 of 3 (MR5, Plot 58)',
                'Sheet 46 Rating Curves Sheet 2 of 3 (MR5, Plot 59)',
                'Sheet 47 Rating Curves Sheet 3 of 3 (MR5, Plot 60)',
                'Sheet 48 Rating Curves Extreme Sheet 1 of 3 (MR5, Plot 61)',
                'Sheet 49 Rating Curves Extreme Sheet 2 of 3 (MR5, Plot 62)',
                'Sheet 50 Rating Curves Extreme Sheet 3 of 3 (MR5, Plot 63)']

fig_name = ['A3-Addendum-Sheet-45',
                'A3-Addendum-Sheet-46',
                'A3-Addendum-Sheet-47',
                'A3-Addendum-Sheet-48',
                'A3-Addendum-Sheet-49',
                'A3-Addendum-Sheet-50']

foot_note ='Fast Model Version 0285\nDetailed Model version 605'
loc_file =[l_file,l_file,l_file,ex_l_file,ex_l_file,ex_l_file]
result_indices = [[1,0,6,7],[3,4,5,2],[8,9,8,9],[1,0,6,7],[3,4,5,2],[8,9,8,9]]  # These are the reporting location indices.
del_axes = [False,False,True, False,False,True]

# Loop through and create all the plots.
for ii, nam in enumerate(report_label):
    rating_curve_out(out_fpath,fig_name[ii],report_label[ii],foot_note,nRow[ii],nCol[ii],result_indices[ii], mc_fm_q, mc_fm_h, mc_dm_q, mc_dm_h,cal_fm_q,cal_fm_h,cal_dm_q,cal_dm_h,loc_file[ii],del_axes[ii])
