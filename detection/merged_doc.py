import cv2
import numpy as np

def detect(image):
    """
    Detects merged documents by comparing header vs body alignment, noise, and intensity.
    Documents merged from different sources often have different paper/background characteristics.
    """
    results = []
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h, w = gray.shape

    # Divide image into top (header) and bottom (body)
    header_end = int(h * 0.25)
    header = gray[0:header_end, :]
    body = gray[header_end:, :]

    # Check for sudden shifts in background intensity or noise patterns
    header_mean = np.mean(header)
    body_mean = np.mean(body)
    header_std = np.std(header)
    body_std = np.std(body)

    intensity_diff = abs(header_mean - body_mean)
    noise_diff = abs(header_std - body_std)

    if intensity_diff > 20 or noise_diff > 15:
        severity = 3 if intensity_diff > 35 else 2
        results.append({
            "box": [0, header_end - 10, w, 20],
            "type": "Merged Document",
            "severity": severity,
            "explanation": f"Significant shift in background characteristics detected at the header boundary (intensity difference: {intensity_diff:.1f}, noise difference: {noise_diff:.1f}), suggesting merging of different document sources."
        })

    return results
