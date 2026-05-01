import os
import time
import json
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import custom utilities

# Import detection modules
from detection import (
    copy_paste, overwrite, added_content, removed_content,
    merged_doc, watermark, spacing, partial_edit, ai_generated
)

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
CORS(app)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'outputs')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Color Mapping (BGR for OpenCV drawing)
COLOR_MAP = {
    'Partial Modification': (0, 0, 255),           # Red
    'Overwritten Text': (255, 0, 0),               # Blue
    'Copy-Paste Forgery': (0, 200, 0),             # Green
    'Content Removed': (0, 255, 255),              # Yellow
    'Added Content': (200, 0, 200),                # Purple
    'Watermark Removed': (19, 69, 139),            # Brown
    'Spacing Anomaly': (200, 200, 0),              # Teal
    'Merged Document': (128, 128, 128),            # Grey
    'AI Generated Approximation': (0, 165, 255)    # Orange
}


def save_to_history(data):
    """Save analysis result to persistent history file."""
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except Exception:
            history = []

    history.insert(0, data)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history[:50], f, indent=2)  # Keep last 50


def aggregate_results(image, gray, thresh, ocr_data):
    """Runs all detection modules and aggregates their findings."""
    all_issues = []

    # Run image-based modules
    all_issues.extend(copy_paste.detect(gray))
    all_issues.extend(overwrite.detect(gray))
    all_issues.extend(added_content.detect(gray))
    all_issues.extend(removed_content.detect(gray))
    all_issues.extend(merged_doc.detect(gray))
    all_issues.extend(watermark.detect(gray))
    all_issues.extend(ai_generated.detect(gray))

    # Run OCR-based modules
    all_issues.extend(spacing.detect(ocr_data))
    all_issues.extend(partial_edit.detect(ocr_data))

    return all_issues


def evaluate_decision(issues):
    """Evaluates aggregated issues to determine final status and confidence."""
    total_severity = sum(issue['severity'] for issue in issues)
    num_types = len(set(issue['type'] for issue in issues))

    status = "Genuine"
    if total_severity > 5 or num_types >= 3:
        status = "Forged"
    elif total_severity >= 1:
        status = "Suspicious"

    # Confidence: higher severity = higher confidence in the forgery finding
    if status == "Genuine":
        confidence = 96
    elif status == "Suspicious":
        confidence = min(100, 55 + total_severity * 8)
    else:
        confidence = min(100, 60 + total_severity * 5 + num_types * 5)

    return status, confidence


# ─── Routes ─────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle document upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    # Add timestamp to prevent collisions
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{int(time.time())}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({
        'success': True,
        'filename': filename,
        'url': f'/static/uploads/{filename}'
    })


@app.route('/verify', methods=['POST'])
def verify():
    """Run forensic analysis on uploaded document."""
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    start_time = time.time()

    try:
        # 1. Preprocessing
        gray, color_img, thresh = preprocessing.preprocess_image(filepath, app.config['OUTPUT_FOLDER'])

        # 2. OCR Data
        ocr_data = ocr_utils.extract_ocr_data(gray)

        # 3. Aggregation — run all detection modules
        issues = aggregate_results(color_img, gray, thresh, ocr_data)

        # 4. Decision Engine
        status, confidence = evaluate_decision(issues)

        # 5. Annotation — draw bounding boxes on image
        annotated_img = color_img.copy()
        for i, issue in enumerate(issues):
            x, y, w, h = issue['box']
            issue_type = issue['type']
            color_bgr = COLOR_MAP.get(issue_type, (255, 255, 255))

            # Clamp coordinates to image bounds
            img_h, img_w = annotated_img.shape[:2]
            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            # Draw rectangle
            cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color_bgr, 2)

            # Draw label badge with number
            badge_w = 28
            badge_h = 22
            badge_y = max(0, y - badge_h)
            cv2.rectangle(annotated_img, (x, badge_y), (x + badge_w, badge_y + badge_h), color_bgr, -1)
            cv2.putText(annotated_img, str(i + 1), (x + 6, badge_y + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        output_filename = f"verified_{filename}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        cv2.imwrite(output_path, annotated_img)

        elapsed = round(time.time() - start_time, 2)

        # Build type counts
        type_counts = {}
        for issue in issues:
            t = issue['type']
            type_counts[t] = type_counts.get(t, 0) + 1

        # Build conclusion text
        if status == "Forged":
            conclusion = f"Multiple types of tampering detected ({len(issues)} issues across {len(type_counts)} categories). Document integrity is compromised. Recommend immediate manual review by a senior forensic analyst."
        elif status == "Suspicious":
            conclusion = f"Minor anomalies detected ({len(issues)} issues). Document shows some irregularities that warrant further investigation. Manual verification recommended."
        else:
            conclusion = "Document appears to be original and untampered. No significant forgery indicators were detected by the rule-based analysis engine."

        result = {
            'status': status,
            'confidence': confidence,
            'issues': issues,
            'type_counts': type_counts,
            'conclusion': conclusion,
            'summary': {
                'total_issues': len(issues),
                'pages_analyzed': 1,
                'time_taken': f"{elapsed}s",
                'file_type': os.path.splitext(filename)[1].upper().lstrip('.')
            },
            'output_image': f'/static/outputs/{output_filename}',
            'original_image': f'/static/uploads/{filename}',
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }

        save_to_history(result)
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/history', methods=['GET'])
def get_history():
    """Return analysis history."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    """Download analyzed output file."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  MedVerify - Document Forensic Analysis System")
    print("  AI-Free Rule-Based Forgery Detection")
    print("=" * 60)
    print(f"  Server running at: http://localhost:5000")
    print(f"  Upload folder:     {UPLOAD_FOLDER}")
    print(f"  Output folder:     {OUTPUT_FOLDER}")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
