import unittest
import tests

loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(tests)
unittest.TextTestRunner(verbosity=2).run(suite)