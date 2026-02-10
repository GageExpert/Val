import unittest

from valuation_dcf import DCFInputs, dcf_valuation, terminal_value_exit_multiple


class TestDCF(unittest.TestCase):
    def test_dcf_basic(self):
        ufcf = [100, 110, 120]
        tv = terminal_value_exit_multiple(120, 10)
        inputs = DCFInputs(ufcf=ufcf, wacc=0.1, terminal_method="exit_multiple", terminal_value=tv, debt=0, cash=0, shares=10)
        result = dcf_valuation(inputs)
        self.assertGreater(result.enterprise_value, 0)


if __name__ == "__main__":
    unittest.main()
