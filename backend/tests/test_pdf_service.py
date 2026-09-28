import pytest

from app.pdf.service import PDFService, PDFValidationError
from tests.fixtures.pdf_fixtures import make_empty_pdf, make_invalid_pdf, make_pdf


def test_validate_pdf_accepts_valid_pdf():
    PDFService().validate_pdf(make_pdf(num_pages=1))


def test_validate_pdf_rejects_invalid_bytes():
    with pytest.raises(PDFValidationError):
        PDFService().validate_pdf(make_invalid_pdf())


def test_validate_pdf_rejects_empty_bytes():
    with pytest.raises(PDFValidationError):
        PDFService().validate_pdf(b"")


def test_validate_pdf_rejects_zero_page_pdf():
    with pytest.raises(PDFValidationError):
        PDFService().validate_pdf(make_empty_pdf())


def test_get_page_count_multi_page():
    data = make_pdf(num_pages=5)
    assert PDFService().get_page_count(data) == 5


def test_render_page_returns_png_bytes():
    data = make_pdf(num_pages=2)
    png = PDFService().render_page(data, 1)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_page_out_of_range_raises():
    data = make_pdf(num_pages=1)
    with pytest.raises(PDFValidationError):
        PDFService().render_page(data, 2)


def test_render_all_pages_returns_one_image_per_page():
    data = make_pdf(num_pages=3)
    images = PDFService().render_all_pages(data)
    assert len(images) == 3
    for img in images:
        assert img[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_dpi_affects_image_size():
    data = make_pdf(num_pages=1)
    small = PDFService(render_dpi=72).render_page(data, 1)
    large = PDFService(render_dpi=300).render_page(data, 1)
    assert len(large) > len(small)
