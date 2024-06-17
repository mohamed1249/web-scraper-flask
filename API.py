from flask import Flask, request, abort
from flask_cors import CORS,cross_origin
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from scr_prp import *


data = {
    'scrape': {
         'API_KEY' : "scr-",
    },
    'drive': {
         'API_KEY' : "drv-",
    }
}

print('Server Started!')
app = Flask(__name__)
app.config['CORS_HEADERS'] = ['Content-Type', 'API-KEY']
cors = CORS(app,origins=['https://sayhaito.com','http://sayhaito.com'])

@app.route("/scrape", methods=['POST'])
@cross_origin(origin=['https://sayhaito.com','http://sayhaito.com'],headers=['Content-Type','API-KEY'])
def scrape():

    api_key = request.headers.get("API-KEY")
    
    if api_key != data["scrape"]['API_KEY']:
        abort(401, "Invalid API key")

    errors = []
    urls = request.json.get('URLs')
    download_pdfs = request.json.get('download_pdfs')
    download_content = request.json.get('download_content')
    db = request.json.get("db")

    # List of directories to ensure existence
    directories_to_create = ['JSONs' ,'PDFs']

    for directory in directories_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory)

    for url, dpdf, dc in zip(urls, download_pdfs, download_content):
        if dpdf.lower() != 'n':
            try:
                # Download PDFs from the page
                PDFs = download_pdfs_from_url(url)
            except Exception as e:
                PDFs = []
                error_message = f'Error downloading PDFs from {url}: {e}'
                print(error_message)
                errors.append(error_message)


        if dc.lower() != 'n':
            # Scrape the content of the page and save it to a JSON file
            try:
                page_content = scrape_page_content(url)
            except Exception as e:
                PDFs = []
                error_message = f'Error geting page contents from {url}: {e}'
                print(error_message)
                errors.append(error_message)
                page_content = False

            if page_content:
                cleaned_title = clean_title(url)
                json_filename = f"{cleaned_title}.json"
                json_path = os.path.join("JSONs", json_filename)
                with open(json_path, "w", encoding="utf-8") as json_file:
                    json.dump({"webpage_url": url, "content": page_content, 'attached_PDFs':PDFs}, json_file, ensure_ascii=False, indent=4)
                print(f"Scraped {url} and saved the content to {json_filename}")

    pdfs_directory = "PDFs"

    for root, _, files in os.walk(pdfs_directory):
        for file in files:
            try:
                if file.endswith(".pdf"):
                    pdf_file_path = os.path.join(root, file)
                    pdf_pages_data = extract_pdf_pages(pdf_file_path)
                    pdf_filename = os.path.splitext(file)[0]
                    output_json_file_path = os.path.join("JSONs", f"{pdf_filename}_pages_data.json")
                    with open(output_json_file_path, "w", encoding="utf-8") as output_json_file:
                        json.dump(pdf_pages_data, output_json_file, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Couldn't process {file}: {e}")

    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db_ = client[db] # DataBase Name
        collection = db_["JSONs"] # collection name
    except:
        abort(402, "Database Connection Error!")

    for file in os.listdir('JSONs'):
        # Save the JSON data to MongoDB
        collection.rep
        with open(os.path.join('JSONs',file), "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)
            save_to_mongodb(collection, file, json_data)

    bad_directories = ['JSONs','PDFs']

    for dir in bad_directories:
        # Delete files in the 'data' directory
        for filename in os.listdir(dir):
            file_path = os.path.join(dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(dir)  # Remove an empty directory

    # Call the function to delete specific file types (e.g., .pdf files)
    delete_files_in_current_directory(file_extensions=['.pdf'])

    print('Done!')

    if errors:
        return {'errors' : errors}
    else:
        return {'errors' : 'All Completed Successfully!'}
    
@app.route("/drive", methods=['POST'])
@cross_origin(origin=['https://sayhaito.com','http://sayhaito.com'],headers=['Content-Type','API-KEY'])
def drive():

    api_key = request.headers.get("API-KEY")
    
    if api_key != data["drive"]['API_KEY']:
        abort(401, "Invalid API key")

    folder_id = request.json.get('folder_id')
    db = request.json.get("db")

     # List of directories to ensure existence
    directories_to_create = ['JSONs' ,'PDFs']

    for directory in directories_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory)

    SCOPES = ['https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_file(
        'llm-search-amphia-01a3fcf335ad.json', scopes=SCOPES)
    
    # Create a service object
    service = build('drive', 'v3', credentials=credentials)

    

    def download_pdf_files_in_folder(folder_id):
        # List all files in the specified folder
        results = service.files().list(q=f"'{folder_id}' in parents").execute()
        files = results.get('files', [])

        if not files:
            print(f'No files found in the folder with ID: {folder_id}')
        else:
            for file in files:
                file_name = file['name']
                file_id = file['id']
                mime_type = file['mimeType']

                if 'pdf' in mime_type:
                    # Download the PDF file
                    request = service.files().get_media(fileId=file_id)
                    with open(os.path.join('PDFs',file_name), 'wb') as file:
                        file.write(request.execute())
                    print(f'Downloaded PDF: {file_name}')

                if mime_type == 'application/vnd.google-apps.folder':
                    # If it's a subfolder, recursively search and download PDFs
                    download_pdf_files_in_folder(file_id)

    download_pdf_files_in_folder(folder_id)

    pdfs_directory = "PDFs"

    for root, _, files in os.walk(pdfs_directory):
        for file in files:
            try:
                if file.endswith(".pdf"):
                    pdf_file_path = os.path.join(root, file)
                    pdf_pages_data = extract_pdf_pages(pdf_file_path)
                    pdf_filename = os.path.splitext(file)[0]
                    output_json_file_path = os.path.join("JSONs", f"{pdf_filename}_pages_data.json")
                    with open(output_json_file_path, "w", encoding="utf-8") as output_json_file:
                        json.dump(pdf_pages_data, output_json_file, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Couldn't process {file}: {e}")

    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db_ = client[db] # DataBase Name
        collection = db_["JSONs"] # collection name
    except:
        abort(402, "Database Connection Error!")

    for file in os.listdir('JSONs'):
        # Save the JSON data to MongoDB
        collection.rep
        with open(os.path.join('JSONs',file), "r") as json_file:
            json_data = json.load(json_file)
            save_to_mongodb(collection, file, json_data)
            print(f"{file} saved to {db}\JSONs database")

    bad_directories = ['JSONs','PDFs']

    for dir in bad_directories:
        # Delete files in the 'data' directory
        for filename in os.listdir(dir):
            file_path = os.path.join(dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(dir)  # Remove an empty directory

    # Call the function to delete specific file types (e.g., .pdf files)
    delete_files_in_current_directory(file_extensions=['.pdf'])

    print('Done!')

    return {'done' : 'All Completed Successfully!'}



if __name__ == "__main__":
    app.run(threaded=True, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
