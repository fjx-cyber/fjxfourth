from flask import Flask, request, send_from_directory, jsonify
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
    return "Math Grader API running"


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/list")
def list_files():
    return jsonify(os.listdir(UPLOAD_DIR))


# ----------- 新增裁剪接口 ----------------
@app.route("/crop", methods=["POST"])
def crop():
    try:
        data = request.json
        image_url = data["image_url"]
        boxes = data["boxes"]

        image_id = str(uuid.uuid4())
        image_path = os.path.join(UPLOAD_DIR, f"{image_id}.jpg")

        img_data = requests.get(image_url).content
        with open(image_path, "wb") as f:
            f.write(img_data)

        img = Image.open(image_path)

        crop_urls = []

        for i, box in enumerate(boxes):
            x, y, w, h = box["x"], box["y"], box["w"], box["h"]
            crop = img.crop((x, y, x + w, y + h))
            crop_name = f"{image_id}_crop_{i}.jpg"
            crop_path = os.path.join(UPLOAD_DIR, crop_name)
            crop.save(crop_path)
            crop_urls.append(f"{request.host_url}image/{crop_name}")

        return jsonify({"crop_urls": crop_urls})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------- 精准圈错接口 ----------------
@app.route("/draw", methods=["POST"])
def draw():
    try:
        data = request.json
        image_url = data.get("image_url")
        errors = data.get("errors", [])
        if not image_url:
            return jsonify({"error": "No image URL"}), 400

        image_id = str(uuid.uuid4())
        image_path = os.path.join(UPLOAD_DIR, f"{image_id}.jpg")
        img_data = requests.get(image_url).content
        with open(image_path, "wb") as f:
            f.write(img_data)

        img = Image.open(image_path)
        draw_obj = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            font = ImageFont.load_default()

        for err in errors:
            x = int(err["x"])
            y = int(err["y"])
            w = int(err["w"])
            h = int(err["h"])

            # 缩小边框，让框贴合笔迹
            shrink = 0.15
            x += int(w * shrink / 2)
            y += int(h * shrink / 2)
            w = int(w * (1 - shrink))
            h = int(h * (1 - shrink))

            draw_obj.rectangle([x, y, x + w, y + h], outline="red", width=4)

            comment = err.get("comment", "错误")
            draw_obj.text((x, y - 28), comment, fill="red", font=font)

        output_name = f"{image_id}_output.jpg"
        output_path = os.path.join(UPLOAD_DIR, output_name)
        img.save(output_path)
        img.close()

        return jsonify({
            "annotated_image_url": f"{request.host_url}image/{output_name}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/image/<path:filename>")
def serve_image(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
