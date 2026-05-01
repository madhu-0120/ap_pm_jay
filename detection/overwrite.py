import cv2
import numpy as np

def detect(image):
    """
    Detects overwriting by looking for high-intensity overlap and irregular strokes.
    Overwritten text tends to have denser ink concentration and overlapping contours.
    """
    results = []
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Use adaptive thresholding to highlight stroke details
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours of strokes
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Look for dense clusters of ink that might indicate overwriting
        if 10 < w < 150 and 10 < h < 100:
            roi = thresh[y:y + h, x:x + w]
            density = np.sum(roi) / (w * h * 255) * 255
            # Higher density threshold for overwriting
            if density > 180:
                results.append({
                    "box": [x, y, w, h],
                    "type": "Overwritten Text",
                    "severity": 2,
                    "explanation": "High ink density and irregular stroke patterns detected in this region, indicating potential text overwriting or character overlap."
                })

    return results[:5]
