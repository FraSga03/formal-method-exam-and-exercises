from scripts.build_figures import figures_for
from volvo.tests.test_anomalies import build


def test_every_figure_is_written(tmp_path):
    paths = figures_for(build({"1": "PQC", "2": "PC", "3": "PQUC"}), tmp_path)

    assert len(paths) >= 5
    for path in paths:
        assert path.exists()
        assert path.stat().st_size > 0


def test_figures_are_png(tmp_path):
    for path in figures_for(build({"1": "PQC", "2": "PC"}), tmp_path):
        assert path.suffix == ".png"
