from flask_cors import CORS
from flask import Flask, request, send_file, Response, render_template
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from zipfile import ZipFile
from io import BytesIO
from pdf2image import convert_from_path
from PIL import Image

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Conversion route compatible frontend
@app.route('/convert', methods=['POST'])
def convert():
    files = request.files.getlist('file')  # frontend sends key="file"
    if not files:
        return "No file provided", 400

    first_file = files[0]
    filename = secure_filename(first_file.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.pdf':  # PDF → PNG
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        first_file.save(pdf_path)
        images = convert_from_path(pdf_path)

        zip_buffer = BytesIO()
        temp_files = []

        with ZipFile(zip_buffer, 'w') as zipf:
            for i, img in enumerate(images, start=1):
                img_filename = f"{os.path.splitext(filename)[0]}_{i}.png"
                img_path = os.path.join(app.config['OUTPUT_FOLDER'], img_filename)
                img.save(img_path, 'PNG')
                temp_files.append(img_path)
                zipf.write(img_path, arcname=img_filename)

        zip_buffer.seek(0)

        # Delete temp files
        os.remove(pdf_path)
        for f in temp_files:
            os.remove(f)

        return send_file(zip_buffer, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}.zip", mimetype='application/zip')

    elif ext in ['.png', '.jpg', '.jpeg']:  # PNG → PDF
        images = []
        temp_files = []

        for file in files:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            temp_files.append(path)
            img = Image.open(path).convert('RGB')
            images.append(img)

        pdf_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], pdf_filename)
        images[0].save(pdf_path, save_all=True, append_images=images[1:])

        # Delete temp files
        for f in temp_files:
            os.remove(f)

        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')

    else:
        return "Unsupported file type", 400

# Terms & Privacy
@app.route('/terms')
def terms():
    return render_template('terms.html')

# Sitemap
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': request.url_root, 'lastmod': datetime.now().date(), 'priority': '1.0'},
        {'loc': request.url_root + 'terms', 'lastmod': datetime.now().date(), 'priority': '0.8'},
    ]
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        sitemap_xml += f'  <url><loc>{page["loc"]}</loc><lastmod>{page["lastmod"]}</lastmod><priority>{page["priority"]}</priority></url>\n'
    sitemap_xml += '</urlset>'
    return Response(sitemap_xml, mimetype='application/xml')

if __name__ == '__main__':
    app.run(debug=True)
