"""The fiscal balance chart (overview, « Solde budgétaire »)."""

import unittest

import pandas as pd

from components.fiscal_balance import combined_figure


def _composite():
    national = pd.DataFrame({
        "year": [2023, 2024],
        "revenue": [1.0e12, 1.1e12],
        "expenditure": [1.3e12, 1.45e12],
        "source": "Togo DGB Budget Execution Report",
    })
    weo = pd.DataFrame({
        "year": [2025, 2026, 2027],
        "revenue": [1.2e12, 1.3e12, 1.4e12],
        "expenditure": [1.5e12, 1.8e12, 2.1e12],
        "is_forecast": [False, True, True],
    })
    return combined_figure(national, None, weo, "XOF", "francs CFA", view_mode="composite", lang="fr")


class ForecastLabelTest(unittest.TestCase):
    def test_lines_stay_below_the_forecast_label(self):
        fig = _composite()
        label = next(a for a in fig.layout.annotations if a.text == "prévision")
        self.assertEqual((label.yref, label.yanchor), ("paper", "top"))
        low, high = fig.layout.yaxis.range
        top_line = 2.1e12
        # The label hangs from the top of the upper panel; the lines leave it
        # the top sixth of the panel.
        self.assertGreaterEqual(high - top_line, (high - low) / 6)

    def test_no_band_no_headroom(self):
        national = pd.DataFrame({
            "year": [2023, 2024], "revenue": [1.0e12, 1.1e12], "expenditure": [1.3e12, 1.45e12],
            "source": "Togo DGB Budget Execution Report",
        })
        fig = combined_figure(national, None, None, "XOF", "francs CFA", view_mode="official", lang="fr")
        self.assertIsNone(fig.layout.yaxis.range)


if __name__ == "__main__":
    unittest.main()
