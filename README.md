# PyDMRG

This code was originally developed as a simple implementation of the Density Matrix Renormalization Group (DMRG) algorithm using the Matrix Product States (MPS) and Matrix Product Operator (MPO) formalisms.
As this code is further developed, I am seeking to maintain the initial simple scripts for those seeking to see how a DMRG algorithm works for simple models such as the Ising and Heisenberg Models.
In addition, a major focus of this project is the application of the DMRG algorithm to stochastic classical processes such as the simple exclusion process and its derivatives. Because of this, many of the Hamiltonians currently implemented in this work are centered in these driven diffusive processes.
Additionally, work has been started to implement two dimensional hamiltonians. Currently, a 2D heisenberg model is implemented for square lattices. The next steps will involve implementing this for the SEP and for rectangular lattices.

## Code Organization
The code is currently divided into three different sections. First is a directory named *efficient* which contains the most efficient implementation of the mps/dmrg algorithm for a few models. Currently, the supported models are:
* Heisenberg
* Ising
* Totally Assymetric Simple Exclusion Process
* General Simple Exclusion Process

In this, and all, implementations, I seek to follow the algorithm and terminology as discussed in the paper [**Density Matrix Renormalization Group in the Age of Matrix Product States**](https://arxiv.org/abs/1008.3477) (Schollwoeck, 2011).


In the second directory, *sep_exact_diagonalization*, I have adapted calculations by [Ushish Ray](http://www.stochasticphysics.org/) to perform exact diagonalization calculations. 
I have begun translating the original matlab scripts into python modules that can be run via the efficient computations, but there are still some details being worked out. 


The final directory is named *simple_scripts* and contains the most simple implementations of the DMRG algorithm. 
This contains scripts that are only approximately 100 lines long an perform DMRG calculations in the simplest implementation I include. 
Currently, there are three scripts which run the calculations for two, four, or an arbitrary number of sites. 

## Running Calculations
### *efficient*
The file *driver.py* contains multiple examples of how the efficient version of the DMRG calculations can be run. 
The majority of these examples are centered on calculations for classical models, but the final shows how this can be done for the heisenberg model.


There are, in addition, examples that demonstrate how the calculations are carried out for a 2D heisenberg model. Additional examples will be added as more functionality is incorporated into the current framework.


In general, a simple calculation can be done via two steps: (1) Initializing an mpo_opt object and (2) running the calculation. 
As the simplest example:
```python
import mps_opt
x = mps_opt.MPS_OPT()
x.kernel()
```
This simple script will run the optimization with all the default settings. If a setting is to be changed, you specify:
```python
x = mps_opt.MPS_OPT(setting1=value1,
                    setting2=value2,
                    ...)
```
Where the available settings and their default values are:

Keyword     | Default     | Description
------------|-------------|-------------
N           |10           |Number of lattice sites
d           |2            |Local state-space dimension
maxBondDim  |8            |Maximum Bond Dimension
tol         |1e-5         |Convergence tolerance 
maxIter     |10           |Maximum number of left and right sweeps
hamType     |'tasep'      |Type of hamiltonian ('heis','tasep','sep','heis_2d')
hamParams   |(0.35,-1,2/3)|Parameters for given hamiltonian. For Heis=(J,h), TASEP=(a,s,b), SEP=(a,g,p,q,b,d,s), 2D Heis=(J,h)
plotExpVals |False        |If True, then a plot of expectation values, such as local spins, is created and updated at each step
plotConv    |False        |If True, then a plot showing the energy as a function of the sweep number is created
eigMethod   |'full'       |Specifies the method used for solving eigenvalue problems. (np.linalg.eig='full',sp.sparse.linalg.eigs='arnoldi')


### *sep_exact_diagonalization*
I will update this section once I've converted the original calculations into python and provided some interaction between this and the *efficient* code.

### *simple_scripts*
This directory contains three scripts, each of which is self-contained, which should give an extremely simple introduction to the DMRG algorithm in the MPS formalism.
In the scripts, and after the required python modules are imported, the key input variables are all defined. 
The script can be controlled by changing values in this section of the code.


Note that currently, all of these calculations are using the simple exclusion model - In the future, the heisenberg model will be implmented.  

## Future Work
* Efficiency Related
    * Implement some form of parallelization for tensor network operations
    * Possibly improve speed of function fed to Davidson Algorithm
    * Growing Bond Dimension during consecutive iterations
* Applications Related
    * Implement infinite algorithm
        * Initially in 1D
        * Then in 2D
    * Implement Periodic Boundary Conditions
    * Implement the use of quantum numbers
    * Implement time evolution

## Known Issues
There are currently no known issues - Please contact me if you come accross any problems. 
* Occasionally an eigenvalue with a large imaginary part will be selected - this could become a significant problem, but currently is not high priority because it occurs seldomly.
    * It should be easy when using np.linalg.eig, but might be more difficult when using the arnoldi algorithm.
