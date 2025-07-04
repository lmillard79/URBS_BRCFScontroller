def getMeta(inmeta,in_loc):

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
    catch_aep = np.zeros([1260,num_loc],dtype=float)
    loc_aep = np.zeros([1260,num_loc],dtype=float)
    catch_rf = np.zeros([1260,num_loc],dtype=float)
    loc_rf = np.zeros([1260,num_loc],dtype=float)
    row  = np.genfromtxt(inmeta, delimiter=",", skip_header=2)

    for i, in_location in enumerate(in_loc):

        try:
            # Append the data to the relevant colummns.
            # Whole of Catchment
            catch_aep[:,i] = row[:,aepCol[0]]
            catch_rf[:,i] = row[:,rfCol[0]]

            # Wivenhoe
            if in_location in [2]:
                loc_aep[:,i] = row[:,aepCol[1]]
                loc_rf[:,i] = row[:,rfCol[1]]

            # Glenore Grove
            elif in_location in [1,3]:
                loc_aep[:,i] = row[:,aepCol[2]]
                loc_rf[:,i] = row[:,rfCol[2]]

            # Savages
            elif in_location in [4,5]:
                loc_aep[:,i] = row[:,aepCol[3]]
                loc_rf[:,i] = row[:,rfCol[3]]

            # Mount Crosby
            elif in_location in [6,7]:
                loc_aep[:,i] = row[:,aepCol[4]]
                loc_rf[:,i] = row[:,rfCol[4]]

            # Walloon
            elif in_location in[19,20]:
                loc_aep[:,i] = row[:,aepCol[5]]
                loc_rf[:,i] = row[:,rfCol[5]]

            # Amberley
            elif in_location in [17]:
                loc_aep[:,i] = row[:,aepCol[6]]
                loc_rf[:,i] = row[:,rfCol[6]]

            # Loamside
            elif in_location in [18]:
                loc_aep[:,i] = row[:,aepCol[7]]
                loc_rf[:,i] = row[:,rfCol[7]]

            # Ipswich
            elif in_location in [24,21,23,22,25,26]:
                loc_aep[:,i] = row[:,aepCol[8]]
                loc_rf[:,i] = row[:,rfCol[8]]

            # Moggill
            elif in_location in [8,27]:
                loc_aep[:,i] = row[:,aepCol[9]]
                loc_rf[:,i] = row[:,rfCol[9]]

            # Centenery
            elif in_location in [9,10,28,29]:
                loc_aep[:,i] = row[:,aepCol[10]]
                loc_rf[:,i] = row[:,rfCol[10]]

            # Brisbane
            elif in_location in [14,12,15,16,13,11]:
                loc_aep[:,i] = row[:,aepCol[11]]
                loc_rf[:,i] = row[:,rfCol[11]]
            else:
                print "Something wrong here!"
                msg = 'Error in location loop'
                return msg



        except:
            print 'Could not open file: ' + inmeta
            msg = 'Could not open file: ' + inmeta
            return msg

    return catch_aep, catch_rf, loc_aep, loc_rf