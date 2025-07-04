# Version 0003 uses multiple plots in one figure as subaxis - see: http://matplotlib.org/users/gridspec.html

#required python libraries
#required python libraries
import os
import csv
import numpy
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
import matplotlib.gridspec as gridspec
from matplotlib.font_manager import FontProperties

#import TUFLOW_results2016           #PAR's super dooper class for dealing with TUFLOW results
import TUFLOW_results2014
import Rating_Input_003
import math
from MR5_Tables import open_res

#events
events = ['C2011']
#events = ['C1974','C2011','C2013']
runid = '0285'
report_label = 'Plot 30 DM Historical Calibration Events Rating Curve Comparison'
fig_name = '30_RT_DM_Calib_Ratings'
RES_FILE = []
RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C1974\plot\BR_F_C1974_0285_ST09.tpc')
RES_FILE.append(r'\\Brandy1515\d\B20702\d\Results\C1974\2d\plot\BR_D_C1974_043_All+30m+ST09.tpc')
RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C1996\plot\BR_F_C1996_0285.tpc')
RES_FILE.append(r'\\Monty1524\d\B20702\d\Results\C1996\2d\plot\BR_D_C1996_043_All+30m.tpc')
RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C1999\plot\BR_F_C1999_0285.tpc')
RES_FILE.append(r'\\Monty1524\d\B20702\d\Results\C1999\2d\plot\BR_D_C1999_043_All+30m.tpc')
RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C2011\plot\BR_F_C2011_0285.tpc')
RES_FILE.append(r'\\brandy1515\d\B20702\d\Results\C2011\2d\plot\BR_D_C2011_043_All+30m.tpc')
RES_FILE.append(r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results\C2013\plot\BR_F_C2013_0285.tpc')
RES_FILE.append(r'\\Brandy1515\d\B20702\d\Results\C2013\2d\plot\BR_D_C2013_043_All+30m.tpc')
Line_Index = [0,1,0,1,0,1,0,1,0,1]
markersymbol = ['^','^','.','.','s','s','*','*','d','d']
mod_marker_size = [4,4,4,4,4,4,4,4,4,4]
marker_edge_colour = ['red','green','red','green','red','green','red','green','red','green']
plot_zorder = [1,12,2,11,3,10,4,9,5,8]

event_label = []
event_label.append('FM 1974')
event_label.append('DM 1974')

event_label.append('FM 1996')
event_label.append('DM 1996')

event_label.append('FM 1999')
event_label.append('DM 1999')

event_label.append('FM 2011')
event_label.append('DM 2011')

event_label.append('FM 2013')
event_label.append('DM 2013')

# define figure layout
nRow = 2
nCol = 2
legends = 1 #one for all legends on, anythign else only display 1 legend
paper_width = 29.7
paper_height = 21.0
mod_colour = ['red','green','red','green','red','green','red','green','red','green']
fontP = FontProperties()
fontP.set_size(12)

#CONFIG DATA
out_fpath = r'C:\Projects\Python\TUFLOW\ReportPlots\Ratings'
indir = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\000_General\000_Scripts\PostProcessing\DM2\Rating'
res_fpath = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results'
#DMT_res_fpath = r'\\Brandy1515\d\B20702\Results\2011\2d\plot'

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


#load data
event_levels = []
event_flows = []
for k, res_file in enumerate(RES_FILE):

    res = TUFLOW_results2014.ResData(res_file)
    #res = open_res(res_file)
    print 'Data loaded - extracting required data'
    z = Line_Index[k]

    #level data
    levels = []
    for i in range(len(mod)):
        found, hdata = res.getYData(mod[i].HID[z],mod[i].HDom[z],mod[i].HRestype[z],mod[i].HGeom[z])
        if found:
            levels.append(hdata)
        else:
 #           print 'For event '+events[i]+' and location '+locs.ShortName[i]+' unable to get data'
            print 'Unable to find data for node: '+mod[i].HID[z]
            exit()
    event_levels.append(levels)

    #flow data
    flows = []
    for i in range(len(mod)):
##        if (res_file.find('C1999')>-1) or (res_file.find('C1996')>-1) or (res_file.find('2013')>-1):
##            if mod[i].QID[z] == 'LO10_18626|38_1':
##                mod[i].QID[z] = 'LO10_18626|38_2'
##            elif mod[i].QID[z] == '29_2':
##                mod[i].QID[z] == '29_1'
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
###create figure
##if nRow*nCol < len(locs.ShortName):
##    print 'ERROR - Number of Rows / Columns not enough to fit in all the plots!'
##    exit()
##else:
##    print 'Canvas large enough to fit all plots, lets create some plots :)'

fig = plt.figure(figsize=(paper_width,paper_height))
axes1 = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # main axes
gs = gridspec.GridSpec(nRow, nCol)
ax=[]
labels = []
np = 0

for i in range(nRow-1,-1,-1):   #reversed to start from bottom
    for j in range(nCol-1,-1,-1):     #right to left
        np = np + 1
        if np > len(locs.ShortName):
            break
        else:
            ax.append(plt.subplot(gs[i, j]))
        if j == 0:
            ax[np-1].set_ylabel('Level (mAHD)', fontsize="18")
        if i == nRow-1:
            ax[np-1].set_xlabel('Flow (cumecs)', fontsize="18")

numpoints_count = []

 #output .csv for location
print 'Writing out data csvs...'
for i, label in enumerate(locs.LongName):
    csv_output=[]
    csv_header=[]
    csvfilename = locs.LongName[i]
    csvfilepath = r'C:\Projects\Python\TUFLOW\ReportPlots\Ratings\csvs'
    csvfullpath= os.path.join(csvfilepath,locs.LongName[i]+'Rat_Data.csv')
    for j, label in enumerate(event_label):
        csv_header.append(event_label[j]+' Flows')
        csv_output.append(event_flows[j][i])
        csv_header.append(event_label[j]+' Levels')
        csv_output.append(event_levels[j][i])
    with open(csvfullpath,'wb') as myfile:
        wr = csv.writer(myfile,quoting=csv.QUOTE_ALL)
        wr.writerow(csv_header)
        wr.writerows(zip(*csv_output))


print 'Plotting data...'
for i in range (0,4):
##    for i, label in enumerate(locs.LongName):
    #add modelled data
    for j, label in enumerate(event_label):
        ax[i].plot(event_flows[j][i],event_levels[j][i],color=mod_colour[j],marker=markersymbol[j],linestyle='None',markersize=mod_marker_size[j],label=label, markeredgecolor=marker_edge_colour[j],zorder = plot_zorder[j])
        numpoints_count.append(4)

    #add other curves
    for j in range(len(ext[i].Source)):
        print 'loading csv file: '+ext[i].Source[j]
        rfile = os.path.join(indir,ext[i].Source[j])
        data = numpy.genfromtxt(rfile, delimiter=",", skip_header=1)
        if (ext[i].line[j].upper() == 'F') or (ext[i].line[j].upper() == 'N'):
            ax[i].plot(data[:,1],data[:,0]+ext[i].datum_shift[j], color=ext[i].colour[j],marker='o',linestyle='None',markersize=ext[i].markersize[j],label=ext[i].Name[j], markeredgecolor=mod_colour[j])
        else:
            ax[i].plot(data[:,1],data[:,0]+ext[i].datum_shift[j], color=ext[i].colour[j],marker='o',markersize=ext[i].markersize[j],label=ext[i].Name[j], markeredgecolor=mod_colour[j])
        numpoints_count.append(1)
    #axes1.plot(data[:,1],data[:,0]+input.datum_shift[i], color=input.colour[i],label=input.Name[i])
    ax[i].grid(True)
    ax[i].set_xlim(locs.xmin[i],locs.xmax[i])
    ax[i].set_ylim(locs.ymin[i],locs.ymax[i])
    if(len(locs.legend_loc[i])>0):
        handles, labels = ax[i].get_legend_handles_labels()
        ax[i].legend(loc=locs.legend_loc[i],prop=fontP, numpoints=4)
    else:
        ax[i].legend(loc=4,prop=fontP,numpoints=4)
    ax[i].set_title(locs.LongName[i],fontsize="20")
##    if (locs.xmin[i]>-98):
##        ax[i].set_xlim([locs.xmin[i],locs.xmax[i]])
##    if (locs.ymin[i]>-98):
##        ax[i].set_ylim([locs.ymin[i],locs.ymax[i]])
# load data

report_label = 'Plot 28 DM Historic Calibration Events Rating Curve Comparison - Sheet A'
fig_name = '28_RT_DM_Calib_Ratings_A'
fig.text(0.6,0.006,'Note: 1974 hydrology on the Bremer River adopts 50/50 Aurecon/ SEQwater losses', fontsize = "16")
fig.text(0.02,0.006,' 1974 event: Fast Model Version: 0285_ST09 Detailed Model Version: 043_ST09\n All other events: Fast Model Version: 0285 Detailed Model Version: 043',fontsize="16")

fig.text(0.45,0.02,report_label,fontsize="28")
plt.tight_layout(pad=10.0, w_pad=7.0, h_pad=2.0)
#fig_fname = 'Bris_'+event+savename+'.png'
fig_file = os.path.join(out_fpath,(fig_name+'.png'))
print 'saving file '+fig_file
fig.savefig(fig_file, dpi=(300))
fig_file = os.path.join(out_fpath,(fig_name+'.pdf'))
print 'saving file '+fig_file
fig.savefig(fig_file, dpi=(300))
#plt.show()
plt.close(fig)

fig = plt.figure(figsize=(paper_width,paper_height))
axes1 = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # main axes
gs = gridspec.GridSpec(nRow, nCol)
ax=[]
labels = []
np = 0

for i in range(nRow-1,-1,-1):   #reversed to start from bottom
    for j in range(nCol-1,-1,-1):     #right to left
        np = np + 1
        if np > len(locs.ShortName):
            break
        else:
            ax.append(plt.subplot(gs[i, j]))
        if j == 0:
            ax[np-1].set_ylabel('Level (mAHD)', fontsize="18")
        if i == nRow-1:
            ax[np-1].set_xlabel('Flow (cumecs)', fontsize="18")

numpoints_count = []
for i in range (4,8):
    axis_count = i-4
##    for i, label in enumerate(locs.LongName):
    #add modelled data
    for j, label in enumerate(event_label):
        ax[axis_count].plot(event_flows[j][i],event_levels[j][i],color=mod_colour[j],marker=markersymbol[j],linestyle='None',markersize=mod_marker_size[j],label=label, markeredgecolor=marker_edge_colour[j],zorder = plot_zorder[j])
        numpoints_count.append(4)
    #add other curves
    for j in range(len(ext[i].Source)):
        print 'loading csv file: '+ext[i].Source[j]
        rfile = os.path.join(indir,ext[i].Source[j])
        data = numpy.genfromtxt(rfile, delimiter=",", skip_header=1)
        if (ext[i].line[j].upper() == 'F') or (ext[i].line[j].upper() == 'N'):
            ax[axis_count].plot(data[:,1],data[:,0]+ext[i].datum_shift[j], color=ext[i].colour[j],marker='o',linestyle='None',markersize=ext[i].markersize[j],label=ext[i].Name[j], markeredgecolor=mod_colour[j])
        else:
            ax[axis_count].plot(data[:,1],data[:,0]+ext[i].datum_shift[j], color=ext[i].colour[j],marker='o',markersize=ext[i].markersize[j],label=ext[i].Name[j], markeredgecolor=mod_colour[j])
        numpoints_count.append(1)
    #axes1.plot(data[:,1],data[:,0]+input.datum_shift[i], color=input.colour[i],label=input.Name[i])
    ax[axis_count].grid(True)
    if(len(locs.legend_loc[i])>0):
        handles, labels = ax[axis_count].get_legend_handles_labels()
        ax[axis_count].legend(loc=locs.legend_loc[i],prop=fontP, numpoints=4)
    else:
        ax[axis_count].legend(loc=4,prop=fontP,numpoints=4)
    ax[axis_count].set_xlim(locs.xmin[i],locs.xmax[i])
    ax[axis_count].set_ylim(locs.ymin[i],locs.ymax[i])
    ax[axis_count].set_title(locs.LongName[i],fontsize="20")
##    if (locs.xmin[i]>-98):
##        ax[axis_count].set_xlim([locs.xmin[i],locs.xmax[i]])
##    if (locs.ymin[i]>-98):
##        ax[axis_count].set_ylim([locs.ymin[i],locs.ymax[i]])
# load data
report_label = 'Plot 29 DM Historic Calibration Events Rating Curve Comparison - Sheet B'
fig_name = '29_RT_DM_Calib_Ratings_B'
fig.text(0.6,0.006,'Note: 1974 hydrology on the Bremer River adopts 50/50 Aurecon/ SEQwater losses', fontsize = "16")
fig.text(0.02,0.006,' 1974 event: Fast Model Version: 0285_ST09 Detailed Model Version: 043_ST09\n All other events: Fast Model Version: 0285 Detailed Model Version: 043',fontsize="16")

fig.text(0.45,0.02,report_label,fontsize="28")
plt.tight_layout(pad=10.0, w_pad=7.0, h_pad=2.0)
#fig_fname = 'Bris_'+event+savename+'.png'
fig_file = os.path.join(out_fpath,(fig_name+'.png'))
print 'saving file '+fig_file
fig.savefig(fig_file, dpi=(300))
fig_file = os.path.join(out_fpath,(fig_name+'.pdf'))
print 'saving file '+fig_file
fig.savefig(fig_file, dpi=(300))
#plt.show()
plt.close(fig)

fig = plt.figure(figsize=(paper_width,paper_height))
axes1 = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # main axes
nRow=1
gs = gridspec.GridSpec(nRow, nCol)
ax=[]
labels = []
np = 0

for i in range(nRow-1,-1,-1):   #reversed to start from bottom
    for j in range(nCol-1,-1,-1):     #right to left
        np = np + 1
        if np > len(locs.ShortName):
            break
        else:
            ax.append(plt.subplot(gs[i, j]))
        if j == 0:
            ax[np-1].set_ylabel('Level (mAHD)', fontsize="18")
        if i == nRow-1:
            ax[np-1].set_xlabel('Flow (cumecs)', fontsize="18")

numpoints_count = []
for i in range (8,10):
    axis_count = i-8

    #add modelled data
    for j, label in enumerate(event_label):
        ax[axis_count].plot(event_flows[j][i],event_levels[j][i],color=mod_colour[j],marker=markersymbol[j],linestyle='None',markersize=mod_marker_size[j],label=label, markeredgecolor=marker_edge_colour[j],zorder = plot_zorder[j])
        numpoints_count.append(4)
    #add other curves
    for j in range(len(ext[i].Source)):
        print 'loading csv file: '+ext[i].Source[j]
        rfile = os.path.join(indir,ext[i].Source[j])
        data = numpy.genfromtxt(rfile, delimiter=",", skip_header=1)
        if (ext[i].line[j].upper() == 'F') or (ext[i].line[j].upper() == 'N'):
            ax[axis_count].plot(data[:,1],data[:,0]+ext[i].datum_shift[j], color=ext[i].colour[j],marker='o',linestyle='None',markersize=ext[i].markersize[j],label=ext[i].Name[j], markeredgecolor=mod_colour[j])
        else:
            ax[axis_count].plot(data[:,1],data[:,0]+ext[i].datum_shift[j], color=ext[i].colour[j],marker='o',markersize=ext[i].markersize[j],label=ext[i].Name[j], markeredgecolor=mod_colour[j])
        numpoints_count.append(1)
    #axes1.plot(data[:,1],data[:,0]+input.datum_shift[i], color=input.colour[i],label=input.Name[i])
    ax[axis_count].grid(True)
    if(len(locs.legend_loc[i])>0):
        handles, labels = ax[axis_count].get_legend_handles_labels()
        ax[axis_count].legend(loc=locs.legend_loc[i],prop=fontP, numpoints=4)
    else:
        ax[axis_count].legend(loc=4,prop=fontP,numpoints=4)
    ax[axis_count].set_title(locs.LongName[i],fontsize="20")
    ax[axis_count].set_xlim(locs.xmin[i],locs.xmax[i])
    ax[axis_count].set_ylim(locs.ymin[i],locs.ymax[i])
##    if (locs.xmin[i]>-98):
##        ax[axis_count].set_xlim([locs.xmin[i],locs.xmax[i]])
##    if (locs.ymin[i]>-98):
##        ax[axis_count].set_ylim([locs.ymin[i],locs.ymax[i]])

# load data
report_label = 'Plot 30 DM Historic Calibration Events Rating Curve Comparison - Sheet C'
fig_name = '30_RT_DM_Calib_Ratings_C'
fig.text(0.6,0.006,'Note: 1974 hydrology on the Bremer River adopts 50/50 Aurecon/ SEQwater losses', fontsize = "16")
fig.text(0.02,0.006,' 1974 event: Fast Model Version: 0285_ST09 Detailed Model Version: 043_ST09\n All other events: Fast Model Version: 0285 Detailed Model Version: 043',fontsize="16")

fig.text(0.45,0.02,report_label,fontsize="28")
plt.tight_layout(pad=10.0, w_pad=7.0, h_pad=2.0)
#fig_fname = 'Bris_'+event+savename+'.png'
fig_file = os.path.join(out_fpath,(fig_name+'.png'))
print 'saving file '+fig_file
fig.savefig(fig_file, dpi=(300))
fig_file = os.path.join(out_fpath,(fig_name+'.pdf'))
print 'saving file '+fig_file
fig.savefig(fig_file, dpi=(300))
#plt.show()
plt.close(fig)