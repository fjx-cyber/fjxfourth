from flask import Flask, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import requests
import os
import uuid
import json

app = Flask(__name__)

UPLOAD_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def home():
    return "Math Grader API is running"


@app.route("/draw", methods=["POST"])
def draw():

    data = request.json
    image_url = data["image_url"]
    errors = data["errors"]

    # 下载图片
    image_id = str(uuid.uuid4())
    image_path = os.path.join(UPLOAD_DIR, f"{image_id}.jpg")

    img_data = requests.get(image_url).content
    with open(image_path, "wb") as f:
        f.write(img_data)

    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()

    for err in errors:
        x = err["x"]
        y = err["y"]
        w = err["w"]
        h = err["h"]

        draw.rectangle(
            [x, y, x + w, y + h],
            outline="red",
            width=5
        )

        draw.text(
            (x, y - 30),
            "错误",
            fill="red",
            font=font
        )

    output_name = f"{image_id}_output.jpg"
    output_path = os.path.join(UPLOAD_DIR, output_name)

    img.save(output_path)

    return {
        "annotated_image_url":
        request.host_url + "image/" + output_name
    }


@app.route('/image/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)