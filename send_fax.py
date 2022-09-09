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

token = os.environ.get("TOKEN")
tokenId = os.environ.get("TOKEN_ID")
faxlineId = os.environ.get("FAXLINE_ID")

FAX_NUMBER_PATTERN = r'\+?\d+'
baseUrl = "https://api.sipgate.com/v2"

def main():
    authorization = requests.auth.HTTPBasicAuth(tokenId, token)
    pdf_filepath, recipient = validate_commandline_arguments()

    with open(pdf_filepath, 'rb') as pdf_file:
        encoded_pdf = base64.b64encode(pdf_file.read())

    pdf_filename = os.path.basename(pdf_filepath)

    session_id = send_fax(encoded_pdf, pdf_filename, recipient, authorization)

    send_status = 'STARTING'
    while send_status in ('STARTING', 'PENDING', 'SENDING'):
        print(send_status)
        send_status = poll_send_status(session_id, authorization)
        time.sleep(5)
    print(send_status)


def validate_commandline_arguments():
    if len(sys.argv) < 3:
        sys.stderr.write('Missing arguments.\n')
        sys.stderr.write('Please pass the recipient fax number and the file path.')
        exit(1)

    recipient = sys.argv[1]
    if not re.match(FAX_NUMBER_PATTERN, recipient):
        sys.stderr.write('Invalid recipient fax number.')
        exit(2)

    pdf_filepath = sys.argv[2]
    if not os.path.isfile(pdf_filepath):
        sys.stderr.write('File not found: {}'.format(pdf_filepath))
        exit(3)

    mimetype, encoding = mimetypes.guess_type(pdf_filepath)
    if not mimetype == 'application/pdf':
        sys.stderr.write('Invalid file type: {}'.format(mimetype))
        exit(4)

    return pdf_filepath, recipient


def send_fax(encoded_pdf, pdf_filename, recipient, authorization):
    url = baseUrl + '/sessions/fax'
    headers = {
        'Content-Type': 'application/json'
    }
    request_body = {
        'faxlineId': faxlineId,
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
    url = '{}/history/{}'.format(baseUrl, session_id)
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
