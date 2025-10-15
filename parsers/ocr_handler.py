try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional
    pytesseract = None  # type: ignore
from PIL import Image
try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional
    fitz = None  # type: ignore
try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional
    cv2 = None  # type: ignore
    np = None  # type: ignore

class OCRHandler:
    def extract_from_page(self, pdf_path: str, page_num: int) -> str:
        """Extract text from scanned PDF page using OCR"""
        if pytesseract is None or fitz is None:
            return ""  # OCR dependencies unavailable
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        # Render page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
        # Convert to PIL Image
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        # Preprocess image for better OCR
        image = self._preprocess_image(image)
        # Extract text
        text = pytesseract.image_to_string(image, lang='eng', config='--psm 6') if pytesseract else ""
        doc.close()
        return text
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR accuracy"""
        if cv2 is None or np is None:
            return image
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        denoised = cv2.fastNlMeansDenoising(thresh)
        return Image.fromarray(denoised)