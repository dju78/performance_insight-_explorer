"""Assessment Brief Extractor Module.
Extracts business requirements, questions, and constraints from assessment documents (.docx, .pdf, .txt).
Ensures briefs are never profiled as operational tabular data.
"""
import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union


def extract_docx_text(file_source: Union[str, io.BytesIO, bytes, Any]) -> str:
    """Extract plain text from a .docx file using standard zipfile XML parsing."""
    try:
        bio: io.BytesIO
        if isinstance(file_source, (str, os.PathLike)):
            with open(file_source, "rb") as f:
                bio = io.BytesIO(f.read())
        elif isinstance(file_source, (bytes, bytearray)):
            bio = io.BytesIO(file_source)
        elif hasattr(file_source, "getvalue"):
            bio = io.BytesIO(file_source.getvalue())
        elif hasattr(file_source, "read"):
            bio = io.BytesIO(file_source.read())
        else:
            bio = file_source

        bio.seek(0)
        with zipfile.ZipFile(bio, "r") as z:
            if "word/document.xml" not in z.namelist():
                return ""
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            
            # Namespace for WordprocessingML
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            
            paragraphs = []
            for p in tree.findall(".//w:p", ns):
                texts = [node.text for node in p.findall(".//w:t", ns) if node.text]
                if texts:
                    paragraphs.append("".join(texts))
            
            return "\n\n".join(paragraphs)
    except Exception as e:
        return f"Error extracting DOCX text: {str(e)}"


def extract_pdf_text(file_source: Union[str, io.BytesIO, bytes, Any]) -> str:
    """Extract plain text from a .pdf file if libraries are available, with safe fallback."""
    try:
        bio: io.BytesIO
        if isinstance(file_source, (str, os.PathLike)):
            with open(file_source, "rb") as f:
                bio = io.BytesIO(f.read())
        elif isinstance(file_source, (bytes, bytearray)):
            bio = io.BytesIO(file_source)
        elif hasattr(file_source, "getvalue"):
            bio = io.BytesIO(file_source.getvalue())
        else:
            bio = file_source

        bio.seek(0)
        
        # Try pypdf / pypdf2
        try:
            import pypdf
            reader = pypdf.PdfReader(bio)
            text_pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(text_pages)
        except ImportError:
            pass

        try:
            from pypdf import PdfReader
            reader = PdfReader(bio)
            text_pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(text_pages)
        except ImportError:
            pass

        # Fallback raw byte extraction for plain text streams
        bio.seek(0)
        raw = bio.read()
        extracted = []
        for match in re.finditer(rb"\((.*?)\)Tj|\[(.*?)\]TJ", raw):
            extracted.append(match.group(0).decode("latin1", errors="ignore"))
        if extracted:
            return "\n".join(extracted[:50])
        return "PDF text extraction requires pypdf library. Please paste the brief text directly."
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"


def extract_plain_text(file_source: Union[str, io.BytesIO, bytes, Any]) -> str:
    """Extract text from plain text / markdown files."""
    try:
        raw_bytes: bytes
        if isinstance(file_source, (str, os.PathLike)):
            with open(file_source, "rb") as f:
                raw_bytes = f.read()
        elif isinstance(file_source, (bytes, bytearray)):
            raw_bytes = bytes(file_source)
        elif hasattr(file_source, "getvalue"):
            raw_bytes = file_source.getvalue()
        elif hasattr(file_source, "read"):
            raw_bytes = file_source.read()
        else:
            return str(file_source)

        for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
            try:
                return raw_bytes.decode(enc)
            except Exception:
                continue
        return raw_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error reading text file: {str(e)}"


def parse_questions_from_text(text: str) -> List[str]:
    """Parse discrete questions or requirements from document text."""
    if not text or not text.strip():
        return []

    # First check if text has explicit numbered lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    line_matches = [line for line in lines if re.match(r"^(?:Question\s*#?\s*\d+|Q\d+[:.]?|\b\d+\.\s+)", line, re.IGNORECASE)]
    if len(line_matches) >= 2:
        return line_matches

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    questions = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        if p in ["Question #", "Question", "Assessment Brief", "Assessment Requirements"]:
            i += 1
            continue
        if p.isdigit() and i + 1 < len(paragraphs):
            num = p
            q_text = paragraphs[i + 1]
            questions.append(f"Question {num}: {q_text}")
            i += 2
            continue
        elif re.match(r"^(?:Question\s*#?\s*\d+|Q\d+[:.]?|\b\d+\.\s+)", p, re.IGNORECASE):
            questions.append(p)
        elif len(p) > 25:
            questions.append(p)
        i += 1

    if not questions:
        for line in lines:
            if len(line) > 15:
                questions.append(line)

    return questions


def extract_assessment_brief(
    file_source: Union[str, io.BytesIO, bytes, Any],
    filename: str = "brief.docx"
) -> Dict[str, Any]:
    """Extract and parse assessment brief from document."""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in [".docx", ".doc"]:
        raw_text = extract_docx_text(file_source)
    elif ext == ".pdf":
        raw_text = extract_pdf_text(file_source)
    else:
        raw_text = extract_plain_text(file_source)

    questions = parse_questions_from_text(raw_text)

    return {
        "filename": filename,
        "raw_text": raw_text,
        "questions": questions,
        "question_count": len(questions),
        "is_assessment_brief": True
    }
