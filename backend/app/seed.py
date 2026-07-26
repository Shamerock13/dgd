from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Brand, Fragrance, TwinMatch

def seed_database(db: Session) -> None:
    if db.scalar(select(Brand.id).limit(1)):
        return

    brands = {
        name: Brand(name=name, country=country)
        for name, country in [
            ("Dior", "Frankreich"),
            ("Lattafa", "Vereinigte Arabische Emirate"),
            ("Tom Ford", "USA"),
            ("Maison Alhambra", "Vereinigte Arabische Emirate"),
            ("Lalique", "Frankreich"),
        ]
    }
    db.add_all(brands.values())
    db.flush()

    fragrances = [
        Fragrance(
            name="Sauvage Elixir", brand=brands["Dior"], year=2021, gender="Herren",
            concentration="Elixir", perfumer="François Demachy", price_eur=165,
            description="Dicht, würzig und aromatisch mit markanter Lavendel- und Gewürzsignatur.",
            top_notes="Muskatnuss, Zimt, Kardamom, Grapefruit",
            heart_notes="Lavendel", base_notes="Süßholz, Sandelholz, Amber, Patchouli, Vetiver",
            accords="würzig, aromatisch, holzig, warm", longevity=9.3, projection=9.0,
            sweetness=5.6, freshness=4.2
        ),
        Fragrance(
            name="Asad", brand=brands["Lattafa"], year=2021, gender="Herren",
            concentration="Eau de Parfum", price_eur=29,
            description="Würzig-süße Alternative mit Vanille, Amber und dunkler Wärme.",
            top_notes="Schwarzer Pfeffer, Tabak, Ananas",
            heart_notes="Patchouli, Kaffee, Iris", base_notes="Vanille, Amber, trockene Hölzer, Benzoin",
            accords="würzig, vanillig, warm, amber", longevity=8.0, projection=7.4,
            sweetness=7.2, freshness=2.8
        ),
        Fragrance(
            name="Ombré Leather", brand=brands["Tom Ford"], year=2018, gender="Unisex",
            concentration="Eau de Parfum", price_eur=145,
            description="Trockenes, elegantes Leder mit Jasmin und warmer Amberbasis.",
            top_notes="Kardamom", heart_notes="Leder, Jasmin-Sambac",
            base_notes="Amber, Moos, Patchouli", accords="leder, animalisch, warm, blumig",
            longevity=8.6, projection=8.0, sweetness=3.0, freshness=2.4
        ),
        Fragrance(
            name="Amber & Leather", brand=brands["Maison Alhambra"], gender="Unisex",
            concentration="Eau de Parfum", price_eur=25,
            description="Preisgünstige Lederinterpretation mit würzigerem und etwas kantigerem Auftakt.",
            top_notes="Kardamom", heart_notes="Leder, Jasmin",
            base_notes="Amber, Moos, Patchouli", accords="leder, würzig, amber, dunkel",
            longevity=7.5, projection=7.1, sweetness=3.4, freshness=2.1
        ),
        Fragrance(
            name="Encre Noire", brand=brands["Lalique"], year=2006, gender="Herren",
            concentration="Eau de Toilette", perfumer="Nathalie Lorson", price_eur=28,
            description="Dunkler, erdiger Vetiverduft mit Zypresse und moschusartigem Holz.",
            top_notes="Zypresse", heart_notes="Vetiver", base_notes="Kaschmirholz, Moschus",
            accords="holzig, erdig, vetiver, trocken", longevity=7.0, projection=6.0,
            sweetness=1.0, freshness=4.0
        ),
    ]
    db.add_all(fragrances)
    db.flush()

    db.add_all([
        TwinMatch(
            original=fragrances[0], alternative=fragrances[1], similarity=82,
            commonalities="Dunkle Würze, kräftige Projektion und warme Basis.",
            differences="Asad ist süßer und vanilliger; Sauvage Elixir wirkt aromatischer und feiner.",
            source_note="Demodatensatz – redaktionell noch zu prüfen."
        ),
        TwinMatch(
            original=fragrances[2], alternative=fragrances[3], similarity=86,
            commonalities="Dominantes Leder, Jasmin und warme Amber-Holz-Basis.",
            differences="Amber & Leather startet kantiger und ist weniger geschmeidig.",
            source_note="Demodatensatz – redaktionell noch zu prüfen."
        ),
    ])
    db.commit()
