import io
import warnings

import Vision
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from elasticapm import capture_span

warnings.filterwarnings("ignore")


class OCR:
	def __init__(
			self,
			image: any = None,
			pdf_path: str = None,
			format: any = "PNG",
			usesLanguageCorrection: bool = False,
			customWords: list[str] = None,
			recognitionLevel: str = "accurate",
			recognitionLanguages: list[str] = ["en"]
	) -> None:
		"""
		OCR class to extract text from images or PDFs.

		Parameters
		----------
		image : object, optional
			The input image to be converted.
		pdf_path : str, optional
			The path to the PDF file to be processed.
		format : str, optional
			The format of the image.
		usesLanguageCorrection : bool, optional
			Whether to use language correction.
		customWords : list[str], optional
			Custom words to improve recognition.
		recognitionLevel : str, optional
			The level of recognition accuracy ('fast' or 'accurate').
		recognitionLanguages : list[str], optional
			List of languages for text recognition.
		"""
		self.image = image
		self.pdf_path = pdf_path
		self.res = None
		self.format = format
		self.data = []
		self.dataframe = None
		self.usesLanguageCorrection = usesLanguageCorrection
		self.customWords = customWords
		self.recognitionLevel = recognitionLevel
		self.recognitionLanguages = recognitionLanguages

	@capture_span(name="recognize")
	def recognize(self) -> any:
		"""Perform text recognition using Apple's Vision framework."""
		if self.pdf_path:
			images = self.extract_images_from_pdf(self.pdf_path)
			results = []
			for page_num, img in enumerate(images, start=1):
				self.image = img
				page_width, page_height = img.size
				results.append({
					"page": page_num,
					"page_width": round(page_width, 2),
					"page_height": round(page_height, 2),
					"results": self.process_image()
				})
			return results
		else:
			page_width, page_height = self.image.size
			return [{
				"page": 1,
				"page_width": round(page_width, 2),
				"page_height": round(page_height, 2),
				"results": self.process_image()
			}]

	@capture_span(name="process_image")
	def process_image(self) -> any:
		buffer = self.imageToBuffer(self.image)

		request_handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(
			buffer, None
		)

		request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(self.completionHandler)

		# Ensure recognitionLevel is set correctly
		if self.recognitionLevel in ["fast", "accurate"]:
			if self.recognitionLevel == "fast":
				request.setRecognitionLevel_(1)
			else:
				request.setRecognitionLevel_(0)

		else:
			raise ValueError("Invalid recognitionLevel. Use 'fast' or 'accurate'.")

		# Ensure recognitionLanguages is a list of strings
		if isinstance(self.recognitionLanguages, list) and all(
				isinstance(lang, str) for lang in self.recognitionLanguages):
			request.setRecognitionLanguages_(self.recognitionLanguages)
		else:
			raise ValueError("recognitionLanguages must be a list of strings.")

		# Ensure usesLanguageCorrection is a boolean
		if isinstance(self.usesLanguageCorrection, bool):
			request.setUsesLanguageCorrection_(self.usesLanguageCorrection)
		else:
			raise ValueError("usesLanguageCorrection must be a boolean.")

		request_handler.performRequests_error_([request], None)

		try:
			for observation in request.results():
				bbox = observation.boundingBox()
				w, h = bbox.size.width * 100, bbox.size.height * 100
				x, y = bbox.origin.x * 100, bbox.origin.y * 100
				self.data.append((observation.text(), observation.confidence(), [x, y, w, h]))

		except:
			pass

		self.dealloc(request, request_handler)

		content, confidences, bbox = zip(*self.data)

		w = [w for (x, y, w, h) in bbox]
		h = [h for (x, y, w, h) in bbox]
		x = [x for (x, y, w, h) in bbox]
		y = [y for (x, y, w, h) in bbox]

		text_areas = np.array(w) * np.array(h)
		total_area = 100 * 100
		densities = text_areas / total_area

		result = []
		for i in range(len(content)):
			result.append({
				"content": content[i],
				"length": round(w[i], 4),
				"width": round(h[i], 4),
				"density": round(float(densities[i]), 4),
				"bbox": {
					"x_pct": round(x[i], 4),
					"y_pct": round(y[i], 4),
					"w_pct": round(w[i], 4),
					"h_pct": round(h[i], 4)
				},
			})

		return result

	@capture_span(name="imageToBuffer")
	def imageToBuffer(self, image: any) -> any:
		"""
		Convert a PIL image to bytes.

		Parameters
		----------
		image : object
			The input image to be converted.

		Returns
		-------
		bytes
			The image data in bytes.
		"""
		buffer = io.BytesIO()
		image.save(buffer, format=self.format)

		return buffer.getvalue()

	@capture_span(name="completionHandler")
	def completionHandler(self, request: any, error: any) -> None:
		"""
		Handle completion of text recognition request.

		This method processes the results of a text recognition request
		and extracts recognized text and its confidence levels.

		Parameters
		----------
		request : object
			The text recognition request object.

		error : object
			Error object, if any.

		Returns
		-------
		None
		"""
		observations = request.results()
		results = []

		try:
			for observation in observations:
				recognized_text = observation.topCandidates_(1)[0]
				results.append([recognized_text.string(), recognized_text.confidence()])
		except:
			pass

		return None

	@capture_span(name="dealloc")
	def dealloc(self, request: any, request_handler: any) -> None:
		"""
		Clean up and deallocate resources.

		This method is responsible for releasing allocated resources and performing essential
		cleanup operations related to text recognition tasks.

		Parameters
		----------
		request : object
			The text recognition request object.

		request_handler : object
			The image request handler object.

		Returns
		-------
		None
		"""
		request.dealloc()
		request_handler.dealloc()

		return None

	@capture_span(name="extract_images_from_pdf")
	def extract_images_from_pdf(self, pdf_path: str) -> list:
		"""
		Extract images from a PDF file.

		Parameters
		----------
		pdf_path : str
			The path to the PDF file.

		Returns
		-------
		list
			A list of PIL images extracted from the PDF.
		"""
		doc = fitz.open(pdf_path)
		images = []
		for page_num in range(len(doc)):
			page = doc.load_page(page_num)
			pix = page.get_pixmap()
			img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
			images.append(img)
		return images
