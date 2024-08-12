import logging
import uuid

import psycopg2
from elasticapm import capture_span

from config.environment import Config

logger = logging.getLogger(__name__)


class Database:
	def __init__(self):
		try:
			self.conn = psycopg2.connect(
				dbname=Config.POSTGRES_DB,
				user=Config.POSTGRES_USER,
				password=Config.POSTGRES_PASSWORD,
				host=Config.POSTGRES_HOST,
				port=Config.POSTGRES_PORT
			)
			self.cursor = self.conn.cursor()
		except (Exception, psycopg2.DatabaseError) as error:
			logger.error(f"Error connecting to the PostgreSQL database: {error}")
			raise

	@capture_span(name="insert_scanned_document")
	def insert_scanned_document(
			self,
			filename,
			filetype,
			current_path,
			original_path
	):
		document_id = str(uuid.uuid4())
		self.cursor.execute("""
            INSERT INTO documents.scanned_document (id, filename, filetype, current_path, original_path)
            VALUES (%s, %s, %s, %s, %s)
        """, (document_id, filename, filetype, current_path, original_path))
		return document_id

	@capture_span(name="insert_scanned_page")
	def insert_scanned_page(
			self,
			scanned_document_id,
			width,
			height
	):
		page_id = str(uuid.uuid4())
		self.cursor.execute("""
            INSERT INTO documents.scanned_page (id, scanned_document_id, width, height)
            VALUES (%s, %s, %s, %s)
        """, (page_id, scanned_document_id, width, height))
		return page_id

	@capture_span(name="insert_scanned_page_content")
	def insert_scanned_page_content(
			self,
			scanned_page_id,
			content,
			bbox_h_pct,
			bbox_w_pct,
			bbox_x_pct,
			bbox_y_pct,
			density
	):
		self.cursor.execute("""
            INSERT INTO documents.scanned_page_content (id,
             scanned_page_id, content, bbox_h_pct, bbox_w_pct, bbox_x_pct, bbox_y_pct, density)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
			str(uuid.uuid4()), scanned_page_id, content, bbox_h_pct, bbox_w_pct, bbox_x_pct, bbox_y_pct, density
		))

	def commit(self):
		self.conn.commit()

	def rollback(self):
		self.conn.rollback()

	def close(self):
		self.cursor.close()
		self.conn.close()
