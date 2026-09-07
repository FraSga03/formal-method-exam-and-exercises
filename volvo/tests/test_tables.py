from scripts.build_tables import latex_escape, latex_table


def test_table_has_a_tabular_environment():
    text = latex_table(["A", "B"], [["1", "2"]], "ll")

    assert text.startswith("\\begin{tabular}{ll}")
    assert text.rstrip().endswith("\\end{tabular}")
    assert "1 & 2" in text


def test_table_is_not_wrapped_in_a_float():
    """The document decides placement and captions, not the generator."""
    assert "\\begin{table}" not in latex_table(["A"], [["1"]], "l")


def test_special_characters_are_escaped():
    escaped = latex_escape("Accepted+Wait_User & 50%")

    assert "\\_" in escaped
    assert "\\&" in escaped
    assert "\\%" in escaped


def test_escaping_is_applied_to_cells():
    assert "\\_" in latex_table(["A"], [["a_b"]], "l")
