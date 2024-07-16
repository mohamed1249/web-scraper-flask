# Web Scraper with Google Drive and MongoDB Integration

This Python project provides a Flask API for scraping webpages, extracting content, and handling PDF files. Additionally, it integrates with Google Drive to download PDFs from specified folders and supports MongoDB for storing the scraped content.

## Key Functionalities

### 1. Scrape Webpage Content:
- **Endpoint:** `/scrape`
- **Method:** POST
- **Description:**
  - Users can submit a list of URLs through a POST request.
  - The API retrieves content from the provided URLs, focusing on text within `<div>` elements.
  - It cleans the extracted content by removing unnecessary characters and whitespaces.
  - Scraped content is saved as JSON files in a directory named "JSONs".

### 2. Download Attached PDFs:
- **Description:**
  - Users can specify whether to download PDFs attached to the webpage in the JSON request.
  - The API identifies and downloads PDFs from the provided URLs.
  - Downloaded PDFs are saved in a directory named "PDFs".

### 3. Extract PDF Text:
- **Description:**
  - Text from downloaded PDFs is extracted and saved as separate JSON files within the "JSONs" directory.
  - Each JSON file represents a single PDF and includes information like page content, source filename, and page number.

### 4. MongoDB Integration (Optional):
- **Description:**
  - Users can provide a database name in the JSON request.
  - The API attempts to connect to a local MongoDB instance (localhost:27017) and save the scraped content to a collection named "JSONs".
  - If MongoDB connection fails, the API returns an error message.

### 5. Google Drive Integration:
- **Endpoint:** `/drive`
- **Method:** POST
- **Description:**
  - Users can specify a Google Drive folder ID to download PDFs from.
  - The API uses Google Drive API to download PDFs from the specified folder and subfolders.
  - Downloaded PDFs are processed similarly to those from webpages.

### 6. API Security:
- **Description:**
  - API endpoints are protected by requiring a valid API key in the request header.
  - Invalid API keys result in a 401 (Unauthorized) error response.

### 7. Error Handling:
- **Description:**
  - The API handles potential errors gracefully and returns appropriate error messages for issues like:
    - Invalid URLs
    - Download failures
    - PDF processing errors
    - MongoDB connection errors
  - Successful scrapes return a message indicating completion.

### Additional Considerations:
- This is a basic implementation and could be extended to support more complex scraping requirements, such as handling multiple content sections or different HTML elements.
- Security could be further enhanced by implementing rate limiting or user authentication mechanisms.
- Error handling could be improved by providing more specific error messages for different failure scenarios.

## Example Usage:

### Install Dependencies:
```bash
pip install flask requests beautifulsoup4 pymongo PyPDF2 google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Run the Server:
```bash
python web_scraper_flask.py
```

### Scrape a Webpage (using `curl`):
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "API-KEY: your_api_key" \
  -d '{"URLs": ["https://example.com"], "download_pdfs": "y", "download_content": "y", "db": "my_database"}' \
  http://localhost:8080/scrape
```
Replace `your_api_key` with your actual API key and adjust the URL and database name as needed. The response will indicate success or any encountered errors.

### Download PDFs from Google Drive (using `curl`):
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "API-KEY: your_api_key" \
  -d '{"folder_id": "your_drive_folder_id", "db": "my_database"}' \
  http://localhost:8080/drive

