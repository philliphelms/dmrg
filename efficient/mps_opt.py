import numpy as np
import matplotlib.pyplot as plt
import time
import mpo
import warnings
from scipy.linalg import eig as fullEig
from scipy.sparse.linalg import eigs as arnoldiEig
from mpl_toolkits.mplot3d import axes3d
from numpy import ma

class MPS_OPT:

    def __init__(self, N=10, d=2, maxBondDim=[10,20], tol=1e-5, maxIter=10,\
                 hamType='tasep', hamParams=(0.35,-1,2/3),\
                 plotExpVals=False, plotConv=False,\
                 usePyscf=True,initialGuess=0.5,ed_limit=12,\
                 saveResults=True,dataFolder='data/',verbose=2):
        # Import parameters
        self.N = N
        self.d = d
        self.maxBondDimInd = 0
        if isinstance(maxBondDim, list):
            self.maxBondDim = maxBondDim
        else:
            self.maxBondDim = [maxBondDim]
        self.iter_time = np.zeros(len(self.maxBondDim))
        self.iter_cnt = np.zeros(len(self.maxBondDim))
        self.maxBondDimCurr = self.maxBondDim[self.maxBondDimInd]
        self.tol = tol
        self.maxIter = maxIter
        self.hamType = hamType
        self.hamParams = hamParams
        self.plotExpVals = plotExpVals
        self.plotConv = plotConv
        self.saveResults = saveResults
        self.dataFolder = dataFolder
        self.verbose = verbose
        if usePyscf:
            from pyscf import lib
            self.einsum = lib.einsum
            self.eig = lib.eig
        else:
            self.einsum = np.einsum
            self.eig = np.linalg.eig
        self.usePyscf = usePyscf
        self.initialGuess = initialGuess
        self.ed_limit = ed_limit

        self.exp_val_figure=False
        self.conv_figure=False

        self.calc_spin_x = [0]*self.N
        self.calc_spin_y = [0]*self.N 
        self.calc_spin_z = [0]*self.N
        self.calc_empty = [0]*self.N
        self.calc_occ = [0]*self.N
        self.bondDimEnergies = np.zeros(len(self.maxBondDim))

    def generate_mps(self):
        if self.verbose > 3:
            print('\t'*2+'Generating MPS')
        self.M = []
        for i in range(int(self.N/2)):
            if self.initialGuess is "zeros":
                self.M.insert(len(self.M),np.zeros((self.d,min(self.d**(i),self.maxBondDimCurr),min(self.d**(i+1),self.maxBondDimCurr))))
            elif self.initialGuess is "ones":
                self.M.insert(len(self.M),np.ones((self.d,min(self.d**(i),self.maxBondDimCurr),min(self.d**(i+1),self.maxBondDimCurr))))
            elif self.initialGuess is "rand":
                self.M.insert(len(self.M),np.random.rand(self.d,min(self.d**(i),self.maxBondDimCurr),min(self.d**(i+1),self.maxBondDimCurr))) 
            else:
                self.M.insert(len(self.M),self.initialGuess*np.ones((self.d,min(self.d**(i),self.maxBondDimCurr),min(self.d**(i+1),self.maxBondDimCurr))))
        for i in range(int(self.N/2))[::-1]:
            if self.initialGuess is "zeros":
                self.M.insert(len(self.M),np.zeros((self.d,min(self.d**(i+1),self.maxBondDimCurr),min(self.d**i,self.maxBondDimCurr))))
            elif self.initialGuess is "ones":
                self.M.insert(len(self.M),np.ones((self.d,min(self.d**(i+1),self.maxBondDimCurr),min(self.d**i,self.maxBondDimCurr))))
            elif self.initialGuess is "rand":
                self.M.insert(len(self.M),np.random.rand(self.d,min(self.d**(i+1),self.maxBondDimCurr),min(self.d**i,self.maxBondDimCurr)))
            else:
                self.M.insert(len(self.M),self.initialGuess*np.ones((self.d,min(self.d**(i+1),self.maxBondDimCurr),min(self.d**i,self.maxBondDimCurr))))

    def generate_mpo(self):
        if self.verbose > 3:
            print('\t'*2+'Generating MPO')
        self.mpo = mpo.MPO(self.hamType,self.hamParams,self.N)

    def right_canonicalize_mps(self):
        if self.verbose > 3:
            print('\t'*2+'Performing Right Canonicalization')
        for i in range(1,len(self.M))[::-1]:
            if self.verbose > 4:
                print('\t'*3+'at site {}'.format(i))
            self.normalize(i,'left')
        # Sloppy fix to prevent super large values in initial matrix
        #self.M[0] = np.copy(self.M[-1])
        self.M[0] = np.swapaxes(self.M[-1],1,2)

    def generate_f(self):
        if self.verbose > 3:
            print('\t'*2+'Generating initial F arrays')
        self.F = []
        self.F.insert(len(self.F),np.array([[[1]]]))
        for i in range(int(self.N/2)):
            self.F.insert(len(self.F),np.zeros((min(self.d**(i+1),self.maxBondDimCurr),4,min(self.d**(i+1),self.maxBondDimCurr))))
        for i in range(int(self.N/2)-1,0,-1):
            self.F.insert(len(self.F),np.zeros((min(self.d**(i),self.maxBondDimCurr),4,min(self.d**i,self.maxBondDimCurr))))
        self.F.insert(len(self.F),np.array([[[1]]]))

    def normalize(self,i,direction):
        if self.verbose > 3:
            print('\t'*2+'Normalization at site {} in direction: {}'.format(i,direction))
        if direction is 'right':
            (n1,n2,n3) = self.M[i].shape
            M_reshape = np.reshape(self.M[i],(n1*n2,n3))
            (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
            self.M[i] = np.reshape(U,(n1,n2,n3))
            self.M[i+1] = self.einsum('i,ij,kjl->kil',s,V,self.M[i+1])
        elif direction is 'left':
            M_reshape = np.swapaxes(self.M[i],0,1)
            (n1,n2,n3) = M_reshape.shape
            M_reshape = np.reshape(M_reshape,(n1,n2*n3))
            (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
            M_reshape = np.reshape(V,(n1,n2,n3))
            self.M[i] = np.swapaxes(M_reshape,0,1)
            self.M[i-1] = self.einsum('klj,ji,i->kli',self.M[i-1],U,s)
        else:
            raise NameError('Direction must be left or right')

    def increaseBondDim(self):
        if self.verbose > 3:
            print('\t'*2+'Increasing Bond Dimensions from {} to {}'.format(self.maxBondDim[self.maxBondDimInd-1],self.maxBondDimCurr))
        Mnew = []
        for i in range(int(self.N/2)):
            Mnew.insert(len(Mnew),np.zeros((self.d,min(self.d**(i),self.maxBondDimCurr),min(self.d**(i+1),self.maxBondDimCurr))))
        for i in range(int(self.N/2))[::-1]:
            Mnew.insert(len(Mnew),np.zeros((self.d,min(self.d**(i+1),self.maxBondDimCurr),min(self.d**i,self.maxBondDimCurr))))
        for i in range(len(Mnew)):
            nx,ny,nz = self.M[i].shape
            Mnew[i][:nx,:ny,:nz] = self.M[i]
            self.M[i] = Mnew[i]

    def calc_initial_f(self):
        if self.verbose > 3:
            print('\t'*2+'Calculating initial F')
        for i in range(int(self.N)-1,0,-1):
            if self.verbose > 4:
                print('\t'*3+'at site {}'.format(i))
            self.F[i] = self.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(self.M[i]),self.mpo.W[i],self.M[i],self.F[i+1])

    def local_optimization(self,i,direction):
        if self.verbose > 3:
            print('\t'*2+'Local optimization at site {}'.format(i))
        if self.usePyscf:
            return self.pyscf_optimization(i,direction)
        else:
            return self.slow_optimization(i,direction)

    def pyscf_optimization(self,i,direction):
        if self.verbose > 5:
            print('\t'*4+'Using Pyscf optimization routine')
        (n1,n2,n3) = self.M[i].shape
        def opt_fun(x):
            if self.verbose > 6:
                print('\t'*5+'Eigenvalue Iteration')
            x_reshape = np.reshape(x,(n1,n2,n3))
            in_sum1 =  self.einsum('ijk,lmk->ijlm',self.F[i+1],x_reshape)
            in_sum2 = self.einsum('njol,ijlm->noim',self.mpo.W[i],in_sum1)
            if (self.hamType is "tasep") or (self.hamType is "sep") or (self.hamType is "sep_2d"):
                fin_sum = -self.einsum('pnm,noim->opi',self.F[i],in_sum2)
            else:
                fin_sum = self.einsum('pnm,noim->opi',self.F[i],in_sum2)
            return np.reshape(fin_sum,-1)
        def precond(dx,e,x0):
            # function(dx, e, x0) => array_like_dx
            return dx
        E,v = self.eig(opt_fun,np.reshape(self.M[i],(-1)),precond)
        self.M[i] = np.reshape(v,(n1,n2,n3))
        if (self.hamType is "tasep") or (self.hamType is "sep") or (self.hamType is "sep_2d"): E = -E
        if self.verbose > 2:
            print('\t'+'Current Energy = {}'.format(E))
        return E


    def slow_optimization(self,i,direction):
        if self.verbose > 5:
            print('\t'*4+'Using slow optimization routine')
        H = self.einsum('jlp,lmin,kmq->ijknpq',self.F[i],self.mpo.W[i],self.F[i+1])
        (n1,n2,n3,n4,n5,n6) = H.shape
        H = np.reshape(H,(n1*n2*n3,n4*n5*n6))
        if (self.hamType is "tasep") or (self.hamType is "sep") or (self.hamType is "sep_2d"): H = -H
        u,v = self.eig(H)
        u_sort = u[np.argsort(u)]
        v = v[:,np.argsort(u)]
        ind = 0
        for j in range(len(u_sort)):
            if np.abs(np.imag(u_sort[j])) < 1e-8:
                ind = j
            break
        E = u_sort[ind]
        v = v[:,ind]
        self.M[i] = np.reshape(v,(n1,n2,n3))
        if self.verbose > 2:
            print('\t'+'Current Energy = {}'.format(E))
        return E

    def update_f(self,i,direction):
        if self.verbose > 3:
            print('\t'*2+'Updating F at site {}'.format(i))
        if direction is 'right':
            self.F[i+1] = self.einsum('jlp,ijk,lmin,npq->kmq',self.F[i],np.conj(self.M[i]),self.mpo.W[i],self.M[i])
        elif direction is 'left':
            self.F[i] = self.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(self.M[i]),self.mpo.W[i],self.M[i],self.F[i+1])
        else:
            raise NameError('Direction must be left or right')

    def calc_observables(self,site):
        if self.verbose > 3:
            print('\t'*2+'Calculating Observables')
        if (self.hamType is "heis") or (self.hamType is "heis_2d") or (self.hamType is 'ising'):
            self.calc_spin_x[site] = self.einsum('ijk,il,ljk->',np.conj(self.M[site]),self.mpo.Sx,self.M[site])
            self.calc_spin_y[site] = self.einsum('ijk,il,ljk->',np.conj(self.M[site]),self.mpo.Sy,self.M[site])
            self.calc_spin_z[site] = self.einsum('ijk,il,ljk->',np.conj(self.M[site]),self.mpo.Sz,self.M[site])
        elif (self.hamType is "tasep") or (self.hamType is "sep") or (self.hamType is "sep_2d"):
            self.calc_empty[site] = self.einsum('ijk,il,ljk->',np.conj(self.M[site]),self.mpo.v,self.M[site])
            self.calc_occ[site] = self.einsum('ijk,il,ljk->',np.conj(self.M[site]),self.mpo.n,self.M[site])

    def energy_contraction(self,site):
        return self.einsum('ijk,jlmn,olp,mio,nkp->',\
                self.F[site],self.mpo.W[site],self.F[site+1],np.conjugate(self.M[site]),self.M[site])

    def plot_observables(self):
        if self.plotExpVals:
            plt.ion()
            if not self.exp_val_figure:
                self.exp_val_figure = plt.figure()
                self.angle = 0
            else:
                plt.figure(self.exp_val_figure.number)
            plt.cla()
            if (self.hamType is "tasep") or (self.hamType is "sep"):
                plt.plot(range(0,int(self.N)),self.calc_occ,linewidth=3)
                plt.ylabel('Average Occupation',fontsize=20)
                plt.xlabel('Site',fontsize=20)
            elif (self.hamType is "sep_2d"):
                plt.clf()
                x,y = (np.arange(self.mpo.N2d),np.arange(self.mpo.N2d))
                currPlot = plt.imshow(np.real(np.reshape(self.calc_occ,(self.mpo.N2d,self.mpo.N2d))))
                plt.colorbar(currPlot)
                plt.gca().set_xticks(range(len(x)))
                plt.gca().set_yticks(range(len(y)))
                plt.gca().set_xticklabels(x)
                plt.gca().set_yticklabels(y)
                plt.gca().grid(False)
            elif (self.hamType is "heis")  or (self.hamType is 'ising'):
                ax = self.exp_val_figure.gca(projection='3d')
                x = np.arange(self.N)
                y = np.zeros(self.N)
                z = np.zeros(self.N)
                ax.scatter(x,y,z,color='k')
                plt.quiver(x,y,z,self.calc_spin_x,self.calc_spin_y,self.calc_spin_z,pivot='tail')
                ax.set_zlim((np.min((-np.abs(np.min(self.calc_spin_z)),-np.abs(np.max(self.calc_spin_z)))),
                             np.max(( np.abs(np.max(self.calc_spin_z)) , np.abs(np.min(self.calc_spin_z))))))
                ax.set_ylim((np.min((-np.abs(np.min(self.calc_spin_y)),-np.abs(np.max(self.calc_spin_y)))),
                             np.max(( np.abs(np.max(self.calc_spin_y)), np.abs(np.min(self.calc_spin_y))))))
                plt.ylabel('y',fontsize=20)
                plt.xlabel('x',fontsize=20)
                ax.set_zlabel('z',fontsize=20)    
                self.angle += 3
                ax.view_init(30, self.angle)
                plt.draw()
            elif self.hamType is "heis_2d":
                ax = self.exp_val_figure.gca(projection='3d')
                x, y = np.meshgrid(np.arange((-self.mpo.N2d+1)/2,(self.mpo.N2d-1)/2+1),
                                   np.arange((-self.mpo.N2d+1)/2,(self.mpo.N2d-1)/2+1))
                ax.scatter(x,y,np.zeros((self.mpo.N2d,self.mpo.N2d)),color='k')
                plt.quiver(x,y,np.zeros((self.mpo.N2d,self.mpo.N2d)),
                           np.reshape(self.calc_spin_x,x.shape),
                           np.reshape(self.calc_spin_y,x.shape),
                           np.reshape(self.calc_spin_z,x.shape),
                           pivot='tail')
                ax.plot_surface(x, y, np.zeros((self.mpo.N2d,self.mpo.N2d)), alpha=0.2)
                ax.set_zlim((min(self.calc_spin_z),max(self.calc_spin_z)))
                plt.ylabel('y',fontsize=20)
                plt.xlabel('x',fontsize=20)
                ax.set_zlabel('z',fontsize=20)
                self.angle += 3
                ax.view_init(30, self.angle)
                plt.draw()
            else:
                raise ValueError("Plotting of expectation values is not implemented for the given hamiltonian type")
            plt.pause(0.0001)

    def plot_convergence(self,i):
        if self.plotConv:
            plt.ion()
            if not self.conv_figure:
                self.conv_figure = plt.figure()
                self.y_vec = [self.E]
                self.x_vec = [i]
            else:
                plt.figure(self.conv_figure.number)
                self.y_vec.insert(-1,self.E)
                self.x_vec.insert(-1,i)
            plt.cla()
            if len(self.y_vec) > 3:
                plt.plot(self.x_vec[:-2],self.y_vec[:-2],'r-',linewidth=2)
            plt.ylabel('Energy',fontsize=20)
            plt.xlabel('Site',fontsize=20)
            plt.pause(0.0001)

    def saveFinalResults(self,calcType):
        if self.verbose > 3:
            print('\t'*2+'Writing final results to output file')
        if self.saveResults:
            # Create Filename:
            filename = 'results_'+self.hamType+'_N'+str(self.N)+'_M'+str(self.maxBondDim)
            for i in range(len(self.hamParams)):
                filename += ('_'+str(self.hamParams[i]))
            if calcType is 'dmrg':
                np.savez(self.dataFolder+'dmrg/'+filename,
                         N=self.N,
                         M=self.maxBondDim,
                         hamParams=self.hamParams,
                         dmrg_energy = self.finalEnergy,
                         calc_empty = self.calc_empty,
                         calc_occ = self.calc_occ,
                         calc_spin_x = self.calc_spin_x,
                         calc_spin_y = self.calc_spin_y,
                         calc_spin_z = self.calc_spin_z)
            elif calcType is 'mf':
                np.savez(self.dataFolder+'mf/'+filename,
                         E_mf = self.E_mf)
            elif calcType is 'ed':
                np.savez(self.dataFolder+'ed/'+filename,
                         E_ed = self.E_ed)

    def kernel(self):
        self.generate_mps()
        self.right_canonicalize_mps()
        self.generate_mpo()
        self.generate_f()
        self.calc_initial_f()
        converged = False
        currIterCnt = 0
        totIterCnt = 0
        self.calc_observables(0)
        E_prev = self.energy_contraction(0)
        while not converged:
            # Right Sweep --------------------------
            if self.verbose > 1:
                print('\t'*0+'Right Sweep {}'.format(totIterCnt))
            for i in range(int(self.N-1)):
                t1 = time.time()
                self.E = self.local_optimization(i,'right')
                self.calc_observables(i)
                self.normalize(i,'right')
                self.update_f(i,'right')
                self.plot_observables()
                self.plot_convergence(i)
                t2 = time.time()
                self.iter_time[self.maxBondDimInd] += t2-t1
                self.iter_cnt[self.maxBondDimInd] += 1
            # Left Sweep ---------------------------
            if self.verbose > 1:
                print('\t'*0+'Left Sweep {}'.format(totIterCnt))
            for i in range(int(self.N-1),0,-1):
                t1 = time.time()
                self.E = self.local_optimization(i,'left')
                self.calc_observables(i)
                self.normalize(i,'left')
                self.update_f(i,'left')
                self.plot_observables()
                self.plot_convergence(i)
                t2 = time.time()
                self.iter_time[self.maxBondDimInd] += t2-t1
                self.iter_cnt[self.maxBondDimInd] += 1
            # Check Convergence --------------------
            if np.abs(self.E-E_prev) < self.tol:
                if self.maxBondDimInd is (len(self.maxBondDim)-1):
                    if self.verbose > 0:
                        print('#'*75+'\nConverged at E = {} for Bond Dimension = {}\nAverage time per iteration = {}'\
                              .format(self.E,self.maxBondDimCurr,self.iter_time[self.maxBondDimInd]/self.iter_cnt[self.maxBondDimInd])\
                              +'\n'+'#'*75)
                    self.finalEnergy = self.E
                    self.bondDimEnergies[self.maxBondDimInd] = self.E
                    converged = True
                else:
                    if self.verbose > 0:
                        print('-'*35+'\nConverged for Bond Dimension = {}\n at Energy = {}\nAverage time per iteration = {}'\
                              .format(self.maxBondDimCurr,self.E,self.iter_time[self.maxBondDimInd]/self.iter_cnt[self.maxBondDimInd]\
                              )+'\n'+'-'*35)
                    self.bondDimEnergies[self.maxBondDimInd] = self.E
                    self.maxBondDimInd += 1
                    self.maxBondDimCurr = self.maxBondDim[self.maxBondDimInd]
                    self.increaseBondDim()
                    self.generate_f()
                    self.calc_initial_f()
                    totIterCnt += 1
                    currIterCnt = 0
            elif currIterCnt >= self.maxIter:
                if self.maxBondDimInd is (len(self.maxBondDim)-1):
                    if self.verbose > 0:
                        print('!'*75+'\nConvergence not acheived\n'+'\tE={}\n'.format(self.E)+'!'*75)
                    self.bondDimEnergies[self.maxBondDimInd] = self.E
                    self.finalEnergy = self.E
                    converged = True
                else:
                    if self.verbose > 0:
                        print('-'*35+'\nNot Converged for Bond Dimension = {}\n at Energy = {}\nAverage time per iteration = {}'\
                              .format(self.maxBondDimCurr,self.E,self.iter_time[self.maxBondDimInd]/self.iter_cnt[self.maxBondDimInd])\
                              +'\n'+'-'*35)
                    self.bondDimEnergies[self.maxBondDimInd] = self.E
                    self.maxBondDimInd += 1
                    self.maxBondDimCurr = self.maxBondDim[self.maxBondDimInd]
                    self.increaseBondDim()
                    self.generate_f()
                    self.calc_initial_f()
                    totIterCnt += 1
                    currIterCnt = 0
            else:
                if self.verbose > 2:
                    print('\t'*1+'Energy Change {}\nNeeded <{}'.format(np.abs(self.E-E_prev),self.tol))
                E_prev = self.E
                currIterCnt += 1
                totIterCnt += 1
        self.saveFinalResults('dmrg')
        return self.finalEnergy


    # ADD THE ABILITY TO DO OTHER TYPES OF CALCULATIONS FROM THE MPS OBJECT
    def exact_diag(self,maxIter=10000,tol=1e-10):
        if self.N > self.ed_limit:
            print('!'*50+'\nExact Diagonalization limited to systems of 12 or fewer sites\n'+'!'*50)
            return 0
        if not hasattr(self,'mpo'):
            self.generate_mpo()
        import exactDiag_meanField
        if self.hamType is 'tasep':
            x = exactDiag_meanField.exactDiag(L=self.N,
                                              clumpSize=self.N,
                                              alpha=self.mpo.alpha,
                                              gamma=0,
                                              beta=0,
                                              delta=self.mpo.beta,
                                              s=self.mpo.s,
                                              p=1,
                                              q=0,
                                              maxIter=maxIter,
                                              tol=tol)
        elif self.hamType is 'sep':
            x = exactDiag_meanField.exactDiag(L=self.N,
                                              clumpSize=self.N,
                                              alpha=self.mpo.alpha,
                                              gamma=self.mpo.gamma,
                                              beta=self.mpo.beta,
                                              delta=self.mpo.delta,
                                              s=self.mpo.s,
                                              p=self.mpo.p,
                                              q=self.mpo.q,
                                              maxIter=maxIter,
                                              tol=tol)
        else:
            raise ValueError("Only 1D SEP and TASEP are supported for Exact Diagonalization")
        self.E_ed = x.kernel()
        self.saveFinalResults('ed')
        return(self.E_ed)

    def mean_field(self,maxIter=10000,tol=1e-10,clumpSize=2):
        if not hasattr(self,'mpo'):
            self.generate_mpo()
        import exactDiag_meanField
        if self.hamType is 'tasep':
            x = exactDiag_meanField.exactDiag(L=self.N,
                                              clumpSize=clumpSize,
                                              alpha=self.mpo.alpha,
                                              gamma=0,
                                              beta=0,
                                              delta=self.mpo.beta,
                                              s=self.mpo.s,
                                              p=1,
                                              q=0,
                                              maxIter=maxIter,
                                              tol=tol)
        elif self.hamType is 'sep':
            x = exactDiag_meanField.exactDiag(L=self.N,
                                              clumpSize=clumpSize,
                                              alpha=self.mpo.alpha,
                                              gamma=self.mpo.gamma,
                                              beta=self.mpo.beta,
                                              delta=self.mpo.delta,
                                              s=self.mpo.s,
                                              p=self.mpo.p,
                                              q=self.mpo.q,
                                              maxIter=maxIter,
                                              tol=tol)
        else:
            raise ValueError("Only 1D SEP and TASEP are supported for Mean Field")
        self.E_mf = x.kernel()
        self.saveFinalResults('mf')
        return(self.E_mf)
