import base64
import json
import mimetypes
import os
import re
import sys
import time
from os.path import join, dirname
from dotenv import load_dotenv
import requests

load_dotenv()

BASE_URL = os.environ.get("BASE_URL")
TOKEN = os.environ.get("TOKEN")
TOKEN_ID = os.environ.get("TOKEN_ID")
FAXLINE_ID = os.environ.get("FAXLINE_ID")
RECIPIENT = os.environ.get("RECIPIENT")
PDF_FILE_PATH = os.environ.get("PDF_FILE_PATH")

FAX_NUMBER_PATTERN = r'\+?\d+'

def main():
    authorization = requests.auth.HTTPBasicAuth(TOKEN_ID, TOKEN)
    validate_env_values()

    with open(PDF_FILE_PATH, 'rb') as pdf_file:
        encoded_pdf = base64.b64encode(pdf_file.read())

    pdf_filename = os.path.basename(PDF_FILE_PATH)

    session_id = send_fax(encoded_pdf, pdf_filename, RECIPIENT, authorization)

    send_status = 'STARTING'
    while send_status in ('STARTING', 'PENDING', 'SENDING'):
        print(send_status)
        send_status = poll_send_status(session_id, authorization)
        time.sleep(5)
    print(send_status)


def validate_env_values():
    if not re.match(FAX_NUMBER_PATTERN, RECIPIENT):
        sys.stderr.write('Invalid recipient fax number.')
        exit(2)

    if not os.path.isfile(PDF_FILE_PATH):
        sys.stderr.write('File not found: {}'.format(PDF_FILE_PATH))
        exit(3)

    mimetype, encoding = mimetypes.guess_type(PDF_FILE_PATH)
    if not mimetype == 'application/pdf':
        sys.stderr.write('Invalid file type: {}'.format(mimetype))
        exit(4)


def send_fax(encoded_pdf, pdf_filename, recipient, authorization):
    url = BASE_URL + '/sessions/fax'
    headers = {
        'Content-Type': 'application/json'
    }
    request_body = {
        'faxlineId': FAXLINE_ID,
        'recipient': recipient,
        'filename': pdf_filename,
        'base64Content': encoded_pdf.decode("utf-8")
    }

    response = requests.post(url,
                             headers=headers,
                             json=request_body,
                             auth=authorization)
    status_code = response.status_code
    if not status_code == 200:
        sys.stderr.write('An error occurred while communicating with the sipgate REST API: ')
        sys.stderr.write('status code {} (see README for details)'.format(status_code))
        exit(5)

    response_body = response.json()
    session_id = response_body['sessionId']
    return session_id


def poll_send_status(session_id, authorization):
    url = '{}/history/{}'.format(BASE_URL, session_id)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get(url,
                            headers=headers,
                            auth=authorization)
    response_body = response.json()
    return response_body['faxStatusType']


if __name__ == '__main__':
    main()
