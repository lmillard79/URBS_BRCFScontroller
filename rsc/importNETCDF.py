#import net

from netCDF4 import Dataset

dir_path = r'B:\B20702 BRCFS Hydraulics\50_Hydraulic_Models\500_MCA\TUFLOW\F\results\048\plot'
#resDirPath = r'/Users/mitchellsmith/WBM/BRFS/plot'
resInDir = glob.glob(resDirPath +  '/*.tpc')
#inmeta = r'/Users/mitchellsmith/WBM/BRFS/metadata/Metadata_Brisbane048.csv'

inmeta = r'C:\Projects\BRFS\Metadata\Metadata_Brisbane048.csv'

#outdir = r'/Users/mitchellsmith/WBM/BRFS/Python/TUFLOW'
outdir = r'C:\Projects\BRFS\Python/TUFLOW'

nc = Dataset('OceanWaterLevel_Brisbane168.nc','r','NETCDF3_CLASSIC')

print nc.variables
