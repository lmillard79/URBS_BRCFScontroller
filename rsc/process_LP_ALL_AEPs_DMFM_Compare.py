import os, re, sys, glob
import fnmatch
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import LP_Data
import VM_LP
import LP_CP_Bank
import LP_Bridge_Deck
import LP_RP
import numpy as npy
import get_plot_name_testing as gpn
import eventFinder as evtFinder
import bris_utilities as utl

#get arguments:
##nArg = len(sys.argv)
##runid = []
##print 'Number of arguments:', len(sys.argv), 'arguments.'
###print 'Argument List:', str(sys.argv)
##for i, arg in enumerate(sys.argv):
##    if i == 0:
##        print 'skipping 1st argument'
##    elif i ==1:
##        loc = str(arg)

def long_sub(fig,ax,xlim,ylim,loc_range,yticks,in_files,fig_t_text,output,rp_loc,aep,obs_fpath,base_res_dir_dm,base_res_dir_fm,cal_runid,base_mc_dir_dm,base_mc_dir_fm,mc_runid,events,mc_events_fm,mc_events_dm,fig_title,outdir,fig_fname,updated_tw_set):
    ###### make a plot for Lower and Mid Brisbane

    mod_colour = ['green','darkorange','blueviolet','darkred','darkgoldenrod','deeppink']
    FM_mod_colour = ['red']
    linew = 4
    colour_100m = 'gold'
    size_100m = 24
    colour_500m = 'deepskyblue'
    size_500m = 16
    bed_colour = 'grey'
    LB_colour = 'lightgrey'
    RB_colour = 'lightgrey'

    dur_col_dict = utl.get_ind_dict()

    #event_label=['FM 1974','FM 1996','FM 1999','FM 2011','FM 2013']
    event_label=['DM 1974','DM 1996','DM 1999','DM 2011','DM 2013']

    # Calibration Events
    LP1 = []
    MC1 = []
    MC1a =[]
    for i, event in enumerate(events):
        year=events[i][1:]
        res_dir = os.path.join(base_res_dir_dm,event)
        #FM modelled
        infpath = os.path.join(res_dir,('LP_003_BR_D_'+events[i]+'_'+cal_runid[i]+ in_files[3]))
        if os.path.isfile(infpath):
            LP1.append(LP_Data.LP_Data(infpath))
            if LP1[i].LP_Mod.count(-99.0) >= 0:
##                for j, data in enumerate(LP1[i].LP_Mod):        #Clean data of blank values
##                    if (data == -99.0):
##                       del LP1[i].LP_dist[j]
##                       del LP1[i].LP_Mod[j]
                mask = npy.array(LP1[i].LP_Mod) != -99.0
                LP1[i].LP_dist = list(npy.array(LP1[i].LP_dist)[mask])
                LP1[i].LP_Mod = list(npy.array(LP1[i].LP_Mod)[mask])

