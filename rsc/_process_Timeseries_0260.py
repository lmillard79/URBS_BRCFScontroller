# Version 0003 uses multiple plots in one figure as subaxis - see: http://matplotlib.org/users/gridspec.html

#required python libraries
import os
import sys
import csv
import numpy as npy
import matplotlib
import matplotlib.dates
from matplotlib.dates import date2num
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import TUFLOW_results2014           #PAR - numerous classes, same as QGIS viewer
import Calib_Data8                  #PAR - working with calibration data
import Calib_TS                     #PAR - workign with calibration timeseries data
import URBS_Res
import datetime                     #Python library for dealing with dates and times
import math
import get_calib_file_MR3
import MR3_get_plot_name as gpn

# setup stuff
cwd = os.path.dirname(sys.argv[0]) #current working directory (i.e. where the script is located)
print 'Script called from: '+cwd
base_res_dir_FM = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results'
base_res_dir_DM = r'\\brandy1515\d\B20702\d\Results'
base_res_dir_UDMT = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\100_Calibration\TUFLOW\B\Results'
base_res_dir_DMT = r'\\brandy1515\d\B20702\Results'

# get arguments:
nArg = len(sys.argv)
FMrunid = []
DMrunid = []
DMgridCell = []
UDMTrunid = []
DMTrunid = []
DMdomain = []
DMSens = []
print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)
for i, arg in enumerate(sys.argv):
    if i == 0:
        print 'skipping 1st argument'
    elif i ==1:
        event = str(arg)
    elif i ==2:
        loc = str(arg)
    elif i ==3:
        reldir = str(arg)
        outdir = os.path.join(cwd,reldir)
    elif i ==4:
        fext = str(arg)
    else:
        run_str = str(arg)
        skip = False
        if(len(run_str)>=3):
            if run_str[0:3].upper() == 'DGS': #detailed model grid size
                skip = True
                try:
                    tmp = float(run_str[3:]) #cell size is used as string in script - but check it is valid
                    DMgridCell.append(run_str[3:])
                except:
                    sys.exit("Unable to convert cell size to float: "+run_str[3:])
            elif run_str[0:3].upper() == 'DOM': #detailed model dom
                skip = True
                DMdomain.append(run_str[3:]) # detailed model domain all or lower
            elif run_str[0:4].upper() == 'SENS': #dm sensitivity
                skip = True
                DMSens.append(run_str[4:]) # sensitivity simulation
        if not skip:
            if run_str[0].upper()=='F':
                FMrunid.append(run_str[1:])
            elif run_str[0].upper()=='D':
                DMrunid.append(run_str[1:])
            elif run_str[0].upper()=='U':
                UDMTrunid.append(run_str[1:])
            elif run_str[0].upper()=='O':
                DMTrunid.append(run_str[1:])
            else:
                print 'Unable to process '+str(arg)
                sys.exit("Expecting 1st letter of run id to be one of F,D, or M")

##FMrunid = ['0285']
##DMrunid = ['037','037','037b','037c']
##DMgridCell = ['30','20','20','20']
##DMdomain = ['All','All','All','All']
##DMSens = ['None','None','None','None']
##UDMTrunid = []
##DMTrunid = []
###UDMTrunid = []
##event = 'C2011'
##loc = 'Brem'
##fext = 'png'
##reldir = r'Images\TS\test'
##outdir = os.path.join(cwd,reldir)

print 'Event: '+event
print 'Location: '+loc
print 'Relative path to output: '+reldir
print 'Path to output: '+outdir
print 'Saving as '+fext+' file type'
print 'number of fast model runs: '+str(len(FMrunid))
for i, id in enumerate(FMrunid):
    print 'Run '+str(i+1)+' '+id
print 'number of detailed model runs: '+str(len(DMrunid))
print 'number of detailed model cell sizes: '+str(len(DMgridCell))
print 'number of detailed model domains: '+str(len(DMdomain))
if len(DMrunid)!=len(DMgridCell):
    sys.exit("ERROR - Number of detailed model runs and cell sizes does not match.")
if len(DMrunid)!=len(DMdomain):
    sys.exit("ERROR - Number of detailed model runs and model domains does not match.")
