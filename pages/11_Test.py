import zipfile
from io import BytesIO

def extract_images_from_zip(zip_file):
    extracted_images = []
    with zipfile.ZipFile(zip_file, 'r') as z:
        for file_info in z.infolist():
            if file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                with z.open(file_info) as file:
                    extracted_images.append((file_info.filename, file.read()))
    return extracted_images

# Test the extraction function
zip_path = r"C:\Users\AtomRyzen\Desktop\test\REF\APP TEST\UOB\New folder\BA.zip"  # Replace this with your zip file path
images = extract_images_from_zip(zip_path)

for name, _ in images:
    print(f"Extracted: {name}")
