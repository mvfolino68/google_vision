# !pip install google.cloud.vision
import os
import io
import requests
import argparse
from enum import Enum

from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw
from IPython.display import display # to display images
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
# from email.mime.application import MIMEApplication
from email import encoders 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/content/sturdy-spanner-221114-891167b05110.json"

def draw_boxes(image, bounds, color):
	"""Draw a border around the image using the hints in the vector list."""

	draw = ImageDraw.Draw(image)
	for bound in bounds:
		draw.polygon([
			bound.vertices[0].x, bound.vertices[0].y,
			bound.vertices[1].x, bound.vertices[1].y,
			bound.vertices[2].x, bound.vertices[2].y,
			bound.vertices[3].x, bound.vertices[3].y], None, color)
	return image


def get_document_bounds(image, feature):
	# [START vision_document_text_tutorial_detect_bounds]
	"""Returns document bounds given an image."""

	client = vision.ImageAnnotatorClient()

	bounds = []
	urlimg = requests.get(image, stream=True)
	content = urlimg.content

	image = types.Image(content=content)
	response = client.document_text_detection(image=image)
	document = response.full_text_annotation

	# Collect specified feature bounds by enumerating all document features
	for page in document.pages:
		for block in page.blocks:
			for paragraph in block.paragraphs:
				for word in paragraph.words:
					for symbol in word.symbols:
						if (feature == FeatureType.SYMBOL):
							bounds.append(symbol.bounding_box)

					if (feature == FeatureType.WORD):
						bounds.append(word.bounding_box)

				if (feature == FeatureType.PARA):
					bounds.append(paragraph.bounding_box)

			if (feature == FeatureType.BLOCK):
				bounds.append(block.bounding_box)

		if (feature == FeatureType.PAGE):
			bounds.append(block.bounding_box)

	# The list `bounds` contains the coordinates of the bounding boxes.
	# [END vision_document_text_tutorial_detect_bounds]
	return bounds

def detect_text(image):
	"""Detects text in the file."""
	client = vision.ImageAnnotatorClient()

	urlimg = requests.get(image, stream=True)
	content = urlimg.content
	image = vision.types.Image(content=content)
	response = client.text_detection(image=image)
	texts = response.text_annotations
	print('Texts:')
	# for text in texts:
	#     print('\n"{}"'.format(text.description))
	return texts

def finish_up(mail, files):

	report_file = open('beefree-4wjl3m27e2d.html')
	html = report_file.read()

	# me == my email address
	# you == recipient's email address
	me = "mtbankedo@gmail.com"
	you = mail
	subject = "M&T EDO Google Vision Demonstration"

	# Create message container - the correct MIME type is multipart/alternative.
	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = me
	msg['To'] = you

	# Record the MIME types of both parts - text/plain and text/html.
	part2 = MIMEText(html, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	msg.attach(part2)
 
 	# # open the file to be sent  
	for f in files:  # add files to the message
			attachment = open(f, "rb") 
			p = MIMEBase('application', 'octet-stream') 
			p.set_payload((attachment).read()) 
			encoders.encode_base64(p) 
			p.add_header('Content-Disposition', "attachment; filename= %s" % f) 
			msg.attach(p) 

	# Send the message via local SMTP server.
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(me, 'gpnfwiubcbvtemfc')

	server.sendmail(me,you,msg.as_string())
	server.quit()


class FeatureType(Enum):
	PAGE = 1
	BLOCK = 2
	PARA = 3
	WORD = 4
	SYMBOL = 5

class ImageToProcess:
	def __init__(self, image_url, to_addr):
		self.image_url = image_url
		self.to_addr = to_addr


	def render_doc_text(self, fileout):
		self.fileout = fileout

		image = Image.open(requests.get(self.image_url, stream=True).raw)
		bounds = get_document_bounds(image = self.image_url, feature = FeatureType.PAGE)
		draw_boxes(image, bounds, 'blue')
		bounds = get_document_bounds(image = self.image_url, feature = FeatureType.PARA)
		draw_boxes(image, bounds, 'red')
		bounds = get_document_bounds(image = self.image_url, feature = FeatureType.WORD)
		draw_boxes(image, bounds, 'yellow')

		if fileout != 0:
				image.save(fileout)
				display(image)
		else:
				display(image)

      
		texts = detect_text(self.image_url)
		total_text = ''
		fileout_txt = "Output_txt.txt"
		with open(fileout_txt, "w+") as text_file:
			for text in texts:
				print('\n"{}"'.format(text.description))
				total_text += '\n"{}"'.format(text.description)			
				text_file.write('\r\n"{}"'.format(text.description))
		
		finish_up(self.to_addr, [fileout, fileout_txt])