if len(DMrunid)!=len(DMSens):
    sys.exit("ERROR - Number of detailed model runs and model sensitivty does not match, specify SensNone")
for i, id in enumerate(DMrunid):
    print 'Run '+str(i+1)+' '+id+' with cell size '+DMgridCell[i]+' and domain '+DMdomain[i]
print 'number of udmt model runs: '+str(len(UDMTrunid))
for i, id in enumerate(UDMTrunid):
    print 'Run '+str(i+1)+' '+id
print 'number of original DMT model runs: '+str(len(DMTrunid))
plot_type = 'TS'

#sys.exit('test')
linew=[5,2,2]
linew_dm = 4
linew_fm = 2
linew_udmt = 2

if os.path.isdir(outdir):
    print 'Directory Already Exists: '+outdir
else:
    print 'Creating folder: '+outdir
    try:
        os.makedirs(outdir)
    except:
        print 'Unable to create directory: '
        sys.exit("ERROR - Unable to create directory "+outdir)

#EVENT and MODEL TYPE SPECIFIC INPUTS
dm_cal_file = []
fm_cal_file = []
udmt_cal_file = []
dmt_cal_file = []
#get_calib_data
dm_calib = []
fm_calib = []
udmt_calib = []
dmt_calib = []


for i in range(len(FMrunid)):
    rel_cal_file = get_calib_file_MR3.get_calib_file_MR3(event,loc,'F',None)
    print rel_cal_file.cal_file
    cal_file = os.path.join(cwd,rel_cal_file.cal_file)
    cal_fpath, cal_fname = os.path.split(cal_file)
    print cal_file
    fm_cal_file.append(cal_file)
    fm_calib.append(Calib_Data8.Calib_Data(cal_file))
##for i in range(len(UDMTrunid)):
##    rel_cal_file = get_calib_file_MR3.get_calib_file_MR3(event,loc,'U',None)
##    print rel_cal_file.cal_file
##    cal_file = os.path.join(cwd,rel_cal_file.cal_file)
##    cal_fpath, cal_fname = os.path.split(cal_file)
##    print cal_file
##    udmt_cal_file.append(cal_file)
##    udmt_calib.append(Calib_Data8.Calib_Data(cal_file))
##for i in range(len(DMTrunid)):
##    rel_cal_file = get_calib_file_MR3.get_calib_file_MR3(event,loc,'U',None)
##    print rel_cal_file.cal_file
##    cal_file = os.path.join(cwd,rel_cal_file.cal_file)
##    cal_fpath, cal_fname = os.path.split(cal_file)
##    print cal_file
##    dmt_cal_file.append(cal_file)
##    dmt_calib.append(Calib_Data8.Calib_Data(cal_file))
for i in range(len(DMrunid)):
    rel_cal_file = get_calib_file_MR3.get_calib_file_MR3(event,loc,'D',DMdomain[i][0])
    print rel_cal_file.cal_file
    cal_file = os.path.join(cwd,rel_cal_file.cal_file)
    print cal_file
    dm_cal_file.append(cal_file)
    dm_calib.append(Calib_Data8.Calib_Data(cal_file))

# need one controlling calib dataset
nFM = len(FMrunid)
nDM = len(DMrunid)
##nUDMT = len(UDMTrunid)
##if nFM>0:
##    calib = fm_calib[0]
if nDM>0:
    calib = dm_calib[0]
##elif FM>0:
##    calib = fm_calib[0]
##    calib = udmt_calib[0]
else:
    sys.exit("No fast, detailed or UDMT modelled datasets specified!")


# define figure layout
nRow = 4
nCol = 3
legends = 1 #one for all legends on, anythign else only display 1 legend
paper_width = 42.0
paper_height = 29.7

#CONFIG DATA
#res_fpath = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results'
#out_fpath = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\000_General\000_Scripts\PostProcessing\TUFLOW\20141210\Images\0212'
ylabel = 'Level (mAHD)'



