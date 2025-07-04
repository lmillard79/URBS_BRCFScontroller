import os, sys, glob,csv,re
from scipy.stats import norm
from scipy import interpolate
import numpy as np
import matplotlib
import matplotlib.dates
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import TUFLOW_results2015_BRFS
import time
from scipy.interpolate import interp1d
from scipy import arange, array, exp
import bris_utilities as utl

'''
This script loops through all TUFLOW results in a given directory. Using the
TUFLOW results python library it populates a series of numpy arrays with data
from all 11340 MC events. The results are then output as npz arrays to disk for
plotting later by the script plotData.py.
The key output from this script are result summary files to the folder
'outdir' via the function mcInfo that were provided to Jacobs for TPT.

'''


#=======================Function Declarations===================================
#===============================================================================
def mcInfo(Loc,eventID, PeakQ, PeakWL, AEP_loc, AEP_catch, RainDepth_loc, RainDepth_catch, PeakQCG, QtH,HtQ, dur,outdir):
    # Ouputs a text file for each reporting location required for SKM processing
    # Each output contains the 1260 events in the following format:
        #Location Duration EventID PeakQ PeakWL AEP RainDepth PeakQCG
    # ==========================================================================

    # Output a text file for each location
    res = zip(Loc,eventID,PeakQ,PeakWL,AEP_loc,AEP_catch,RainDepth_loc,RainDepth_catch,PeakQCG,QtH,HtQ,dur)
    res.sort(key = lambda t: t[6])
    f = open(os.path.join(outdir,Loc[0]+'.txt'),'w')
    f.write('Location    Dur   Event        PeakQ    PeakWL          AEPLoc        AEPWhole        RFLoc     RFCatch     Peak_BCG         QtH     HtQ\n')

    for row in res:
       f.write('%(Loc)s      %(dur)s    %(eventID)04d    %(PeakQ)9.2f    %(PeakWL)6.2f    %(AEP_loc)1.10f    %(AEP_catch)1.10f      %(RainDepth_loc)7.2f     %(RainDepth_catch)7.2f    %(PeakQCG)9.2f   %(QtH)9.2f  %(HtQ)6.2f\n' % \
       {"Loc": row[0],"dur": row[11],"eventID": row[1],"PeakQ":row[2],"PeakWL": row[3] ,"AEP_loc": row[4], "AEP_catch": row[5], "RainDepth_loc": row[6],"RainDepth_catch": row[7],"PeakQCG": row[8],"QtH": row[9],"HtQ": row[10]})
    f.close

def interp_aep(ifd_in, rain_in, location,duration):

    # Setup the duration id arrays
    duration_ifd = [2,3,4,5,6,7,8,9,11] # Index to row within AEP data.
    duration_ifd = duration_ifd[duration] # Get the right duration row from the ifd data

    # Get the data
    data = get_ifd(ifd_in,float)
    m,n = data.shape

    # Remove the nan values
    mask = np.logical_not(np.isnan(data))
    data = data[mask]
    data = np.reshape(data,[13,n-1])

    # Get Standard Normal Variate for the AEP
    z_std = norm_s_inv(data[0,:])

    # Get the ifd rainfall data only
    rainfall_ifd_data = data[1:,:]
    rainfall_ifd_log_data = np.log10(rainfall_ifd_data)

    # Get the input rain that will be interpolated
    log_rain_depth = np.log10(rain_in)

    # Setup arrays for interpolation.
    interp_x = log_rain_depth
    interp_xi = rainfall_ifd_log_data[duration_ifd,:]
    interp_yi = z_std

    # Interpolate the AEP based on the rainfall data and duration
    f_i = interpolate.interp1d(interp_xi,interp_yi)
    f_x = extrap1d(f_i)
    interp_zstd = f_x(interp_x)
    interp_aep = norm_s_dist(interp_zstd)
    return interp_aep

def get_ifd(file_loc,data_type):
    data  = np.genfromtxt(file_loc, delimiter=";",dtype=data_type)
    return data

def norm_s_inv(data):
    data = -norm.ppf(1/data)
    return data

def norm_s_dist(data):
    data = 1 - norm.cdf(data)
    return data

def extrap1d(interpolator):
    xs = interpolator.x
    ys = interpolator.y

    def pointwise(x):
        if x < xs[0]:
            return ys[0]+(x-xs[0])*(ys[1]-ys[0])/(xs[1]-xs[0])
        elif x > xs[-1]:
            return ys[-1]+(x-xs[-1])*(ys[-1]-ys[-2])/(xs[-1]-xs[-2])
        else:
            return interpolator(x)

    def ufunclike(xs):
        return array(map(pointwise, array(xs)))

    return ufunclike

