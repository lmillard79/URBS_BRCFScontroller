import csv

class LP_RP():
    """
    For reading in reporting point data
    """

    def __init__(self,fullpath,aep):
        self.fpath = fullpath
        self.chainage = []
        self.WL = []
        self.label = []
        print 'Reading: '+fullpath

        dep_dict = {'2':2,
                    '5':3,
                    '10':4,
                    '20':5,
                    '50':6,
                    '100':7,
                    '200':8,
                    '500':9,
                    '2000':10,
                    '10000':11,
                    '100000':12}

        aep = dep_dict[aep]

        with open(fullpath, 'rb') as csvfile:
            next(csvfile) #skip header
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                try:
                    self.chainage.append(float(row[0]))
                except:
                    print 'ERROR - extracting chainage from line: '+row
                try:
                    self.WL.append(float(row[aep]))
                except:
                    print 'ERROR - extracting water level from line: '+row
                self.label.append(row[1].strip())