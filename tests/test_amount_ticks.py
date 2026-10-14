"""Amount axes labelled with the dashboard's magnitude suffixes.

Plotly prints its own short-scale suffixes on an amount axis ("200B",
"1.5T", "26k") whatever the language. The helpers in utils place round tick
values over the plotted data and label them with millify's suffixes
(" Md" in French, up to milliards; " bi", " tri" in Portuguese; " B", " T"
in English).
"""

import unittest

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import (
    amount_ticks,
    apply_amount_axis,
    apply_amount_colorbar,
    millify,
)

MINUS = "\u2212"


class AmountTicksTest(unittest.TestCase):
    def test_about_five_round_steps_from_zero(self):
        values, labels = amount_ticks(0, 2.1e12, lang="fr")
        self.assertEqual(values, [0, 0.5e12, 1e12, 1.5e12, 2e12, 2.5e12])
        self.assertEqual(labels, ["0", "500 Md", "1\u202f000 Md", "1\u202f500 Md", "2\u202f000 Md", "2\u202f500 Md"])

    def test_zero_is_a_tick_even_when_the_data_starts_above_it(self):
        values, _ = amount_ticks(4e11, 2.1e12, lang="fr")
        self.assertIn(0, values)

    def test_one_suffix_per_axis_taken_from_the_largest_tick(self):
        _, labels = amount_ticks(0, 240e9, lang="fr")
        self.assertEqual(labels, ["0", "50 Md", "100 Md", "150 Md", "200 Md", "250 Md"])

    def test_negative_values_carry_a_minus_sign(self):
        values, labels = amount_ticks(-430e9, 0, lang="fr")
        self.assertEqual(values[0], -500e9)
        self.assertEqual(values[-1], 0)
        self.assertEqual(labels[0], MINUS + "500 Md")
        self.assertEqual(labels[-1], "0")

    def test_each_language_uses_its_own_suffixes(self):
        self.assertEqual(amount_ticks(0, 2e12, lang="en")[1][-1], "2.0 T")
        self.assertEqual(amount_ticks(0, 2e12, lang="pt")[1][-1], "2,0 tri")
        self.assertEqual(amount_ticks(0, 180e3, lang="fr")[1][-1], "200 k")

    def test_without_zero_the_ticks_cover_only_the_span(self):
        values, labels = amount_ticks(17_000, 28_000, lang="fr", include_zero=False)
        self.assertEqual(values, [16_000, 18_000, 20_000, 22_000, 24_000, 26_000, 28_000])
        self.assertEqual(labels[1], "18 k")

    def test_no_span_gives_no_ticks(self):
        self.assertEqual(amount_ticks(0, 0, lang="fr"), ([], []))
        self.assertEqual(amount_ticks(None, None, lang="fr"), ([], []))


class MillifyDecimalsTest(unittest.TestCase):
    def test_defaults_are_unchanged(self):
        self.assertEqual(millify(2_000_000_000, lang="fr"), "2,00 Md")

    def test_decimals_and_a_forced_magnitude(self):
        self.assertEqual(millify(500e6, lang="fr", decimals=1, magnitude=3), "0,5 Md")

    def test_french_amounts_stay_in_milliards_with_grouped_thousands(self):
        self.assertEqual(millify(3.5e12, lang="fr"), "3\u202f500,00 Md")
        self.assertEqual(millify(-1.25e12, lang="fr", decimals=1), "-1\u202f250,0 Md")


