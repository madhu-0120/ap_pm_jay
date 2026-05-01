import cv2
import numpy as np

def detect(image):
    """
    Detects copy-paste forgery using ORB feature matching for repeated regions.
    Uses keypoint clustering to merge nearby detections into coherent bounding boxes.
    """
    results = []
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    orb = cv2.ORB_create(nfeatures=1000)
    kp, des = orb.detectAndCompute(gray, None)

    if des is None or len(kp) < 10:
        return results

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(des, des, k=2)

    suspicious_points = []
    for m, n in matches:
        if m.distance < 0.15 * n.distance and m.queryIdx != m.trainIdx:
            pt1 = kp[m.queryIdx].pt
            pt2 = kp[m.trainIdx].pt
            dist = np.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)
            if dist > 30:
                suspicious_points.append(pt1)
                suspicious_points.append(pt2)

    if not suspicious_points:
        return results

    # Cluster nearby points into bounding boxes
    points = np.array(suspicious_points, dtype=np.float32)
    # Use simple grid-based clustering
    clusters = {}
    cell_size = 60
    for pt in points:
        key = (int(pt[0] // cell_size), int(pt[1] // cell_size))
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(pt)

    for key, pts in clusters.items():
        pts_arr = np.array(pts)
        x_min = int(np.min(pts_arr[:, 0])) - 10
        y_min = int(np.min(pts_arr[:, 1])) - 10
        x_max = int(np.max(pts_arr[:, 0])) + 10
        y_max = int(np.max(pts_arr[:, 1])) + 10
        w = x_max - x_min
        h = y_max - y_min
        if w > 15 and h > 15:
            results.append({
                "box": [max(0, x_min), max(0, y_min), w, h],
                "type": "Copy-Paste Forgery",
                "severity": 3,
                "explanation": f"Identical visual patterns detected in repeated regions ({len(pts)} matching keypoints), suggesting a copy-paste operation was performed."
            })

    return results[:5]
