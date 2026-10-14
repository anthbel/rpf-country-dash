"""The outcome charts of the « Répartition spatiale » tabs (education and health).

They read boost.expenditure_and_outcome_by_country_geo1_func_year: one row per
region, spending year and sector, with ``outcome_index`` — school attendance
for education, Global Data Lab's health index for health.
"""

import copy
import unittest
from unittest.mock import patch

import pandas as pd

from translations import t

with patch("dash.register_page"):
    from components import edu_health_across_space as space

REGIONS = ["Centrale", "Kara", "Maritime", "Plateaux", "Savanes"]
GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"country": "Togo", "region": region},
            "geometry": {"type": "Polygon", "coordinates": [[[i, 8], [i + 1, 8], [i + 1, 9], [i, 8]]]},
        }
        for i, region in enumerate(REGIONS)
    ],
}


def _rows(func, years, outcome):
    """Five regions and Central Scope for each spending year; ``outcome`` maps a
    spending year to (outcome_index base, outcome_year) or None."""
    rows = []
    for year in years:
        paired = outcome(year)
        for i, region in enumerate(REGIONS):
            rows.append({
                "country_name": "Togo", "year": year, "func": func, "adm1_name": region,
                "expenditure": 1e9 * (i + 1), "per_capita_expenditure": 1_000.0 * (i + 1),
                "outcome_index": None if paired is None else paired[0] + 0.01 * i,
                "outcome_year": None if paired is None else paired[1],
            })
        rows.append({
            "country_name": "Togo", "year": year, "func": func, "adm1_name": "Central Scope",
            "expenditure": 9e9, "per_capita_expenditure": None,
            "outcome_index": None, "outcome_year": None,
        })
    return pd.DataFrame(rows)


def _store(geo):
    values = {
        "basic_country_info": {"Togo": {"currency_code": "XOF", "display_lat": 8, "display_lon": 1, "zoom": 5}},
        "geo1_func_expenditure": geo,
        "subnat_boundaries": GEOJSON,
        "disputed_boundaries": {},
    }
    return (
        patch.object(space.server_store, "get", side_effect=lambda key: copy.deepcopy(values[key])),
        patch.object(space.server_store, "lookup",
                     side_effect=lambda key, default=None: copy.deepcopy(values.get(key, default))),
    )


def _health_exact_year():
    """The table before outcome_year: an outcome only where GDL has that year."""
    geo = _rows("Health", [2021, 2022, 2023, 2024], lambda y: (0.62, y) if y <= 2023 else None)
    return geo.drop(columns="outcome_year")


class HealthIndexNameTest(unittest.TestCase):
    """The health maps plot GDL's health index (life expectancy), not the UHC index."""

    def test_outcome_map_names_the_health_index(self):
        get, lookup = _store(_health_exact_year())
        with get, lookup:
            fig = space.update_hd_index_map(["d"], ["d"], "Togo", 2023, ["d"], "Health", "light", lang="fr")
        self.assertEqual(fig.layout.title.text, "Indice de santé (espérance de vie) au niveau infranational")
        self.assertIn("Indice de santé (espérance de vie)", fig.data[0].hovertemplate)

    def test_sankey_names_the_health_index(self):
        get, lookup = _store(_health_exact_year())
        with get, lookup:
            fig, narrative = space.render_func_subnat_rank(["d"], "Togo", 2023, "Health", "XOF", lang="fr")
        headers = [a.text for a in fig.layout.annotations]
        self.assertTrue(any("Indice de santé (espérance de vie)" in h for h in headers), headers)
        self.assertNotIn("CSU", " ".join(headers))
        self.assertIn("mesuré par l'indice de santé (espérance de vie)", narrative)

    def test_section_introduction_names_the_health_index(self):
        for lang, phrase in (("fr", "espérance de vie"), ("en", "life expectancy"), ("pt", "expectativa de vida")):
            with self.subTest(lang=lang):
                text = t("narrative.health_subnational_motivation", lang, country="le Togo", year=2023)
                self.assertIn(phrase, text)
                self.assertNotIn("CSU", text)
                self.assertNotIn("UHC", text)


if __name__ == "__main__":
    unittest.main()