#USER DATA
#event = 'C2011'
#runID = ['0052','0053A']
#runLabel = ['0052','0053A']
plotColour = ['red','green','darkorange','blueviolet','darkred','darkgoldenrod','deeppink']
udmt_plotColour = ['Magenta']
urbs_colour = 'GoldenRod'
fm_mod_colour = 'red'

#event timing stuff
if event=='C2013':
    TF_zero_time = datetime.datetime(2013, 1, 23, 9, 0, 0) # 09:00 23/01/2013
    Xlim1 = datetime.datetime(2013, 1, 23, 9, 0, 0) # 09:00 23/01/2013
    Xlim2 = datetime.datetime(2013, 2, 6, 9, 0, 0) # 09:00 06/02/2013
elif event=='C2011':
    TF_zero_time = datetime.datetime(2011, 1, 2, 9, 0, 0) # 09:00 02/01/2011
    Xlim1 = datetime.datetime(2011, 1, 2, 9, 0, 0) # 09:00 02/01/2011
    Xlim2 = datetime.datetime(2011, 1, 20, 9, 0, 0) # 09:00 20/01/2011
elif event=='C1999':
    TF_zero_time = datetime.datetime(1999, 2, 7, 9, 0, 0) # 09:00 07/02/1999
    Xlim1 = datetime.datetime(1999, 2, 7, 9, 0, 0) # 09:00 07/02/1999
    Xlim2 = datetime.datetime(1999, 2, 17, 9, 0, 0) # 09:00 17/02/1999
elif event=='C1996':
    TF_zero_time = datetime.datetime(1996, 4, 30, 9, 0, 0) # 09:00 30/04/1996
    Xlim1 = datetime.datetime(1996, 4, 30, 9, 0, 0) # 09:00 30/04/1996
    Xlim2 = datetime.datetime(1996, 5, 10, 9, 0, 0) # 09:00 10/05/1996
elif event=='C1974':
    TF_zero_time = datetime.datetime(1974, 1, 24, 9, 0, 0) # 09:00 24/01/1974
    Xlim1 = datetime.datetime(1974, 1, 24, 9, 0, 0) # 09:00 24/01/1974
    Xlim2 = datetime.datetime(1974, 2, 1, 9, 0, 0) # 09:00 01/02/1974
else:
    print 'Error unrecognised event'
    exit()
year=event[1:]
DMTresEvent=year+'_20m'

#Legend Labelling and sesitivity tests
FM_runLabel=['FM']
if len(DMgridCell) >=2:
    if DMgridCell[2]=='20':
        DM_label=['DM - 30m','DM - 20m','DM - 20m n+10%', 'DM - 20m n+20%']
    else:
        DM_label=['DM','DM - ST02 +10%','DM - ST02 -10%']
else:
    DM_label=['DM','DM - ST02 +10%','DM - ST02 -10%']

if event == 'C1974' and loc=='Brem':
    legend_loc = 'lower left'
elif event == 'C1974' and loc =='Lockyer':
    legend_loc = 'lower center'
else:
    legend_loc = 'upper left'

#get plot labels
plot_name = gpn.getNP(event,FMrunid,DMrunid,loc,plot_type,DMSens)
plot_number = plot_name[5:7]
print 'plot name: '+ plot_name
fig_name = plot_number+'_TS_'+event+'_'+loc+'_'+DMrunid[0]



##
##fig_name = 'TS_'+event+'_'+loc
##plot_name = event[1:]+' Timeseries Plots'
##for i, id in enumerate(DMrunid):
##    sens = DMSens[i]
##    if sens.upper() == 'NONE':
##        fig_name = fig_name+'_D'+id
##        plot_name = 'D'+id+' '+plot_name
##    else:
##        fig_name = fig_name+'_D'+id+sens
##        plot_name = 'D'+id+sens+' '+plot_name
##for id in FMrunid:
##    fig_name = fig_name+'_F'+id
##    plot_name = 'F'+id+' '+plot_name
##for id in UDMTrunid:
##    fig_name = fig_name+'_U'+id
##    plot_name = 'D'+id+' '+plot_name





#load results data
print 'Loading results data...'
FM_RES = []
DM_RES = []
UDMT_RES = []
DMT_RES = []

