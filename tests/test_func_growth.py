"""Budget growth by function (overview, « Croissance des budgets par fonction »)."""

import unittest

import pandas as pd

from components import budget_increment_analysis as bia


class FuncGrowthFigureTest(unittest.TestCase):
    def test_source_note_starts_inside_the_figure(self):
        df = pd.DataFrame({
            "func": ["Health", "Health"], "year": [2022, 2023],
            "yoy_domestic_funded_budget": [10.0, 12.0],
        })
        fig = bia.create_func_growth_figure(df, "domestic_funded_budget", lang="fr")
        note = fig.layout.annotations[0]
        # Left of x = 0 (paper) the note runs past the figure's left margin and is cut.
        self.assertEqual(note.x, 0)
        self.assertEqual(note.xanchor, "left")


if __name__ == "__main__":
    unittest.main()
