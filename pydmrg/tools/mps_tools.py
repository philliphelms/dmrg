import numpy as np

def move_gauge_right(mps,site):
    (n1,n2,n3) = mps[site].shape
    M_reshape = np.reshape(mps[site],(n1*n2,n3))
    (u,s,v) = np.linalg.svd(M_reshape,full_matrices=False)
    mps[site] = np.reshape(u,(n1,n2,n3))
    mps[site+1] = np.einsum('i,ij,kjl->kil',s,v,mps[site+1])
    return mps

def move_gauge_left(mps,site):
    M_reshape = np.swapaxes(mps[site],0,1)
    (n1,n2,n3) = M_reshape.shape
    M_reshape = np.reshape(M_reshape,(n1,n2*n3))
    (u,s,v) = np.linalg.svd(M_reshape,full_matrice=False)
    M_reshape = np.reshape(v,(n1,n2,n3))
    mps[site] = np.swapaxes(M_reshape,0,1)
    mps[site-1] = np.einsum('klj,ji,i->kli',mps[site-1],u,s)
    return mps

def move_gauge(mps,init_site,fin_site):
    if init_site < fin_site:
        # Right Sweep
        for site in range(init_site,fin_site):
            mps = move_gauge_right(mps,site)
    else:
        # Left Sweep
        for site in range(fin_site,init_site,-1):
            mps = move_gauge_left(mps,site)
    return mps

def list_occs(N):
    occ = np.zeros((2**N,N),dtype=int)
    for i in range(2**N):
        occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
    return occ

def return_mat_dims(N,mbd):
    fbd_site = []
    mbd_site = []
    fbd_site.insert(0,1)
    mbd_site.insert(0,1)
    for i in range(int(N/2)):
        fbd_site.insert(-1,2**i)
        mbd_site.insert(-1,min(2**i,mbd))
    for i in range(int(N/2))[::-1]:
        fbd_site.insert(-1,2**(i+1))
        mbd_site.insert(-1,min(2**(i+1),mbd))
    return fbd_site,mbd_site

def state2mps(N,psi,mbd,return_ee=True):
    psi = np.reshape(psi,[2]*N)
    fbd_site,mbd_site = return_mat_dims(N,mbd)
    mps = []
    EE = np.zeros(N-1)
    for i in range(N,1,-1):
        psi = np.reshape(psi,(2**(i-1),-1))
        (u,s,v) = np.linalg.svd(psi,full_matrices=False)
        B = np.reshape(v,(-1,2,mbd_site[i]))
        B = B[:mbd_site[i-1],:,:mbd_site[i]]
        B = np.swapaxes(B,0,1)
        mps.insert(0,B)
        psi = np.einsum('ij,j->ij',u[:,:mbd_site[i-1]],s[:mbd_site[i-1]])
        # Calculate & Print Entanglement Entropy
        EE[i-2] = -np.dot(s**2.,np.log2(s**2.))
    #assert(np.isclose(eer[int(N/2)-1],old_entanglement))
    mps.insert(0,np.reshape(psi,(2,1,min(2,mbd))))
    if return_ee:
        return mps,EE[int(N/2)-1]
    else:
        return mps

def create_rand_mps(N,mbd,d=2):
    # Create MPS
    M = []
    for i in range(int(N/2)):
        #M.insert(len(M),np.random.rand(d,min(d**(i),mbd),min(d**(i+1),mbd)))
        M.insert(len(M),np.ones((d,min(d**(i),mbd),min(d**(i+1),mbd))))
    if N%2 is 1:
        #M.insert(len(M),np.random.rand(d,min(d**(i+1),mbd),min(d**(i+1),mbd)))
        M.insert(len(M),np.ones((d,min(d**(i+1),mbd),min(d**(i+1),mbd))))
    for i in range(int(N/2))[::-1]:
        #M.insert(len(M),np.random.rand(d,min(d**(i+1),mbd),min(d**i,mbd)))
        M.insert(len(M),np.ones((d,min(d**(i+1),mbd),min(d**i,mbd))))
    return M

def load_mps(N,fname):
    npzfile = np.load(fname+'.npz')
    M = []
    gaugeSite = npzfile['site']
    for i in range(N):
        M.append(npzfile['M'+str(i)])
    return M,gaugeSite

def increase_mbd(M,mbd,periodic=False,constant=False,d=2):
    N = len(M)
    if periodic == False:
        if constant == False:
            for site in range(int(N/2)):
                nx,ny,nz = M[site].shape
                sz1 = min(d**site,mbd)
                sz2 = min(d**(site+1),mbd)
                M[site] = np.pad(M[site], ((0,0), (0,sz1-ny), (0,sz2-nz)), 'constant', constant_values=0j)
            if N%2 is 1:
                site += 1
                nx,ny,nz = M[site].shape
                sz1 = min(d**(site),mbd)
                sz2 = min(d**(site),mbd)
                M[site] = np.pad(M[site], ((0,0), (0,sz1-ny), (0,sz2-nz)), 'constant', constant_values=0j)
            for i in range(int(N/2))[::-1]:
                site = N - i - 1
                nx,ny,nz = M[site].shape
                sz1 = min(d**(N-(site)),mbd)
                sz2 = min(d**(N-(site+1)),mbd)
                M[site] = np.pad(M[site], ((0,0), (0,sz1-ny), (0,sz2-nz)), 'constant', constant_values=0j)
        else:
            for site in range(N):
                nx,ny,nz = M[site].shape
                sz1 = mbd
                sz2 = mbd
                if site == 0: sz1 = 1
                if site == N-1: sz2 = 1
                M[site] = np.pad(M[site], ((0,0), (0,sz1-ny), (0,sz2-nz)), 'constant', constant_values=0j)
    else:
        for site in range(N):
            nx,ny,nz = M[site].shape
            sz1 = mbd
            sz2 = mbd
            M[site] = np.pad(M[site], ((0,0), (0,sz1-ny), (0,sz2-nz)), 'constant', constant_values=0j)
    return M

def save_mps(M,fname,gaugeSite=0):
    if fname is not None:
        Mdict = {}
        for i in range(len(M)):
            Mdict['M'+str(i)] = M[i]
        np.savez(fname+'.npz',site=gaugeSite,**Mdict)