DM_DATE = []
FM_DATE = []
UDMT_DATE = []
DMT_DATE = []

for i, id in enumerate(FMrunid):
    res_fname = 'BR_F_'+event+'_'+id+'.tpc'
    res_file = os.path.join(base_res_dir_FM,event,'plot',res_fname)
    fm_res_file = res_file
    if os.path.isfile(res_file):
        FM_RES.append(TUFLOW_results2014.ResData(res_file))
        date = []
        for t in FM_RES[i].times:
            date.append(TF_zero_time + datetime.timedelta(hours=t))
        FM_DATE.append(date)
        del date
    else:
        sys.exit("Does not exist: "+res_file)
for i, id in enumerate(DMrunid):
    sens = DMSens[i]
    if sens.upper() == 'NONE':
        res_fname = 'BR_D_'+event+'_'+id+'_'+DMdomain[i]+'+'+DMgridCell[i]+'m.tpc'
    else:
        res_fname = 'BR_D_'+event+'_'+id+'_'+DMdomain[i]+'+'+DMgridCell[i]+'m+'+sens+'.tpc'
    res_file = os.path.join(base_res_dir_DM,event,'2d','plot',res_fname)
    DM_res_file = res_file
    if os.path.isfile(res_file):
        DM_RES.append(TUFLOW_results2014.ResData(res_file))
        date = []
        for t in DM_RES[i].times:
            date.append(TF_zero_time + datetime.timedelta(hours=t))
        DM_DATE.append(date)
        del date
    else:
        sys.exit("Does not exist: "+res_file)

if len(FMrunid)==0 and len(UDMTrunid)>0:
    model_scheme='2D'
    FM_DATE = UDMT_DATE
    UDMT_res_fname = 'BR_B_'+event+'_'+id+'.tpc'
    res_file = os.path.join(base_res_dir_UDMT,year+'_20m','plot',UDMT_res_fname)
#    infile2 = os.path.join(base_res_dir_UDMT,DMTresEvent,'plot',UDMT_res_fname)
else:
    model_scheme='1D'
    FM_res_fname = 'BR_F_'+event+'_'+'0285.tpc'
    res_fname = FM_res_fname
    res_file = os.path.join(base_res_dir_FM,event,'plot',res_fname)
#    infile2 = os.path.join(base_res_dir_FM,event,'plot',FM_res_fname)



#create plots
if nRow*nCol < len(calib.ID):
    print 'ERROR - Number of Rows / Columns not enough to fit in all the plots!'
    exit()
else:
    print 'Canvas large enough to fit all plots, lets create some plots :)'

fig = plt.figure(figsize=(paper_width,paper_height))
fig.autofmt_xdate()
gs = gridspec.GridSpec(nRow, nCol)
ax=[]
labels = []
np = 0

for i in range(nRow-1,-1,-1):   #reversed to start from bottom
    for j in range(nCol-1,-1,-1):     #right to left
        np = np + 1
        if np > len(calib.ID):
            break
        else:
            ax.append(plt.subplot(gs[i, j]))
        if j == 0:
            ax[np-1].set_ylabel(ylabel, fontsize="28")
        if i == nRow-1:
            labels.append(ax[np-1].get_xticklabels())
            ax[np-1].xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d %b %Y'))



for np in range(len(ax)):
    ax[np].grid(True)               #make all grids visible
    if np >= nCol:
        ax[np].set_xticklabels([])  #only show the x labels for the bottom charts
print 'Finished creating axes'

