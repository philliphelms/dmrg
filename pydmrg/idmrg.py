import numpy as np
from mpo.asep import return_mpo
from tools.mps_tools import *
from tools.diag_tools import *

# Calculation Details
mbd = 10
nStates = 1

# Get the MPO
p = 0.1
alpha = 0.5      # in at left
gamma = 1.-alpha  # Out at left
q     = 1.-p      # Jump left
beta  = 0.5     # Out at right
delta = 1.-beta   # In at right
s = -0.5
hamParams = np.array([alpha,gamma,p,q,beta,delta,s])
mpoList = return_mpo(2,hamParams)

# Initialize by generating random MPS of size 2
mpsList = create_all_mps(2,mbd,nStates)
print('Length of mps List: {}'.format(len(mpsList)))
print('Length of mps: {}'.format(len(mpsList[0])))
print('Length of mpo List: {}'.format(len(mpoList)))
print('Length of mpo: {}'.format(len(mpoList[0])))

# Set up empty initial environment
#envList = []
#for state in range(nStates):
#    env = [np.array([[[1.]]],dtype=np.complex_),np.array([[[1.]]],dtype=np.complex_)]
#    envList.append(env)
# Do two-site optimization of random MPS of size 2
#E,vecs,ovlp = calc_eigs(mpsList,mpoList,envList,0,nStates,oneSite=False,alg='davidson')
# Normalize vectors
#for state in range(nStates):
#    vecs[:,state] /= np.dot(vecs[:,state],vecs[:,state].conj())
#print('Resulting Energy = {}'.format(E))
#print('Resulting davidson vector = {}'.format(vecs[:,0]))
# Calculate Hamiltonian as practice:
Ham = np.einsum('abIi,bcKk->IKik',mpoList[0][0],mpoList[0][1])
(n1,n2,n3,n4) = Ham.shape
Ham = np.reshape(Ham,(n1*n2,n3*n4))
E,vecs = np.linalg.eig(Ham)

# Do SVD Of resulting sites (also figure out how to use the RDM to do this?)
(n1,n2,n3) = mpsList[0][0].shape
(n4,n5,n6) = mpsList[0][1].shape
for state in range(nStates):
    psi = np.reshape(vecs[:,state],(n1*n2,n4*n6))
    U,S,V = np.linalg.svd(psi,full_matrices=False)
    # Something
    leftSide = np.einsum('ij,j,jk->ik',U,S,V)
    rightSide = np.einsum('IJ,J,JK->IK',U.conj(),S.conj(),V.conj())
    rightSide = np.einsum('IJ,J,JK->IK',U,S,V)
    Ham = np.einsum('abIi,bcKk->IiKk',mpoList[0][0],mpoList[0][1])
    E = np.einsum('ik,IiKk,IK->',leftSide,Ham,rightSide)
    norm = np.einsum('ik,ik->',leftSide,rightSide)
    print('Not Normalized E: {}'.format(E))
    print('Norm Factor: {}'.format(norm))
    # Put back into the MPS
    print('U shape {}'.format(U.shape))
    print('S shape {}'.format(S.shape))
    print('V shape {}'.format(V.shape))
    print('Recontracted Energy = {}'.format(E/norm))
# Update Environment

