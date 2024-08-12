import os

from PIL import Image
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from processors.apple_ocr import OCR

main_bp = Blueprint('main', __name__)


@main_bp.route('/upload', methods=['POST'])
def upload_file():
	if "file" not in request.files:
		return jsonify({"error": "File not provided"}), 400
	file = request.files["file"]
	if file.filename == "":
		return jsonify({"error": "No selected file"}), 400
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		filepath = os.path.join("/tmp", filename)
		file.save(filepath)
		try:
			if filename.lower().endswith(".pdf"):
				ocr_instance = OCR(pdf_path=filepath)
			else:
				image = Image.open(filepath)
				ocr_instance = OCR(image=image)
			text_result = ocr_instance.recognize()
			os.remove(filepath)
			return jsonify({"texts": text_result}), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 500
	else:
		return jsonify({"error": "File type not supported"}), 400


def allowed_file(filename):
	ALLOWED_EXTENSIONS: set[str] = {'pdf', 'jpeg', 'jpg', 'png', 'gif'}
	return "." in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
