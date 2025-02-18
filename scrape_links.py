from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.schema import Document
from pymongo import MongoClient
import dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime
from bson import ObjectId

from mongo_utils import update_chatbot_state

dotenv.load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


client = AsyncIOMotorClient(MONGO_URI)
db = client.arivubotDB

# Scrape Links
# async def scrape_links(url, visited=None):
#     if visited is None:
#         visited = set()

#     links_to_visit = set()
#     base_netloc = urlparse(url).netloc  

#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, 'html.parser')

#         for a_tag in soup.find_all('a', href=True):
#             absolute_url = urljoin(url, a_tag['href'])
#             normalized_url, _ = urldefrag(absolute_url)
#             normalized_url = normalized_url.rstrip('/')

#             # Only add links with the same base domain that haven't been visited
#             if urlparse(normalized_url).netloc == base_netloc and normalized_url not in visited:
#                 links_to_visit.add(normalized_url)

#         visited.add(url.rstrip('/'))

#         for link in links_to_visit.copy():
#             yield link
#             # Change 'await scrape_links(link, visited)' to async for to iterate over the generator
#             async for new_link in scrape_links(link, visited):
#                 yield new_link

#         # Yield the links instead of returning them
#         for link in links_to_visit:
#             yield link

#     except requests.exceptions.RequestException as e:
#         yield f"Error occurred while fetching the webpage: {e}\n"

async def scrape_links(url, visited):
    """Crawl links within the same domain and yield unique ones."""
    base_netloc = urlparse(url).netloc
    links_to_visit = set()

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for a_tag in soup.find_all('a', href=True):
            absolute_url = urljoin(url, a_tag['href'])
            normalized_url, _ = urldefrag(absolute_url)
            normalized_url = normalized_url.rstrip('/')

            if urlparse(normalized_url).netloc == base_netloc and normalized_url not in visited:
                links_to_visit.add(normalized_url)

        visited.add(url.rstrip('/'))

        for link in links_to_visit:
            yield link
            async for new_link in scrape_links(link, visited):
                yield new_link

    except requests.exceptions.RequestException as e:
        yield f"Error: {e}"


async def scrape_text(data, chatbot_id):
    await update_chatbot_state(chatbot_id,"modelTrain")
    if type(data) == list:
        loader = UnstructuredURLLoader(data)
        docs = loader.load()
    elif type(data) == str:
        docs = [Document(page_content=data)]
    return docs
