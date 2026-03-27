"""
OCR + Document Text Extraction
Cascading fallback: PyMuPDF → pdfplumber → Tesseract OCR
"""


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using cascading strategy."""

    # Attempt 1: PyMuPDF (fast, handles most PDFs)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pages_text = [page.get_text() for page in doc]
        full_text = "\n".join(pages_text)
        doc.close()

        avg_chars = len(full_text) / max(len(pages_text), 1)
        if avg_chars > 100:
            return full_text.strip()
    except ImportError:
        print("[OCR] PyMuPDF not installed")
    except Exception as e:
        print(f"[OCR] PyMuPDF error: {e}")

    # Attempt 2: pdfplumber (better table/layout extraction)
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            if len(text.strip()) > 200:
                return text.strip()
    except ImportError:
        print("[OCR] pdfplumber not installed")
    except Exception as e:
        print(f"[OCR] pdfplumber error: {e}")

    # Attempt 3: OCR fallback (scanned PDF)
    try:
        import fitz
        import pytesseract
        from PIL import Image

        doc = fitz.open(file_path)
        ocr_text = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text.append(pytesseract.image_to_string(img))
        doc.close()

        return "\n".join(ocr_text).strip()
    except ImportError:
        print("[OCR] pytesseract or PIL not installed")
    except Exception as e:
        print(f"[OCR] Tesseract error: {e}")

    return ""
