from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    response: str
    driving_status: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    driving_status: Optional[str] = "parked"  # parked, city_driving, highway, traffic

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str


# AI Car Assistant System Prompt
def get_car_assistant_prompt(driving_status: str = "parked") -> str:
    base_prompt = """You are an expert AI car assistant specializing in automotive maintenance, performance optimization, and driving advice. You have extensive knowledge about:

- Car maintenance schedules and procedures
- Performance optimization techniques
- Fuel efficiency tips
- Engine diagnostics and troubleshooting
- Tire care and safety
- Seasonal car care
- Emergency roadside assistance
- Car features and technology

Current driving context: {driving_status}

Guidelines:
- Always provide practical, safe, and actionable advice
- Consider the current driving status when giving recommendations
- Prioritize safety above all else
- Be specific about maintenance intervals and procedures
- Explain technical concepts in accessible language
- Ask clarifying questions when needed (car make/model, year, etc.)

For performance optimization:
- If parked: Focus on maintenance planning, pre-drive checks, and long-term optimization
- If city driving: Emphasize fuel efficiency, stop-and-go techniques, and urban driving tips
- If highway driving: Focus on cruise control, aerodynamics, and highway efficiency
- If in traffic: Provide stress reduction tips, engine care during idling, and safety advice

Always be helpful, knowledgeable, and safety-conscious."""

    driving_specific = {
        "parked": "The user is currently parked. Focus on maintenance planning, pre-drive checks, and preparation advice.",
        "city_driving": "The user is city driving. Provide real-time advice for stop-and-go traffic, fuel efficiency in urban environments, and city-specific tips.",
        "highway": "The user is on the highway. Focus on cruise control optimization, highway fuel efficiency, and long-distance driving tips.",
        "traffic": "The user is stuck in traffic. Provide advice for engine care during idling, stress reduction, and traffic-specific safety tips."
    }
    
    return base_prompt.format(driving_status=driving_status) + "\n\n" + driving_specific.get(driving_status, driving_specific["parked"])


async def get_ai_response(message: str, session_id: str, driving_status: str = "parked") -> str:
    """Get AI response using emergentintegrations LlmChat with fallback"""
    try:
        # Initialize chat with car-focused system prompt
        system_prompt = get_car_assistant_prompt(driving_status)
        
        chat = LlmChat(
            api_key=os.environ['OPENAI_API_KEY'],
            session_id=session_id,
            system_message=system_prompt
        ).with_model("openai", "gpt-4o")
        
        # Create user message
        user_message = UserMessage(text=message)
        
        # Get response
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        logging.error(f"AI response error: {str(e)}")
        
        # Check if it's a quota/billing error and provide more specific guidance
        if "quota" in str(e).lower() or "billing" in str(e).lower():
            return get_fallback_response(message, driving_status)
        
        return "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment."


def get_fallback_response(message: str, driving_status: str = "parked") -> str:
    """Provide intelligent fallback responses when AI is unavailable"""
    message_lower = message.lower()
    
    # Cold weather checks
    if any(word in message_lower for word in ["cold", "winter", "morning", "start"]):
        return f"""For cold weather starting (Current status: {driving_status}):

🔧 **Pre-Start Checks:**
• Check tire pressure (cold weather reduces pressure)
• Ensure battery connections are clean and tight
• Verify coolant levels aren't frozen
• Check oil viscosity (use winter-grade oil if needed)

⚡ **Starting Tips:**
• Turn off all accessories before starting
• Let the engine warm up for 30-60 seconds before driving
• Don't rev the engine while cold
• Check that lights and defrosters work properly

💡 **Performance Tip for {driving_status.replace('_', ' ').title()}:**
{get_status_specific_tip(driving_status)}

*Note: AI service temporarily unavailable - using expert-curated responses*"""

    # Maintenance questions
    elif any(word in message_lower for word in ["maintenance", "service", "check", "schedule"]):
        return f"""**Regular Maintenance Schedule:**

🔧 **Every Month:**
• Check tire pressure and tread depth
• Inspect lights, wipers, and fluid levels
• Test battery connections

🛠️ **Every 3,000-5,000 miles:**
• Oil and filter change
• Check belts and hoses
• Inspect brake pads

📅 **Every 6 months:**
• Rotate tires
• Check alignment
• Replace air filter

**Current Status Consideration ({driving_status.replace('_', ' ').title()}):**
{get_status_specific_tip(driving_status)}

*Note: AI service temporarily unavailable - using expert-curated responses*"""

    # Performance optimization
    elif any(word in message_lower for word in ["performance", "optimize", "fuel", "efficiency", "mpg"]):
        return f"""**Performance Optimization Tips:**

⚡ **Fuel Efficiency:**
• Maintain steady speeds (use cruise control on highway)
• Keep tires properly inflated
• Remove excess weight from vehicle
• Regular engine tune-ups

🏎️ **Engine Performance:**
• Use recommended octane fuel
• Replace air filter regularly
• Keep fuel injectors clean
• Monitor engine oil quality

**For {driving_status.replace('_', ' ').title()} Status:**
{get_status_specific_tip(driving_status)}

*Note: AI service temporarily unavailable - using expert-curated responses*"""

    # General car questions
    else:
        return f"""**General Car Care Advice:**

🚗 **Daily Checks:**
• Monitor dashboard warning lights
• Check that all lights function properly
• Ensure adequate fuel levels
• Listen for unusual noises

🔧 **Weekly Checks:**
• Tire pressure and visual inspection
• Fluid levels (oil, coolant, washer fluid)
• Battery terminals for corrosion

**Context for {driving_status.replace('_', ' ').title()}:**
{get_status_specific_tip(driving_status)}

For specific questions about your vehicle, consult your owner's manual or a certified mechanic.

*Note: AI service temporarily unavailable - using expert-curated responses*"""


def get_status_specific_tip(driving_status: str) -> str:
    """Get driving status specific tips"""
    tips = {
        "parked": "Perfect time for maintenance checks and planning your next service!",
        "city_driving": "Use gentle acceleration/braking to improve fuel economy in stop-and-go traffic.",
        "highway": "Maintain steady speeds and use cruise control for optimal fuel efficiency.",
        "traffic": "Turn off A/C if overheating in traffic, and avoid excessive idling to save fuel."
    }
    return tips.get(driving_status, "Safe driving is the best performance optimization!")


# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "AI Car Assistant API"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get AI response
        ai_response = await get_ai_response(
            request.message, 
            session_id, 
            request.driving_status or "parked"
        )
        
        # Save to database
        chat_message = ChatMessage(
            session_id=session_id,
            message=request.message,
            response=ai_response,
            driving_status=request.driving_status
        )
        
        await db.chat_messages.insert_one(chat_message.dict())
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            message_id=chat_message.id
        )
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@api_router.get("/chat/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        
        return [ChatMessage(**msg) for msg in messages]
        
    except Exception as e:
        logging.error(f"Chat history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
