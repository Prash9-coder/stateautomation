import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import cv2
import numpy as np

class OCRHandler:
    def extract_from_page(self, pdf_path: str, page_num: int) -> str:
        """Extract text from scanned PDF page using OCR"""
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        
        # Render page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
        img_data = pix.tobytes("png")
        
        # Convert to PIL Image
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Preprocess image for better OCR
        image = self._preprocess_image(image)
        
        # Extract text
        text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
        
        doc.close()
        return text
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR accuracy"""
        # Convert to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        # Convert back to PIL
        return Image.fromarray(denoised)