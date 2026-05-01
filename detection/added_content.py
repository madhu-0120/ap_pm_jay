import cv2
import numpy as np

def detect(image):
    """
    Detects added content (stamps, signatures, text) by looking for edge density anomalies.
    Uses Canny edge detection + contour analysis to find isolated high-detail regions.
    """
    results = []
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Canny edge detection
    edges = cv2.Canny(gray, 100, 200)

    # Kernel for dilation to group edges
    kernel = np.ones((15, 15), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h_img, w_img = gray.shape
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Look for large, isolated objects like stamps or signatures
        if 80 < w < int(w_img * 0.5) and 80 < h < int(h_img * 0.5):
            # Check edge density in the ROI
            roi_edges = edges[y:y + h, x:x + w]
            edge_density = np.sum(roi_edges > 0) / (w * h)
            if 0.05 < edge_density < 0.6:
                results.append({
                    "box": [x, y, w, h],
                    "type": "Added Content",
                    "severity": 3,
                    "explanation": "Isolated region with high edge complexity detected, possibly an inserted stamp, seal, signature, or text block that was added after original creation."
                })

    return results[:4]
