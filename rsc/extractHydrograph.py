#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Mitchell.Smith
#
# Created:     20/05/2015
# Copyright:   (c) Mitchell.Smith 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import TUFLOW_results2015_BRFS
import glob



def main():

    eventNo = '0834'
    dur = '024'
    loc_ind == ['RL_001','RL_014','RL_022','RL_017'] #
    result_dir = 'B:\\B20702 BRCFS Hydraulics\\50_Hydraulic_Models\\500_MCA\\TUFLOW\\F\\results\\'+ dur +'\\plot'
    res_in_dir = glob.glob(result_dir + '\*' + dur + '*.tpc')

    for row in res_in_dir:
        #initialise results
        res = TUFLOW_results2015_BRFS.ResData()

        #load results
        error, message = res.Load(row)

        if error:
            print message

        print 'loaded'



if __name__ == '__main__':
    main()
