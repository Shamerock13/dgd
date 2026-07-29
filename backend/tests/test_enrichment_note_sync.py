from app.enrichment_finding_routes import _note_names


def test_note_names_accepts_list_and_removes_duplicates():
    assert _note_names(["Kardamom", " Toffee ", "kardamom", "Amberholz"]) == [
        "Kardamom",
        "Toffee",
        "Amberholz",
    ]


def test_note_names_splits_legacy_text_values():
    assert _note_names("Kardamom, Toffee; Amberholz\nVanille") == [
        "Kardamom",
        "Toffee",
        "Amberholz",
        "Vanille",
    ]
