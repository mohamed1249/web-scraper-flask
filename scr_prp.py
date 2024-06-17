import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import json
from pymongo import MongoClient
import uuid
from PyPDF2 import PdfReader


def clean_title(title):
    # Remove invalid characters from the title and replace them with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', title)

def scrape_page_content(url):
    # try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            divs = soup.find_all("div")
            # paragraphs = soup.find_all('p')
            # spans = soup.find_all("span")
            # lis = soup.find_all("li")
            # h1s = soup.find_all("h1")
            # h2s = soup.find_all("h2")


            content = '\n'.join(div.get_text() for div in divs)
            # content += '\n'.join(paragraph.get_text() for paragraph in paragraphs)
            # content += '\n'.join(span.get_text() for span in spans)
            # content += '\n'.join(li.get_text() for li in lis)
            # content += '\n'.join(h1.get_text() for h1 in h1s)
            # content += '\n'.join(h2.get_text() for h2 in h2s)
            clean_content = []
            for c in content.split('\n'):
                if c in clean_content:
                    continue
                else:
                    clean_content.append(c)

            content = re.sub('\n+', '\n', re.sub(r'[ \t]+', ' ','\n'.join(clean_content))).strip().replace('\n ','\n').replace('\n\n', '\n')

            return content
        else:
            print(f"\tFailed to fetch {url}")
            return None
    # except:
    #     scrape_page_content(url[1:])
        

def save_seprated(dct,path):
    for key, value in dct.items():
        sub_dict = {'URL':key, 'Content': value['content']}
        cleaned_title = clean_title(key)
        json_filename = f"{cleaned_title}.json"
        json_path = os.path.join(path, json_filename)
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(sub_dict, json_file, ensure_ascii=False, indent=4)

