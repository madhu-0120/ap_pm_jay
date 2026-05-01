import numpy as np

def detect(ocr_data):
    """
    Detects spacing anomalies using OCR word spacing analysis.
    Abnormal gaps between words can indicate content insertion or deletion.
    """
    results = []
    if not ocr_data:
        return results

    # Group OCR data by lines (approximate by y-coordinate)
    lines = {}
    for item in ocr_data:
        y = item['top']
        line_key = round(y / 15) * 15
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(item)

    for line_y in lines:
        line_words = sorted(lines[line_y], key=lambda x: x['left'])
        spacings = []
        for i in range(len(line_words) - 1):
            space = line_words[i + 1]['left'] - (line_words[i]['left'] + line_words[i]['width'])
            if 0 < space < 500:
                spacings.append((space, line_words[i], line_words[i + 1]))

        if not spacings:
            continue

        all_spaces = [s[0] for s in spacings]
        avg_spacing = np.mean(all_spaces)
        std_spacing = np.std(all_spaces)

        for space, word1, word2 in spacings:
            if std_spacing > 0 and space > avg_spacing + 3 * std_spacing and space > 30:
                results.append({
                    "box": [word1['left'] + word1['width'], word1['top'], int(space), word1['height']],
                    "type": "Spacing Anomaly",
                    "severity": 1,
                    "explanation": f"Abnormal gap of {space}px detected between words '{word1['text']}' and '{word2['text']}', which may indicate text deletion or manual character insertion."
                })

    return results[:5]
