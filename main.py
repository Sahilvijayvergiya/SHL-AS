from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest, ChatResponse, HealthResponse
from agent import ConversationalAgent
from catalog import SHLCatalog
from retrieval import RetrievalSystem
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

app = FastAPI(title="SHL Assessment Recommendation Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for catalog and agent
catalog = SHLCatalog()
retrieval_system = None
agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize catalog and agent on startup."""
    global retrieval_system, agent
    
    # Try to load from JSON file first
    catalog_path = "shl_catalog_data.json"
    if os.path.exists(catalog_path):
        print("Loading catalog from JSON file...")
        catalog.load_from_json(catalog_path)
        print(f"Loaded {len(catalog.assessments)} assessments from catalog")
    else:
        print("Catalog file not found. Using empty catalog.")
        print("Please run scrape_catalog.py to generate the catalog first.")
        # Create a comprehensive sample catalog with realistic SHL assessments
        from catalog import Assessment
        catalog.assessments = [
            # Technical/Programming Assessments
            Assessment(
                name="Java 8 (New)",
                url="https://www.shl.com/products/product-catalog/view/java-8-new/",
                test_type="K",
                description="Assesses Java 8 programming skills including lambdas, streams, and functional programming.",
                duration="40 minutes",
                languages=["English"],
                job_levels=["Entry", "Junior", "Mid", "Senior"],
                categories=["IT", "Engineering", "Software Development"]
            ),
            Assessment(
                name="Python Programming",
                url="https://www.shl.com/products/product-catalog/view/python-programming/",
                test_type="K",
                description="Assesses Python programming skills including data structures, OOP, and common libraries.",
                duration="35 minutes",
                languages=["English"],
                job_levels=["Junior", "Mid", "Senior"],
                categories=["IT", "Engineering", "Software Development"]
            ),
            Assessment(
                name="JavaScript Programming",
                url="https://www.shl.com/products/product-catalog/view/javascript-programming/",
                test_type="K",
                description="Evaluates JavaScript skills including ES6+, DOM manipulation, and frameworks.",
                duration="35 minutes",
                languages=["English"],
                job_levels=["Junior", "Mid", "Senior"],
                categories=["IT", "Engineering", "Software Development"]
            ),
            Assessment(
                name="C++ Programming",
                url="https://www.shl.com/products/product-catalog/view/cpp-programming/",
                test_type="K",
                description="Tests C++ programming knowledge including memory management, STL, and OOP concepts.",
                duration="45 minutes",
                languages=["English"],
                job_levels=["Mid", "Senior"],
                categories=["IT", "Engineering", "Software Development"]
            ),
            Assessment(
                name=".NET Programming",
                url="https://www.shl.com/products/product-catalog/view/dotnet-programming/",
                test_type="K",
                description="Assesses .NET framework skills including C#, VB.NET, and ASP.NET.",
                duration="40 minutes",
                languages=["English"],
                job_levels=["Junior", "Mid", "Senior"],
                categories=["IT", "Engineering", "Software Development"]
            ),
            # Personality Assessments
            Assessment(
                name="OPQ32r",
                url="https://www.shl.com/products/product-catalog/view/occupational-personality-questionnaire-opq32r/",
                test_type="P",
                description="Occupational Personality Questionnaire measuring 32 personality traits relevant to workplace performance.",
                duration="30 minutes",
                languages=["English", "Spanish", "French", "German"],
                job_levels=["Entry", "Junior", "Mid", "Senior", "Executive"],
                categories=["Leadership", "Sales", "IT", "General"]
            ),
            Assessment(
                name="OPQ32i",
                url="https://www.shl.com/products/product-catalog/view/opq32i/",
                test_type="P",
                description="Internet-based version of OPQ32r with similar personality trait measurement.",
                duration="30 minutes",
                languages=["English", "Spanish"],
                job_levels=["Entry", "Junior", "Mid", "Senior", "Executive"],
                categories=["Leadership", "Sales", "IT", "General"]
            ),
            # Cognitive/Aptitude Assessments
            Assessment(
                name="GMA (General Mental Ability)",
                url="https://www.shl.com/products/product-catalog/view/gma/",
                test_type="A",
                description="Measures cognitive ability including numerical, verbal, and abstract reasoning.",
                duration="45 minutes",
                languages=["English", "Spanish"],
                job_levels=["Entry", "Junior", "Mid", "Senior"],
                categories=["IT", "Finance", "Sales", "General"]
            ),
            Assessment(
                name="Numerical Reasoning",
                url="https://www.shl.com/products/product-catalog/view/verify-numerical-ability/",
                test_type="A",
                description="Tests ability to interpret and analyze numerical data, charts, and graphs.",
                duration="20 minutes",
                languages=["English", "Spanish", "French"],
                job_levels=["Entry", "Junior", "Mid", "Senior"],
                categories=["Finance", "IT", "Sales", "General"]
            ),
            Assessment(
                name="Verbal Reasoning",
                url="https://www.shl.com/products/product-catalog/view/verify-verbal-ability/",
                test_type="A",
                description="Evaluates ability to understand written information and draw logical conclusions.",
                duration="20 minutes",
                languages=["English", "Spanish", "French", "German"],
                job_levels=["Entry", "Junior", "Mid", "Senior"],
                categories=["Finance", "Sales", "General"]
            ),
            Assessment(
                name="Abstract Reasoning",
                url="https://www.shl.com/products/product-catalog/view/verify-abstract-reasoning/",
                test_type="A",
                description="Measures logical reasoning ability through pattern recognition and problem-solving.",
                duration="15 minutes",
                languages=["English"],
                job_levels=["Entry", "Junior", "Mid", "Senior"],
                categories=["IT", "Engineering", "General"]
            ),
            # Skills/Competency Assessments
            Assessment(
                name="Customer Service Skills",
                url="https://www.shl.com/products/product-catalog/view/customer-service-skills/",
                test_type="S",
                description="Evaluates customer service competencies including communication and problem-solving.",
                duration="25 minutes",
                languages=["English", "Spanish"],
                job_levels=["Entry", "Junior", "Mid"],
                categories=["Customer Service", "Sales"]
            ),
            Assessment(
                name="Sales Skills",
                url="https://www.shl.com/products/product-catalog/view/sales-skills/",
                test_type="S",
                description="Assesses sales competencies including prospecting, negotiation, and closing.",
                duration="30 minutes",
                languages=["English", "Spanish"],
                job_levels=["Junior", "Mid", "Senior"],
                categories=["Sales"]
            ),
            Assessment(
                name="Leadership Skills",
                url="https://www.shl.com/products/product-catalog/view/leadership-skills/",
                test_type="S",
                description="Evaluates leadership competencies including team management and decision-making.",
                duration="35 minutes",
                languages=["English"],
                job_levels=["Mid", "Senior", "Executive"],
                categories=["Leadership", "Management"]
            ),
            Assessment(
                name="Communication Skills",
                url="https://www.shl.com/products/product-catalog/view/communication-skills/",
                test_type="S",
                description="Tests verbal and written communication abilities in business contexts.",
                duration="25 minutes",
                languages=["English"],
                job_levels=["Entry", "Junior", "Mid", "Senior"],
                categories=["General", "Sales", "Customer Service"]
            ),
            Assessment(
                name="Problem Solving Skills",
                url="https://www.shl.com/products/product-catalog/view/problem-solving-skills/",
                test_type="S",
                description="Assesses analytical thinking and problem-solving abilities in work scenarios.",
                duration="30 minutes",
                languages=["English"],
                job_levels=["Entry", "Junior", "Mid", "Senior"],
                categories=["IT", "Engineering", "General"]
            ),
            # Industry-Specific
            Assessment(
                name="Financial Analysis",
                url="https://www.shl.com/products/product-catalog/view/financial-analysis/",
                test_type="K",
                description="Tests financial analysis skills including financial statements and ratio analysis.",
                duration="40 minutes",
                languages=["English"],
                job_levels=["Junior", "Mid", "Senior"],
                categories=["Finance", "Accounting"]
            ),
            Assessment(
                name="Project Management Skills",
                url="https://www.shl.com/products/product-catalog/view/project-management-skills/",
                test_type="S",
                description="Evaluates project management competencies including planning and risk management.",
                duration="35 minutes",
                languages=["English"],
                job_levels=["Mid", "Senior"],
                categories=["IT", "Engineering", "Management"]
            ),
            Assessment(
                name="Data Analysis",
                url="https://www.shl.com/products/product-catalog/view/data-analysis/",
                test_type="K",
                description="Assesses data analysis skills using Excel, SQL, and statistical methods.",
                duration="40 minutes",
                languages=["English"],
                job_levels=["Junior", "Mid", "Senior"],
                categories=["IT", "Finance", "Analytics"]
            ),
            Assessment(
                name="Mechanical Reasoning",
                url="https://www.shl.com/products/product-catalog/view/mechanical-reasoning/",
                test_type="A",
                description="Tests understanding of mechanical principles and physical concepts.",
                duration="25 minutes",
                languages=["English"],
                job_levels=["Entry", "Junior", "Mid"],
                categories=["Engineering", "Manufacturing"]
            )
        ]
        print(f"Created sample catalog with {len(catalog.assessments)} assessments")
    
    retrieval_system = RetrievalSystem(catalog)
    agent = ConversationalAgent(retrieval_system)
    print("Agent initialized successfully")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for conversational agent."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Check for off-topic or injection attempts
        last_user_msg = request.messages[-1].content if request.messages else ""
        
        if agent._is_off_topic(last_user_msg):
            return ChatResponse(
                reply="I can only help you with SHL assessment recommendations. For general hiring advice, legal questions, or other topics, please consult appropriate resources.",
                recommendations=[],
                end_of_conversation=False
            )
        
        if agent._is_prompt_injection(last_user_msg):
            return ChatResponse(
                reply="I can only assist with SHL assessment recommendations. Please let me know if you need help finding the right assessments for your hiring needs.",
                recommendations=[],
                end_of_conversation=False
            )
        
        # Process conversation
        response = agent.process_conversation(request.messages)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
