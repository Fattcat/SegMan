import subprocess
import os
import base64
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def prepare_image(img_file):
    img = Image.open(img_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    target_path = os.path.join(UPLOAD_FOLDER, "temp_input.jpg")
    img.save(target_path, "JPEG", quality=95)
    return target_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    try:
        img_file = request.files['image']
        secret_text = request.form['text'] # Flask/Python 3 už rieši UTF-8 automaticky
        password = request.form['password']
        
        img_path = prepare_image(img_file)
        text_path = os.path.join(UPLOAD_FOLDER, "secret.txt")
        output_path = os.path.join(UPLOAD_FOLDER, "stego_output.jpg")
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(secret_text)

        # Použitie úvodzoviek okolo hesla pre podporu špeciálnych znakov v hesle
        cmd = ["steghide", "embed", "-cf", img_path, "-ef", text_path, "-sf", output_path, "-p", password, "-f"]
        subprocess.run(cmd, check=True)
        
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/decrypt', methods=['POST'])
def decrypt():
    try:
        img_file = request.files['image']
        password = request.form['password']
        
        img_path = os.path.join(UPLOAD_FOLDER, "to_decrypt.jpg")
        img_file.save(img_path)
        out_txt = os.path.join(UPLOAD_FOLDER, "decrypted.txt")

        if os.path.exists(out_txt): os.remove(out_txt)

        cmd = ["steghide", "extract", "-sf", img_path, "-xf", out_txt, "-p", password, "-f"]
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode == 0:
            with open(out_txt, "rb") as f:
                content_bytes = f.read()
                # Zakódujeme do Base64 pre bezpečný prenos v JSON
                encoded_content = base64.b64encode(content_bytes).decode('utf-8')
            return jsonify({"success": True, "base64_data": encoded_content})
        else:
            return jsonify({"success": False, "error": "Nesprávne heslo alebo súbor neobsahuje dáta."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Chyba: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
