import cv2
import numpy as np

def detect(image):
    """
    Detects removed/erased content by identifying unnaturally smooth patches.
    Areas where content was erased often lack the natural noise/texture of surrounding regions.
    """
    results = []
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Blur image and look for areas that are too "perfect"
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
    diff = cv2.absdiff(gray, blurred)

    # Threshold to find smooth areas (low diff means smooth)
    _, smooth_mask = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY_INV)

    # Clean up mask
    kernel = np.ones((20, 20), np.uint8)
    smooth_mask = cv2.morphologyEx(smooth_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(smooth_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Look for significant smooth patches in expected text areas
        if 40 < w < 500 and 20 < h < 100:
            results.append({
                "box": [x, y, w, h],
                "type": "Content Removed",
                "severity": 1,
                "explanation": "Unnaturally smooth patch detected in this region, suggesting potential erasure or background cloning to conceal original text or markings."
            })

    return results[:3]
