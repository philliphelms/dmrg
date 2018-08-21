import numpy as np
import time
import mps_opt
import matplotlib.pyplot as plt

#----------------------------------------------------------
# A simple script to run a calculation for the tasep
# at a single point in phase space.
#----------------------------------------------------------

# Set Plotting parameters
plt.rc('text', usetex=True)
plt.rcParams['text.latex.preamble'] = [r'\boldmath']
plt.rc('font', family='serif')
plt.rcParams['text.latex.unicode']=False
np.set_printoptions(suppress=True)
np.set_printoptions(precision=3)
plt.style.use('ggplot') #'fivethirtyeight') #'ggplot'

# Create MPS object
a = 0.35
b = 2/3
s = -10
x = mps_opt.MPS_OPT(N = 8,
                    hamType = 'tasep',
                    hamParams = (a,s,b))
# Run optimization
x.kernel()
# Calculate current
print('Calculated Current: {}'.format(x.current))
print('Calculated Current/site: {}'.format(x.current/len(x.calc_occ)))
if s == 0:
    if b < 0.5 and a > b:
        print('Analytic Current (TDL): {}'.format(b*(1-b)))
    elif a < 0.5 and b > a:
        print('Analytic Current (TDL): {}'.format(a*(1-a)))
    else:
        print('Analytic Current (TDL): {}'.format(0.25))