def scrape_page_and_subpages_content(url, main_content=True, timeout=30):
    """
    Scrapes the text content of a webpage and optionally its sub-links recursively.

    Args:
      url: The URL of the page to scrape.
      main_content: Boolean indicating whether to scrape the main content of the page.
      timeout: The maximum time to wait for a response in seconds (default: 10).

    Returns:
      A dictionary containing the combined text content of the page and its sub-links.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"\tFailed to fetch {url}: {e}")
        return None

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract content from current page
        content = {}
        if main_content:
            content[url] = {'content': scrape_page_content(url), 'main_content': True, 'link_no': 0}
            print(f"\t{0} - Scraped main-content from {url}")

        # Extract and recursively scrape sub-links
        sub_links = list({a['href'] for a in soup.find_all('a', href=True) if 'facebook' not in a['href']})
        print(f' ({len(sub_links)} links)')
        for i, sub_link in enumerate(sub_links):
            try:
                sub_content = scrape_page_content(sub_link)
                if sub_content:
                    content[sub_link] = {'content': sub_content, 'main_content': False, 'link_no': i+1}
                    print(f"\t{i+1} - Scraped sub-content from {sub_link}")
            except:
                sub_link = '/'.join(url.split('/')[:-1]) + sub_link
                try:
                    sub_content = scrape_page_content(sub_link)
                    if sub_content:
                        content[sub_link] = {'content': sub_content, 'main_content': False, 'link_no': i+1}
                        print(f"\t{i+1} - Scraped sub-content from {sub_link}")
                except:
                    print(f"\t{i+1} - Failed to scrape sub-content from {sub_link}")
        return content, len(sub_links)

    else:
        print(f"\tFailed to fetch {url}")
        return None


def download_pdfs_from_url(url):
    PDFs = {}
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)

        for i,link in enumerate(links):
            href = link['href']
            title = link.get_text()
            download_link = urljoin(url, href)
            try:
                filename = download_pdf(download_link, title, i)
                if filename and is_valid_pdf(os.path.join('PDFs',filename)):
                    PDFs[filename] = download_link
                    print(f"Downloaded: {filename}")
                else:
                    if filename:
                        os.remove(os.path.join('PDFs',filename))  # Delete the invalid PDF file
                    print(f"Invalid PDF found at {download_link}")
            except Exception as e:
                print(f'Error processing {download_link}: {e}')

        return PDFs
    else:
        print(f"Failed to fetch {url}")

def make_valid_filename(url):
    # Define a regular expression pattern to match invalid characters
    invalid_chars_pattern = r'[\/:*?"<>|]'

    # Replace invalid characters with underscores
    valid_filename = re.sub(invalid_chars_pattern, '_', url)

    return valid_filename

def download_pdf(url, title, i):
    response = requests.get(url)
    if response.status_code == 200:
        # Clean the title before using it as the filename
        cleaned_title = clean_title(title).strip()
        if cleaned_title:
            filename = f"{cleaned_title}.pdf"
        else:
            filename = f"{make_valid_filename(url)}{i}.pdf"
        filename = unquote(filename)  # Decode any URL-encoded characters in the title
        with open(os.path.join('PDFs',filename), 'wb') as file:
            file.write(response.content)
        return filename
    else:
        print(f"Failed to download {url}")
        return None

def is_valid_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            return len(pdf_reader.pages) > 0
    except Exception as e:
        print(e)
        return False

# if __name__ == "__main__":

#     # Read the URLs from the URLs.txt file
#     with open("URLs.txt", "r") as file:
#         urls = file.read().splitlines()

#     for url in urls:
#         # Download PDFs from the page
#         PDFs = download_pdfs_from_url(url)

#         # Scrape the content of the page and save it to a JSON file
#         page_content = scrape_page_content(url)
#         if page_content:
#             cleaned_title = clean_title(url)
#             json_filename = f"{cleaned_title}.json"
#             json_path = os.path.join("JSONs", json_filename)
#             with open(json_path, "w", encoding="utf-8") as json_file:
#                 json.dump({"webpage_url": url, "content": page_content, 'attached_PDFs':PDFs}, json_file, ensure_ascii=False, indent=4)
#             print(f"Scraped {url} and saved the content to {json_filename}")

from PyPDF2 import PdfReader

def extract_pdf_pages(pdf_file_path):
    pdf_pages = []
    with open(pdf_file_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        for page_number in range(len(reader.pages)):
            pdf_page_info = {
                'information': reader.pages[page_number].extract_text(),
                'source_file_name': os.path.basename(pdf_file_path),
                'page_number': page_number + 1
            }
            pdf_pages.append(pdf_page_info)
    return pdf_pages

# # Load the content JSON files
# json_files_directory = "JSONs"

# for root, _, files in os.walk(json_files_directory):
#     for file in files:
#         if file.endswith(".json"):
#             json_file_path = os.path.join(root, file)
#             with open(json_file_path, "r", encoding="utf-8") as json_file:
#                     data = json.load(json_file)
#                     attached_pdfs = data.get("attached_PDFs")
#                     page_URL = data.get("webpage_url")
#                     if attached_pdfs:
#                         for pdf_file_name, pdf_download_url in attached_pdfs.items():
#                             pdf_file_path = os.path.join("PDFs", pdf_file_name)
#                             pdf_pages_data = extract_pdf_pages(pdf_file_path, pdf_download_url, page_URL)
#                             # Save the collected PDF pages data to a new JSON file
#                             pdf_filename = os.path.splitext(pdf_file_name)[0]
#                             output_json_file_path = os.path.join("JSONs", f"{pdf_filename}_pages_data.json")
#                             with open(output_json_file_path, "w", encoding="utf-8") as output_json_file:
#                                 json.dump(pdf_pages_data, output_json_file, ensure_ascii=False, indent=4)


def save_to_mongodb(collection, file_name, content):
    # Check if a document with the same file_name exists in the collection
    existing_document = collection.find_one({"file_name": file_name})

    # If an existing document is found, update it; otherwise, insert a new document
    if existing_document:
        collection.replace_one({"file_name": file_name}, {'content':content})
        print(f'Updated: {file_name} in {collection.name} of {collection.database.name}')
    else:
        collection.insert_one({"file_name": file_name, "content": content})
        print(f'Saved: {file_name} to {collection.name} of {collection.database.name}')

# # Connect to MongoDB
# client = MongoClient("mongodb://localhost:27017/")
# db = client["ggdwb"] # DataBase Name
# collection = db["JSONs"] # collection name

# for file in os.listdir('JSONs'):
#     # Save the JSON data to MongoDB
#     collection.rep
#     with open(os.path.join('JSONs',file), "r", encoding="utf-8") as json_file:
#         json_data = json.load(json_file)
#         save_to_mongodb(collection, file, json_data)

# bad_directories = ['JSONs','PDFs']

# for dir in bad_directories:
#     # Delete files in the 'data' directory
#     for filename in os.listdir(dir):
#         file_path = os.path.join(dir, filename)
#         if os.path.isfile(file_path):
#             os.remove(file_path)

def delete_files_in_current_directory(file_extensions=None):
    current_directory = os.getcwd()  # Get the current working directory

    if file_extensions is None:
        file_extensions = []  # Delete all files

    for filename in os.listdir(current_directory):
        if any(filename.lower().endswith(ext.lower()) for ext in file_extensions):
            try:
                os.remove(filename)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")