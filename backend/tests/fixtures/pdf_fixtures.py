import pymupdf


def make_pdf(num_pages: int = 1, texts: list[str] | None = None) -> bytes:
    doc = pymupdf.open()
    for i in range(num_pages):
        page = doc.new_page()
        text = texts[i] if texts and i < len(texts) else f"Page {i + 1} sample content"
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def make_empty_pdf() -> bytes:
    """A structurally valid PDF with zero pages. PyMuPDF's writer refuses to
    save a zero-page document, so this is hand-written instead."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
        b"trailer<</Size 3/Root 1 0 R>>\n"
        b"%%EOF"
    )


def make_invalid_pdf() -> bytes:
    return b"this is not a real pdf file at all"