#-------------------------------------------------------------------------------
def getMeta(inmeta,in_loc,duration_index):

    # Inputs
    # This is the string location of the metadata file
    #
    # This can be a integer, or a list of locations. the integer -1 specifies all locations
    # Returns a 1260 x len(in_loc) numpy array.
    import csv
    import numpy as np

    # Sort out the number of input locations
    if isinstance( in_loc, int ) and in_loc >0:
         in_loc= [in_loc]

    elif  in_loc == -1:
        in_loc = range(1,29)
    else:
        print 'Error with input'
        return

    num_loc = len(in_loc)

    # For a given duration and location return the rainfall AEP and depth
    aepCol = [4,29,39,49,59,69,89,99,109,119,129,139]
    rfCol = [xx-1 for xx in aepCol]
    qCol = [-99,26,36,46,56,66,86,96,106,116,126,136]  # -99 added so that numbers matched in the location switch in the try block below.
    catch_aep = np.zeros([1260,num_loc],dtype=float)
    loc_aep = np.zeros([1260,num_loc],dtype=float)
    catch_rf = np.zeros([1260,num_loc],dtype=float)
    loc_rf = np.zeros([1260,num_loc],dtype=float)
    urbs = np.zeros([1260,num_loc],dtype=float)   # NOTE: ALTHOUGH GROUPED BELOW, THIS IS ONLY CORRECT AT THE GAUGE LOCATIONS. This was added on 05/08/15 to allow urbs vs mc plot reporting
    row  = np.genfromtxt(inmeta, delimiter=",", skip_header=2)

    for i, in_location in enumerate(in_loc):

        try:
            # Append the data to the relevant colummns.
            # Whole of Catchment
            catch_aep[:,i] = row[:,aepCol[0]]
            catch_rf[:,i] = row[:,rfCol[0]]

            # Wivenhoe
            if in_location in [2]:
                #loc_aep[:,i] = row[:,aepCol[1]]
                loc_rf[:,i] = row[:,rfCol[1]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesWivenhoe_L_540177.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[1]]

            # Glenore Grove
            elif in_location in [1,3]:
                #loc_aep[:,i] = row[:,aepCol[2]]
                loc_rf[:,i] = row[:,rfCol[2]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesGlenoreGrove_L_540149.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[2]]

            # Savages
            elif in_location in [4,5]:
                #loc_aep[:,i] = row[:,aepCol[3]]
                loc_rf[:,i] = row[:,rfCol[3]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesSavages_L_540066.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[3]]

            # Mount Crosby
            elif in_location in [6,7]:
                #loc_aep[:,i] = row[:,aepCol[4]]
                loc_rf[:,i] = row[:,rfCol[4]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesMountCrosby_L_540199.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[4]]

            # Walloon
            elif in_location in[19,20]:
                #loc_aep[:,i] = row[:,aepCol[5]]
                loc_rf[:,i] = row[:,rfCol[5]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesWalloon_L_540504.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[5]]

            # Amberley
            elif in_location in [17]:
                #loc_aep[:,i] = row[:,aepCol[6]]
                loc_rf[:,i] = row[:,rfCol[6]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesAmberley_L_540505.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[6]]


            # Loamside
            elif in_location in [18]:
                #loc_aep[:,i] = row[:,aepCol[7]]
                loc_rf[:,i] = row[:,rfCol[7]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesLoamside_L_540062.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[7]]


            # Ipswich
            elif in_location in [24,21,23,22,25,26]:
                #loc_aep[:,i] = row[:,aepCol[8]]
                loc_rf[:,i] = row[:,rfCol[8]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesIpswich_L_40831.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[8]]


            # Moggill
            elif in_location in [8,27]:
                #loc_aep[:,i] = row[:,aepCol[9]]
                loc_rf[:,i] = row[:,rfCol[9]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesMoggill_L_540200.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[9]]


            # Centenery
            elif in_location in [9,10,28,29]:
                #loc_aep[:,i] = row[:,aepCol[10]]
                loc_rf[:,i] = row[:,rfCol[10]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesCentenaryBridge_L_100001.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[10]]


            # Brisbane
            elif in_location in [14,12,15,16,13,11]:
                #loc_aep[:,i] = row[:,aepCol[11]]
                loc_rf[:,i] = row[:,rfCol[11]]
                loc_aep[:,i] = interp_aep(r'C:\Projects\BRFS\IFD\2013IFDTablesBrisbane_L_540198.csv', loc_rf[:,i], i, duration_index)
                urbs[:,i] = row[:,qCol[11]]

            else:
                print "Something wrong here!"
                msg = 'Error in location loop'
                return msg

        except:
            print 'Could not open file: ' + inmeta
            msg = 'Could not open file: ' + inmeta
            return msg

    return catch_aep, catch_rf, loc_aep, loc_rf,urbs
#-------------------------------------------------------------------------------



