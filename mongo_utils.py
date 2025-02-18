import os
import uuid
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import dotenv

dotenv.load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.arivubotDB

def get_db():
    return db

async def save_links_to_db(chatBotId, links):
    """Save unique links in MongoDB under the given user_id."""
    collection = db.weblink
    await collection.update_one(
        {"chatBotId": chatBotId}, 
        {"$addToSet": {"links": {"$each": list(links)}}}, 
        upsert=True
    )

async def create_chatbot(user_id, name, flag):
    """Create a new chatbot and store it in the database."""
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
    return chatbot_id

async def update_chatbot_state(chatbot_id, state):
    """Update chatbot state in the database."""
    chatbots_collection = db.chatbots
    await chatbots_collection.update_one(
        {"chatbotId": chatbot_id}, 
        {"$set": {"botState": state}}
    )
