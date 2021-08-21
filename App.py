from flask import Flask, request, json
import os
import time
import ppimg
import base64

app = Flask(__name__)
app.config['UPLOAD_IMAGES'] = './imgs-upload'
app.config['PROCESS_IMAGES'] = './imgs-process'

def nameFile():
    return str(int(round(time.time() * 1000))) + '.jpg'

@app.route('/')
def Index():
    return "Hello World"


@app.route('/upload', methods=["POST"])
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
def image():
    filename = request.args.get('filename')
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


