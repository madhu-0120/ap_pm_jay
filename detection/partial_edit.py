def detect(ocr_data):
    """
    Detects partial edits (name/date changes) by checking for font misalignment.
    Modified text often has slight vertical offset from the original baseline.
    """
    results = []
    if not ocr_data:
        return results

    # Group by line
    lines = {}
    for item in ocr_data:
        y_center = item['top'] + item['height'] / 2
        line_key = round(y_center / 10) * 10
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(item)

    for line_y in lines:
        line_words = lines[line_y]
        if len(line_words) < 2:
            continue

        # Check for vertical misalignment within a line
        tops = [w['top'] for w in line_words]
        heights = [w['height'] for w in line_words]
        most_common_top = max(set(tops), key=tops.count)
        avg_height = sum(heights) / len(heights)

        for word in line_words:
            vertical_shift = abs(word['top'] - most_common_top)
            height_diff = abs(word['height'] - avg_height)
            # If a word is vertically shifted or has different height
            if vertical_shift > 4 or height_diff > avg_height * 0.3:
                results.append({
                    "box": [word['left'], word['top'], word['width'], word['height']],
                    "type": "Partial Modification",
                    "severity": 3,
                    "explanation": f"Text '{word['text']}' shows vertical misalignment ({vertical_shift}px shift) from baseline. Modified text often shows slight offset from the original document's text baseline."
                })

    return results[:5]
