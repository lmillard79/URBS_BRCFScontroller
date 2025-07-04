#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Mitchell.Smith
#
# Created:     19/05/2015
# Copyright:   (c) Mitchell.Smith 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import numpy as np
import csv, sys
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pylab as P
import process_MC_Results as mc
import bris_utilities as utl
import eventFinder as evFinder
import TUFLOW_results2015_BRFS as tr
from mpl_toolkits.axes_grid1 import make_axes_locatable
import re
import plot_RF_AEPs as prf
from matplotlib.patches import Polygon
from matplotlib.patches import Patch
from scipy import stats
from matplotlib.backends.backend_pdf import PdfPages

# NOTE ALL FUNCTIONS ARE IN ALPHABETICAL ORDER
def aep_bin(catch_aep,bins):

    # Make a copy of the data
    binned_aep = catch_aep

    # Bin the data
    for i,b in enumerate(bins):
        if i < len(bins)-1:
            lower,upper = (b,bins[i+1])
            mask = (catch_aep <=lower) & (catch_aep > upper)
            binned_aep[mask]= b

    return binned_aep

def aep_cross_plot(fig,ax,num,x,y,dur,loc):

    #fig = plt.figure()
    #ax = plt.gca()
    d = ax[num].scatter(x ,y, c=dur, alpha=0.3, edgecolors='none',cmap=plt.cm.jet,label='dur',rasterized=True)
    divider = make_axes_locatable(ax[num])
    cax = divider.append_axes("right", "5%", pad="3%")
    cb = fig.colorbar(d,cax=cax)
    cb.set_label ('Duration (hrs)',fontsize=18)
    # add 1:1 line
    ax[num].plot([0.00000001,1],[0.00000001,1],'k',linewidth=2.0)
    #ax.legend()
    # Setup axes
    ax[num].set_yscale('log')
    ax[num].set_xscale('log')
    ax[num].set_xlim([0.00000001,1])
    ax[num].set_ylim([0.00000001,1])
    ax[num].grid('on')
    ax[num].set_title(loc,fontsize=20)
    ax[num].invert_xaxis()
    ax[num].invert_yaxis()
    return fig, ax

def bab_plot(fig,ax,num,ev_set,data_reorder,max_reorder,tol_reorder,lims_reorder,loc_names_reorder,aep):

    dur_col = utl.get_ind_dict()
    ax[num].plot(range(28),tol_reorder,'r',linewidth=4,label='Critical Event\nTolerance (CET)',linestyle='--')

    # Make the shaded region
    a = min(range(28))
    b = max(range(28))
    ix = np.arange(a, b+1, 1.0)
    ixi = ix[::-1]
    iy = lims_reorder
    iyi = lims_reorder*-1
    iyi = iyi[::-1]
    ix = np.r_[ix,ixi]
    iy = np.r_[iy,iyi]

    # Add the starting point
    ix = np.r_[ix,0.0]
    iy = np.r_[iy,0.5]
    verts = zip(ix, iy)
    poly = Polygon(verts, facecolor='0.9', edgecolor='0.5')
    ax[num].add_patch(poly)
    grey_patch = Patch(color='grey',label='ITO Desired Accuracy')
    leg1 = ax[num].legend(handles=[grey_patch],loc=1)


    ax[num].plot(range(28),max_reorder,'k',linewidth=5,label='Maximum')

    for i,ens in enumerate(ev_set):
        out_str = evFinder.index_to_dur_event(ens)
        dur,ev = out_str.split('_')
        ax[num].plot(range(28),data_reorder[:,i],dur_col[str(i)],linewidth=3,label=out_str)

    leg2 = ax[num].legend(loc=4)
    leg1 = ax[num].add_artist(leg1)
    leg2 = ax[num].add_artist(leg2)

    #if aep == '100000':   # If block removed 19/02 at request of client.
    #    ax[num].set_title('Event Selection - PMF' ,fontsize=20.0)
    #else:
    ax[num].set_title('Event Selection - 1 in ' + aep + '  AEP',fontsize=20.0)

    ax[num].set_ylim([-1.5,0.6])
    return fig,ax


def bar_plot(fig, ax, num, x,bins,title):
    #x =
    m,n = x.shape
    bar_width = 0.35
    ind = [1]*m

    rect1 = ax[num].bar(m,x[:,0],bar_width,color='blue')
#    ax[num].bar(index,x, color=['blue', 'green','yellow','red'])
    ax[num].bar(index,x,bar_width)
    ax[num].set_title(title)
    ax[num].legend()
    ax[num].grid(True)
    ax[num].xticks(index + bar_width, ('tH', 'tdH', 'tQ','tdQ'))
    return fig,ax

def cross_plot(fig,ax,num,x,y,title):
    ax[num].plot(x,y,'bo')
    ax[num].set_xscale('log')
    ax[num].set_xlim([0.0000001,1])
    ax[num].invert_xaxis()
    ax[num].set_title(title)
    ax[num].grid(True)
    return fig,ax

