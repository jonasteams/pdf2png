from pdf2image import convert_from_path
import os

POPPLER_PATH = r"C:\poppler\bin"  # ici le bon dossier

def pdf_to_png(pdf_path):
    output_folder = os.path.splitext(pdf_path)[0] + "_png"
    os.makedirs(output_folder, exist_ok=True)

    images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)

    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f"page_{i + 1}.png")
        image.save(image_path, "PNG")
        print(f"Page {i + 1} saved as {image_path}")

if __name__ == "__main__":
    pdf_file = input("Enter the path of the PDF file: ").strip()
    if not os.path.isfile(pdf_file):
        print("Error: The specified file does not exist.")
    else:
        pdf_to_png(pdf_file)