for i, id in enumerate(calib.Label):
    #get calib data
    infile = os.path.join(cal_fpath,calib.Source[i])
    obs = Calib_TS.Calib_TS(infile,float(calib.datum_shift[i]))

    #add observed data to plot:
    if calib.obs_colour[i] == 'DeepSkyBlue':
        ax[i].plot(obs.xdate, obs.yval,color=calib.obs_colour[i],marker='.',markersize=calib.marker_size1[i]+4,linestyle='None',markeredgecolor=calib.obs_colour[i],label='Observed')
    else:
        ax[i].plot(obs.xdate, obs.yval,color=calib.obs_colour[i],marker='.',markersize=calib.marker_size1[i]+4,linestyle='None',markeredgecolor=calib.obs_colour[i],label='Observed-Questionable Data')

    #add road deck levels
    if calib.bridge_invert[i] == 0:
        print 'loading bridge data'
        #do nothing
    else:
        ax[i].axhline(calib.bridge_invert[i], color = 'silver',linewidth=3)
        ax[i].axhline(calib.bridge_obvert[i], color = 'silver',linewidth=3)
        ax[i].text(0.85,((calib.bridge_invert[i]-calib.ymin[i])/(calib.ymax[i]-calib.ymin[i]))-0.03,calib.bridge_name[i],transform=ax[i].transAxes)

    #add adjusted moggill gauge to 2011
    if (event=='C2011' and  calib.Label[i] == 'Moggill Alert') or (event=='C2011' and calib.Label[i] == 'Moggill Alert (Brisbane)') or (event=='C2011' and calib.Label[i] == 'Moggill Alert (Brisbane River)'):
        MogPeakDate=[]
        MogPeakVal=[]
        MogPeakDate =[(datetime.datetime(2011,1,12,10,02)), (datetime.datetime(2011,1,12,20,02))]
        MogPeakDate2Num=[float(date2num(MogPeakDate[0])),float(date2num(MogPeakDate[1]))]
        MogPeakVal = [18.17,18.17]
        ax[i].plot(MogPeakDate2Num,MogPeakVal,color='navy',linewidth=8,label='Adjusted Peak Level')
        print 'Adding Moggill Adjusted Peak Level'

    #add MODELLED secondary data
    mod_add = []
    if calib.mod_add_source[i]:
        print 'loading modelled secondary data'
        print 'Creating secondary axis'
        ax2 = ax[i].twinx()
        ax2.set_ylabel('Flow\n(cumecs)', rotation=0, fontsize=15)
        ax2.yaxis.set_label_coords(1,1.05)
        ax2.set_zorder(1)
        ax2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d %b %Y'))
        if (loc == 'Lockyer' and calib.mod_add_label[i]== 'Modelled Lockyer Flow') or (calib.Label[i]== 'Moggill Alert (Brisbane River)') or (loc == 'Lockyer' and calib.mod_add-label[i]=='Modelled Upper Brisbane Flow'):
            #do nothing
            print'tralalala'
        else:
            ax2.set_xticklabels([])  #on't show dates for twin axes

        mod_add = calib.mod_add_source[i].split('|')
        mod_dom = calib.mod_add_dom[i].split('|')
        mod_label =  calib.mod_add_label[i].split('|')
        mod_colour =  calib.mod_add_colour[i].split('|')
        mod_marker =  calib.mod_add_marker[i].split('|')
        mod_line =  calib.mod_add_line[i].split('|')

        for j, add in enumerate(mod_add):
            #for recorded data
            if mod_add[j].endswith('.csv'):
                print 'adding recorded secondary data from '+calib.mod_add_source[i]
                infile2 = os.path.join(cal_fpath,calib.mod_add_source[i])
                add_data = Calib_TS.Calib_TS(infile2,float(0.0))
                if calib.mod_add_line[i] == 'y':
                    ax2.plot(add_data.xdate, add_data.yval,color=calib.mod_add_colour[i],marker='.',markersize=int(float(calib.mod_add_marker[i]))+3,linestyle='-',markeredgecolor=calib.mod_add_colour[i],label=calib.mod_add_label[i],zorder=-1)
                else:
                    ax2.plot(add_data.xdate, add_data.yval,color=calib.mod_add_colour[i],marker='.',markersize=int(float(calib.mod_add_marker[i]))+3,linestyle='none',markeredgecolor=calib.mod_add_colour[i],label=calib.mod_add_label[i],zorder=-1)
            res=DM_RES[0]
            #if need to add results
            if mod_add[j].find('+')>-1:
                print 'multiple modelled IDs specified, adding results'
                mod_add2 = mod_add[j].split('+')
                mod_dom2 = mod_dom[j].split('+')
                mod_add_data = []
                for k in range (len(mod_add2)):
                    if k==0:
                        found, mod_add_data = res.getYData(mod_add2[k],mod_dom2[k],'Q','L')
                    else:
                        found, mod_add_data2 = res.getYData(mod_add2[k],mod_dom2[k],'Q','L')
                        mod_add_data = mod_add_data +mod_add_data2
            else:
                #if we dont need to add results
                print 'adding modelled secondary data from '+mod_add[j]
                found, mod_add_data = res.getYData(mod_add[j],mod_dom[j],'Q','L')
                if not found:
                    print 'Error loading secondary modelled data:'+mod_add[j]
                    exit()
            #plot the secondary modelled data
            if mod_line[j] == 'y':
                ax2.plot(DM_DATE[0],mod_add_data, color=mod_colour[j],linestyle = '--',linewidth = 6, label=mod_label[j],zorder=-5)
            else:
                ax2.plot(DM_DATE[0],mod_add_data, color=mod_colour[j],linestyle = 'none',linewidth = 6,marker='.',markersize=int(float(mod_marker[j]))+3,markeredgecolor=mod_colour[j], label=mod_label[j],zorder=-5)


    #add URBS secondary data
    urbs_add = []
    if calib.urbs_add_source[i]:
        print 'loading URBS secondary data'
        print 'Creating secondary axis'
        if calib.mod_add_source[i]:
            print 'Rachel needs to work on her python skills'
        else:
            ax2 = ax[i].twinx()
            ax2.set_ylabel('Flow\n(cumecs)', rotation=0, fontsize=15)
            ax2.yaxis.set_label_coords(1,1.05)
            ax2.set_zorder(1)
            ax2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d %b %Y'))
            if (loc == 'Lockyer' and calib.urbs_add_label[i]== 'Wivenhoe Outflow') or (calib.Label[i]== 'Moggill Alert (Brisbane River)') or (loc == 'Lockyer' and calib.urbs_add_label[i]=='Modelled Upper Brisbane Flow'):
                #do nothing
                print'tralalala'
            else:
                ax2.set_xticklabels([])  #on't show dates for twin axes

        urbs_add = calib.urbs_add_source[i].split('|')
        urbs_name = calib.urbs_add_name[i].split('|')
        urbs_label =  calib.urbs_add_label[i].split('|')
        urbs_colour =  calib.urbs_add_colour[i].split('|')
        urbs_marker =  calib.urbs_add_marker[i].split('|')
        urbs_line =  calib.urbs_add_line[i].split('|')

            #for URBS data
        for j in range (len(urbs_add)):
            if urbs_add[j].endswith('.csv'):
                print 'adding recorded data from '+calib.urbs_add_source[i]
                infile2 = os.path.join(cal_fpath,calib.urbs_add_source[i])
                add_data = Calib_TS.Calib_TS(infile2,float(0.0))
                if urbs_line[j] == 'y':
                    ax2.plot(add_data.xdate, add_data.yval,color=calib.urbs_add_colour[i],marker='.',markersize=int(float(calib.urbs_add_marker[i]))+3,linestyle='-',markeredgecolor=calib.urbs_add_colour[i],label=calib.urbs_add_label[i],zorder=-1)
                else:
                    ax2.plot(add_data.xdate, add_data.yval,color=calib.urbs_add_colour[i],marker='.',markersize=int(float(calib.urbs_add_marker[i]))+3,linestyle='none',markeredgecolor=calib.urbs_add_colour[i],label=calib.urbs_add_label[i],zorder=-1)
            elif urbs_add[j].find('+')>-1:
                print 'multiple URBS IDs specified, adding results'
                urbs_add2 = urbs_add[j].split('+')
                urbs_name2 = urbs_name[j].split('+')
                urbs_data = []
                urbs_data2 = []
                for k in range (len(urbs_add2)):
                    if k==0:
                        infile = os.path.join(cal_fpath,urbs_add2[k])
                        urbs = URBS_Res.URBS_Res(infile)
                        found, urbs_data = urbs.get_data(urbs_name2[k],'calc')
                    else:
                        infile = os.path.join(cal_fpath,urbs_add2[k])
                        urbs = URBS_Res.URBS_Res(infile)
                        found, urbs_data2 = urbs.get_data(urbs_name2[k],'calc')
                        urbs_data = [sum(t) for t in zip(urbs_data, urbs_data2)]
                for s in range(len(urbs_data)):
                    urbs_data[s] = urbs_data[s] +calib.datum_shift[i]
                #plot the secondary urbs data
                if urbs_line[j] == 'y':
                    ax2.plot(urbs.date,urbs_data, color=urbs_colour[j],linestyle = '--',linewidth = 6, label=urbs_label[j],zorder=-5)
                else:
                    ax2.plot(urbs.date,urbs_data, color=urbs_colour[j],linestyle = 'none',linewidth = 6,marker='.',markersize=urbs_marker[j],markeredgecolor=urbs_colour[j], label=urbs_label[j],zorder=-5)
                del urbs
            else:
                #if we dont need to add results
                urbs_data = []
                infile = os.path.join(cal_fpath,urbs_add[j])
                urbs = URBS_Res.URBS_Res(infile)
                print 'adding URBS secondary data from '+urbs_add[j]
                found, urbs_data = urbs.get_data(urbs_name[j],'calc')
                if not found:
                        print 'Error loading secondary URBS data:'+urbs_add[j]
                        exit()
                for k in range(len(urbs_data)):
                    urbs_data[k] = urbs_data[k] +calib.datum_shift[i]
                #plot the secondary urbs data
                if urbs_line[j] == 'y':
                    ax2.plot(urbs.date,urbs_data, color=urbs_colour[j],linestyle = '--',linewidth = 6, label=urbs_label[j],zorder=-5)
                else:
                    ax2.plot(urbs.date,urbs_data, color=urbs_colour[j],linestyle = 'none',linewidth = 6,marker='.',markersize=urbs_marker[j],markeredgecolor=urbs_colour[j], label=urbs_label[j],zorder=-5)
                del urbs

