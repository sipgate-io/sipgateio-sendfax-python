import base64
import json
import mimetypes
import os
import re
import sys
import time

import requests

FAX_NUMBER_PATTERN = r'\+?\d+'


def main():
    authorization = requests.auth.HTTPBasicAuth(config['username'], config['password'])
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


def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)


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
    url = config['baseUrl'] + '/sessions/fax'
    headers = {
        'Content-Type': 'application/json'
    }
    request_body = {
        'faxlineId': config['faxlineId'],
        'recipient': recipient,
        'filename': pdf_filename,
        'base64Content': encoded_pdf
    }
    response = requests.post(url,
                             headers=headers,
                             json=request_body,
                             auth=authorization)
    response_body = response.json()
    session_id = response_body['sessionId']
    return session_id


def poll_send_status(session_id, authorization):
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get('{}/history/{}'.format(config['baseUrl'], session_id), headers=headers, auth=authorization)
    response_body = response.json()
    return response_body['faxStatusType']


if __name__ == '__main__':
    config = load_config()
    main()
