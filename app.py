import subprocess
import os
import base64
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_input_file(file):
    filename = file.filename.lower()
    ext = os.path.splitext(filename)[1]
    path = os.path.join(UPLOAD_FOLDER, f"temp_input{ext}")
    file.save(path)

    # Ak je to obrázok, konvertujeme na JPG pre kompatibilitu
    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        new_path = os.path.join(UPLOAD_FOLDER, "input_processed.jpg")
        img.save(new_path, "JPEG", quality=95)
        return new_path, ".jpg"
    
    # Audio (WAV) necháme v pôvodnom stave
    return path, ext

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    try:
        img_file = request.files['image']
        secret_text = request.form['text']
        password = request.form['password']

        input_path, extension = process_input_file(img_file)
        text_path = os.path.join(UPLOAD_FOLDER, "secret.txt")
        output_path = os.path.join(UPLOAD_FOLDER, f"stego_vault_output{extension}")

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(secret_text)

        # Príkaz pre steghide
        cmd = ["steghide", "embed", "-cf", input_path, "-ef", text_path, "-sf", output_path, "-p", password, "-f"]
        subprocess.run(cmd, check=True)

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/decrypt', methods=['POST'])
def decrypt():
    try:
        img_file = request.files['image']
        password = request.form['password']

        ext = os.path.splitext(img_file.filename)[1]
        path = os.path.join(UPLOAD_FOLDER, f"to_decrypt{ext}")
        img_file.save(path)

        out_txt = os.path.join(UPLOAD_FOLDER, "decrypted.txt")
        if os.path.exists(out_txt): os.remove(out_txt)

        cmd = ["steghide", "extract", "-sf", path, "-xf", out_txt, "-p", password, "-f"]
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode == 0:
            with open(out_txt, "rb") as f:
                content_bytes = f.read()
                encoded_content = base64.b64encode(content_bytes).decode('utf-8')
            return jsonify({"success": True, "base64_data": encoded_content})
        else:
            return jsonify({"success": False, "error": "Nesprávne heslo alebo poškodený súbor."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)