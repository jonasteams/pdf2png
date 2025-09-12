from flask import Flask, render_template, request, send_file, Response, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from zipfile import ZipFile
from io import BytesIO
from pdf2image import convert_from_path
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Home route
@app.route('/')
def home():
    tab = request.args.get('tab')
    # Default to PNG→PDF
    if not tab:
        return redirect(url_for('home', tab='png2pdf'))
    return render_template('index.html', tab=tab)

# Conversion route
@app.route('/convert', methods=['POST'])
def convert():
    tab = request.form.get('tab')
    message = None

    if tab == 'pdf2png':
        file = request.files.get('file')
        if not file:
            message = "Please upload a PDF file."
            return render_template('index.html', tab=tab, message=message)

        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)

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

        # Delete temporary files
        os.remove(pdf_path)
        for f in temp_files:
            os.remove(f)

        return send_file(zip_buffer, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}.zip", mimetype='application/zip')

    elif tab == 'png2pdf':
        files = request.files.getlist('files')
        if not files:
            message = "Please upload at least one PNG/JPG file."
            return render_template('index.html', tab=tab, message=message)

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

        # Delete temporary files
        for f in temp_files:
            os.remove(f)

        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')

    else:
        message = "Unknown conversion type."
        return render_template('index.html', tab='png2pdf', message=message)

# Terms & Privacy route
@app.route('/terms')
def terms():
    return render_template('terms.html')

# Sitemap XML
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    pages = [
        {'loc': request.url_root, 'lastmod': datetime.now().date(), 'priority': '1.0'},
        {'loc': request.url_root + '?tab=pdf2png', 'lastmod': datetime.now().date(), 'priority': '0.9'},
        {'loc': request.url_root + '?tab=png2pdf', 'lastmod': datetime.now().date(), 'priority': '0.9'},
        {'loc': request.url_root + 'terms', 'lastmod': datetime.now().date(), 'priority': '0.8'},
    ]

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{page["loc"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    sitemap_xml += '</urlset>'

    return Response(sitemap_xml, mimetype='application/xml')

if __name__ == '__main__':
    app.run(debug=True)
