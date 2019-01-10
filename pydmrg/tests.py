import unittest
import numpy as np

class pydmrg_test(unittest.TestCase):
    def test_eigMethodsCheck(self):
        import tests.asep.eigMethodsCheck as eigCheck
        E1,E2,E3 = eigCheck.run_test()
        self.assertTrue(np.isclose(E1,E2))
        self.assertTrue(np.isclose(E2,E3))

    def test_periodic2D(self):
        import tests.asep2D.periodicCheck as perCheck
        E1,E2,E3,E4,E5,E6,E7,E8,E9 = perCheck.run_test()
        self.assertTrue(np.isclose(E1,E2))
        self.assertTrue(np.isclose(E1,E3))
        self.assertTrue(np.isclose(E1,E4))
        self.assertTrue(np.isclose(E1,E5))
        self.assertTrue(np.isclose(E1,E6))
        self.assertTrue(np.isclose(E1,E7))
        self.assertTrue(np.isclose(E1,E8))
        self.assertTrue(np.isclose(E1,E9))

if __name__ == "__main__":
    unittest.main()