#            ax.plot(LP1[i].LP_dist,LP1[i].LP_Mod, color=mod_colour[i],linewidth=2,label=event_label[i],linestyle='--')

        else:
            print 'Doesn''t exists skipping: '+ infpath

    pp = []

	# DETAILED MODEL PLOTTING
    for aa, aep_ev in enumerate(aep):
        mc_evts = mc_events_dm[aa]

        for i, mc_ev in enumerate(mc_evts):
        #year=events[i][1:]

            # Get the start of the long section name
            crud,dm_file = os.path.split(mc_ev)
            ev_str = dm_file[18:-8]
            dm_file = 'LP_003_' + dm_file[:-4]

            #FM modelled
            infpath = os.path.join(base_mc_dir_dm,(dm_file + in_files[4]))

            if os.path.isfile(infpath):
                MC1.append(LP_Data.LP_Data(infpath))
                MC1a.append(LP_Data.LP_Data(infpath))
                mask = npy.array(MC1[i].LP_Mod) <= -99.0
                if mask.any():
                    tmp_dist = npy.array(MC1[i].LP_dist)
                    tmp_mod = npy.array(MC1[i].LP_Mod)
                    tmp_dist[mask] = npy.nan
                    tmp_mod[mask] = npy.nan
                    MC1[i].LP_dist = list(tmp_dist)
                    MC1[i].LP_Mod =  list(tmp_mod)

                if MC1[i].LP_dist == []:
                    continue
            else:
                print 'Doesn''t exists skipping: '+ infpath

        # Extract and Plot the Maximum
        max_array = npy.zeros([len(MC1a[0].LP_Mod),len(MC1a)])
        dist_array = npy.zeros([len(MC1a[0].LP_Mod),len(MC1a)])
        for i, dat in enumerate(MC1a):
            max_array[:,i] = MC1a[i].LP_Mod
            dist_array[:,i] = MC1a[i].LP_dist

        max_ev = npy.nanmax(max_array,axis=1)
        dist_array = npy.nanmax(dist_array,axis=1)

        mask = npy.logical_or(max_ev <= -99.,  npy.isnan(max_ev))
        if mask.any():
            max_ev[mask] = npy.nan
            dist_array[mask] = npy.nan

        ax.plot(dist_array,max_ev, color=dur_col_dict[str(aa)],linewidth=3,label='MC_Max_'+ aep_ev+'_DM')


    # FAST MODEL PLOTTING
    for aa,aep_ev in enumerate(aep):
        MC1 = []
        evvents = list(set(mc_events_fm[aa]))
        for k, ev in enumerate(evvents):

            # Get the duration and event name
            out_str = utl.index_to_dur_event(float(ev))
            dur, ee = out_str.split('_')
            res_dir = os.path.join(base_mc_dir_fm,dur)

            # Point at the right event if tailwaters have been amended.
            if set.intersection(set([utl.index_to_dur_event(float(ev))]) ,updated_tw_set):
                # Return the duration and event name from the index
                mc_runid = '0380'
            else:
                mc_runid = '0360'
            infpath = os.path.join(res_dir,('LP_003_BR_F_'+ dur +'_' + ee + '_MC_' + mc_runid + '_MC'+ in_files[4]))

            if os.path.isfile(infpath):
                MC1.append(LP_Data.LP_Data(infpath))

            else:
                print 'Doesn''t exists skipping: '+ infpath

        # Extract and Plot the Maximum
        max_array = npy.zeros([len(MC1[0].LP_Mod),len(MC1)])
        dist_array = npy.zeros([len(MC1[0].LP_Mod),len(MC1)])

        for l, dat in enumerate(MC1):
            max_array[:,l] = MC1[l].LP_Mod
            dist_array[:,l] = MC1[l].LP_dist

        max_ev = npy.nanmax(max_array,axis=1)
        dist_array = npy.nanmax(dist_array,axis=1)

        mask = npy.logical_and(max_ev != -99., max_ev != npy.isnan)
        max_ev = max_ev[mask]
        dist_array = dist_array[mask]

        print "plotting event aep: " + aep_ev
        ax.plot(dist_array,max_ev, color=dur_col_dict[str(aa)],linewidth=3,label='MC_Max_'+ aep_ev+ '_FM',linestyle='dotted')
        #else:
        #    ax.plot(dist_array,max_ev, color=dur_col_dict[aep_ev],linewidth=3,label='MC_Max_PMF')


    #bridge decks
    road_file = os.path.join(obs_fpath,in_files[1])
    if os.path.isfile(road_file):
        road = LP_Bridge_Deck.LP_Bridge_Deck(road_file)
        for i in range(len(road.chainage)):
            ax.plot([road.chainage[i],road.chainage[i]],[road.Invert[i],road.Obvert[i]], linestyle='-', color='black', marker='',linewidth=4)
            if road.label[i] == 'Centenary Motorway' and event == 'C1974':  # This is currently redundant or not working due to multiple calibration plots on one sheet.
                road.chainage[i] = road.chainage[i]-400
            elif road.label[i] == 'Mt Crosby Weir' and event == 'C2013':
                    road.chainage[i] = road.chainage[i]-400
            else:
                road.chainage[i] = road.chainage[i]
                ax.text(road.chainage[i],road.Obvert[i]+0.25,road.label[i],rotation=90,verticalalignment='bottom',fontsize=12)

    #Bed and bank levels
    bank_file = os.path.join(obs_fpath,in_files[2])
    if os.path.isfile(bank_file):
        bank_data = LP_CP_Bank.LP_CP_Bank(bank_file)
        ax.plot(bank_data.chainage,bank_data.invert,linestyle='-', marker='',color=bed_colour)

    ax.set_xlabel('Chainage (m)',fontsize=16)
    ax.set_ylabel('Level (mAHD)',fontsize=16)
    ax.yaxis.set_ticks(yticks)
    ax.grid(True)
    ax.legend(numpoints=1,prop={'size':16})
    ax.set_title(fig_t_text,fontsize=24)
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)

    major_ticks = npy.arange(ylim[0],ylim[1],5)
    minor_ticks = npy.arange(ylim[0],ylim[1],1)
    ax.set_yticks(major_ticks)
    ax.set_yticks(minor_ticks, minor = True)
    ax.grid(which = 'minor', alpha=0.5, linewidth=2)
    ax.grid(which = 'major', alpha = 1, linewidth=2)

    if output:
        suffix = ''
        for event in events:
            suffix='_'+event

        #fig_fname = 'LP_LowBris_MidBris'+year+suffix+'.'+fext
        plt.tight_layout(pad=5.0, w_pad=2.0, h_pad=3.0)
        fig.text(0.60,0.02,fig_title,fontsize="28")
        fig.text(0.06,0.015,'Bridge Levels shown are lowest soffit and lowest deck level',fontsize="26")
        #fig.text(0.06,0.006,'Fast Model Version: 0285',fontsize="16")
        fig_file = os.path.join(outdir,(fig_fname+'.png'))
        print 'saving file '+fig_file
        fig.savefig(fig_file, dpi=(200))
        fig_file = os.path.join(outdir,(fig_fname+'.pdf'))
        print 'saving file '+fig_file
        fig.savefig(fig_file, dpi=(300))
        print 'done'
        plt.close(fig)

