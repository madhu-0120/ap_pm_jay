import cv2

def extract_ocr_data(image):
    """
    Extracts text and bounding boxes using PyTesseract.
    Falls back gracefully if Tesseract is not installed.
    """
    try:
        import pytesseract
        from pytesseract import Output
        d = pytesseract.image_to_data(image, output_type=Output.DICT)

        ocr_results = []
        n_boxes = len(d['text'])
        for i in range(n_boxes):
            text = d['text'][i].strip()
            if text and int(d['conf'][i]) > 0:
                ocr_results.append({
                    'text': text,
                    'left': d['left'][i],
                    'top': d['top'][i],
                    'width': d['width'][i],
                    'height': d['height'][i],
                    'conf': d['conf'][i]
                })

        return ocr_results
    except ImportError:
        print("Warning: pytesseract not installed. OCR-based detection will be skipped.")
        return []
    except Exception as e:
        print(f"OCR Error: {e}")
        return []
