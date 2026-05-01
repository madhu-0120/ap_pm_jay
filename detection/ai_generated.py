import cv2
import numpy as np

def detect(image):
    """
    Approximates AI-generated document detection by looking for overly clean image signatures.
    Checks for: no noise, perfect alignment, uniform font characteristics.
    This is NOT AI-based — it uses statistical analysis of image properties.
    """
    results = []
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h, w = gray.shape

    # 1. Noise Analysis
    # Real scans/photos have sensor noise or paper grain. AI/Digital exports are "perfect".
    mean, stddev = cv2.meanStdDev(gray)
    std_val = stddev[0][0]

    # 2. Edge Analysis — check for unnaturally perfect horizontal/vertical lines
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=w // 2, maxLineGap=5)

    # 3. Histogram uniformity — AI-generated docs often have very uniform intensity distribution
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_std = np.std(hist)

    flags = []
    if std_val < 35:
        flags.append("low noise variance")
    if lines is not None and len(lines) > 10:
        flags.append("excessive perfectly straight lines")
    if hist_std < 50:
        flags.append("unnaturally uniform intensity distribution")

    if len(flags) >= 1 and std_val < 35:
        results.append({
            "box": [10, 10, w - 20, 40],
            "type": "AI Generated Approximation",
            "severity": 1,
            "explanation": f"Document lacks natural paper grain and sensor noise. Detected indicators: {', '.join(flags)}. Overly uniform structure suggests digital/AI synthesis rather than a physical scan."
        })

    return results
