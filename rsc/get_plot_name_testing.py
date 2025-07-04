def getNP(event,FMrunid,UDMTrunid,DMTrunid,loc,plot_type,ST0X):
    plot_name = ''
    plot_number = ''
    if plot_type == 'TS':
        if len(DMTrunid) > 0:
            if event == 'C2011':
                if loc == 'Lockyer':
                    plot_number = '01'
                    plot_name = 'UDMT & DMT 2011 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '02'
                    plot_name = 'UDMT & DMT 2011 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '03'
                    plot_name = 'UDMT & DMT 2011 Brisbane River Water Level Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C2013':
                if loc == 'Lockyer':
                    plot_number = '05'
                    plot_name = 'UDMT & DMT 2013 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '06'
                    plot_name = 'UDMT & DMT 2013 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '07'
                    plot_name = 'UDMT & DMT 2013 Brisbane River Water Level Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C1974':
                if loc == 'Lockyer':
                    plot_number = '09'
                    plot_name = 'UDMT & DMT 1974 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '10'
                    plot_name = 'UDMT & DMT 1974 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '11'
                    plot_name = 'UDMT & DMT 1974 Brisbane River Water Level Gauges'
                elif loc == 'Add_Bris':
                    plot_number = '12'
                    plot_name = 'UDMT & DMT 1974 Brisbane River Water Level Additional Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
        elif len(FMrunid)>0 and ST0X ==['ST01']:
            if loc == 'Bris':
                plot_number = '45'
                plot_name = 'ST01 FM Mannings n and Bend Loss Tests \n2011 Brisbane River Water Level Gauges'
        elif len(FMrunid)>0 and ST0X ==['ST02']:
            if loc == 'Lockyer':
                plot_number = '49'
                plot_name = 'ST02 FM Mannings n and Bend Loss $\pm$10% \n2011 Lockyer Creek Water Level Gauges'
            elif loc == 'Brem':
                plot_number = '50'
                plot_name = 'ST02 FM Mannings n and Bend Loss $\pm$10% \n2011 Bremer River Water Level Gauges'
            elif loc == 'Bris':
                plot_number = '51'
                plot_name = 'ST02 FM Mannings n and Bend Loss $\pm$10% \n2011 Brisbane River Water Level Gauges'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(FMrunid)>0 and ST0X ==['ST03']:
            if loc == 'Lockyer':
                plot_number = '55'
                plot_name = 'ST03 URBS Alpha Values $\pm$20% \n2011 Lockyer Creek Water Level Gauges'
            elif loc == 'Brem':
                plot_number = '56'
                plot_name = 'ST03 URBS Alpha Values $\pm$20% \n2011 Bremer River Water Level Gauges'
            elif loc == 'Bris':
                plot_number = '57'
                plot_name = 'ST03 URBS Alpha Values $\pm$20% \n2011 Brisbane River Water Level Gauges'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(FMrunid)>0 and ST0X ==['ST04']:
            if loc == 'Lockyer':
                plot_number = '61'
                plot_name = 'ST04 URBS Beta Values $\pm$20% \n2011 Lockyer Creek Water Level Gauges'
            elif loc == 'Brem':
                plot_number = '62'
                plot_name = 'ST04 URBS Beta Values $\pm$20% \n2011 Bremer River Water Level Gauges'
            elif loc == 'Bris':
                plot_number = '63'
                plot_name = 'ST04 URBS Beta Values $\pm$20% \n2011 Brisbane River Water Level Gauges'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(FMrunid)>0 and ST0X ==['ST05']:
            if loc == 'Lockyer':
                plot_number = '67'
                plot_name = 'ST05 Lowood-Fernvale Coss-Sections \n2011 Lockyer Creek Water Level Gauges'
            elif loc == 'Brem':
                plot_number = '68'
                plot_name = 'ST05 Lowood-Fernvale Coss-Sections \n2011 Bremer River Water Level Gauges'
            elif loc == 'Bris':
                plot_number = '69'
                plot_name = 'ST05 Lowood-Fernvale Coss-Sections \n2011 Brisbane River Water Level Gauges'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(DMTrunid) == 0 and len(FMrunid)>0:
            if event == 'C2013':
                if loc == 'Lockyer':
                    plot_number = '14'
                    plot_name = 'FM & UDMT 2013 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '15'
                    plot_name = 'FM & UDMT 2013 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '16'
                    plot_name = 'FM & UDMT 2013 Brisbane River Water Level Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C1996':
                if loc == 'Lockyer':
                    plot_number = '20'
                    plot_name = 'FM 1996 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '21'
                    plot_name = 'FM 1996 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '22'
                    plot_name = 'FM 1996 Brisbane River Water Level Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C1999':
                if loc == 'Lockyer':
                    plot_number = '23'
                    plot_name = 'FM 1999 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '24'
                    plot_name = 'FM 1999 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '25'
                    plot_name = 'FM 1999 Brisbane River Water Level Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C2011':
                if loc == 'Lockyer':
                    plot_number = '26'
                    plot_name = 'FM & UDMT 2011 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '27'
                    plot_name = 'FM & UDMT 2011 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '28'
                    plot_name = 'FM & UDMT 2011 Brisbane River Water Level Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C1974':
                if loc == 'Lockyer':
                    plot_number = '32'
                    plot_name = 'FM & UDMT 1974 Lockyer Creek Water Level Gauges'
                elif loc == 'Brem':
                    plot_number = '33'
                    plot_name = 'FM & UDMT 1974 Bremer River Water Level Gauges'
                elif loc == 'Bris':
                    plot_number = '34'
                    plot_name = 'FM & UDMT 1974 Brisbane River Water Level Gauges'
                elif loc == 'Add_Bris':
                    plot_number = '35'
                    plot_name = 'FM & UDMT 1974 Brisbane River Water Level Additional Gauges'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
    elif plot_type == 'LP':
        if len(FMrunid)>0 and ST0X ==['ST01']:
            if loc == 'Bris':
                plot_number = '46'
                plot_name = 'ST01 FM Mannings n and Bend Loss Tests \n2011 Brisbane River Longitudinal Profiles'
            elif loc == 'Other':
                plot_number = '47'
                plot_name = 'ST01 FM Mannings n and Bend Loss Tests \n2011 Lockyer / Bremer Longitudinal Profiles'
        elif len(FMrunid)>0 and ST0X ==['ST02']:
            if loc == 'Other':
                plot_number = '53'
                plot_name = 'ST02 FM Mannings n and Bend Loss $\pm$10% \n2011 Lockyer / Bremer Longitudinal Profiles'
            elif loc == 'Bris':
                plot_number = '52'
                plot_name = 'ST02 FM Mannings n and Bend Loss $\pm$10% \n2011 Brisbane River Longitudinal Profiles'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(FMrunid)>0 and ST0X ==['ST03']:
            if loc == 'Other':
                plot_number = '59'
                plot_name = 'ST03 URBS Alpha Values $\pm$20% \n2011 Lockyer / Bremer Longitudinal Profiles'
            elif loc == 'Bris':
                plot_number = '58'
                plot_name = 'ST03 URBS Alpha Values $\pm$20% \n2011 Brisbane River Longitudinal Profiles'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(FMrunid)>0 and ST0X ==['ST04']:
            if loc == 'Other':
                plot_number = '65'
                plot_name = 'ST04 URBS Beta Values $\pm$20% \n2011 Lockyer / Bremer Longitudinal Profiles'
            elif loc == 'Bris':
                plot_number = '64'
                plot_name = 'ST04 URBS Beta Values $\pm$20% \n2011 Brisbane River Longitudinal Profiles'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(FMrunid)>0 and ST0X ==['ST05']:
            if loc == 'Other':
                plot_number = '71'
                plot_name = 'ST05 Lowood-Fernvale Coss-Sections \n2011 Lockyer / Bremer Longitudinal Profiles'
            elif loc == 'Bris':
                plot_number = '70'
                plot_name = 'ST05 Lowood-Fernvale Coss-Sections \n2011 Brisbane River Longitudinal Profiles'
            else:
                print 'invalid plot for naming'
                plot_number == 'XX'
                plot_name = ''
        elif len(FMrunid)>0:
            if event == 'C2013':
                if loc == 'Other':
                    plot_number = '19'
                    plot_name = 'FM & UDMT 2013 Lockyer / Bremer Longitudinal Profiles'
                elif loc == 'Bris':
                    plot_number = '18'
                    plot_name = 'FM & UDMT 2013 Brisbane River Longitudinal Profiles'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C2011':
                if loc == 'Other':
                    plot_number = '31'
                    plot_name = 'FM & UDMT 2011 Lockyer / Bremer Longitudinal Profiles'
                elif loc == 'Bris':
                    plot_number = '30'
                    plot_name = 'FM & UDMT 2011 Brisbane River Longitudinal Profiles'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
            if event == 'C1974':
                if loc == 'Other':
                    plot_number = '37'
                    plot_name = 'FM & UDMT 1974 Lockyer / Bremer Longitudinal Profiles'
                elif loc == 'Bris':
                    plot_number = '36'
                    plot_name = 'FM & UDMT 1974 Brisbane River Longitudinal Profiles'
                else:
                    print 'invalid plot for naming'
                    plot_number == 'XX'
                    plot_name = ''
    elif plot_type == 'CB':
        if len(FMrunid)>0 and ST0X ==['ST01']:
            plot_number = '48'
            plot_name = 'ST01 FM Mannings n and Bend Loss Tests \n2011 Centenary Bridge Flow Recordings'
        elif len(FMrunid)>0 and ST0X ==['ST02']:
            plot_number = '54'
            plot_name = 'ST02 FM Mannings n and Bend Loss $\pm$10% \n2011 Centenary Bridge Flow Recordings'
        elif len(FMrunid)>0 and ST0X ==['ST03']:
            plot_number = '60'
            plot_name = 'ST03 URBS Alpha Values $\pm$20% \n2011 Centenary Bridge Flow Recordings'
        elif len(FMrunid)>0 and ST0X ==['ST04']:
            plot_number = '66'
            plot_name = 'ST04 URBS Beta Values $\pm$20% \n2011 Centenary Bridge Flow Recordings'
        elif len(FMrunid)>0 and ST0X ==['ST05']:
            plot_number = '72'
            plot_name = 'ST05 Lowood-Fernvale Coss-Sections \n2011 Centenary Bridge Flow Recordings'
        elif len(DMTrunid)>0 and len(UDMTrunid)>0:
            if event == 'C2013':
                plot_number = '08'
                plot_name = 'UDMT & DMT 2013 Centenary Bridge Flow Recordings'
            if event == 'C2011':
                plot_number = '04'
                plot_name = 'UDMT & DMT 2011 Centenary Bridge Flow Recordings'
            if event == 'C1974':
                plot_number = '13'
                plot_name = 'UDMT & DMT 1974 Centenary Bridge Flow Recordings'
        elif len(FMrunid)>0:
            if event == 'C2013':
                plot_number = '17'
                plot_name = 'FM & UDMT 2013 Centenary Bridge Flow Recordings'
            if event == 'C2011':
                plot_number = '29'
                plot_name = 'FM & UDMT 2011 Centenary Bridge Flow Recordings'
            if event == 'C1974':
                plot_number = '36'
                plot_name = 'FM & UDMT 1974 Centenary Bridge Flow Recordings'

##        plot_name = plot_name
##        plot_number = plot_number
    return 'Plot '+plot_number + ' ' + plot_name

