from flask import Flask, request, render_template, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import fitz  # PyMuPDF
import os
from io import BytesIO
from zipfile import ZipFile
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Dossiers
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "outputs"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    tab = request.args.get("tab", "pdf2png")
    return render_template("index.html", active_tab=tab, message=None, download_link=None)

@app.route("/convert", methods=["POST"])
def convert():
    tab = request.form.get("tab")

    # === PDF -> PNG ===
    if tab == "pdf2png":
        file = request.files.get("file")
        if not file or file.filename == "":
            return render_template("index.html", message="No file provided", active_tab="pdf2png")

        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(input_path)

        try:
            doc = fitz.open(input_path)
            img_paths = []
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                out_file = os.path.join(app.config["OUTPUT_FOLDER"], f"page_{i+1}.png")
                pix.save(out_file)
                img_paths.append(out_file)
            doc.close()
        except Exception as e:
            return render_template("index.html", message=f"Conversion error: {e}", active_tab="pdf2png")

        # Créer un ZIP à télécharger
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zf:
            for p in img_paths:
                zf.write(p, os.path.basename(p))
        zip_buffer.seek(0)

        return send_file(zip_buffer, as_attachment=True,
                         download_name="converted.zip", mimetype="application/zip")

    # === PNG -> PDF ===
    elif tab == "png2pdf":
        files = request.files.getlist("files")
        if not files or files[0].filename == "":
            return render_template("index.html", message="No file provided", active_tab="png2pdf")

        output_pdf = os.path.join(app.config["OUTPUT_FOLDER"], "output.pdf")

        try:
            images = [Image.open(f).convert("RGB") for f in files]
            images[0].save(output_pdf, save_all=True, append_images=images[1:])
        except Exception as e:
            return render_template("index.html", message=f"Conversion error: {e}", active_tab="png2pdf")

        return send_file(output_pdf, as_attachment=True, download_name="converted.pdf")

    return render_template("index.html", message="Invalid request", active_tab="pdf2png")

# === SEO : sitemap.xml ===
@app.route("/sitemap.xml", methods=["GET"])
def sitemap():
    base_url = request.url_root.strip("/")
    lastmod = datetime.now().date().isoformat()

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{lastmod}</lastmod>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/?tab=pdf2png</loc>
    <lastmod>{lastmod}</lastmod>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/?tab=png2pdf</loc>
    <lastmod>{lastmod}</lastmod>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/terms.html</loc>
    <lastmod>{lastmod}</lastmod>
    <priority>0.5</priority>
  </url>
</urlset>
"""
    return app.response_class(xml, mimetype="application/xml")

# === Terms & Privacy ===
@app.route("/terms.html", methods=["GET"])
def terms():
    return render_template("terms.html")

if __name__ == "__main__":
    app.run(debug=True)