####        if (loc == 'Lockyer' and calib.add_label[i]== 'Wivenhoe Outflow') or (calib.Label[i]== 'Moggill Alert (Brisbane River)') or (loc == 'Lockyer' and calib.add_label[i]=='Modelled Upper Brisbane Flow'):
####            #do nothing
####            print'tralalala'
####        else:
##

#    for j, plotlabel in enumerate(runLabel): #for each timeseries
    # Add DETAILED model results
    for j in range(len(DMrunid)):
        res = DM_RES[j]
        sens = DMSens[j]
        #get modelled data
        found, mod_data = res.getYData(dm_calib[j].ID[i],dm_calib[j].Dom[i],dm_calib[j].ResType[i],dm_calib[j].Geom[i])
        if found:
            ax[i].plot(DM_DATE[j],mod_data, color=plotColour[j+nFM],linewidth = linew_dm,label=DM_label[j],zorder = 5)
        else:
            sys.exit("Unable to find DM results: "+dm_calib[j].ID[i])

    # Add UDMT model results
    for j in range(len(UDMTrunid)):
        res = UDMT_RES[j]
        #get modelled data
        found, mod_data = res.getYData(udmt_calib[j].ID[i],udmt_calib[j].Dom[i],udmt_calib[j].ResType[i],udmt_calib[j].Geom[i])
        if found:
            ax[i].plot(UDMT_DATE[j],mod_data, color=udmt_plotColour[j],linewidth = linew_udmt,label='Updated DMT',linestyle='--',zorder = 3)
        else:
            sys.exit("Unable to find UDMT results: "+udmt_calib[j].ID[i])

    # Add FAST model results
    for j in range(len(FMrunid)):
        res = FM_RES[j]
        #get modelled data
        found, mod_data = res.getYData(fm_calib[j].ID[i],fm_calib[j].Dom[i],fm_calib[j].ResType[i],fm_calib[j].Geom[i])
        if found:
            #ax[i].plot(FM_DATE[j],mod_data, color=plotColour[j],linewidth = linew_fm,label=FM_runLabel[j],zorder = 5)
            ax[i].plot(FM_DATE[j],mod_data, color=fm_mod_colour,linewidth = linew_fm,label=FM_runLabel[j],zorder = 6,linestyle='--')
        else:
            sys.exit("Unable to find FM results: "+fm_calib[j].ID[i])

    # Add DMT model results
    if event == 'C1999' or event == 'C1996':
        print 'NO DMT results'
    else:
        for j in range(len(DMTrunid)):
            res = DMT_RES[j]
            #get modelled data
            found, mod_data = res.getYData(dmt_calib[j].ID[i],dmt_calib[j].Dom[i],dmt_calib[j].ResType[i],dmt_calib[j].Geom[i])
            if found:
                ax[i].plot(DMT_DATE[j],mod_data, color=plotColour[j],linewidth = linew_udmt,label='Original DMT',zorder = 4)
                print 'adding Original DMT results for: '+ calib.Label[i]
            else:
                sys.exit("Unable to find UMT results: "+dmt_calib[j].ID[i])


    major_ticks = npy.arange(calib.ymin[i],calib.ymax[i],5)
    minor_ticks = npy.arange(calib.ymin[i],calib.ymax[i],1)
    ax[i].set_yticks(major_ticks)
    ax[i].set_yticks(minor_ticks, minor = True)
    ax[i].grid(which = 'minor', alpha=0.5, linewidth=2)
    ax[i].grid(which = 'major', alpha = 1, linewidth=2)

    h1, l1 = ax[i].get_legend_handles_labels()
    ax[i].set_zorder(99)
    ax[i].set_frame_on(True)

    if (len(calib.mod_add_source[i])>0) or (len(calib.urbs_add_source[i])>0):
        ax2.set_frame_on(True)
        ax[i].set_frame_on(False)
        h2, l2 = ax2.get_legend_handles_labels()
        secondary_legend=ax[i].legend(h2, l2, loc='upper right',prop={'size':14}, numpoints = 4, title='Flow')
        secondary_legend.get_title().set_fontsize(16)
        secondary_legend.get_title().set_fontweight('bold')

        primary_legend=ax[i].legend(h1, l1, loc=legend_loc,prop={'size':14}, numpoints = 4, title='Water level')
        ax[i].add_artist(secondary_legend)
    else:
        primary_legend=ax[i].legend(h1, l1, loc=legend_loc,prop={'size':14}, numpoints = 4, title='Water Level')

    primary_legend.get_title().set_fontsize(16)
    primary_legend.get_title().set_fontweight('bold')
    primary_legend.set_zorder(20)

    ax[i].set_title(calib.Label[i], fontsize=26)
    ax[i].set_xlim([Xlim1,Xlim2])
    if (calib.ymin[i] != -99.):
        ax[i].set_ylim([calib.ymin[i],calib.ymax[i]])


