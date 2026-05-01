import cv2
import numpy as np
import os

def preprocess_image(file_path, output_dir):
    """
    Handles PDF to Image conversion and basic image preprocessing.
    Returns: (gray_image, color_image, thresholded_image)
    """
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    # Handle PDF
    if ext == '.pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            if doc.page_count == 0:
                raise ValueError("No pages found in PDF.")
            # Process the first page
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=300) # Good quality for OCR
            temp_img_name = f"{os.path.splitext(filename)[0]}_p1.png"
            temp_img_path = os.path.join(output_dir, temp_img_name)
            pix.save(temp_img_path)
            img = cv2.imread(temp_img_path)
            doc.close()
        except ImportError:
            raise ValueError("PyMuPDF not installed. Install it with: pip install PyMuPDF")
        except Exception as e:
            raise ValueError(f"Failed to convert PDF: {str(e)}")
    else:
        img = cv2.imread(file_path)

    if img is None:
        raise ValueError("Could not read image file.")

    # Resize if too large (keep aspect ratio, max 2000px on longest side)
    h, w = img.shape[:2]
    max_dim = 2000
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Noise Removal (Gaussian Blur)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Sharpening
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    # 4. Thresholding (Otsu's)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return gray, img, thresh
