import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
DOCX_SUFFIXES = {".docx"}
PPTX_SUFFIXES = {".pptx"}
PDF_SUFFIXES = {".pdf"}
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def effective_suffix(source, filename_hint=None):
    for value in (filename_hint, source):
        suffix = Path(value or "").suffix.lower()
        if suffix:
            return suffix
    return ""


def extract_asset_text(path, mime_type=None, filename_hint=None):
    source = Path(path or "")
    if not source.exists() or not source.is_file():
        return "", "source file not found"

    suffix = effective_suffix(source, filename_hint)
    mime = mime_type or ""
    if suffix in TEXT_SUFFIXES or (mime_type or "").startswith("text/"):
        return read_text(source), ""
    if suffix in DOCX_SUFFIXES or mime == DOCX_MIME or looks_like_docx(source):
        return extract_docx_text(source), ""
    if suffix in PPTX_SUFFIXES or mime == PPTX_MIME or looks_like_pptx(source):
        return extract_pptx_text(source), ""
    if suffix in PDF_SUFFIXES or mime == "application/pdf":
        return extract_pdf_text(source)
    return "", "text extraction is not supported for this file type"


def read_text(path):
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_docx_text(path):
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", ns):
        pieces = [node.text or "" for node in paragraph.findall(".//w:t", ns)]
        text = "".join(pieces).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def looks_like_docx(path):
    try:
        with zipfile.ZipFile(path) as archive:
            return "word/document.xml" in archive.namelist()
    except Exception:
        return False


def looks_like_pptx(path):
    try:
        with zipfile.ZipFile(path) as archive:
            return any(name.startswith("ppt/slides/slide") and name.endswith(".xml") for name in archive.namelist())
    except Exception:
        return False


def extract_pptx_text(path):
    slides = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name for name in archive.namelist()
            if re.match(r"ppt/slides/slide\d+\.xml$", name)
        )
        for name in names:
            root = ElementTree.fromstring(archive.read(name))
            texts = [
                node.text or ""
                for node in root.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}t")
            ]
            slide_text = "\n".join(item.strip() for item in texts if item.strip())
            if slide_text:
                slides.append(slide_text)
    return "\n\n".join(slides)


def extract_pdf_text(path):
    try:
        from pypdf import PdfReader
    except Exception:
        return "", "PDF text extraction requires pypdf"
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages), ""


def summarize_text(text, limit=160):
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
