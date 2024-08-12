import logging
import os
import shutil
from logging import Handler

import time
from PIL import Image
from elasticapm import capture_span
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from database import Database
from processors.apple_ocr import OCR

DIRECTORY_TO_WATCH = "/Volumes/epson_scans"
DIRECTORY_TO_MOVE_COMPLETED_TO = DIRECTORY_TO_WATCH + "/processed"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Watcher:
	def __init__(self):
		self.observer = Observer()

	def run(self):
		event_handler = Handler()
		self.observer.schedule(event_handler, DIRECTORY_TO_WATCH, recursive=False)
		self.observer.start()
		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			self.observer.stop()
		self.observer.join()


@capture_span(name="Handler")
class Handler(FileSystemEventHandler):
	@staticmethod
	def process_file(filepath: str) -> None:
		db = None
		try:
			db = Database()

			if filepath.lower().endswith(".pdf"):
				ocr_instance = OCR(pdf_path=filepath)
				filetype = "pdf"
			else:
				image = Image.open(filepath)
				ocr_instance = OCR(image=image)
				filetype = image.format.lower()

			pages = ocr_instance.recognize()

			# Insert into scanned_document
			document_id = db.insert_scanned_document(
				filename=filepath.split('/')[-1],
				filetype=filetype,
				current_path=filepath,
				original_path=filepath
			)

			# Insert into scanned_page and scanned_page_content
			for page in pages:
				page_id = db.insert_scanned_page(
					scanned_document_id=document_id,
					width=page['page_width'],
					height=page['page_height']
				)

				for result in page["results"]:
					db.insert_scanned_page_content(
						scanned_page_id=page_id,
						content=result['content'],
						bbox_h_pct=result['bbox']['h_pct'],
						bbox_w_pct=result['bbox']['w_pct'],
						bbox_x_pct=result['bbox']['x_pct'],
						bbox_y_pct=result['bbox']['y_pct'],
						density=result['density']
					)

			db.commit()
			logging.info(f"Processed {filepath}")
			shutil.move(filepath, DIRECTORY_TO_MOVE_COMPLETED_TO)
		except Exception as e:
			if db:
				db.rollback()
			logging.error(f"Error processing {filepath}: {e}")
		finally:
			if db:
				db.close()

	@staticmethod
	def wait_for_file_to_stabilize(filepath: str, wait_time: int = 5) -> bool:
		previous_size = -1
		while True:
			current_size = os.path.getsize(filepath)
			if current_size == previous_size:
				return True
			previous_size = current_size
			logging.info(f"Waiting for file {filepath} to stabilize...")
			time.sleep(wait_time)

	@capture_span(name="on_created")
	def on_created(self, event):
		if event.is_directory:
			return None
		elif event.src_path:
			logging.info(f"New file detected: {event.src_path}")
			if self.wait_for_file_to_stabilize(event.src_path):
				self.process_file(event.src_path)


@capture_span(name="process_existing_files")
def process_existing_files():
	for filename in os.listdir(DIRECTORY_TO_WATCH):
		filepath = os.path.join(DIRECTORY_TO_WATCH, filename)
		if os.path.isfile(filepath) and filename.lower().endswith(".pdf"):
			Handler.process_file(filepath)


if __name__ == "__main__":
	process_existing_files()
	w = Watcher()
	w.run()
