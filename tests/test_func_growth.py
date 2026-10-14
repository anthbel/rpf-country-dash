"""Budget growth by function (overview, « Croissance des budgets par fonction »)."""

import unittest
from unittest.mock import patch

import pandas as pd

from components import budget_increment_analysis as bia
from constants import END_YEAR as E


def _by_function(funcs, years, grow=1.1):
    """Each function's budget, all of it domestically funded unless
    ``funcs`` gives a foreign share, growing by ``grow`` a year."""
    rows = []
    for func, (base, foreign_share) in funcs.items():
        for k, year in enumerate(years):
            budget = base * grow ** k
            rows.append({
                "country_name": "Togo", "year": year, "func": func,
                "budget": budget, "real_budget": budget,
                "domestic_funded_budget": budget * (1 - foreign_share),
                "real_domestic_funded_budget": budget * (1 - foreign_share),
            })
    return pd.DataFrame(rows)


def _render(frame, lang="en"):
    with patch.object(bia.server_store, "get", side_effect={"func_by_country_year": frame}.__getitem__):
        return bia.render_fig_and_narrative(True, "Togo", "domestic_funded_budget", lang)


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



class AverageGrowthTest(unittest.TestCase):
    def test_five_years_grow_over_four_intervals(self):
        # 10 % a year from the first to the fifth year is four years of growth:
        # 1.1 ** 4. Spread over five, the rate read 7.9 %.
        frame = _by_function({"Health": (100.0, 0.2), "Education": (200.0, 0.1)}, range(E - 4, E + 1))
        _, narrative = _render(frame)
        text = "".join(narrative)
        self.assertIn("Over the past 5 years, the national budget has grown at an average rate of 10.0% per year", text)
        self.assertIn("10.0%", text)
        self.assertNotIn("7.9%", text)

    def test_a_single_year_has_no_growth_to_report(self):
        frame = _by_function({"Health": (100.0, 0.2), "Education": (200.0, 0.1)}, [E])
        fig, narrative = _render(frame)
        self.assertEqual(narrative, bia.t("error.data_unavailable", "en"))


if __name__ == "__main__":
    unittest.main()