for axis in ax:
    for tick in axis.yaxis.get_major_ticks():
        tick.label.set_fontsize(20)


#show it
for label in labels:
    plt.setp(label, rotation=90, fontsize="20")
fig.text(0.5,0.015,plot_name,fontsize="35")
fig.text(0.06,0.032,'Date Labels are at 00:00 hours on that date',fontsize="18")
fig.text(0.06,0.023,'Bridge Levels shown are lowest soffit and lowest deck level',fontsize="18")
fig.text(0.06,0.014,'Further Details on Questionable or Adjusted data is provided in Appendix B',fontsize="18")
if event == 'C1974':
    fig.text(0.06,0.006,'Fast Model Version: '+FMrunid[0]+' Detailed Model Version: '+DMrunid[0]+' '+DMSens[0],fontsize="16")
    fig.text(0.5,0.006,'Note: 1974 hydrology on the Bremer River adopts 50/50 Aurecon/ SEQwater losses', fontsize = "16")
else:
    fig.text(0.06,0.006,'Fast Model Version: '+FMrunid[0]+' Detailed Model Version: '+DMrunid[0],fontsize="16")

#plt.show()
plt.tight_layout(pad=10.0, w_pad=7.0, h_pad=2.0)
fig_file = os.path.join(outdir,fig_name+'.'+fext)
print 'saving file '+fig_file
fig.savefig(fig_file, dpi=(300))

#plt.show()
plt.close(fig)
print 'finished'