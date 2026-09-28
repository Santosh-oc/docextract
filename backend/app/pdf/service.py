import io

import pymupdf as fitz


class PDFValidationError(Exception):
    pass


class PDFService:
    """PDF inspection and rendering, independent of any Vision Model provider."""

    def __init__(self, render_dpi: int = 150):
        self.render_dpi = render_dpi

    def validate_pdf(self, data: bytes) -> None:
        if not data:
            raise PDFValidationError("The uploaded file is empty.")
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:  # PyMuPDF raises varied exception types
            raise PDFValidationError("The uploaded file is not a valid PDF document.") from exc
        try:
            if doc.page_count == 0:
                raise PDFValidationError("The PDF document contains no pages.")
            if doc.is_encrypted and not doc.authenticate(""):
                raise PDFValidationError("The PDF document is password-protected.")
        finally:
            doc.close()

    def get_page_count(self, data: bytes) -> int:
        doc = fitz.open(stream=data, filetype="pdf")
        try:
            return doc.page_count
        finally:
            doc.close()

    def render_page(self, data: bytes, page_number: int, dpi: int | None = None) -> bytes:
        """Render a single 1-indexed page as PNG bytes."""
        dpi = dpi or self.render_dpi
        doc = fitz.open(stream=data, filetype="pdf")
        try:
            if page_number < 1 or page_number > doc.page_count:
                raise PDFValidationError(f"Page {page_number} does not exist in this document.")
            page = doc.load_page(page_number - 1)
            zoom = dpi / 72.0
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            return pix.tobytes("png")
        finally:
            doc.close()

    def render_all_pages(self, data: bytes, dpi: int | None = None) -> list[bytes]:
        dpi = dpi or self.render_dpi
        doc = fitz.open(stream=data, filetype="pdf")
        try:
            zoom = dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            images = []
            for page_number in range(doc.page_count):
                pix = doc.load_page(page_number).get_pixmap(matrix=matrix)
                images.append(pix.tobytes("png"))
            return images
        finally:
            doc.close()


def bytes_io(data: bytes) -> io.BytesIO:
    return io.BytesIO(data)