def main():
    #==============Variable Declarations and Array Initilisation================
    #===========================================================================


    all_dur = ['012','018','024','036','048','072','096','120','168']
    loc_names = []
    total_ev = 1260
    llocs = 28
    hlocs = 32

    # Open up all the files and process.
    loc_names = utl.get_loc_names()

     # Flow based
    allResQ = np.zeros((len(all_dur), total_ev,llocs),dtype=float)      # Peak Flow
    allRestQ = np.zeros((len(all_dur), total_ev,llocs),dtype=float)     # Time of Peak Flow
    allResdQ = np.zeros((len(all_dur), total_ev,llocs),dtype=float)     # Peak change in Flow
    allRestdQ = np.zeros((len(all_dur), total_ev,llocs),dtype=float)    # Time of Peak change
    allResHtQ = np.zeros((len(all_dur), total_ev,llocs),dtype=float)    # Flow at time of peak WL
    allResVol = np.zeros((len(all_dur), total_ev,llocs),dtype=float)    # Calculated Volumes

    # Water level based
    allResH = np.zeros((len(all_dur), total_ev,hlocs),dtype=float)      # Water level equiv of flow refer above.
    allRestH = np.zeros((len(all_dur), total_ev,hlocs),dtype=float)
    allResdH = np.zeros((len(all_dur), total_ev,hlocs),dtype=float)
    allRestdH = np.zeros((len(all_dur), total_ev,hlocs),dtype=float)
    allResQtH = np.zeros((len(all_dur), total_ev,hlocs),dtype=float)

    # Timeseries Based Maxes
    allResTSQ = np.zeros((len(all_dur), total_ev,llocs),dtype=float)      # Peak Flow
    allResTSH = np.zeros((len(all_dur), total_ev,hlocs),dtype=float)      # Water level equiv of flow refer above.


    # Rainfall Arrays
    rain_aep = np.zeros((len(all_dur), total_ev,llocs),dtype=float)
    rain_depth = np.zeros((len(all_dur), total_ev,llocs),dtype=float)
    rain_depth_catch = np.zeros((len(all_dur), total_ev,llocs),dtype=float)
    rain_aep_catch = np.zeros((len(all_dur), total_ev,llocs),dtype=float)

    # Urbs Flow
    urbs_flow = np.zeros((len(all_dur), total_ev,llocs),dtype=float)


    # Event array
    ev = np.zeros((len(all_dur), total_ev),dtype=int)

    # Get array shape info for later manipulation
    a,b,c = allResH.shape

    #==============Loop through each duration and extract data types============
    for dd,dur in enumerate(all_dur):

        resDirPath = 'B:\\B20702 BRCFS Hydraulics\\50_Hydraulic_Models\\500_MCA\\TUFLOW\\F\\results\\360\\360\\' + dur +'\\plot'
        resInDir = glob.glob(resDirPath +  '\*MC_0360_MC*.tpc')
        inmeta = 'C:\\Projects\\BRFS\\Metadata\\Metadata_Brisbane' + dur + '.csv'
        outdir = 'C:\\Projects\\Python\\TUFLOW\\MC_Out\\RL\\'+ dur
        outdirP = 'C:\\Projects\\Python\\TUFLOW\\MC_Out\\P'
        rundir = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\TUFLOW\F\runs'

        first = True
    #===============Loop through all results for a given duration===============

        # Loop through all results in folder

        if resInDir == []:
            print 'No results for this duration'
            continue

        for i, rr in enumerate(resInDir):
            if i % 1260 == 0:
                print 'Currently Processing Duration: ' + dur

            #initialise and load results
            res = TUFLOW_results2015_BRFS.ResData()
            error, message = res.Load(rr)           # Be careful as I have turned the error checking off.
            if error:
                print message

            # If the first time step setup the array for result storage
            if first:

                # Intialise result array. Assumes all results the same size
                #ev = len(resInDir)  # Number of runs. Should be 1260
                l_loc = res.Data_RL.nLine # This assumes that the list of lines is the same for all durations
                p_loc = res.Data_RL.nPoint # This assumes that the list of points is the same for all durations
                first = False

                # Extract the duration and run number from the event file name.
                did =re.compile('\d{3}') # first set of three digits is the dur number
                rid =re.compile('\d{4}')
                pp,resName =  os.path.split(resInDir[i])
                durNo = re.search(did,resName)
                durNo = [durNo.group()]*b
                l_loc = res.Data_RL.L_Max.ID
                p_loc = res.Data_RL.P_Max.ID

            try:
                # Assign all the flow and water level results
                allResQ[dd,i,:]= res.Data_RL.L_Max.QMax     #[9 x 1260 x 28]
                allRestQ[dd,i,:]= res.Data_RL.L_Max.tQmax
                allResdQ[dd,i,:]= res.Data_RL.L_Max.dQMax
                allRestdQ[dd,i,:]= res.Data_RL.L_Max.tdQmax
                allResHtQ[dd,i,:]= res.Data_RL.L_Max.HtQmax
                allResVol[dd,i,:]= np.sum(res.Data_RL.Q_L.Values[:,2:],axis=0)

                # Water Level Peaks
                allResH[dd,i,:]= res.Data_RL.P_Max.HMax     #[9 x 1260 x 32]
                allRestH[dd,i,:]= res.Data_RL.P_Max.tHmax
                allResdH[dd,i,:]= res.Data_RL.P_Max.dHMax
                allRestdH[dd,i,:]= res.Data_RL.P_Max.tdHmax
                allResQtH[dd,i,:]= res.Data_RL.P_Max.QtHmax

                # Extracted from hourly time series.
                allResTSQ[dd,i,:] = np.max(abs(res.Data_RL.Q_L.Values[:,2:]),axis=0) # Ignore time and number [:,2:]
                allResTSH[dd,i,:] = np.max(abs(res.Data_RL.H_P.Values[:,2:]),axis=0)

                # Get the event number
                pp,resName =  os.path.split(resInDir[i])
                rid= re.compile('\d{4}') # first set of four digits is the run number
                runNo = re.search(rid,resName)
                runNo = int(runNo.group())
                ev[dd,i] = runNo

            except: # Output to Submit Files
                # The following will output a condor submit file for runs that have issues and complete processing on successful runs
                print "Issue with run ID : " + str(i+1)
                f = open(os.path.join(rundir,'Stragglers_'+ dur +'.sub'),'a')
                rr2 = re.search(rid,resName)
                f.write('executable = Run02.bat\n')
                f.write('arguments = %(dur)s %(run)04d\n' % {"dur":dur,"run": int(rr2.group())})
                f.write('should_transfer_files = IF_NEEDED\n')
                f.write('when_to_transfer_output = ON_EXIT\n')
                f.write('run_as_owner = True\n')
                f.write('queue\n')
                f.write('\n')

        # Get the rainfall data
        tc_aep, tc_rf, tloc_aep, tloc_rf,urbs = getMeta(inmeta,-1,dd)
        rain_aep[dd,:,:] = tloc_aep
        rain_depth[dd,:,:] = tloc_rf
        rain_aep_catch[dd,:,:] = tc_aep
        rain_depth_catch[dd,:,:] =tc_rf
        urbs_flow[dd,:,:] = urbs

        # Now that you have all the data for a given duration, interate through each location and output
        for i, rr in enumerate(l_loc):

            # Sort the water level data into a column consistant with the flow data
            # get column index for both the h and q datasets
            try:
                ss = p_loc.index(rr[:-1]+'P')  # Ensures the water level point is at the same location as the flow section.
                cg = l_loc.index('RL_013_L')
            except: # Allow for new reporting location outputs
                ss = p_loc.index(rr)  # Ensures the water level point is at the same location as the flow section.
                cg = l_loc.index('RL_013')

            allResH[dd,:,i] = allResH[dd,:,ss] # This ensures that the water level point is at the same location as the flow section.
            allRestH[dd,:,i] = allRestH[dd,:,ss]
            allResdH[dd,:,i] = allResdH[dd,:,ss]
            allRestdH[dd,:,i] = allRestdH[dd,:,ss]
            allResQtH[dd,:,i] = allResQtH[dd,:,ss]
            allResTSH[dd,:,i] =  allResTSH[dd,:,ss]

            PeakQCG = allResQ[dd,:,cg]
            ll =[rr]*b

            # Output the Frequency Analysis process files for each location for the currently processing duration.
            mcInfo(ll,ev[dd,:],allResQ[dd,:,i],allResH[dd,:,i],rain_aep[dd,:,i],rain_aep_catch[dd,:,i], \
            rain_depth[dd,:,i], rain_depth_catch[dd,:,i], PeakQCG, allResQtH[dd,:,i], \
             allResHtQ[dd,:,i], durNo, outdir)
            print 'Processed Location: ' + rr

    # Save all the processed results
    np.savez('MC_results_360', allResH=allResH, allRestH=allRestH, allResdH=allResdH, \
    allRestdH=allRestdH, allResQ=allResQ, allRestQ=allRestQ, allResdQ=allResdQ, \
     allRestdQ=allRestdQ, rain_depth=rain_depth, rain_aep=rain_aep,loc_names=loc_names, \
      l_loc=l_loc,rain_aep_catch=rain_aep_catch,event=ev,allResQtH=allResQtH,allResHtQ=allResHtQ, allResTSH= allResTSH, allResTSQ=allResTSQ, urbs_flow=urbs_flow, allResVol= allResVol) # This includes all durations


if __name__ == "__main__":



    main()