def hh_cross_plot(fig,ax,num,x,y,dur,loc):

    #fig = plt.figure()
    #ax = plt.gca()

    xmax = np.max(x)
    ymax = np.max(y)
    axmax = max(xmax,ymax)

    d = ax[num].scatter(x ,y, c=dur,  edgecolors='none',cmap=plt.cm.jet,label='dur',rasterized=True)
    divider = make_axes_locatable(ax[num])
    cax = divider.append_axes("right", "5%", pad="3%")
    cb = fig.colorbar(d,cax=cax)
    cb.set_label ('Duration (hrs)',fontsize=18)
    # add 1:1 line
    ax[num].plot([1,axmax],[1,axmax],'k',linewidth=2.0)
    #ax.legend()
    # Setup axes
    #ax[num].set_yscale('log')
    #ax[num].set_xscale('log')
    ax[num].set_xlim([1,axmax])
    ax[num].set_ylim([1,axmax])
    ax[num].grid('on')
    ax[num].set_title(loc,fontsize=20)
    #ax[num].invert_xaxis()
    #ax[num].invert_yaxis()
    return fig, ax

def hist(x,bins,title):
    mu = np.mean(x)
    sigma= np.std(x)
    plt.hist(x,bins)
    plt.title(title)
    plt.grid()
    return plt

def plot_A3_Bab(ev_set_all,data_reorder, max_reorder, tol_reorder,lims_reorder,ylabel,loc_names_reorder, outdir,fig_title,aep_list):

# This is the core function for the plotting of multiple locations on a single A3 sheet.
# It uses a series of if statements using the pltType switch to determine what type of subplot
# will be output.

    # Setup the subplots and A3 Sheet
    nRow = 2
    nCol = 2
    num_pages = 3
    paper_width = 42.0
    paper_height = 29.7
    ii = 0

    for pp in range(num_pages):
        fig = plt.figure(figsize=(paper_width,paper_height))
        fig.autofmt_xdate()
        gs = gridspec.GridSpec(nRow, nCol)
        ax=[]
        labels = []
        nplots = 0

      #create axes
        for i in range(nRow):
            for j in range(nCol):
                nplots = nplots + 1
                ax.append(plt.subplot(gs[i, j]))
                ax[nplots-1].set_yticks(np.arange(-1.5, 1+1, 0.5)) # Update to have a set ymin
                ax[nplots-1].set_ylabel(ylabel, fontsize=18)
                ax[nplots-1].set_xticks(np.arange(min(range(28)), max(range(28))+1, 1.0))
                ax[nplots-1].set_xticklabels(loc_names_reorder,rotation=90,fontsize=18.0)
                labels.append(ax[nplots-1].get_xticklabels())
                ax[nplots-1].grid(True)               #make all grids visible

        print 'Finished creating axes'

        #plot output for each AEP. There will be 3 sheets for 11 AEPs
        for i in range(nRow*nCol):
            try:
                # Plot the Data
                fig,ax = bab_plot(fig,ax,i,ev_set_all[ii],data_reorder[ii],max_reorder[ii],tol_reorder[ii],lims_reorder,loc_names_reorder,aep_list[ii])
                ii+=1
            except:
                print 'Issue with plotting routine!'
                break

            # Remove the unwanted axis from the third page of the plots
            if pp == 2:
                for xx in range(3,4):
                    ax[xx].axis("off")

        # Output
        fig.text(0.55,0.02,fig_title[pp],fontsize="28")
        plt.tight_layout(pad=10.0, w_pad=7.0, h_pad=2.0)

        # Get the plot number and pad it with zeros
        rid = re.compile('Plot\s+\d+')
        tmp,left_overs = re.split(rid,fig_title[pp])
        plot_number = re.search(rid,fig_title[pp])
        plot_number = plot_number.group()

        # split the plot number and change the number to be padded
        tmp, nn = plot_number.split(' ')
        nn = nn.zfill(3)
        tmp = tmp + ' ' + nn
        fig_out = tmp + left_overs

        save_fig(fig,outdir,fig_out,200)

        print 'finished'


def plot_A3_RL(x, y, z, w, xlabel, ylabel,var, loc_names, dur, outdir,pltType,alldir,event_ll,fig_title):
# This is the core function for the plotting of multiple locations on a single A3 sheet.
# It uses a series of if statements using the pltType switch to determine what type of subplot
# will be output.
# Inputs

    # define figure layout
    dur_scatter_array = dur # This is needed for scatter plot output. Sloppy coding, can be improved.

    if alldir == False or pltType == 'aep_cross_plot':
        dur = ['000']

    for dd, row in enumerate(dur):

        nRow = 4
        nCol = 3
        paper_width = 42.0
        paper_height = 29.7
        ii = 0

        if pltType == 'urbs_cross_plot' or pltType == 'urbs_cross_plot_vol':
            num_pages = 1
            site_order = [16,17,18,21,4,5,7,8,13]
            nRow = 3
            nCol = 3

        else:
            num_pages = 3

            # Lockyer and Bremer First then Brisbane. Upstream to Downstream
            site_order = [2,0,16,17,18,19,20,22,21,23,25,24,1,3,4,5,6,7,26,8,27,9,10,11,12,13,14,15]

        for pp in range(num_pages):
            fig = plt.figure(figsize=(paper_width,paper_height))
            fig.autofmt_xdate()
            gs = gridspec.GridSpec(nRow, nCol)
            ax=[]
            ax2 =[]
            labels = []
            nplots = 0

          #create axes
            for i in range(nRow):
                for j in range(nCol):
                    nplots = nplots + 1

                    # Setup the axes for the cross plots so they are square
                    if pltType == 'aep_cross_plot' or pltType == 'urbs_cross_plot' or pltType == 'urbs_cross_plot_vol' or pltType == 'qq_cross_plot'or pltType == 'hh_cross_plot':
                        ax.append(plt.subplot(gs[i, j], aspect='equal'))
                    else:
                        ax.append(plt.subplot(gs[i, j]))

                    ax[nplots-1].set_ylabel(ylabel, fontsize="16")
                    labels.append(ax[nplots-1].get_xticklabels())
                    ax[nplots-1].set_xlabel(xlabel,fontsize='16')
                    ax[nplots-1].grid(True)               #make all grids visible

                    if pltType == 'time_series' or pltType == 'time_series_dm':
                        ax2.append(ax[nplots-1].twinx())
                        ax2[nplots-1].set_ylabel('Flow ($m^3/s$)', fontsize="16")
                        labels.append(ax2[nplots-1].get_xticklabels())
                        ax2[nplots-1].set_xlabel(xlabel,fontsize='16')

            print 'Finished creating axes'
