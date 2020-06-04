# simple_website_crawler
Just a simple website_crawler - very basic, using Python. Returns all internal links, it can found.

Internal links are selected using BeautifulSoup's SoupSieve select. It looks for a[href] in the html, which starts with URL's hostname or,
in case of relative links, it starts with "/".

## Requirements:
- Python3.+
- Packages:

  - BeautifulSoup4
  
  - lxml
  
  - requests
  
  - Colorama
  
## Usage:
Enter `python3 script.y http[s]://<hostname>`

Example: `python3 script.py https://www.example.com`

## Output:
- Displayes scanned links in the console, with response time and response code
- When the scan is done, saves links into the timestamped .csv file
