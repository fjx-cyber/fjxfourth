from flask import Flask, request, send_from_directory, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
import os
import uuid

app = Flask(__name__)

UPLOAD_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def home():
    return "Math Grader API running"


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/list")
def list_files():
    return jsonify(os.listdir(UPLOAD_DIR))


@app.route("/draw", methods=["POST"])
def draw():
    try:
        data = request.json

        image_url = data.get("image_url")

        if not image_url:
            return jsonify({"error": "No image URL"}), 400

        errors = data.get("errors", [])

        image_id = str(uuid.uuid4())
        image_path = os.path.join(UPLOAD_DIR, f"{image_id}.jpg")

        img_data = requests.get(image_url).content

        with open(image_path, "wb") as f:
            f.write(img_data)

        img = Image.open(image_path)
        draw_obj = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()

        for err in errors:
            x = int(err["x"])
            y = int(err["y"])
            w = int(err["w"])
            h = int(err["h"])

            draw_obj.rectangle(
                [x, y, x + w, y + h],
                outline="red",
                width=5
            )

            draw_obj.text(
                (x, y - 30),
                "错误",
                fill="red",
                font=font
            )

        output_name = f"{image_id}_output.jpg"
        output_path = os.path.join(UPLOAD_DIR, output_name)

        img.save(output_path)
        img.close()

        return jsonify({
            "annotated_image_url":
            f"{request.host_url}image/{output_name}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/image/<path:filename>")
def serve_image(filename):
    return send_from_directory(
        UPLOAD_DIR,
        filename,
        as_attachment=False
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