# ==============================================================================
# ==============================================================================
            # Output plots to the grid depending on what type you are after
            for i in range(nRow*nCol):
                try:
                    if pltType == 'multihist':
                        fig,ax = stacked_hist(fig,ax,i,x[:,:,site_order[ii]],20,loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'multihist2':
                            # Histograms with tH, tQ, tdH, tdQ
                        # Concatenate input
                        time_data = np.zeros([9*1260,4])
                        time_data[:,0] = np.reshape(x[:,:,site_order[ii]],-1)
                        time_data[:,1] = np.reshape(y[:,:,site_order[ii]],-1)
                        time_data[:,2] = np.reshape(z[:,:,site_order[ii]],-1)
                        time_data[:,3] = np.reshape(w[:,:,site_order[ii]],-1)

                        fig,ax = stacked_hist2(fig,ax,i,time_data,20,'Frequency of ' + var + ' - ' + loc_names[ii])
                        ii+=1

                    elif pltType == 'bar':
                            # Histograms with tH, tQ, tdH, tdQ
                        # Concatenate input
                        time_data = np.zeros([9*1260,4])
                        time_data[:,0] = np.reshape(x[:,:,site_order[ii]],-1)
                        time_data[:,1] = np.reshape(y[:,:,site_order[ii]],-1)
                        time_data[:,2] = np.reshape(z[:,:,site_order[ii]],-1)
                        time_data[:,3] = np.reshape(w[:,:,site_order[ii]],-1)

                        fig,ax = bar_plot(fig,ax,i,time_data,20,'Frequency of ' + var + ' - ' + loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'crossplot':
                        fig,ax = cross_plot(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],'Frequency of ' + var + ' - ' + loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'aep_cross_plot':
                        fig,ax = aep_cross_plot(fig,ax,i,x[:,site_order[ii]],y[:,site_order[ii]],dur_scatter_array[:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'scatterplot':   # THIS IS BROKEN 16/06 JMJS
                        d = np.zeros([len(dur_scatter_array),1260])
                        for j,xx in enumerate(dur_scatter_array):
                            d[j,:].fill(float(xx))
                        fig,ax = scatter_plot(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],d,loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'scatter_plot_diffs':
                        aep_168 = w[0]
                        diff_168 = w[1]
                        fig,ax = scatter_plot_diffs(fig,ax,i,x[:,site_order[ii]],y[:,site_order[ii]],z,aep_168[:,site_order[ii]],diff_168[:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'scatterplotdur':
                        fig,ax = scatter_plot_dur(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],z[:,:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'scatterplotdurwl':
                        fig,ax = scatter_plot_dur_wl(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],z[:,:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'scatterplotwlq':
                        fig,ax = scatter_plot_wl_q(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],z[:,:,site_order[ii]],w[:,:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'time_series':

                        # Now that we have all the data, plot out all the data one site at a time
                        fig,ax,ax2 = ts_plot(fig,ax,ax2, i, x, y[:,:,site_order[ii]], z[:,:,site_order[ii]], w, loc_names[site_order[ii]],site_order[ii],event_ll)
                        ii+=1

                    elif pltType == 'time_series_dm':

                        # Now that we have all the data, plot out all the data one site at a time
                        fig,ax,ax2 = ts_plot_dm(fig,ax,ax2, i, x, y[:,:,site_order[ii]], z[:,:,site_order[ii]], w, loc_names[site_order[ii]],site_order[ii],event_ll)
                        ii+=1


                    elif pltType == 'urbs_cross_plot':
                        fig,ax = urbs_cross_plot(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],z[:,:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'qq_cross_plot':
                        fig,ax = qq_cross_plot(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],z[:,:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'hh_cross_plot':
                        fig,ax = hh_cross_plot(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],z[:,:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1

                    elif pltType == 'urbs_cross_plot_vol':
                        fig,ax = urbs_cross_plot_vol(fig,ax,i,x[:,:,site_order[ii]],y[:,:,site_order[ii]],z[:,:,site_order[ii]],loc_names[site_order[ii]])
                        ii+=1


                except:
                    print 'Issue with plotting routine!'
                    break

            # Remove the unwanted axis from the third page of the plots
            if pltType == 'urbs_cross_plot':
               # for xx in range(9,12):
                #    ax[xx].axis("off")
                pass

            elif pp == 2:
                for xx in range(4,12):
                    ax[xx].axis("off")
                    if pltType == 'time_series' or pltType == 'time_series_dm':
                        ax2[xx].axis("off")

            if pltType == 'time_series' or pltType == 'time_series_dm':
                tmp, aep =var.split('out')

                # For Woogaroo do not show data 10 y or below.
##                if (aep == '2' or aep == '5' or aep == '10') and pp == 1:
##                    ax[6].cla()
##                    ax2[6].cla()
##                    ax[6].axis('off')
##                    ax2[6].axis('off')
##                    # Add text
##                    fig.text(0.13,0.38,'Deliberately left blank.',fontsize="36",color='dimgrey')

                aep_dict = {'2': 0,
                            '5': 3,
                            '10': 6,
                            '20': 9,
                            '50': 12,
                            '100': 15,
                            '200': 18,
                            '500': 21,
                            '2000': 24,
                            '10000': 27,
                            '100000':30}

            if pltType == 'time_series' or pltType == 'time_series_dm':
                fig.text(0.50,0.02,fig_title[pp],fontsize="28")
            else:
                fig.text(0.55,0.02,fig_title[pp],fontsize="28")

            if pltType != 'urbs_cross_plot' and pltType != 'urbs_cross_plot_vol':
                if pp == 0:
                    fig.text(0.06,0.015,'Lockyer/Bremer',fontsize="28")
                elif pp == 1:
                    fig.text(0.06,0.015,'Mid to Lower Brisbane',fontsize="28")
                else:
                    fig.text(0.06,0.015,'Brisbane City',fontsize="28")

            # Output
            plt.tight_layout(pad=10.0, w_pad=7.0, h_pad=2.0)
            #plt.tight_layout(pad=5.0, w_pad=2.0, h_pad=3.0)

            # Get the plot number and pad it with zeros
            rid = re.compile('Plot\s+\d+')
            tmp,left_overs = re.split(rid,fig_title[pp])
            plot_number = re.search(rid,fig_title[pp])
            plot_number = plot_number.group()

            # split the plot number and change the number to be padded
            tmp, nn = plot_number.split(' ')
            nn = nn.zfill(3)
            tmp = tmp + ' ' + nn
            fig_out = tmp + left_overs

            fig_out = fig_out.replace('.','_')
            save_fig(fig,outdir,fig_out,200)

        print 'finished'

# ==============================================================================
# ==============================================================================

def plot_events(ev_set,results_dir,save_loc,aep,aep_levels,plot_figs,updated_tw_set):
     # Result dir
        # Plot the water levels for a given ensemble
        #ev_set = list(ensemble_set[0])

        # Intitialise some time series arrays
        # Get the location names
        loc_names = utl.get_loc_names()
        m = len(loc_names)
        HH = np.zeros([len(ev_set),231,m])
        QQ = np.zeros([len(ev_set),231,m])  # Dodgey hardcode of time. Fix this later.

        # Loop through and populate the arrays with flow and water level data
        event_ll =[]
        dur_list =[]
        run_list = []

        for ee,ev in enumerate(ev_set):

            if set.intersection(set([utl.index_to_dur_event(float(ev))]),updated_tw_set):
                # Return the duration and event name from the index
                out_str = utl.index_to_dur_event(float(ev))
                event_ll.append(out_str)
                dur, event = out_str.split('_')
                file_name = 'BR_F_' + dur + '_' + event + '_MC_0380_MC.tpc'

            else:
                out_str = utl.index_to_dur_event(float(ev))
                event_ll.append(out_str)
                dur, event = out_str.split('_')
                file_name = 'BR_F_' + dur + '_' + event + '_MC_0360_MC.tpc'


            # Turn this into a path for the results files
            res_path = os.path.join(results_dir,dur,'plot',file_name)

            #initialise results
            res = tr.ResData()

            #load results
            error, message = res.Load(res_path)

            if error:
                print message

            print 'loaded'

            # Loop through each location and output a series of plots
            for i, loc_name in enumerate(loc_names):

                # Get the time and flow data
                t = res.Data_RL.Q_L.Values[:,1]
                QQ[ee,:,i] = res.Data_RL.Q_L.Values[:,i+2]
                HH[ee,:,i] = res.Data_RL.H_P.Values[:,i+2]

        ## Need to ensure that event number is output to file
        plot_A3_RL(t,QQ,HH,aep_levels,'Time (hrs)','Water Level (mAHD)','EV_TS_out'+str(aep),loc_names,dur,save_loc,'time_series',False,event_ll,plot_figs)

        print 'Plotting Complete'

def qq_cross_plot(fig,ax,num,x,y,dur,loc):

    #fig = plt.figure()
    #ax = plt.gca()

    xmax = np.max(x)
    ymax = np.max(y)
    axmax = max(xmax,ymax)

    d = ax[num].scatter(x ,y, c=dur,  edgecolors='none',cmap=plt.cm.jet,label='dur',rasterized=True)
    divider = make_axes_locatable(ax[num])
    cax = divider.append_axes("right", "5%", pad="3%")
    cb = fig.colorbar(d,cax=cax)
    cb.set_label ('Duration (hrs)',fontsize=18)
    # add 1:1 line
    ax[num].plot([1,axmax],[1,axmax],'k',linewidth=2.0)
    #ax.legend()
    # Setup axes
    #ax[num].set_yscale('log')
    #ax[num].set_xscale('log')
    ax[num].set_xlim([1,axmax])
    ax[num].set_ylim([1,axmax])
    ax[num].grid('on')
    ax[num].set_title(loc,fontsize=20)
    #ax[num].invert_xaxis()
    #ax[num].invert_yaxis()
    return fig, ax


def save_fig(fig,outdir,fname,dpi):
    fig_file = os.path.join(outdir, fname)
    print 'saving file '+ fig_file
    fig.savefig(fig_file, dpi=(dpi))

    # Turned off pdf output MJS 01/12/2015
    fig_file = os.path.join(outdir, (fname+'.pdf'))
    pdf= PdfPages(fig_file)
    print 'saving file '+fig_file
    pdf.savefig()
    pdf.close()

    plt.close(fig)

def scatter_plot(fig,ax,num,x,y,duration,title):
    pp = ax[num].scatter(x ,y, c=duration, alpha=0.3, edgecolors='none',cmap=plt.cm.jet,label='dur',rasterized=True)
    ax[num].set_xscale('log')
    ax[num].set_xlim([0.0000001,1])
    ax[num].grid(True)
    ax[num].invert_xaxis()
    ax[num].set_title(title)
#    cb = colorbar(pp)
 #   cb.set_label='AEP'
    return fig,ax

def scatter_plot2(fig,ax,num,x,y,z,title):
    ax[num].scatter(x ,y, c='blue', alpha=0.3, edgecolors='none',label = 'Q',rasterized=True)
    ax[num].scatter(x ,z, c='red', alpha=0.3, edgecolors='none',label = 'H',rasterized=True)
    ax[num].set_xscale('log')
    ax[num].set_xlim([0.0000001,1])
    ax[num].grid(True)
    ax[num].invert_xaxis()
    ax[num].legend()
    return fig,ax

def scatter_plot_dur(fig,ax,num,x,y,aep,title):
    pp = ax[num].scatter(x ,y, c=aep, alpha=0.3, edgecolors='none',cmap=plt.cm.jet,label='AEP',rasterized=True)
    ax[num].grid(True)
    ax[num].set_xlim([0.0,200])
    ax[num].set_ylim([0,250])
    ax[num].plot([0.0,250],[0,250],'k',linewidth=2.0,)
    ax[num].set_title(title)
#    cb = colorbar(pp)
#    cb.set_label='AEP'
    return fig,ax

def scatter_plot_dur_wl(fig,ax,num,x,y,aep,title):
    d = ax[num].scatter(x ,y, c=np.log(aep), alpha=0.3, edgecolors='none',cmap=plt.cm.jet_r,label='Rainfall AEP',rasterized=True)
    ax[num].grid(True)
    divider = make_axes_locatable(ax[num])
    cax = divider.append_axes("right", "5%", pad="3%")
    cb = fig.colorbar(d,cax=cax)
    cb.set_label ('Rainfall AEP',fontsize=18)
    cb.set_ticks(np.log([1, 0.2, 0.1, 0.05, 0.02, 0.01, 0.002, 0.001, 0.0001, 0.00001, 0.000001]))
    cb.set_ticklabels(['1', '0.2', '0.1', '0.05', '0.02', '0.01', '0.002', '0.001', '0.0001', '0.00001', '0.000001'], update_ticks=True)

    ax[num].set_title(title,fontsize=20)
    return fig,ax

def scatter_plot_wl_q(fig,ax,num,x,y,z,w,title):
    pp = ax[num].scatter(x ,y,c='royalblue', alpha=0.5, edgecolors='none',label='QH',rasterized=True)
    ppp = ax[num].scatter(x ,w,c='crimson', alpha=0.5, edgecolors='none',label='H at Peak Q',rasterized=True)
    pppp = ax[num].scatter(z ,y,c='yellowgreen', alpha=0.5, edgecolors='none',label='Q at Peak H',rasterized=True)
#    ax[num].set_xlim([-15000,250000])
 #   ax[num].set_ylim([0,80])
    ax[num].grid(True)
    ax[num].set_title(title)
    ax[num].legend(loc='lower right',numpoints=1)
    return fig,ax

def scatter_plot_diffs(fig,ax,num,x,y,z,aep_168,diff_168,title):

    bin_means, bin_edges, binnumber = stats.binned_statistic(x,y,'mean',bins=z)
    pp = ax[num].scatter(x,y,label='Non-168hr',rasterized=True)
    rr = ax[num].scatter(aep_168,diff_168,color='orange',label='168hr',rasterized=True)
    #ppp = ax[num].scatter(bin_edges[:-1],bin_means, color='red',s=10,marker='s')
    ppp = ax[num].plot(bin_edges[:-1],bin_means, color='red',linewidth=2.0,label='Mean of non-168hr')

    #ax = pp.axes
    #ax[num].set_ylim([-0.1,0.6])
    ax[num].set_xlim([1,1000000])
    ax[num].set_xscale("log")
    ax[num].set_title(title)
    ax[num].legend()
    # Add some labels
    #for k, txt in enumerate(bin_means):
     #   ax[num].annotate(np.round(txt,2), (bin_edges[k],bin_means[k]),color='red', fontsize=10,fontweight='bold')

    #ax.grid(True)
    ax[num].grid(b=True, which='major', color='k', linestyle='-')
    ax[num].grid(b=True, which='minor', color=[0.7,0.7,0.7], linestyle='--')
    return fig,ax

def stacked_hist(fig,ax,num,x,bins,title):
    from matplotlib.patches import Rectangle

    x = np.swapaxes(x,0,1)
    ax[num].hist(x, bins,color=['midnightblue','aqua','darkgreen', 'yellowgreen','orange', 'steelblue','maroon','grey','crimson'], \
        label=['12', '18', '24','36','48','72','96','120','168'],histtype='bar',fill=True)
    ax[num].set_title(title)
    extra = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    ax[num].legend(title='Duration')
    ax[num].grid(True)
    return fig,ax

def stacked_hist2(fig, ax, num, x,bins,title):

    ax[num].hist(x, bins,color=['blue', 'green','yellow','red'], \
        label=['tH', 'tdH', 'tQ','tdQ'],histtype='bar',fill=True,)
    ax[num].set_title(title)
    ax[num].legend()
    ax[num].grid(True)
    return fig,ax

def ts_plot(fig, ax, ax2, num, x, y, z, w,title,ii,event_ll):
    # z  is the water level array
    # y is the flow array
    # x is time
    # w is the aep level

    # Get the colours to plot by duration
    dur_col = utl.get_ind_dict()  # this needs to be updated to not depend on duration. Only number of events

    m,n = y.shape
    # Plot the AEP Level
    ax[num].plot(list(x),[w[ii][1]]*len(x),'k',linewidth=2,linestyle='--',label='AEP Level\nfrom Frequency\nLevel Assessment')

    # Set up some axes properties
    ax[num].set_xlim([0,240])
    ax[num].set_title(title)

    # Which event gives the maximum level for this site?
    evmax = np.max(z,axis=1)
    ismax = np.argmax(evmax)

    # Loop through each event and plot
    for i in range(m):
        dur, event = event_ll[i].split('_')
       # Plot the required info
        if i==ismax:
            ax[num].plot(x,z[i,:],color=dur_col[str(i)],label=event_ll[i] + ' WL',linewidth=4)
            ax2[num].plot(x,y[i,:],color=dur_col[str(i)],alpha=0.2,label=event_ll[i] + ' Q', linewidth=4,linestyle='--')  # Note could be ev
        else:
            ax[num].plot(x,z[i,:],color=dur_col[str(i)],label=event_ll[i] + ' WL')
            ax2[num].plot(x,y[i,:],color=dur_col[str(i)],alpha=0.5,label=event_ll[i] + ' Q',linestyle='--')  # Note could be ev

    #if ii==0 or ii == 12 or ii == 24:
    h1, l1 = ax[num].get_legend_handles_labels()
    ax[num].set_zorder(99)
    ax[num].set_frame_on(True)

    ax2[num].set_frame_on(True)
    ax[num].set_frame_on(False)
    h2, l2 = ax2[num].get_legend_handles_labels()
    secondary_legend=ax[num].legend(h2, l2, loc=4,prop={'size':12})
    secondary_legend.get_title().set_fontsize(20)
    secondary_legend.get_title().set_fontweight('bold')

    primary_legend=ax[num].legend(h1, l1, loc=1,prop={'size':12})
    ax[num].add_artist(secondary_legend)

    return fig,ax,ax2

def ts_plot_dm(fig, ax, ax2, num, x, y, z, w,title,ii,event_ll):
    # z  is the water level array
    # y is the flow array
    # x is time
    # w is the aep level

    # Get the colours to plot by duration
    dur_col = utl.get_ind_dict()  # this needs to be updated to not depend on duration. Only number of events

    m,n = y.shape
    # Plot the AEP Level
#    ax[num].plot(list(x),[w[ii][1]]*len(x),'k',linewidth=2,linestyle='--',label='AEP Level\nfrom Frequency\nLevel Assessment')

    # Set up some axes properties
    ax[num].set_xlim(w)
    ax[num].set_title(title)

    # Which event gives the maximum level for this site?
    evmax = np.nanmax(z,axis=1)
    ismax = np.argmax(evmax)

    # Loop through each event and plot
    for i in range(m):
        #dur, event = event_ll[i].split('_')
       # Plot the required info
        if i==ismax:
            ax[num].plot(x,z[i,:],color=dur_col[str(i)],label=event_ll[i] + ' WL',linewidth=4)
            ax2[num].plot(x,y[i,:],color=dur_col[str(i)],alpha=0.3,label=event_ll[i] + ' Q', linewidth=4,linestyle='--')  # Note could be ev
        else:
            ax[num].plot(x,z[i,:],color=dur_col[str(i)],label=event_ll[i] + ' WL')
            ax2[num].plot(x,y[i,:],color=dur_col[str(i)],alpha=0.7,label=event_ll[i] + ' Q',linestyle='--')  # Note could be ev

    #if ii==0 or ii == 12 or ii == 24:
    h1, l1 = ax[num].get_legend_handles_labels()
    ax[num].set_zorder(99)
    ax[num].set_frame_on(True)

    ax2[num].set_frame_on(True)
    ax[num].set_frame_on(False)
    h2, l2 = ax2[num].get_legend_handles_labels()
    secondary_legend=ax[num].legend(h2, l2, loc=4,prop={'size':12})
    secondary_legend.get_title().set_fontsize(20)
    secondary_legend.get_title().set_fontweight('bold')

    primary_legend=ax[num].legend(h1, l1, loc=1,prop={'size':12})
    ax[num].add_artist(secondary_legend)

    return fig,ax,ax2



def urbs_cross_plot(fig,ax,num,x,y,dur,loc):

    #fig = plt.figure()
    #ax = plt.gca()

    if num > 4:
        axmax = 200000
    else:
        xmax = np.max(x)
        ymax = np.max(y)
        axmax = max(xmax,ymax)

    d = ax[num].scatter(x ,y, c=dur,  edgecolors='none',cmap=plt.cm.jet,label='dur',rasterized=True)
    divider = make_axes_locatable(ax[num])
    cax = divider.append_axes("right", "5%", pad="3%")
    cb = fig.colorbar(d,cax=cax)
    cb.set_label ('Duration (hrs)',fontsize=18)
    # add 1:1 line
    ax[num].plot([1,axmax],[1,axmax],'k',linewidth=2.0)
    #ax.legend()
    # Setup axes
    #ax[num].set_yscale('log')
    #ax[num].set_xscale('log')
    ax[num].set_xlim([1,axmax])
    ax[num].set_ylim([1,axmax])
    ax[num].grid('on')
    ax[num].set_title(loc,fontsize=20)
    #ax[num].invert_xaxis()
    #ax[num].invert_yaxis()
    return fig, ax


def urbs_cross_plot_vol(fig,ax,num,x,y,dur,loc):

    #fig = plt.figure()
    #ax = plt.gca()

    #if num > 4:
    axmax = 10000
    #else:
    #    xmax = np.max(x)
    #    ymax = np.max(y)
    #    axmax = max(xmax,ymax)

    d = ax[num].scatter(x ,y, c=dur,  edgecolors='none',cmap=plt.cm.jet,label='dur',rasterized=True)
    divider = make_axes_locatable(ax[num])
    cax = divider.append_axes("right", "5%", pad="3%")
    cb = fig.colorbar(d,cax=cax)
    cb.set_label ('Duration (hrs)',fontsize=18)
    # add 1:1 line
    ax[num].plot([1,axmax],[1,axmax],'k',linewidth=2.0)
    #ax.legend()
    # Setup axes
    ax[num].set_yscale('log')
    ax[num].set_xscale('log')
    ax[num].set_xlim([10,axmax])
    ax[num].set_ylim([10,axmax])
    ax[num].grid('on')
    ax[num].set_title(loc,fontsize=20)
    #ax[num].invert_xaxis()
    #ax[num].invert_yaxis()
    return fig, ax

def main():
#===============================================================================
    all_dur = ['012','018','024','036','048','072','096','120','168']
    outdirP = r'C:\Projects\Python\TUFLOW\ReportPlots'
    outdirH = r'C:\Projects\Python\TUFLOW\ReportPlots'
    loc_names = []

    # Load in the previously processed datasets
    data = np.load("MC_results_360.npz")

#===============================================================================

    # Load WL
    allResH = data['allResH']
    allResdH = data['allResdH']
    allRestH = data['allRestH']
    allRestdH = data['allRestdH']
    allResHtQ = data['allResHtQ']

    # Load Flows
    allResQ = data['allResQ']
    allResdQ = data['allResdQ']  #[9 x 1260 x 28]
    allRestQ = data['allRestQ']  #[9 x 1260 x 28]
    allRestdQ = data['allRestdQ']  #[9 x 1260 x 28]
    rain_aep= data['rain_aep']       # Local catchment rainfall AEP
    allResQtH = data['allResQtH']
    d,m,n = allResH.shape

    # Nuke any results that have 0,0 for their flow rate and water level.
    Qmask = allResQ == 0.0
    Hmask = allResH == 0.0

    # Set crap values to nan
    allResQ[Qmask] = np.nan
    allResH[Hmask] = np.nan
    allResHtQ[Qmask] = np.nan
    allResQtH[Hmask] = np.nan

    # Load URBS Flows
    urbs_flow = data['urbs_flow']

    # Get loc names
    loc_names = utl.get_loc_names()

    # Setup duration array
    dur_array = np.zeros([d,m,n])
    for i,d in enumerate(dur_array):
        dur_array[i,:,:].fill(float(all_dur[i]))

    # Setup binned aep for plotting
    aep_bins = [1, 0.2, 0.1, 0.05, 0.02, 0.01, 0.002, 0.001, 0.0001, 0.00001, 0.000001]
    binned_aep = aep_bin(rain_aep,aep_bins)

    #========================Do the plotting====================================
    # Histogram with time variables

    # REPORT PLOTS. Note: Long sections and time series are completed with 'eventFinder_Stage5.py'

####    # AEP vs AEP plots
    plot_figs = ['Plot 1 - Whole of Catchment vs Local Rainfall AEP - Sheet 1 of 3','Plot 2 - Whole of Catchment vs Local Rainfall AEP - Sheet 2 of 3','Plot 3 - Whole of Catchment vs Local Rainfall AEP - Sheet 3 of 3']
    prf.main(plot_figs)

    # URBS vs MC Plot
    plot_figs = ['Plot 4 - Fast Model Peak Flow vs URBS Peak Flow']
    plot_A3_RL(urbs_flow,allResQ,dur_array, [],  'URBS Flow ($m^3/s$)', 'Fast Model Flow ($m^3/s$)', 'dur_Q_WL', loc_names, all_dur,outdirH,'urbs_cross_plot',False,[],plot_figs)

    # Flow vs Water Level
    plot_figs = ['Plot 5 - Peak Water Level vs Peak Flow - Sheet 1 of 3','Plot 6 - Peak Water Level vs Peak Flow - Sheet 2 of 3','Plot 7 - Peak Water Level vs Peak Flow - Sheet 3 of 3']
    plot_A3_RL(allResQ, allResH,rain_aep, [],  'Flow ($m^3/s$)', 'Water Level (mAHD)', 'dur_Q_WL', loc_names, all_dur,outdirH,'scatterplotdurwl',False,[],plot_figs)

    plot_figs = ['Plot 8 - Water Level versus Flow at Peak Level and Peak Flow - Sheet 1 of 3','Plot 9 - Water Level versus Flow at Peak Level and Peak Flow - Sheet 2 of 3','Plot 10 - Water Level versus Flow at Peak Level and Peak Flow - Sheet 3 of 3']
    plot_A3_RL(allResQ, allResH,allResQtH, allResHtQ,  'Flow ($m^3/s$)', 'Water Level (mAHD)', 'Q_WL', loc_names, all_dur,outdirH,'scatterplotwlq',False,[],plot_figs)

    # Histograms of key variables binned by freqency and duration
    plot_figs = ['Plot 11 - Maximum Change in Water Level over One Timestep - Sheet 1 of 3','Plot 12 - Maximum Change in Water Level over One Timestep - Sheet 2 of 3','Plot 13 - Maximum Change in Water Level over One Timestep - Sheet 3 of 3']
    plot_A3_RL(allResdH, [], [], [], 'dH (m)', 'Count', 'dH', loc_names, all_dur,outdirH,'multihist',False,[],plot_figs)

    plot_figs = ['Plot 14 - Maximum Change in Flow over One Timestep - Sheet 1 of 3','Plot 15 - Maximum Change in Flow over One Timestep - Sheet 2 of 3','Plot 16 - Maximum Change in Flow over One Timestep - Sheet 3 of 3']
    plot_A3_RL(allResdQ, [], [], [], 'dQ ($m^3/s$)', 'Count', 'dQ', loc_names, all_dur,outdirH,'multihist',False,[],plot_figs)

    plot_figs = ['Plot 17 - Time of Peak Water Level - Sheet 1 of 3','Plot 18 - Time of Peak Water Level - Sheet 2 of 3','Plot 19 - Time of Peak Water Level - Sheet 3 of 3']
    plot_A3_RL(allRestH, [], [], [], 'Time of Peak Water Level (hrs)', 'Count', 'tH', loc_names, all_dur,outdirH,'multihist',False,[],plot_figs)

    plot_figs = ['Plot 20 - Time of Peak Flow - Sheet 1 of 3','Plot 21 - Time of Peak Flow - Sheet 2 of 3','Plot 22 - Time of Peak Flow - Sheet 3 of 3']
    plot_A3_RL(allRestQ, [], [], [], 'Time of Peak Flow (hrs)', 'Count', 'tQ', loc_names, all_dur,outdirH,'multihist',False,[],plot_figs)

# ================Do pCME fMCE testing=========================================
# This assumes that the script
    log_data = np.load('CME_results.npz')
    pCME=log_data['pCME']
    fCME=log_data['fCME'] # This includes all durations

    # Count how many runs are below 2 %
    pmask = pCME < -2
    fmask = pCME < -2

    print 'Num of runs with Peak below 2%'
    print np.sum(pmask)
    print ''
    print np.sum(fmask)
    print 'Num of runs with Cumulative below 2%'

    # As there is only one bad run below 2% remove it.
    pCME[pmask] = 0.0
    fCME[fmask] = 0.0

    fig = plt.figure()
    p = hist(pCME,30,'Peak Cumulative Mass Error')
    plt.xlabel('Mass Balance (%)')
    plt.ylabel('Count')
    save_fig(fig,outdirH,'pCME',200)

    fig = plt.figure()
    p = hist(fCME,30,'Final Cumulative Mass Error')
    plt.xlabel('Mass Balance (%)')
    plt.ylabel('Count')
    save_fig(fig,outdirH,'fCME',200)



if __name__ == '__main__':
    main()

