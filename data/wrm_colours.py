import matplotlib as mpl
from matplotlib import cycler

from matplotlib.figure import Figure
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
#watermark = r"R:\Marketing\WRM logo\2_WRM_TAGLINE\WRM_TAGLINE_POS.svg"

wrmTag = "\data\WRM_TAGLINE_POS.svg"
wrmLogo = "\data\WRM_POS.svg"
wrmDrop = "\data\WRM_DROPLET.svg"   


wrmcol = ['WRM Green','WRM Teal','WRM Blue','Bright Blue', 'Bright Teal', 'Charcoal', 'Citrus', 'Light orange', 'Sky']
WRM    = ['#8dc63f', '#00928f', '#1e4164' ,'#00539b', '#00b49d','#485253','#d7df23','#d3bd2a','#6dcff6']
WRMcolour = dict(zip(wrmcol,WRM))

WRM_cmap = mpl.colors.ListedColormap(WRM, name='WRM_colours')
### --> mpl.colormaps.register(cmap=WRM_cmap)

## https://matplotlib.org/stable/api/matplotlib_configuration_api.html#matplotlib.rcParams
## https://matplotlib.org/stable/tutorials/introductory/customizing.html#customizing-with-matplotlibrc-files

mpl.rcParams['axes.prop_cycle']  = cycler('color', ['#8dc63f', '#00928f', '#1e4164' ,'#00539b', '#00b49d','#485253','#d7df23','#d3bd2a','#6dcff6'])

mpl.rcParams['figure.figsize']   = [10, 5]  # inches
mpl.rcParams['figure.dpi']       = 200
mpl.rcParams['savefig.dpi']      = 200

mpl.rcParams['font.family']      = 'Calibri'
mpl.rcParams['font.size']        = 10
mpl.rcParams['legend.fontsize']  = 'small'
mpl.rcParams['figure.titlesize'] = 'medium'
mpl.rcParams['grid.color']       = '0.7'
mpl.rcParams['grid.linestyle']   = '--'
mpl.rcParams['grid.linewidth']   = 0.5
mpl.rcParams['axes.titlepad']    = 20     #makes it possible to crop the title of a chart off without clipping y axis text
