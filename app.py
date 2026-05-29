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
    return "Math Grader API is running"


@app.route("/draw", methods=["POST"])
def draw():
    try:
        data = request.json

        # 兼容 Dify 的不同输入格式
        image_url = None

        if "image_url" in data:
            image_url = data["image_url"]

        elif "homework_image" in data:
            image_url = data["homework_image"].get("url")

        if not image_url:
            return jsonify({"error": "No image URL found"}), 400

        errors = data.get("errors", [
            {
                "x": 100,
                "y": 100,
                "w": 200,
                "h": 120
            }
        ])

        # 下载图片
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
            x = err["x"]
            y = err["y"]
            w = err["w"]
            h = err["h"]

            # 红框
            draw_obj.rectangle(
                [x, y, x + w, y + h],
                outline="red",
                width=5
            )

            # 标记文字
            draw_obj.text(
                (x, y - 30),
                "错误",
                fill="red",
                font=font
            )

        output_name = f"{image_id}_output.jpg"
        output_path = os.path.join(UPLOAD_DIR, output_name)

        img.save(output_path)

        return jsonify({
            "annotated_image_url":
                request.host_url + "image/" + output_name
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/image/<filename>")
def serve_image(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
