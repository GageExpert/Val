import unittest

from sensitivity import dcf_sensitivity
from valuation_dcf import DCFInputs


class TestSensitivity(unittest.TestCase):
    def test_grid(self):
        inputs = DCFInputs(ufcf=[100, 110], wacc=0.1, terminal_method="exit_multiple", terminal_value=1000, debt=0, cash=0, shares=1)
        grid = dcf_sensitivity(inputs, wacc_range=(0.08, 0.12), terminal_range=(8, 12), size=5, terminal_method="exit_multiple")
        self.assertEqual(len(grid.x_values), 5)
        self.assertEqual(len(grid.y_values), 5)
        self.assertEqual(grid.grid.shape, (5, 5))


if __name__ == "__main__":
    unittest.main()
