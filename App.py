from flask import Flask, request, json
import os
import time
import ppimg
import base64
from flask_cors import CORS, cross_origin
import requests

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_IMAGES'] = './imgs-upload'
app.config['PROCESS_IMAGES'] = './imgs-process'

def nameFile():
    return str(int(round(time.time() * 1000))) + '.jpg'

@app.route('/')
def Index():
    return "Hello World"


@app.route('/upload', methods=["POST"])
@cross_origin()
def upload():
    if request.method == 'POST':

        names = []

        uploaded_files = request.files.getlist("images")

        for f in uploaded_files:
            filename = nameFile()
            f.save(os.path.join(app.config['UPLOAD_IMAGES'], filename))
            names.append(filename)

        response = app.response_class(
            response = json.dumps({ "names": names}),
            status = 200,
            mimetype = 'application/json'
        )
        return response

@app.route('/processing', methods=["POST"])
@cross_origin()
def processing():
    if request.method == 'POST':
        json_data = request.json
        names = json_data["names"]
        rutas = ppimg.init(names)

        response = app.response_class(
            response = json.dumps({ "names": rutas}),
            status = 200,
            mimetype = 'application/json'
        )
        return response

@app.route('/image', methods=['GET'])
@cross_origin()
def image():
    filename = request.args.get('filename')

    response = requests.post(
        'https://sdk.photoroom.com/v1/segment',
        headers={'x-api-key': '302937c00bf3f8eb2727f91d9734a35e0bcd7eb7'},
        files={'image_file': open(os.path.join(app.config['PROCESS_IMAGES'], filename), 'rb')},
    )

    response.raise_for_status()
    with open(os.path.join(app.config['PROCESS_IMAGES'], filename), 'wb') as f:
        f.write(response.content)

    with open(os.path.join(app.config['PROCESS_IMAGES'], filename), "rb") as image_file:
        encoded = base64.b64encode(image_file.read())
        data = encoded.decode('ascii') 

        response = app.response_class(
            response = json.dumps({ "filename": filename, "base64": data }),
            status = 200,
            mimetype = 'application/json'
        )
        return response

if __name__ == '__main__':
    app.run(port = 3000, debug = True)


