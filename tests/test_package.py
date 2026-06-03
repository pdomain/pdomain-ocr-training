import pdomain_ocr_training


def test_version_is_exposed():
    assert pdomain_ocr_training.__version__
    assert isinstance(pdomain_ocr_training.__version__, str)
    assert pdomain_ocr_training.__version__ != "0.2.1"
