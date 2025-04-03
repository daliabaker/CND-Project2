import os
from flask import Flask, redirect, request, send_file, render_template_string
from google.cloud import storage
import json
import google.generativeai as genai
import re 

BUCKET_NAME= "project2-cnd"
storage_client = storage.Client()

genai.configure(api_key=os.environ['GEMINI_API'])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
PROMPT = "Generate a short title and a description for this image. Respond strictly in JSON format with 'title' and 'description' fields."


os.makedirs('files', exist_ok = True)

app = Flask(__name__)
@app.route('/serve-image/<filename>')
def serve_image(filename):
    file_path = os.path.join("files", filename)
    return send_file(file_path, mimetype="image/jpeg")


def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    response = model.generate_content([file, "\n\n", PROMPT])

    print("Gemini API Raw Response:", response)

    if not response or not response.text.strip():
        raise ValueError("Empty response from Gemini API")

    # Extract JSON from Markdown-formatted response
    cleaned_text = re.sub(r"```json|```", "", response.text).strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", cleaned_text)
        raise e

def save_metadata(bucket_name, image_name, metadata):
    json_blob = storage_client.bucket(bucket_name).blob(image_name.replace('.jpeg', '.json').replace('.jpg', '.json'))
    json_blob.upload_from_string(json.dumps(metadata), content_type='application/json')

def get_list_of_files(bucket_name):
    """Lists all the blobs in the bucket."""
    print("\n")
    print("get_list_of_files: "+bucket_name)

    blobs = storage_client.list_blobs(bucket_name)
    print(blobs)
    files = []
    for blob in blobs:
        files.append(blob.name)

    return files

def upload_file(bucket_name, file_name):
    """Send file to bucket."""
    print("\n")
    print("upload_file: "+bucket_name+"/"+file_name)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    blob.upload_from_filename(file_name)

    return 

def download_file(bucket_name, file_name):
    """ Retrieve an object from a bucket and saves locally"""  
    print("\n")
    print("download_file: "+bucket_name+"/"+file_name)
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(file_name)
    blob.download_to_filename('files/'+file_name)
    blob.reload()

    return

@app.route('/')
def index():
    files = get_list_of_files(BUCKET_NAME)
    image_list = [file for file in files if file.lower().endswith(('.jpeg', '.jpg'))]
    
    index_html = """
    <body style="background-color: green;">
    <form method="post" enctype="multipart/form-data" action="/upload">
      <label for="file">Choose file to upload</label>
      <input type="file" id="file" name="form_file" accept="image/jpeg"/>
      <button>Submit</button>
    </form>
    <ul>
    """
    for img in image_list:
        index_html += f'<li><a href="/files/{img}"><img src="/serve-image/{img}" style="width:100px;height:auto;"></a></li>'
    index_html += "</ul>"
    return index_html

@app.route('/upload', methods=["POST"])
def upload():
    file = request.files['form_file']  # item name must match name in HTML form
    file.save(file.filename)

    upload_file(BUCKET_NAME, file.filename)

    metadata = upload_to_gemini(file.filename, mime_type="image/jpeg")
    save_metadata(BUCKET_NAME, file.filename, metadata)
  
    return redirect("/")

@app.route('/files')
def list_files():
    files = get_list_of_files(BUCKET_NAME)
    jpegs = []
    for file in files:
        if file.lower().endswith(".jpeg") or file.lower().endswith(".jpg"):
            jpegs.append(file)
    
    return jpegs

@app.route('/files/<filename>')
def get_file(filename):
    download_file(BUCKET_NAME, filename)  

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    json_blob = bucket.blob(filename.replace('.jpeg', '.json').replace('.jpg', '.json'))

    if json_blob.exists():
        metadata = json.loads(json_blob.download_as_text())
        return render_template_string("""
        <h1>{{ title }}</h1>
         <img src="{{ url_for('serve_image', filename=filename) }}" style="max-width:100%;">
        <p>{{ description }}</p>
        <a href="/">Back</a>
        """, title=metadata["title"], description=metadata["description"], bucket=BUCKET_NAME, filename=filename)
    else:
        return "Metadata not found", 404

        
if __name__ == '__main__':
    app.run(debug=True)