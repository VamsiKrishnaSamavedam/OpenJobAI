from io import BytesIO

from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF resume.
    """

    pdf_file = BytesIO(file_bytes)
    reader = PdfReader(pdf_file)

    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text from a DOCX resume.
    """

    docx_file = BytesIO(file_bytes)
    document = Document(docx_file)

    text_parts = []

    for paragraph in document.paragraphs:
        if paragraph.text:
            text_parts.append(paragraph.text)

    return "\n".join(text_parts)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extracts text from a TXT resume.
    """

    return file_bytes.decode("utf-8", errors="ignore")


def parse_resume_file(filename: str, file_bytes: bytes) -> str:
    """
    Detects the resume file type and extracts text from it.

    Supported file types:
    - PDF
    - DOCX
    - TXT
    """

    filename = filename.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    if filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    if filename.endswith(".txt"):
        return extract_text_from_txt(file_bytes)

    raise ValueError("Unsupported file type. Please upload PDF, DOCX, or TXT.")