def long_section(loc,mc_events_dm,mc_events_fm,fig_title,spliced,aep,updated_tw_set):

    #for loc in locations:
    #user
    cal_runid = ['043_All+30m+ST09','043_All+30m','043_All+30m','043_All+30m','043_All+30m']
    mc_runid = '600'
    events = ['C1974','C1996','C1999','C2011','C2013']
    outdir = r'C:\Projects\Python\TUFLOW\ReportPlots'
    rp_loc = r'C:\Projects\BRFS\Long_Sections'
    base_res_dir_dm = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\000_General\000_Scripts\PostProcessing\DM2\calib_data\LP\DM'
    base_mc_dir_dm = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\600_D_Design_Events\TUFLOW\D\results\600\B15\LongSections'
    obs_fpath = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\000_General\000_Scripts\PostProcessing\DM2\calib_data\LP\OBS'

    base_res_dir_fm = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\200_Calibration_S2\TUFLOW\F\results'
    base_mc_dir_fm = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\TUFLOW\F\results\360\360'


    xlim = [0,80000]
    mb_ylim = [5,65]
    lb_ylim = [0,40]
    lk_ylim = [30,110]
    bm_ylim = [0,40]

    # ranges
    lb_range = lb_ylim[1]-lb_ylim[0]
    mb_range = mb_ylim[1]-mb_ylim[0]
    lk_range = lk_ylim[1]-lk_ylim[0]
    bm_range = bm_ylim[1]-bm_ylim[0]

    #xticks
    lb_ytick = range(lb_ylim[0],lb_ylim[1]+1,5)
    mb_ytick = range(mb_ylim[0],mb_ylim[1]+1,5)
    lk_ytick = range(lk_ylim[0],lk_ylim[1]+1,5)
    bm_ytick = range(bm_ylim[0],bm_ylim[1]+1,5)

    # Add limits etc to lists
    yticks =[lb_ytick,mb_ytick,lk_ytick,bm_ytick]
    ylims = [lb_ylim,mb_ylim,lk_ylim,bm_ylim]
    loc_range =[lb_range,mb_range,lk_range,bm_range]



   # Need to add a list here of the gauge file, bridge deck file,fm res
    #if aep == '2' or aep == '5' or aep == '10':
    #    gfile = ['RP_Gauges_LBris_noWoo.csv','RP_Gauges_Mid_Bris.csv','RP_Gauges_Lock.csv','RP_Gauges_Brem_noWoo.csv']
    #else:
    gfile = ['RP_Gauges_LBris.csv','RP_Gauges_Mid_Bris.csv','RP_Gauges_Lock.csv','RP_Gauges_Brem.csv']
    brd_file = ['LP_Roads_Lower_Brisbane_002.csv','LP_Roads_Mid_Brisbane_002.csv','LP_Roads_Lockyer_002.csv','LP_Roads_Bremer_002.csv']
    bed_file = ['LP_inverts_DM_check_021_Lower Brisbane.csv','LP_inverts_DM_check_021_Mid Brisbane.csv','LP_inverts_DM_check_021_Lockyer.csv','LP_inverts_DM_check_021_Bremer.csv']
    fm_cal_file = ['_h_Max_Lower Brisbane.csv','_h_Max_Mid Brisbane.csv','_h_Max_Lockyer.csv','_h_Max_Bremer.csv']
    fm_mc_file = ['_h_Max_Lower Brisbane.csv','_h_Max_Mid Brisbane.csv','_h_Max_Lockyer.csv','_h_Max_Bremer.csv']
    #fm_mc_file = ['_MC_h_Max_Lower Brisbane.csv','_MC_h_Max_Mid Brisbane.csv','_MC_h_Max_Lockyer.csv','_MC_h_Max_Bremer.csv']
    fig_t_text = ['Lower Brisbane','Mid Brisbane','Lockyer','Bremer']


    # Get the plot number and pad it with zeros
    rid = re.compile('Plot\s+\d+')
    tmp,left_overs = re.split(rid,fig_title)
    plot_number = re.search(rid,fig_title)
    plot_number = plot_number.group()

    # split the plot number and change the number to be padded
    tmp, nn = plot_number.split(' ')
    nn = nn.zfill(3)
    tmp = tmp + ' ' + nn
    fig_out = tmp + left_overs
    fig_fname = fig_out.replace('.','_')
    fig_fname = fig_fname.replace('Bremer/Lockyer','Bremer_Lockyer')

    if loc.upper()=='BRIS':

        #fig_fname = 'BR_LS_' + fig_fname
        fig = plt.figure(figsize=(42.0,29.7))
        gs = gridspec.GridSpec(2, 1,height_ratios=[mb_range,lb_range])
        ax1 = plt.subplot(gs[1, 0])
        ax2 = plt.subplot(gs[0, 0])
        ax_both = [ax1,ax2]

        output = False
        for i in range(len(ax_both)):
            in_files = [gfile[i],brd_file[i],bed_file[i],fm_cal_file[i],fm_mc_file[i]]
            long_sub(fig,ax_both[i],xlim,ylims[i],loc_range[i],yticks[i],in_files,fig_t_text[i],output,rp_loc,aep,obs_fpath,base_res_dir_dm,base_res_dir_fm,cal_runid,base_mc_dir_dm,base_mc_dir_fm,mc_runid,events,mc_events_fm,mc_events_dm,fig_title,outdir,fig_fname,updated_tw_set)
            output = True

    else:
        #fig_title = 'Lockyer Creek / Bremer River Longitudinal Profiles ' + fig_title
        #fig_fname = 'BR_LOC_LS_' + fig_fname

        ###### make a plot for Lockyer / Bremer
        fig = plt.figure(figsize=(42.0,29.7))
        gs = gridspec.GridSpec(2, 1,height_ratios=[lk_ylim[1]-lk_ylim[0],bm_ylim[1]-bm_ylim[0]])
        ax2 = plt.subplot(gs[1, 0])
        ax1 = plt.subplot(gs[0, 0])
        ax_both = [ax1,ax2]

        output = False
        for i in range(len(ax_both),len(ax_both)+len(ax_both)):    # Start 2 after the previous run through
            in_files = [gfile[i],brd_file[i],bed_file[i],fm_cal_file[i],fm_mc_file[i]]
            long_sub(fig,ax_both[i-2],xlim,ylims[i],loc_range[i],yticks[i],in_files,fig_t_text[i],output,rp_loc,aep,obs_fpath,base_res_dir_dm,base_res_dir_fm,cal_runid,base_mc_dir_dm,base_mc_dir_fm,mc_runid,events,mc_events_fm,mc_events_dm,fig_title,outdir,fig_fname,updated_tw_set)
            output = True


#===============================================================================