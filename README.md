<img src="https://www.sipgatedesign.com/wp-content/uploads/wort-bildmarke_positiv_2x.jpg" alt="sipgate logo" title="sipgate" align="right" height="112" width="200"/>

# sipgate.io Python send fax example

To demonstrate how to send an Fax, we queried the `/sessions/fax` endpoint of the sipgate REST API.

For further information regarding the sipgate REST API please visit https://api.sipgate.com/v2/doc

- [sipgate.io Python send fax example](#sipgateio-python-send-fax-example)
  - [Prerequisites](#prerequisites)
  - [How To Use](#how-to-use)
  - [Configuration](#configuration)
  - [How It Works](#how-it-works)
  - [Fax Extensions](#fax-extensions)
  - [Common Issues](#common-issues)
    - [Fax added to the sending queue, but sending failed](#fax-added-to-the-sending-queue-but-sending-failed)
    - [HTTP Errors](#http-errors)
  - [Related](#related)
  - [Contact Us](#contact-us)
  - [License](#license)
  - [External Libraries](#external-libraries)

## Prerequisites
- python3
- pip3

## How To Use

Install dependencies:
```bash
$ pip3 install -r requirements.txt
```

## Configuration
In the [.env](./.env) file located in the project root directory insert `YOUR_SIPGATE_TOKEN_ID`, `YOUR_SIPGATE_TOKEN`, and `YOUR_SIPGATE_FAXLINE_EXTENSION`:

```json
...
TOKEN_ID="YOUR_SIPGATE_TOKEN_ID",
TOKEN="YOUR_SIPGATE_TOKEN",
FAXLINE_ID="YOUR_SIPGATE_FAXLINE_EXTENSION",
...
```

The token must have the `sessions:fax:write` and `history:read` scopes.
For more information about personal access tokens visit our [website.](https://www.sipgate.io/rest-api/authentication#personalAccessToken)

The `FAXLINE_ID` uniquely identifies the extension from which you wish to send your fax. Further explanation is given in the section [Fax Extensions](#fax-extensions).

Run the application:

```bash
python3 send_fax.py <RECIPIENT> <PDF_DOCUMENT>
```
**Note:** Although the API accepts various formats of fax numbers the recommended format for the `RECIPIENT` is the [E.164 standard](https://en.wikipedia.org/wiki/E.164).

## How It Works

In our main script, the send_fax.py, we check that the user provides the recipient phone number and a PDF, we also ensure that the mime-type of the file is `application/pdf`.

```python
pdf_filepath, recipient = validate_commandline_arguments()
```

```python
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
```

After that we read the file contents and encode it with Base64.
```python
with open(pdf_filepath, 'rb') as pdf_file:
	encoded_pdf = base64.b64encode(pdf_file.read())
```

After that we call our `send_fax` function and pass the encoded_pdf, pdf_filename, recipient and authorization as arguments.
```python
session_id = send_fax(encoded_pdf, pdf_filename, recipient, authorization)
```

In the `send_fax` function, we define the headers and the request body, which contains the `faxlineId`, `recipient`, `filename`, and `base64Content`.
```python
headers = {
	'Content-Type': 'application/json'
}
```

```python
request_body = {
    'faxlineId': config['faxlineId'],
    'recipient': recipient,
    'filename': pdf_filename,
    'base64Content': encoded_pdf
}
```

We use the python package 'requests' for request generation and execution. The `post` function takes as arguments the request URL, headers, an authorization header, and the request body. The request URL consists of the base URL defined above and the endpoint `/sessions/fax`. The function `HTTPBasicAuth` from the 'requests' package takes credentials and generates the required Basic Auth header (for more information on Basic Auth see our [code example](https://github.com/sipgate-io/sipgateio-basicauth-python)).

```python
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
```


Next we check if the status of our `response` is 200, meaning that the request to send the fax was successfully received.
**Note:** Although the Api returns the status 200 it does not mean that the fax was sent. It was only added to a queue for sending.

To check the status of the fax we use the `session_id`, returned by the `send_fax` function, and pass it to the `poll_send_status` function. In this example we use `time.sleep` to check the status of the fax every five seconds.
```python
send_status = 'STARTING'
while send_status in ('STARTING', 'PENDING', 'SENDING'):
	print(send_status)
    send_status = poll_send_status(session_id, authorization)
    time.sleep(5)
```

In the `poll_send_status` function we use requests again to query the `/history/{sessionId}` endpoint to get the history entry for our fax. In this case we are only interested in the `faxStatusType`.
```python
def poll_send_status(session_id, authorization):
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get('{}/history/{}'.format(config['baseUrl'], session_id), headers=headers, auth=authorization)
    response_body = response.json()
    return response_body['faxStatusType']

```

The `faxStatusType` can contain the following values:
- `PENDING`: The fax was added to the queue for sending, but the sending process has not started yet
- `SENDING`: The fax is currently being sent
- `FAILED`: The fax could not be sent
- `SENT`: The fax was sent successfully
- `SCHEDULED`: The fax is scheduled for sending at the specified timestamp (it is not `PENDING` because it is not waiting in the queue of faxes to be sent yet)

## Fax Extensions

A fax extension consists of the letter 'f' followed by a number (e.g. 'f0'). The sipgate API uses the concept of fax extensions to identify devices within your account that are enabled to send fax. In this context the term 'device' does not necessarily refer to a hardware fax but rather a virtual representation.

You can find out what your extension is as follows:

1. Log into your [sipgate account](https://app.sipgate.com/w0/routing)
2. Use the sidebar to navigate to the **Routing** (_Telefonie_) tab
3. Click on any **Fax** device in your routing table
4. Select any option (gear icon) to open the corresponding menu
5. The URL of the page should have the form `https://app.sipgate.com/w0/routing/dialog/{option}/{faxlineId}` where `{faxlineId}` is your Fax extension.

## Common Issues

### Fax added to the sending queue, but sending failed

Possible reasons are:

- PDF file not encoded correctly in base64
- PDF file with text fields or forms are not supported
- PDF file is corrupt

### HTTP Errors

| reason                                                                                                                                                | errorcode |
|-------------------------------------------------------------------------------------------------------------------------------------------------------| :-------: |
| bad request (e.g. request body fields are empty or only contain spaces, timestamp is invalid etc.)                                                    |    400    |
| TOKEN_ID and/or TOKEN are wrong                                                                                                                       |    401    |
| your account balance is insufficient                                                                                                                  |    402    |
| no permission to use specified Fax extension (e.g. Fax feature not booked or user password must be reset in [web app](https://app.sipgate.com/login)) |    403    |
| wrong REST API endpoint                                                                                                                               |    404    |
| wrong request method                                                                                                                                  |    405    |
| invalid recipient fax number                                                                                                                          |    407    |
| wrong or missing `Content-Type` header with `application/json`                                                                                        |    415    |
| internal server error or unhandled bad request                                                                                                        |    500    |

## Related

- [requests documentation](http://docs.python-requests.org/en/master/)
- [base64 documentation](https://docs.python.org/3/library/base64.html)

## Contact Us

Please let us know how we can improve this example.
If you have a specific feature request or found a bug, please use **Issues** or fork this repository and send a **pull request** with your improvements.

## License

This project is licensed under **The Unlicense** (see [LICENSE file](./LICENSE)).

## External Libraries
This code uses the following external libraries

- requests:  
  - Licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)  
  - Website: http://docs.python-requests.org/en/master/
- python-dotenv
  - Website: https://pypi.org/project/python-dotenv/
---

[sipgate.io](https://www.sipgate.io) | [@sipgateio](https://twitter.com/sipgateio) | [API-doc](https://api.sipgate.com/v2/doc)

