from fastapi import FastAPI, Request, APIRouter, BackgroundTasks, Query
from sse_starlette import EventSourceResponse
from fastapi.responses import JSONResponse
import asyncio
import importlib
import prompts
import uuid
from pydantic import BaseModel
from typing import List
from scrape_links import scrape_links, scrape_text
from mongo_utils import save_links_to_db, create_chatbot
from store_response import store_extra, store_text, proper_query, notification, chat_activity, delete_chat_history,get_prompt,update_prompt,store_test,getpage,deletechroma
from typing import Optional

api2_router = APIRouter()

async def process_links(url, user_id, chatbot_name,chatbotId=None):
    """Process scraped links and persist data even if the client disconnects."""
    print("data called")
    visited_links = set()
    async for link in scrape_links(url, visited_links):
        visited_links.add(link)
    chatBotId = chatbotId if chatbotId else await create_chatbot(user_id, chatbot_name, 'weblink')
    print("data saved")
    await save_links_to_db(chatBotId, visited_links)
    

@api2_router.get("/links")
async def scrape(
    request: Request, url: str, user_id: str, chatbotName: str, chatbotId: Optional[str] = Query(None)
): 
    try:
        visited_links = set()
        print("Links are fetching")
        # Start processing links in the background immediately
        # background_tasks.add_task(process_links, url, user_id, chatbotName, chatbotId)
        asyncio.create_task(process_links(url, user_id, chatbotName, chatbotId))

        async def link_stream():
            try:
                async for link in scrape_links(url, visited_links):
                    yield link
                    await asyncio.sleep(0.1)
            except GeneratorExit:  # Triggers when the client disconnects
                print(f"Client disconnected: Stopping data stream for {user_id}")

        return EventSourceResponse(link_stream())
    
    except Exception as e:
        print("The error is:", e)


class LinksRequest(BaseModel):
    links: List[str]
    chatbotId: str

class LinkRequest(BaseModel):
    url:str

# Combined API endpoint
@api2_router.post("/linktest")
async def scrape(request: LinkRequest):
    try:
        url = request.url
        visited_links = set()
        links = []
        async for link_message in scrape_links(url, visited_links):
            links.append(link_message)
        text_data = scrape_text(links)
        collection_id = store_test(text_data)
        return {"chatbotId": collection_id}
    except Exception as e:
        print("The error is: ",e)

async def background_scrape_and_store(links, chatbotId):
    """Scrape text from links and store it, ensuring it runs to completion."""
    try:
        text_data = await scrape_text(links, chatbotId)
        collection_id = await store_text(text_data, chatbotId)
        print(f"Scraping completed successfully for chatbotId: {chatbotId}")
    except Exception as e:
        print(f"Error in background processing: {e}")

@api2_router.post("/scrape")
async def scrape(request: LinksRequest, background_tasks: BackgroundTasks):
    try:
        links = request.links  
        chatbot_id = request.chatbotId if request.chatbotId != "null" else str(uuid.uuid4())
        if request.chatbotId == "null":
            create_chatbot(request.userId, request.chatbot_name, "modelTrain", chatbot_id)
        asyncio.create_task(background_scrape_and_store(links, chatbot_id))
        return {"message": "Scraping started, data will be stored once completed", "chatbotId": request.get("chatbotId")}
    
    except Exception as e:
        print("Error training model:", e)
        return JSONResponse(content={"error": "Error training model"}, status_code=500)

class TextRequest(BaseModel):
    chatbotId: str
    textData: str

@api2_router.post("/texttrain")
async def scrape(request: TextRequest):
    text = request.textData  
    text_data = scrape_text(text)  
    collection_id = store_text(text_data)
    return {"chatbotId": collection_id}

@api2_router.post("/addData")
async def scrape(request: TextRequest):
    chatbotId = request.chatbotId
    text = request.textData
    return {"chatbotId": store_extra(chatbotId,text)}

class ResponseRequest(BaseModel):
    question: str
    userid: str
    chatbotid: str

@api2_router.post('/chatresponse')
async def response(request: ResponseRequest):
    result = proper_query(request.question, request.userid, request.chatbotid)
    return {"data": result}

@api2_router.get('/chathistory')
async def history(request: Request, userid: str, chatbotid: str):
    return notification(userid, chatbotid)

@api2_router.get('/chatactivity')
async def activity(request: Request, chatbotid: str):
    return chat_activity(chatbotid)

qbotpromptnew=prompts.qbotprompt_new

def prompt_change(prompt:str):
    global qbotpromptnew
    qbotpromptnew=prompt
    return {"message": f"Prompt updated successfully: {qbotpromptnew}"}

class PromptRequest(BaseModel):
    prompt:str

# Pydantic model for the prompt
class PromptUpdate(BaseModel):
    prompt: str

@api2_router.get("/prompt", response_model=dict)
def get_prompt1():
    return get_prompt()

@api2_router.put("/prompt")
def update_prompt1(prompt_update: PromptUpdate):
    return update_prompt(prompt_update.prompt)

@api2_router.delete('/reset')
async def delete_chat_historys(userid="dbfudovn",chatbotid="nvnobvneri"):
    userid="dbfudovn"
    chatbotid="nvnobvneri"
    deletechroma(chatbotid)
    return delete_chat_history(userid,chatbotid)

class QuestionRequest(BaseModel):
    question: str

@api2_router.post('/testing')
async def testing(questions:QuestionRequest):
    result = proper_query(questions.question, "dbfudovn","nvnobvneri")
    return {"data": result}

@api2_router.get("/pageview")
async def pageview(id:str):
    page=getpage(id)
    return page

    
@api2_router.get("/")
async def hello():
    return JSONResponse(content={"response": "Hello!"})

# app.include_router(api2_router, prefix='/chatlaps')

# uvicorn api2_router:api2_router --host 192.168.0.100 --port 5001 --reload
