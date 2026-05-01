import cv2
import numpy as np

def detect(image):
    """
    Detects watermark removal by identifying patchy background intensity variations.
    Removed watermarks leave behind inconsistent background patterns.
    """
    results = []
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Enhance low-frequency variations
    blurred = cv2.GaussianBlur(gray, (51, 51), 0)
    diff = cv2.absdiff(gray, blurred)

    # If a watermark was removed, the background will have inconsistent variance
    _, thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)

    # Looking for large, faint blobs in the background
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 150 < w < 600 and 150 < h < 600:
            results.append({
                "box": [x, y, w, h],
                "type": "Watermark Removed",
                "severity": 1,
                "explanation": "Irregular background intensity patterns detected in a large area, indicating potential removal of a digital watermark, seal, or repeating background pattern."
            })

    return results[:2]
