import numpy as np
import time
import mps_opt
import matplotlib.pyplot as plt

#-----------------------------------------------------------------------------
#
#-----------------------------------------------------------------------------

# Set Plotting parameters
plt.rc('text', usetex=True)
plt.rcParams['text.latex.preamble'] = [r'\boldmath']
plt.rc('font', family='serif')
plt.rcParams['text.latex.unicode']=False
np.set_printoptions(suppress=True)
np.set_printoptions(precision=100)
plt.style.use('ggplot') #'fivethirtyeight') #'ggplot'

N = 10
s_vec = np.linspace(-2,2,100)
E_dmrg = np.zeros(s_vec.shape)
E = np.zeros(s_vec.shape)
E_mf = np.zeros(s_vec.shape)
for i in range(len(s_vec)):
    x = mps_opt.MPS_OPT(N=N,
                        hamType = "sep",
                        hamParams = (0.9,0.1,0.5,0.5,0.1,0.9,s_vec[i]),
                        #hamParams = (0.5,0.8,0.2,0.6,0.8,0.7,s_vec[i]),
                        usePyscf = True)
    E_dmrg[i] = x.kernel()
    E[i] = x.exact_diag()
    E_mf[i] = x.mean_field()
# CGF PLOT
fig1 = plt.figure()
plot_ed = plt.plot(s_vec,E,label='Exact Diag')
plot_mf = plt.plot(s_vec,E_mf,label='Mean Field')
plot_dmrg = plt.plot(s_vec,E_dmrg,label='DMRG')
plt.legend()
plt.grid(True)
plt.xlabel('$s$')
plt.ylabel('CGF')
plt.show()
# CGF ERROR PLOT
fig2 = plt.figure()
plot_mf = plt.semilogy(s_vec,np.abs(E-E_mf)/E*100,label='Mean Field Error')
plot_dmrg = plt.semilogy(s_vec,np.abs(E-E_dmrg)/E*100,label='DMRG Error')
plt.legend()
plt.grid(True)
plt.xlabel('$s$')
plt.ylabel('\% CGF Error')
plt.show()
# Current Plot
Ediff = E[1:]-E[:len(E)-1]
E_dmrg_diff = E_dmrg[1:]-E_dmrg[:len(E_dmrg)-1]
E_mf_diff = E_mf[1:]-E_mf[:len(E_mf)-1]
Sdiff = s_vec[1:]-s_vec[:len(s_vec)-1]
slope = -Ediff/(Sdiff)
slope_dmrg = -E_dmrg_diff/(Sdiff)
slope_mf = -E_mf_diff/(Sdiff)
fig3 = plt.figure()
plt.plot(s_vec[1:],slope,label='Exact Diag')
plt.plot(s_vec[1:],slope_dmrg,label='DMRG')
plt.plot(s_vec[1:],slope_mf,label='Mean Field')
plt.grid(True)
plt.legend()
plt.xlabel('$s$')
plt.ylabel('Current')
plt.show()
fig3.savefig('vary_s_comp_sep_current.pdf')
# Current Error Plot
fig4 = plt.figure()
plot_dmrg = plt.semilogy(s_vec[1:],np.abs(slope-slope_dmrg)/slope*100,label='DMRG Error')
plot_mf = plt.semilogy(s_vec[1:],np.abs(slope-slope_mf)/slope*100,label='MF Error')
plt.grid(True)
plt.legend()
plt.xlabel('$s$')
plt.ylabel('Current')
plt.show()
fig4.savefig('vary_s_comp_sep_current_error.pdf')