class ApplyAmountAxisTest(unittest.TestCase):
    def test_stacked_bars_are_ranged_on_their_summed_stack(self):
        fig = go.Figure([
            go.Bar(x=[2021, 2022], y=[600e9, 700e9]),
            go.Bar(x=[2021, 2022], y=[500e9, 600e9]),
        ])
        fig.update_layout(barmode="stack")
        apply_amount_axis(fig, "yaxis", lang="fr")
        # The 2022 stack reaches 1 300 Md; a single bar never passes 700 Md.
        self.assertGreaterEqual(max(fig.layout.yaxis.tickvals), 1.3e12)
        self.assertEqual(fig.layout.yaxis.tickmode, "array")

    def test_stacked_negatives_sum_apart_from_positives(self):
        fig = go.Figure([
            go.Bar(x=[2021], y=[300e9]),
            go.Bar(x=[2021], y=[-200e9]),
            go.Bar(x=[2021], y=[-150e9]),
        ])
        fig.update_layout(barmode="relative")
        apply_amount_axis(fig, "yaxis", lang="fr")
        self.assertLessEqual(min(fig.layout.yaxis.tickvals), -350e9)
        self.assertGreaterEqual(max(fig.layout.yaxis.tickvals), 300e9)

    def test_grouped_bars_are_ranged_on_each_bar(self):
        fig = go.Figure([
            go.Bar(x=[2021], y=[600e9]),
            go.Bar(x=[2021], y=[500e9]),
        ])
        fig.update_layout(barmode="group")
        apply_amount_axis(fig, "yaxis", lang="fr")
        self.assertLess(max(fig.layout.yaxis.tickvals), 1e12)

    def test_secondary_axis_reads_only_its_own_traces(self):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=[2021, 2022], y=[40, 60]), secondary_y=False)
        fig.add_trace(go.Scatter(x=[2021, 2022], y=[100e9, 240e9]), secondary_y=True)
        apply_amount_axis(fig, "yaxis2", lang="fr")
        self.assertEqual(fig.layout.yaxis2.ticktext[-1], "250 Md")
        self.assertIsNone(fig.layout.yaxis.tickvals)

    def test_horizontal_bars_label_the_x_axis(self):
        fig = go.Figure([go.Bar(y=["A", "B"], x=[100e9, 430e9], orientation="h")])
        apply_amount_axis(fig, "xaxis", lang="fr")
        self.assertEqual(fig.layout.xaxis.ticktext[-1], "500 Md")
        self.assertIsNone(fig.layout.yaxis.tickvals)

    def test_an_explicit_range_sets_the_span(self):
        fig = go.Figure([go.Scatter(x=[2021], y=[10_000])])
        fig.update_yaxes(range=[0, 24_000])
        apply_amount_axis(fig, "yaxis", lang="fr")
        self.assertGreaterEqual(max(fig.layout.yaxis.tickvals), 24_000)

    def test_missing_points_are_skipped(self):
        fig = go.Figure([
            go.Scatter(x=[None], y=[None]),
            go.Scatter(x=[2021, 2022], y=[None, 80e9]),
        ])
        apply_amount_axis(fig, "yaxis", lang="fr")
        self.assertEqual(fig.layout.yaxis.ticktext[-1], "80 Md")

    def test_an_axis_without_data_is_left_alone(self):
        fig = go.Figure([go.Scatter(x=[2021], y=[5])])
        apply_amount_axis(fig, "yaxis2", lang="fr")
        self.assertNotIn("yaxis2", fig.layout)


class ApplyAmountColorbarTest(unittest.TestCase):
    def test_colorbar_ticks_cover_the_color_range(self):
        fig = go.Figure(go.Choroplethmapbox(z=[17_500, 27_800], locations=["A", "B"], coloraxis="coloraxis"))
        fig.update_layout(coloraxis=dict(cmin=17_000, cmax=28_000))
        apply_amount_colorbar(fig, lang="fr")
        colorbar = fig.layout.coloraxis.colorbar
        self.assertEqual(colorbar.tickmode, "array")
        self.assertTrue(all(17_000 <= v <= 28_000 for v in colorbar.tickvals))
        self.assertEqual(colorbar.ticktext[0], "18 k")

    def test_colorbar_falls_back_to_the_data_range(self):
        fig = go.Figure(go.Choroplethmapbox(z=[2_300, 5_800], locations=["A", "B"], coloraxis="coloraxis"))
        apply_amount_colorbar(fig, lang="fr")
        colorbar = fig.layout.coloraxis.colorbar
        self.assertTrue(all(2_300 <= v <= 5_800 for v in colorbar.tickvals))
        self.assertTrue(all(label.endswith(" k") for label in colorbar.ticktext))


if __name__ == "__main__":
    unittest.main()
