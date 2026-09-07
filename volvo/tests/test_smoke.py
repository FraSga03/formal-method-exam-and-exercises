def test_package_imports():
    import volvo

    assert volvo is not None


def test_dependencies_available():
    import pm4py
    import flloat
    import gradio

    assert pm4py is not None
    assert flloat is not None
    assert gradio is not None
