import os
from flask import Flask, render_template, request, send_file, flash
from PIL import Image
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/encrypted/'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def to_bin(data):
    """Convert data to binary format."""
    if isinstance(data, str):
        return ''.join([format(ord(i), "08b") for i in data])
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [format(i, "08b") for i in data]
    elif isinstance(data, int):
        return format(data, "08b")
    else:
        raise TypeError("Input type not supported")

def hide_data(image, secret_message):
    """Hide a secret message in an image using LSB."""
    binary_message = to_bin(secret_message) + '1111111111111110'
    data_index = 0
    img = image.copy()
    pixels = np.array(img)

    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = to_bin(pixels[i, j])
            if data_index < len(binary_message):
                pixels[i, j, 0] = int(pixel[0][:-1] + binary_message[data_index], 2)
                data_index += 1
            if data_index >= len(binary_message):
                break
        if data_index >= len(binary_message):
            break

    return Image.fromarray(pixels)

def extract_data(image):
    """Extract the hidden data from the image."""
    binary_data = ""
    pixels = np.array(image)

    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = to_bin(pixels[i, j])
            binary_data += pixel[0][-1]

    all_bytes = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    decoded_data = ""

    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        if decoded_data[-8:] == '11111110':
            break

    return decoded_data[:-8]

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    if 'image' not in request.files:
        flash('No image file provided.')
        return render_template('index.html')

    file = request.files['image']
    message = request.form['message']

    if file.filename == '':
        flash('No image selected.')
        return render_template('index.html')

    if message == '':
        flash('No message provided.')
        return render_template('index.html')

    image = Image.open(file)
    encrypted_image = hide_data(image, message)
    output_path = os.path.join(UPLOAD_FOLDER, 'encrypted_image.png')
    encrypted_image.save(output_path)

    return send_file(output_path, as_attachment=True)

@app.route('/decrypt', methods=['POST'])
def decrypt():
    if 'image' not in request.files:
        flash('No image file provided.')
        return render_template('index.html')

    file = request.files['image']
    user_message = request.form['message']

    if file.filename == '':
        flash('No image selected.')
        return render_template('index.html')

    image = Image.open(file)
    hidden_message = extract_data(image)

    if user_message == '':
        flash(f"{hidden_message}")
    else:
        if user_message in hidden_message:
            flash(f"Match found in decrypted message.")
        else:
            flash(f"Match not found")

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
