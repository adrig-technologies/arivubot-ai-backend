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

async def save_links_to_db(user_id, links):
    """Save unique links in MongoDB under the given user_id."""
    collection = db.weblink
    await collection.update_one(
        {"user_id": user_id}, 
        {"$addToSet": {"links": {"$each": list(links)}}}, 
        upsert=True
    )

async def create_chatbot(user_id,name, flag):
    chatbots_collection = db.chatbots
    chatbot_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()
    new_chatbot = {
        "name": name,
        "chatbotId": chatbot_id,
        "userid": ObjectId(user_id),
        "botState": flag,
        "fontSize": 12,
        "fontColor": "#111827",
        "fontStyle": "font-sans",
        "desc": "",
        "headerAlign": "justify-center",
        "bgColor": "#fff",
        "innerButtonColor": "#000000",
        "outerButtonColor": "#000000",
        "userChatBg": "#d1fae5",
        "botChatBg": "#f1f0f0",
        "logoPosition": "right",
        "logoBottomPosition": 20,
        "createdAt": current_time,
        "updatedAt": current_time,
    }
    result = await chatbots_collection.insert_one(new_chatbot)
    return result

async def scrape_text(data, chatbot_id):
    chatbots_collection = db.chatbots
    await chatbots_collection.update_one(
    {"chatbotId": chatbot_id},  
    {"$set": {"botState": "modelTrain"}}  
    )
    if type(data) == list:
        loader = UnstructuredURLLoader(data)
        docs = loader.load()
    elif type(data) == str:
        docs = [Document(page_content=data)]
    return docs
