"""
EatSmartly Backend - FastAPI Application with Multi-Agent System.
Main entry point for the barcode food analyzer API.
"""
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
import shutil
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os
from PIL import Image
import io
import requests
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import settings
from agents.data_collection import DataCollectionAgent
from agents.web_scraping import WebScrapingAgent
from agents.personalization import PersonalizationAgent
from agents.ingredient_analyzer import IngredientAnalysisAgent
from agents.meal_planner import get_meal_planner
# from agents.autogen_orchestrator import AutoGenOrchestrator  # Temporarily disabled
from agents.utils import setup_logger

# Ingredient Intelligence System
from knowledge.decode_service import decode_ingredients, quick_decode, compare_products
from knowledge.regulatory_db import (
    lookup_ingredient, search_ingredients, get_database_stats,
    get_ingredients_by_concern, get_ingredients_by_category,
    ConcernLevel, IngredientCategory,
)
from knowledge.ingredient_parser import parse_ingredient_list, extract_ingredient_names
import asyncio
from sqlalchemy import text
from vision_usage_tracker import get_usage_tracker
 
# Optional Google Vision client (lazy import)
google_vision_available = False
vision_client = None
try:
    from google.cloud import vision_v1 as vision
    google_vision_available = True
except Exception:
    google_vision_available = False


# Setup logging
logger = setup_logger(__name__, settings.LOG_LEVEL)

# Initialize FastAPI app
app = FastAPI(
    title="EatSmartly API",
    description="AI-powered barcode food analyzer with multi-agent system",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware for Flutter app and Next.js frontend
app.add_middleware(
    CORSMiddleware,
    # Allow all origins for mobile app development (Flutter doesn't send Origin header)
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static upload directory exists and mount it
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

# Initialize agents (optional)
try:
    # data_agent = DataCollectionAgent()
    # scraping_agent = WebScrapingAgent()
    # personalization_agent = PersonalizationAgent()
    data_agent = None
    scraping_agent = None
    personalization_agent = None
    ingredient_analyzer = None
    logger.info("Agents disabled for testing")
except Exception as e:
    logger.warning(f"Agent initialization failed: {e}. OCR will still work.")
    data_agent = None
    scraping_agent = None
    personalization_agent = None
    ingredient_analyzer = None

# Google Vision client will be initialized on first use
if google_vision_available:
    logger.info("Server initialized - Google Cloud Vision API enabled (primary OCR), OCR.space fallback available")
else:
    logger.info("Server initialized - Google Cloud Vision API not available, using OCR.space")

# If a local service account JSON is present and GOOGLE_APPLICATION_CREDENTIALS
# is not set, try to use `vision-sa.json` in the backend folder for local dev.
sa_path = os.path.join(os.path.dirname(__file__), 'vision-sa.json')
# Only set GOOGLE_APPLICATION_CREDENTIALS if the file is non-empty and looks like a service-account JSON
if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(sa_path):
    try:
        if os.path.getsize(sa_path) == 0:
            logger.warning(f"Found empty vision service account file at {sa_path}; skipping credentials setup.")
        else:
            import json
            try:
                with open(sa_path, 'r', encoding='utf-8') as f:
                    j = json.load(f)
                # Minimal validation
                if isinstance(j, dict) and ('private_key' in j or 'client_email' in j):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_path
                    logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to local file: {sa_path}")
                else:
                    logger.warning(f"vision-sa.json exists but doesn't look like a service account JSON; skipping.")
            except Exception as je:
                logger.warning(f"Failed to parse vision-sa.json: {je}; skipping credentials setup.")
    except Exception as e:
        logger.warning(f"Failed while checking vision-sa.json: {e}")

# Semaphore to limit concurrent uploads (allow 3 at a time)
upload_semaphore = asyncio.Semaphore(3)


@app.on_event("startup")
async def startup_event():
    """Initialize agents and verify DB connectivity on startup."""
    global data_agent, scraping_agent, personalization_agent, ingredient_analyzer
    try:
        # Initialize DataCollectionAgent which will attempt DB and Redis connections
        data_agent = DataCollectionAgent()
        scraping_agent = WebScrapingAgent()
        personalization_agent = PersonalizationAgent()
        ingredient_analyzer = IngredientAnalysisAgent()

        # Verify DB connection if available
        if data_agent and data_agent.db_engine:
            try:
                with data_agent.db_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Database connectivity verified on startup")
            except Exception as db_e:
                logger.warning(f"Database reachable but test query failed: {db_e}")
        else:
            logger.warning("No database engine available — running without DB")
        
        # Initialize background tasks (product scraper)
        try:
            from knowledge.background_scheduler import initialize_background_tasks
            logger.info("Initializing background tasks...")
            await initialize_background_tasks()
        except Exception as bg_e:
            logger.warning(f"Could not initialize background tasks: {bg_e}")

    except Exception as e:
        logger.error(f"Startup initialization error: {e}")
        data_agent = None
        scraping_agent = None
        personalization_agent = None


@app.on_event("shutdown")
async def shutdown_event():
    """Shut down background tasks and cleanup on application shutdown."""
    try:
        from knowledge.background_scheduler import shutdown_background_tasks
        logger.info("Shutting down background tasks...")
        await shutdown_background_tasks()
    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")


def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Preprocess image for OCR (resize, convert to PNG, greyscale optimization).
    """
    try:
        # Open image with PIL
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Resize if too large to reduce upload size for OCR.space
        max_size = 2000
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert back to compressed JPEG bytes to reduce upload time
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='JPEG', quality=75, optimize=True)
        return output_buffer.getvalue()

    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}, using original")
        return image_bytes

## OCR.space integration

def ocr_space_extract(image_bytes: bytes) -> dict:
    """Send image bytes to OCR.space and return parsed text and metadata."""
    # Retry with exponential backoff on transient network/timeouts
    retries = max(1, int(settings.MAX_RETRIES))
    # Increase timeout to handle slower uploads/processing on OCR.space
    timeout = max(int(settings.API_TIMEOUT), 120)
    processed = preprocess_image(image_bytes)

    files = {
        'file': ('nutrition.png', processed, 'image/png')
    }

    data = {
        'language': 'eng',
        'isOverlayRequired': 'false',
        'detectOrientation': 'true',
        'scale': 'true',
        'OCREngine': '2',
        'isTable': 'true'
    }

    headers = {}
    if settings.OCR_SPACE_API_KEY:
        headers['apikey'] = settings.OCR_SPACE_API_KEY

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"🔁 OCR.space request attempt {attempt}/{retries} (timeout={timeout}s)")
            resp = requests.post(
                'https://api.ocr.space/parse/image',
                files=files,
                data=data,
                headers=headers,
                timeout=timeout
            )

            # Log response status for debugging
            logger.debug(f"OCR.space HTTP status: {resp.status_code}")

            resp.raise_for_status()

            try:
                j = resp.json()
            except Exception:
                body = resp.text[:1000]
                logger.error(f"OCR.space returned non-JSON response: {body}")
                raise Exception(f"Non-JSON response from OCR.space: {resp.status_code}")

            if j.get('IsErroredOnProcessing'):
                # OCR.space returns error messages as list or string
                err = j.get('ErrorMessage') or j
                # If it's a transient server-side E500, retry if attempts remain
                if attempt < retries and isinstance(err, list) and any('E500' in str(x) for x in (err if isinstance(err, list) else [err])):
                    logger.warning(f"OCR.space transient error, will retry: {err}")
                    last_exc = Exception(err)
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise Exception(err)

            parsed = j.get('ParsedResults')
            if not parsed or len(parsed) == 0:
                raise Exception('No text detected in image')

            parsed_text = parsed[0].get('ParsedText', '')
            exit_code = parsed[0].get('FileParseExitCode', None)

            return {
                'text': parsed_text,
                'success': exit_code == 1,
                'raw': j
            }

        except requests.exceptions.Timeout as e:
            logger.error(f"OCR.space timeout on attempt {attempt}: {e}")
            last_exc = e
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))
                continue
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"OCR.space request exception on attempt {attempt}: {e}")
            last_exc = e
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))
                continue
            raise
        except Exception as e:
            logger.error(f"OCR.space error: {e}")
            last_exc = e
            # don't retry on client-side parse errors
            raise

    # If we exit loop with last_exc, raise a descriptive exception
    if last_exc:
        raise last_exc



# ==================== Request/Response Models ====================

class BarcodeAnalysisRequest(BaseModel):
    """Request model for barcode analysis."""
    barcode: Optional[str] = Field(None, description="Product barcode")
    product_id: Optional[int] = Field(None, description="Product ID from database")
    product_name: Optional[str] = Field(None, description="Product name")
    user_id: str = Field(..., description="User identifier")
    detailed: bool = Field(default=False, description="Include detailed nutrition breakdown")


class ProductAnalysisRequest(BaseModel):
    """Request model for product analysis by name/ID."""
    product_id: Optional[int] = Field(None, description="Product ID from database")
    product_name: Optional[str] = Field(None, description="Product name")
    user_id: str = Field(..., description="User identifier")
    detailed: bool = Field(default=False, description="Include detailed nutrition breakdown")


class FoodAnalysisResponse(BaseModel):
    """Response model for food analysis."""
    barcode: str
    food_name: Optional[str]
    brand: Optional[str]
    verdict: str  # safe, caution, avoid
    risk_level: str  # low, medium, high
    health_score: float
    alerts: List[str]
    warnings: List[str]
    suggestions: List[str]
    alternatives: List[Dict[str, str]]
    recipes: List[Dict[str, Any]]
    nutrition_tips: List[str]
    detailed_nutrition: Optional[Dict[str, Any]] = None
    ingredient_intelligence: Optional[Dict[str, Any]] = None  # Decoded ingredient label with source citations
    timestamp: str


class UserProfileRequest(BaseModel):
    """Request model for comprehensive user health profile."""
    # Layer 1: Body Context
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    health_goal: Optional[str] = None

    # Calculated values (optional - will be computed server-side)
    bmr_calories: Optional[float] = None
    tdee_calories: Optional[float] = None
    target_calories: Optional[float] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None

    # Layer 2: Health Context
    health_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []
    medications: Optional[List[str]] = []

    # Layer 3: Life Context
    dietary_type: Optional[str] = None
    cuisine_preferences: Optional[List[str]] = []
    cooking_skill: Optional[str] = None
    max_cooking_time_minutes: Optional[int] = None
    budget_per_meal_inr: Optional[int] = None
    household_size: Optional[int] = None
    cooking_for_kids: Optional[bool] = False
    kitchen_equipment: Optional[List[str]] = []

    # Profile metadata
    profile_completed: Optional[bool] = False


class UserProfileResponse(BaseModel):
    """Response model for user profile operations."""
    success: bool
    message: Optional[str] = None
    profile: Optional[UserProfileRequest] = None
    error: Optional[str] = None


class MealChatRequest(BaseModel):
    """Request model for meal planning chat with optional profile."""
    message: str
    history: Optional[List[Dict[str, Any]]] = []
    user_profile: Optional[UserProfileRequest] = None  # NEW: Include profile in chat


class MealChatResponse(BaseModel):
    """Response model for meal planning chat."""
    success: bool
    response: str
    error: Optional[str] = None


class SearchRequest(BaseModel):
    """Request model for food search."""
    query: str = Field(..., description="Food name to search")
    user_id: str = Field(..., description="User identifier")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum results")


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "EatSmartly API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze-barcode",
            "search": "/search",
            "profile": "/user/{user_id}/profile"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        try:
            if data_agent and data_agent.db_engine:
                data_agent.db_engine.connect()
                db_status = "connected"
            else:
                db_status = "optional"
        except:
            db_status = "optional"
        
        # Check Redis connection
        try:
            if data_agent and data_agent.redis_client:
                data_agent.redis_client.ping()
                redis_status = "connected"
            else:
                redis_status = "optional"
        except:
            redis_status = "optional"

        # Determine overall health (Both Redis and DB are optional for basic meal planning)
        all_healthy = True  # AI agents work without DB/Redis
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_status,
                "redis": redis_status,
                "agents": "active" if data_agent else "disabled"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.get("/server-info")
async def get_server_info(request: Request):
    """
    Get server connection information for client configuration
    Returns IP address, port, and connection URLs
    """
    from server_utils import get_local_ip, get_all_network_ips

    # Get server host info from request
    host = request.client.host
    port = request.url.port or 8000

    local_ip = get_local_ip()
    all_ips = get_all_network_ips()

    return {
        "server_ip": local_ip,
        "all_ips": all_ips,
        "port": port,
        "base_url": f"http://{local_ip}:{port}",
        "docs_url": f"http://{local_ip}:{port}/docs",
        "health_url": f"http://{local_ip}:{port}/health",
        "configuration": {
            "flutter_api_service": f"static const String baseUrl = 'http://{local_ip}:{port}';",
            "android_emulator": f"http://10.0.2.2:{port}",
            "localhost": f"http://localhost:{port}"
        },
        "instructions": {
            "physical_device": f"Update api_service.dart line 12 to: 'http://{local_ip}:{port}'",
            "android_emulator": f"Update api_service.dart line 12 to: 'http://10.0.2.2:{port}'",
            "same_wifi_required": "Ensure phone and PC are on the same WiFi network"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/vision-usage")
async def get_vision_usage():
    """
    Get Google Vision API usage statistics.
    
    Shows current usage against the free tier limit (1000 units/month).
    Each DOCUMENT_TEXT_DETECTION call = 1 unit.
    """
    try:
        tracker = get_usage_tracker()
        stats = tracker.get_usage_stats()
        
        return {
            "usage": stats,
            "limits": {
                "monthly_free_tier": 1000,
                "feature": "DOCUMENT_TEXT_DETECTION",
                "unit_calculation": "1 feature × 1 image = 1 unit"
            },
            "pricing_note": "First 1000 units/month free per feature. Additional units: $1.50 per 1000 units.",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get Vision usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage stats: {str(e)}"
        )


@app.post("/analyze-barcode", response_model=FoodAnalysisResponse)
async def analyze_barcode(request: BarcodeAnalysisRequest):
    """
    Analyze a barcode using AutoGen multi-agent system.
    
    Features:
    1. Multi-source data collection (Open Food Facts, USDA, Nutritionix)
    2. Cross-verification and consensus calculation
    3. Web scraping for recipes and alternatives
    4. Personalized recommendations based on user profile
    
    The AutoGen orchestrator coordinates all agents for accurate analysis.
    """
    try:
        logger.info("\n" + "="*100)
        logger.info(f"🔍 BARCODE ANALYSIS REQUEST")
        logger.info(f"📊 Barcode: {request.barcode}")
        logger.info(f"👤 User ID: {request.user_id}")
        logger.info(f"📝 Detailed: {request.detailed}")
        logger.info("="*100)
        
        logger.info("🚀 STEP 1/4: Initiating AutoGen Multi-Agent Orchestrator...")
        
        logger.info("🚀 STEP 1/4: Initiating AutoGen Multi-Agent Orchestrator...")
        
        # === USE SIMPLE ANALYSIS (AutoGen disabled) ===
        logger.info("🤖 STEP 2/4: Running simple analysis...")
        # Get basic product data from database
        product_data = data_agent.fetch_food_data(request.barcode)
        
        if not product_data:
            logger.error(f"❌ ANALYSIS FAILED: Product {request.barcode} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with barcode {request.barcode} not found"
            )
        
        # Simple evaluation
        user_profile = personalization_agent.get_user_profile(request.user_id)
        evaluation = personalization_agent.evaluate_food_safety(product_data, user_profile)
        
        analysis = {
            "product_name": product_data.get("name"),
            "brand": product_data.get("brand"),
            "nutrition": {
                "calories": product_data.get("calories"),
                "protein_g": product_data.get("protein_g"),
                "carbs_g": product_data.get("carbs_g"),
                "fat_g": product_data.get("fat_g"),
                "sugar_g": product_data.get("sugar_g"),
                "fiber_g": product_data.get("fiber_g"),
                "sodium_mg": product_data.get("sodium_mg")
            },
            "ingredients": product_data.get("ingredients"),
            "allergens": product_data.get("allergens"),
            "verdict": evaluation.get("verdict", "caution"),
            "risk_level": evaluation.get("risk_level", "medium"),
            "health_score": evaluation.get("health_score", 50),
            "alerts": evaluation.get("alerts", []),
            "warnings": evaluation.get("warnings", []),
            "suggestions": evaluation.get("suggestions", []),
            "alternatives": [],
            "recipes": [],
            "nutrition_tips": ["Check nutrition labels regularly"],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "data_quality": {
                "sources_found": 1,
                "confidence": "Database",
                "variance": 0
            }
        }
        
        logger.info("✅ STEP 3/4: Analysis complete, processing results...")
        
        logger.info("✅ STEP 3/4: Analysis complete, processing results...")
        
        # Check if product was found
        if "error" in analysis:
            logger.error(f"❌ ANALYSIS FAILED: {analysis['error']}")
            logger.error(f"🚨 Product {request.barcode} not found in any data source")
            logger.info("="*100 + "\n")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analysis["error"]
            )
        
        # Build detailed nutrition if requested
        detailed_nutrition = None
        if request.detailed:
            nutrition = analysis.get("nutrition", {})
            detailed_nutrition = {
                "serving_size": 100,  # Consensus data is per 100g
                "serving_unit": "g",
                "calories": nutrition.get("calories"),
                "protein_g": nutrition.get("protein_g"),
                "carbs_g": nutrition.get("carbs_g"),
                "fat_g": nutrition.get("fat_g"),
                "saturated_fat_g": nutrition.get("saturated_fat_g"),
                "sodium_mg": nutrition.get("sodium_mg"),
                "sugar_g": nutrition.get("sugar_g"),
                "fiber_g": nutrition.get("fiber_g"),
                "ingredients": analysis.get("ingredients"),
                "allergens": analysis.get("allergens"),
                "data_sources": analysis.get("data_quality", {}).get("sources_found", 0),
                "data_confidence": analysis.get("data_quality", {}).get("confidence", "Unknown"),
                "data_variance": analysis.get("data_quality", {}).get("variance", 0)
            }
        
        # === INGREDIENT INTELLIGENCE ===
        # Decode the ingredient list against regulatory knowledge base
        ingredient_intel = None
        ingredients_text = product_data.get("ingredients") or analysis.get("ingredients", "")
        if ingredients_text:
            try:
                ingredient_intel = quick_decode(
                    ingredient_text=ingredients_text,
                    product_name=analysis.get("product_name", ""),
                )
                logger.info(f"🧪 Ingredient Intelligence: {ingredient_intel.get('ingredients_identified', 0)}/{ingredient_intel.get('total_ingredients', 0)} identified, "
                            f"concern={ingredient_intel.get('overall_concern', 'none')}, "
                            f"sources={ingredient_intel.get('sources_cited', 0)}")
            except Exception as e:
                logger.warning(f"Ingredient decode failed (non-critical): {e}")

        # Build response
        response = FoodAnalysisResponse(
            barcode=request.barcode,
            food_name=analysis.get("product_name"),
            brand=analysis.get("brand"),
            verdict=analysis.get("verdict"),
            risk_level=analysis.get("risk_level"),
            health_score=analysis.get("health_score"),
            alerts=analysis.get("alerts", []),
            warnings=analysis.get("warnings", []),
            suggestions=analysis.get("suggestions", []),
            alternatives=analysis.get("alternatives", []),
            recipes=analysis.get("recipes", []),
            nutrition_tips=analysis.get("nutrition_tips", []),
            detailed_nutrition=detailed_nutrition,
            ingredient_intelligence=ingredient_intel,
            timestamp=analysis.get("analysis_timestamp")
        )
        
        logger.info(f"Analysis complete for barcode: {request.barcode}")
        logger.info(f"📊 Data sources used: {analysis.get('data_quality', {}).get('sources_found', 0)}/4")
        logger.info(f"🎯 Data confidence: {analysis.get('data_quality', {}).get('confidence', 'Unknown')}")
        logger.info(f"🔴 Verdict: {analysis.get('verdict', 'Unknown').upper()}")
        logger.info(f"💯 Health Score: {analysis.get('health_score', 0)}/100")
        logger.info("✅ STEP 4/4: Response prepared and sent to client")
        logger.info("="*100 + "\n")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("="*100)
        logger.error("🚨 CRITICAL ERROR IN BARCODE ANALYSIS")
        logger.error(f"🐞 Error Type: {type(e).__name__}")
        logger.error(f"📝 Error Message: {str(e)}")
        logger.error(f"📊 Barcode: {request.barcode}")
        logger.error("="*100, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/analyze-product", response_model=FoodAnalysisResponse)
async def analyze_product(request: BarcodeAnalysisRequest):
    """
    Analyze a product by barcode, name, or ID.
    
    This endpoint allows analysis of products using barcode, product name, or database ID.
    """
    try:
        logger.info("\n" + "="*100)
        logger.info(f"🔍 PRODUCT ANALYSIS REQUEST")
        logger.info(f"📊 Barcode: {request.barcode}")
        logger.info(f"📊 Product ID: {request.product_id}")
        logger.info(f"📝 Product Name: {request.product_name}")
        logger.info(f"👤 User ID: {request.user_id}")
        logger.info(f"📝 Detailed: {request.detailed}")
        logger.info("="*100)
        
        # Get product data based on what's provided
        product_data = None
        
        if request.barcode:
            logger.info("   Using barcode for analysis")
            product_data = data_agent.fetch_food_data(request.barcode)
        elif request.product_id:
            logger.info("   Using product ID for analysis")
            product_data = data_agent.get_product_by_id(request.product_id)
        elif request.product_name:
            logger.info("   Using product name for analysis")
            # Search for the product and get the first match
            search_results = data_agent.search_food_by_name(request.product_name, 1)
            if search_results:
                product_data = search_results[0]
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{request.product_name}' not found"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide barcode, product_id, or product_name"
            )
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info("🚀 STEP 1/3: Product found, running analysis...")
        
        # Analyze the product
        if request.barcode:
            # Use simple barcode analysis
            analysis = await _analyze_barcode_simple(request.barcode, request.user_id)
        else:
            # Create analysis from database data
            analysis = await _analyze_product_from_data(product_data, request.user_id)
        
        logger.info("✅ STEP 2/3: Analysis complete, processing results...")
        
        # Check if analysis was successful
        if "error" in analysis:
            logger.error(f"❌ ANALYSIS FAILED: {analysis['error']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analysis["error"]
            )
        
        # Build detailed nutrition if requested
        detailed_nutrition = None
        if request.detailed:
            nutrition = analysis.get("nutrition", {})
            detailed_nutrition = {
                "serving_size": 100,
                "serving_unit": "g",
                "calories": nutrition.get("calories"),
                "protein_g": nutrition.get("protein_g"),
                "carbs_g": nutrition.get("carbs_g"),
                "fat_g": nutrition.get("fat_g"),
                "saturated_fat_g": nutrition.get("saturated_fat_g"),
                "sodium_mg": nutrition.get("sodium_mg"),
                "sugar_g": nutrition.get("sugar_g"),
                "fiber_g": nutrition.get("fiber_g"),
                "ingredients": analysis.get("ingredients"),
                "allergens": analysis.get("allergens"),
                "data_sources": 1,  # Database only
                "data_confidence": "Database",
                "data_variance": 0
            }
        
        # === INGREDIENT INTELLIGENCE ===
        ingredient_intel = None
        ingredients_text = product_data.get("ingredients") or analysis.get("ingredients", "")
        if ingredients_text:
            try:
                ingredient_intel = quick_decode(
                    ingredient_text=ingredients_text,
                    product_name=analysis.get("product_name", ""),
                )
            except Exception as e:
                logger.warning(f"Ingredient decode failed (non-critical): {e}")

        # Build response
        response = FoodAnalysisResponse(
            barcode=request.barcode or f"no-barcode-{product_data.get('id', 'unknown')}",
            food_name=analysis.get("product_name"),
            brand=analysis.get("brand"),
            verdict=analysis.get("verdict"),
            risk_level=analysis.get("risk_level"),
            health_score=analysis.get("health_score"),
            alerts=analysis.get("alerts", []),
            warnings=analysis.get("warnings", []),
            suggestions=analysis.get("suggestions", []),
            alternatives=analysis.get("alternatives", []),
            recipes=analysis.get("recipes", []),
            nutrition_tips=analysis.get("nutrition_tips", []),
            detailed_nutrition=detailed_nutrition,
            ingredient_intelligence=ingredient_intel,
            timestamp=analysis.get("analysis_timestamp")
        )
        
        logger.info(f"Product analysis complete for: {product_data.get('name', 'Unknown')}")
        logger.info(f"🔴 Verdict: {analysis.get('verdict', 'Unknown').upper()}")
        logger.info(f"💯 Health Score: {analysis.get('health_score', 0)}/100")
        logger.info("✅ STEP 3/3: Response prepared and sent to client")
        logger.info("="*100 + "\n")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("="*100)
        logger.error("🚨 CRITICAL ERROR IN PRODUCT ANALYSIS")
        logger.error(f"🐞 Error Type: {type(e).__name__}")
        logger.error(f"📝 Error Message: {str(e)}")
        logger.error(f"📊 Barcode: {request.barcode}")
        logger.error(f"📊 Product ID: {request.product_id}")
        logger.error(f"📝 Product Name: {request.product_name}")
        logger.error("="*100, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


async def _analyze_product_from_data(product_data: dict, user_id: str) -> dict:
    """Analyze product using database data when barcode analysis isn't available."""
    try:
        # Get user profile for personalization
        user_profile = personalization_agent.get_user_profile(user_id)
        
        # Extract nutrition data
        nutrition = {
            "calories": product_data.get("calories"),
            "protein_g": product_data.get("protein_g"),
            "carbs_g": product_data.get("carbs_g"),
            "fat_g": product_data.get("fat_g"),
            "saturated_fat_g": product_data.get("saturated_fat_g"),
            "sugar_g": product_data.get("sugar_g"),
            "fiber_g": product_data.get("fiber_g"),
            "sodium_mg": product_data.get("sodium_mg")
        }
        
        # Analyze ingredients for hidden sugars
        ingredient_analysis = {}
        if ingredient_analyzer and product_data.get("ingredients"):
            ingredient_analysis = ingredient_analyzer.analyze_ingredients(
                ingredients=product_data.get("ingredients", ""),
                product_name=product_data.get("name", ""),
                labels=[]  # Could be extracted from product data if available
            )
        else:
            ingredient_analysis = {"analysis": "not_available", "warnings": []}
        
        # Evaluate food safety
        evaluation = personalization_agent.evaluate_food_safety({
            "name": product_data.get("name"),
            "nutrition": nutrition,
            "ingredients": product_data.get("ingredients"),
            "allergens": product_data.get("allergens")
        }, user_profile, ingredient_analysis)
        
        # Find alternatives
        alternatives = []
        if product_data.get("name"):
            search_term = product_data["name"].split()[0]  # First word
            similar_products = data_agent.search_food_by_name(search_term, 5)
            
            for alt_product in similar_products:
                if alt_product.get("id") != product_data.get("id"):
                    alt_score = 0
                    improvements = []
                    
                    # Compare sugar content
                    if alt_product.get("sugar_g", 999) < product_data.get("sugar_g", 999):
                        alt_score += 25
                        improvements.append("Lower sugar")
                    
                    # Compare protein
                    if alt_product.get("protein_g", 0) > product_data.get("protein_g", 0):
                        alt_score += 20
                        improvements.append("Higher protein")
                    
                    # Compare fiber
                    if alt_product.get("fiber_g", 0) > product_data.get("fiber_g", 0):
                        alt_score += 15
                        improvements.append("Higher fiber")
                    
                    if alt_score > 0:
                        alternatives.append({
                            "name": alt_product.get("name"),
                            "brand": alt_product.get("brand"),
                            "reason": "better_nutrition",
                            "score_improvement": alt_score,
                            "description": ", ".join(improvements)
                        })
        
        return {
            "product_name": product_data.get("name"),
            "brand": product_data.get("brand"),
            "nutrition": nutrition,
            "ingredients": product_data.get("ingredients"),
            "allergens": product_data.get("allergens"),
            "ingredient_analysis": ingredient_analysis,
            "verdict": evaluation.get("verdict", "caution"),
            "risk_level": evaluation.get("risk_level", "medium"),
            "health_score": evaluation.get("health_score", 50),
            "alerts": evaluation.get("alerts", []),
            "warnings": evaluation.get("warnings", []),
            "suggestions": evaluation.get("suggestions", []),
            "alternatives": alternatives,
            "recipes": [],
            "nutrition_tips": [
                "Check nutrition labels regularly",
                "Compare similar products for better choices",
                "Consider your daily nutritional goals"
            ],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "data_quality": {
                "sources_found": 1,
                "confidence": "Database",
                "variance": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing product from data: {e}")
        return {
            "error": f"Failed to analyze product: {str(e)}"
        }


async def _analyze_barcode_simple(barcode: str, user_id: str) -> dict:
    """Simple barcode analysis without AutoGen."""
    try:
        # Get product data from database
        product_data = data_agent.fetch_food_data(barcode)
        
        if not product_data:
            return {"error": f"Product with barcode {barcode} not found"}
        
        # Get user profile for personalization
        user_profile = personalization_agent.get_user_profile(user_id)
        
        # Extract nutrition data
        nutrition = {
            "calories": product_data.get("calories"),
            "protein_g": product_data.get("protein_g"),
            "carbs_g": product_data.get("carbs_g"),
            "fat_g": product_data.get("fat_g"),
            "saturated_fat_g": product_data.get("saturated_fat_g"),
            "sugar_g": product_data.get("sugar_g"),
            "fiber_g": product_data.get("fiber_g"),
            "sodium_mg": product_data.get("sodium_mg")
        }
        
        # Analyze ingredients for hidden sugars
        ingredient_analysis = {}
        if ingredient_analyzer and product_data.get("ingredients"):
            ingredient_analysis = ingredient_analyzer.analyze_ingredients(
                ingredients=product_data.get("ingredients", ""),
                product_name=product_data.get("name", ""),
                labels=[]  # Could be extracted from product data if available
            )
        else:
            ingredient_analysis = {"analysis": "not_available", "warnings": []}
        
        # Evaluate food safety
        evaluation = personalization_agent.evaluate_food_safety({
            "name": product_data.get("name"),
            "nutrition": nutrition,
            "ingredients": product_data.get("ingredients"),
            "allergens": product_data.get("allergens")
        }, user_profile, ingredient_analysis)
        
        return {
            "product_name": product_data.get("name"),
            "brand": product_data.get("brand"),
            "nutrition": nutrition,
            "ingredients": product_data.get("ingredients"),
            "allergens": product_data.get("allergens"),
            "ingredient_analysis": ingredient_analysis,
            "verdict": evaluation.get("verdict", "caution"),
            "risk_level": evaluation.get("risk_level", "medium"),
            "health_score": evaluation.get("health_score", 50),
            "alerts": evaluation.get("alerts", []),
            "warnings": evaluation.get("warnings", []),
            "suggestions": evaluation.get("suggestions", []),
            "alternatives": [],
            "recipes": [],
            "nutrition_tips": ["Check nutrition labels regularly"],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "data_quality": {
                "sources_found": 1,
                "confidence": "Database",
                "variance": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error in simple barcode analysis: {e}")
        return {
            "error": f"Failed to analyze barcode: {str(e)}"
        }


@app.post("/search")
async def search_food(request: SearchRequest):
    """Search for food by name."""
    try:
        logger.info(f"🔍 Searching for: {request.query}")
        
        results = data_agent.search_food_by_name(request.query, request.limit)
        
        logger.info(f"✅ Found {len(results)} results for '{request.query}'")
        
        return {
            "query": request.query,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


class AlternativesRequest(BaseModel):
    """Request model for alternatives."""
    barcode: Optional[str] = Field(None, description="Product barcode")
    product_id: Optional[int] = Field(None, description="Product ID from database")
    product_name: Optional[str] = Field(None, description="Product name")
    user_id: str = Field(..., description="User identifier")
    criteria: str = Field(default="all", description="Criteria: 'protein', 'sugar', 'fat', 'fiber', 'all'")


@app.post("/alternatives")
async def get_alternatives(request: AlternativesRequest):
    """
    Get healthier alternatives for a product.
    
    Args:
        request: AlternativesRequest with barcode, product_id, product_name, user_id, and criteria
    """
    try:
        logger.info(f"🔄 Finding alternatives for barcode: {request.barcode}, product_id: {request.product_id}, product_name: {request.product_name}")
        logger.info(f"   Criteria: {request.criteria}")
        
        # Get product data based on what's provided
        product_data = None
        
        if request.barcode:
            logger.info("   Using barcode for alternatives")
            product_data = data_agent.fetch_food_data(request.barcode)
        elif request.product_id:
            logger.info("   Using product ID for alternatives")
            product_data = data_agent.get_product_by_id(request.product_id)
        elif request.product_name:
            logger.info("   Using product name for alternatives")
            # Search for the product and get the first match
            search_results = data_agent.search_food_by_name(request.product_name, 1)
            if search_results:
                product_data = search_results[0]
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{request.product_name}' not found"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide barcode, product_id, or product_name"
            )
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_name = product_data.get("name", "")
        nutrition = {
            "calories": product_data.get("calories"),
            "protein_g": product_data.get("protein_g"),
            "carbs_g": product_data.get("carbs_g"),
            "fat_g": product_data.get("fat_g"),
            "sugar_g": product_data.get("sugar_g"),
            "fiber_g": product_data.get("fiber_g"),
            "saturated_fat_g": product_data.get("saturated_fat_g")
        }
        
        # Search for similar products
        search_query = product_name.split()[0]  # First word of product name
        similar_products = data_agent.search_food_by_name(search_query, 10)
        
        # Filter and rank alternatives
        alternatives = []
        
        for product in similar_products:
            # Skip the same product
            if (request.barcode and product.get("barcode") == request.barcode) or \
               (request.product_id and product.get("id") == request.product_id) or \
               (request.product_name and product.get("name") == request.product_name):
                continue
            
            score = 0
            improvements = []
            
            # Compare nutrition
            if request.criteria in ["protein", "all"]:
                if product.get("protein_g", 0) > nutrition.get("protein_g", 0):
                    score += 20
                    diff = product.get("protein_g", 0) - nutrition.get("protein_g", 0)
                    improvements.append(f"+{diff:.1f}g protein")
            
            if request.criteria in ["sugar", "all"]:
                if product.get("sugar_g", 999) < nutrition.get("sugar_g", 999):
                    score += 25
                    diff = nutrition.get("sugar_g", 0) - product.get("sugar_g", 0)
                    improvements.append(f"-{diff:.1f}g sugar")
            
            if request.criteria in ["fat", "all"]:
                if product.get("saturated_fat_g", 999) < nutrition.get("saturated_fat_g", 999):
                    score += 20
                    improvements.append("Lower saturated fat")
            
            if request.criteria in ["fiber", "all"]:
                if product.get("fiber_g", 0) > nutrition.get("fiber_g", 0):
                    score += 15
                    diff = product.get("fiber_g", 0) - nutrition.get("fiber_g", 0)
                    improvements.append(f"+{diff:.1f}g fiber")
            
            # Lower calories is generally better
            if product.get("calories", 999) < nutrition.get("calories", 999):
                score += 20
                diff = nutrition.get("calories", 0) - product.get("calories", 0)
                improvements.append(f"-{int(diff)} calories")
            
            if score > 0:
                alternatives.append({
                    "name": product.get("name"),
                    "brand": product.get("brand"),
                    "barcode": product.get("barcode"),
                    "score": score,
                    "improvements": improvements,
                    "nutrition": {
                        "calories": product.get("calories"),
                        "protein_g": product.get("protein_g"),
                        "carbs_g": product.get("carbs_g"),
                        "fat_g": product.get("fat_g"),
                        "sugar_g": product.get("sugar_g"),
                        "fiber_g": product.get("fiber_g")
                    }
                })
        
        # Sort by score
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"✅ Found {len(alternatives)} better alternatives")
        
        return {
            "original_product": product_name,
            "criteria": request.criteria,
            "count": len(alternatives),
            "alternatives": alternatives[:5]  # Top 5
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alternatives error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find alternatives: {str(e)}"
        )


# ===== ENHANCED PRODUCT SEARCH (Database + Local) =====

class ProductSearchComprehensiveRequest(BaseModel):
    """Request for comprehensive product search"""
    query: str = Field(..., description="Product name, brand, or keywords")
    limit: int = Field(default=20, le=100, description="Maximum results")
    strict_dedup: bool = Field(default=False, description="If True, only return 1 product per brand (no variants)")


class ProductSearchComprehensiveResponse(BaseModel):
    """Response for comprehensive search"""
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    sources: List[str]


@app.post("/search-products", response_model=ProductSearchComprehensiveResponse, tags=["Product Search"])
async def search_products_comprehensive(request: ProductSearchComprehensiveRequest):
    """
    🔍 COMPREHENSIVE PRODUCT SEARCH
    
    Searches across:
    1. Local database (products you added from Amazon, etc.)
    2. Supabase food_products table
    3. Open Food Facts (if local searches found nothing)
    
    Returns all matching products sorted by relevance.
    Results are DEDUPLICATED to avoid showing 20 "Coca Cola" variants.
    
    Example: POST /search-products with body:
    {
        "query": "pasta",
        "limit": 20
    }
    """
    try:
        logger.info(f"🔍 Comprehensive search for: '{request.query}' (strict_dedup={request.strict_dedup})")
        
        from knowledge.local_product_db import local_db
        from knowledge.product_deduplicator import deduplicate_search_results
        
        results = []
        sources = set()
        
        # Fetch with buffer to account for deduplication
        fetch_limit = request.limit * 3 if request.strict_dedup else request.limit * 2
        
        # 1. Search local product database (highest priority)
        logger.info("  📁 Searching local database...")
        try:
            local_results = local_db.search(request.query, limit=fetch_limit)
            if local_results:
                results.extend(local_results)
                sources.add("Local Database")
                logger.info(f"  ✅ Found {len(local_results)} in local database")
        except Exception as e:
            logger.warning(f"  ⚠️ Local search error: {e}")
        
        # 2. Search Supabase/main database
        logger.info("  🗄️ Searching Supabase...")
        try:
            db_results = data_agent.search_food_by_name(request.query, limit=fetch_limit)
            if db_results:
                # Avoid duplicates by checking names
                existing_names = {r.get('name', '').lower() for r in results}
                new_results = [
                    r for r in db_results 
                    if r.get('name', '').lower() not in existing_names
                ]
                results.extend(new_results)
                sources.add("Supabase")
                logger.info(f"  ✅ Found {len(new_results)} in Supabase")
        except Exception as e:
            logger.warning(f"  ⚠️ Supabase search error: {e}")
        
        # 3. DEDUPLICATE results before limiting
        logger.info("  🔄 Deduplicating results...")
        max_variants = 1 if request.strict_dedup else 2
        results = deduplicate_search_results(results, strict_mode=False, max_variants=max_variants)
        
        # Limit final results
        results = results[:request.limit]
        
        logger.info(f"✅ Search complete: {len(results)} results from {len(sources)} sources")
        
        return ProductSearchComprehensiveResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            sources=list(sources)
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# ==================== MEAL PLANNER REQUEST/RESPONSE MODELS ====================

class MealPlanRequest(BaseModel):
    """Request for meal planning"""
    available_ingredients: List[str] = Field(..., description="Ingredients available at home")
    nutritional_goals: Dict[str, Any] = Field(
        default={"protein_g": 30, "calories": 2000},
        description="Nutritional targets per day"
    )
    dietary_restrictions: Optional[List[str]] = Field(
        None,
        description="Dietary restrictions (vegan, gluten_free, dairy_free, etc.)"
    )
    cuisine_preferences: Optional[List[str]] = Field(
        None,
        description="Preferred cuisines (indian, italian, asian, etc.)"
    )
    meal_type: str = Field(
        default="balanced",
        description="Type: balanced, high_protein, weight_loss, muscle_gain"
    )
    num_meals: int = Field(default=5, ge=1, le=10, description="Number of meal suggestions")
    cooking_time_limit: int = Field(default=30, ge=5, le=120, description="Max cooking time in minutes")


class WeeklyMealPlanRequest(BaseModel):
    """Request for weekly meal plan"""
    available_ingredients: List[str] = Field(..., description="Ingredients at home")
    nutritional_goals: Dict[str, Any] = Field(
        default={"protein_g": 150, "calories": 14000},
        description="Weekly nutritional targets"
    )
    dietary_restrictions: Optional[List[str]] = Field(None)
    cuisine_preferences: Optional[List[str]] = Field(None)


class RecipeSuggestionRequest(BaseModel):
    """Request for recipe suggestions"""
    ingredients: List[str] = Field(..., description="Available ingredients")
    cuisine: Optional[str] = Field(None, description="Preferred cuisine")
    skill_level: str = Field(
        default="intermediate",
        description="beginner, intermediate, or advanced"
    )
    dietary_needs: Optional[List[str]] = Field(None, description="Special dietary requirements")


class NutritionAnalysisRequest(BaseModel):
    """Request for nutrition analysis"""
    meal_description: str = Field(..., description="Description of the meal")
    serving_size: str = Field(default="1 serving", description="Serving size")


class MealPlanResponse(BaseModel):
    """Response for meal planning"""
    success: bool
    meal_type: Optional[str] = None
    available_ingredients: Optional[List[str]] = None
    nutritional_goals: Optional[Dict[str, Any]] = None
    meals: Optional[List[Dict[str, Any]]] = None
    daily_nutrition: Optional[Dict[str, Any]] = None
    shopping_list: Optional[List[str]] = None
    error: Optional[str] = None
    generated_at: Optional[str] = None


class MealChatRequest(BaseModel):
    """Request for conversational meal chat with optional user profile"""
    message: str = Field(..., description="User's chat message")
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Chat history - list of {'role': 'user'|'model', 'parts': ['text']}"
    )
    user_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User's comprehensive health profile for personalized recommendations"
    )


class MealChatResponse(BaseModel):
    """Response for conversational meal chat"""
    success: bool
    response: str = Field(..., description="AI assistant response")
    error: Optional[str] = None


class AddProductRequest(BaseModel):
    """Request to add a product"""
    name: str = Field(..., description="Product name")
    brand: Optional[str] = Field(None, description="Brand name")
    barcode: Optional[str] = Field(None, description="Barcode")
    serving_size: Optional[float] = Field(None, description="Serving size")
    serving_unit: Optional[str] = Field(None, description="Serving unit (g, ml, etc)")
    calories: Optional[float] = Field(None, description="Calories per serving")
    protein_g: Optional[float] = Field(None, description="Protein in grams")
    carbs_g: Optional[float] = Field(None, description="Carbohydrates in grams")
    fat_g: Optional[float] = Field(None, description="Fat in grams")
    sugar_g: Optional[float] = Field(None, description="Sugar in grams")
    fiber_g: Optional[float] = Field(None, description="Fiber in grams")
    ingredients: Optional[str] = Field(None, description="Ingredient list")
    source: Optional[str] = Field(default="manual", description="Data source (amazon, bigbasket, manual, etc)")


@app.post("/add-product", tags=["Product Management"])
async def add_product(request: AddProductRequest):
    """
    ➕ ADD A NEW PRODUCT
    
    Saves a product to the local database (and optionally Supabase).
    Great for adding products from Amazon, BigBasket, or manually entering nutrition data.
    
    Example: POST /add-product with body:
    {
        "name": "Barilla Penne Pasta",
        "brand": "Barilla",
        "barcode": "8076808000062",
        "source": "amazon",
        "calories": 131,
        "protein_g": 5,
        "carbs_g": 25,
        "fat_g": 1.1,
        "sugar_g": 1.2
    }
    """
    try:
        from knowledge.local_product_db import local_db
        
        logger.info(f"➕ Adding product: {request.name} ({request.brand or 'No brand'})")
        
        # Add to local database
        product_dict = request.dict(exclude_none=True)
        product_id = local_db.add_product(product_dict)
        
        logger.info(f"✅ Product saved with ID: {product_id}")
        
        return {
            "success": True,
            "product_id": product_id,
            "message": f"Product '{request.name}' added successfully",
            "product": product_dict
        }
        
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add product: {str(e)}"
        )


@app.get("/local-products/count", tags=["Product Management"])
async def get_local_products_count():
    """Get count of products in local database"""
    try:
        from knowledge.local_product_db import local_db
        count = local_db.count()
        return {
            "total_local_products": count,
            "message": f"Local database has {count} products"
        }
    except Exception as e:
        logger.error(f"Error getting count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/local-products", tags=["Product Management"])
async def get_local_products(skip: int = 0, limit: int = 50):
    """Get all products from local database with pagination"""
    try:
        from knowledge.local_product_db import local_db
        
        all_products = local_db.get_all()
        paginated = all_products[skip:skip + limit]
        
        return {
            "skip": skip,
            "limit": limit,
            "total": len(all_products),
            "returned": len(paginated),
            "products": paginated
        }
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Get user health profile."""
    try:
        profile = personalization_agent.get_user_profile(user_id)
        
        return {
            "user_id": user_id,
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@app.post("/user/{user_id}/profile")
async def update_user_profile(user_id: str, profile: UserProfileRequest):
    """Update user health profile."""
    try:
        profile_data = {
            "age": profile.age,
            "gender": profile.gender,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "activity_level": profile.activity_level,
            "health_goal": profile.health_goal,
            "allergies": profile.allergies,
            "health_conditions": profile.health_conditions,
            "dietary_restrictions": profile.dietary_restrictions,
            # Calculate targets (simplified)
            "daily_calorie_target": 2000,  # Default, should calculate based on profile
            "daily_protein_target_g": 50,
            "daily_carbs_target_g": 250,
            "daily_fat_target_g": 65
        }
        
        success = personalization_agent.save_user_profile(user_id, profile_data)
        
        if success:
            return {
                "message": "Profile updated successfully",
                "user_id": user_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@app.post("/batch-analysis")
async def batch_analysis(barcodes: List[str], user_id: str):
    """Analyze multiple barcodes in batch."""
    try:
        logger.info(f"Batch analysis for {len(barcodes)} barcodes")
        
        results = []
        for barcode in barcodes[:10]:  # Limit to 10 per batch
            try:
                food_data = data_agent.fetch_food_data(barcode)
                if food_data:
                    user_profile = personalization_agent.get_user_profile(user_id)
                    evaluation = personalization_agent.evaluate_food_safety(food_data, user_profile)
                    
                    results.append({
                        "barcode": barcode,
                        "food_name": food_data.get("name"),
                        "verdict": evaluation["verdict"],
                        "health_score": evaluation["health_score"]
                    })
            except Exception as e:
                logger.warning(f"Error processing barcode {barcode}: {e}")
                continue
        
        return {
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


class NutritionTextRequest(BaseModel):
    """Request model for text-based nutrition extraction."""
    query: str = Field(..., description="Natural language food description (e.g., '1 cup rice', '2 eggs and toast')")
    user_id: str = Field(..., description="User identifier")


class SaveProductRequest(BaseModel):
    """Request model for saving a product extracted from OCR."""
    barcode: Optional[str] = Field(None, description="Product barcode if available")
    name: str = Field(..., description="Product name")
    brand: Optional[str] = Field(None, description="Brand name")
    serving_size: Optional[float] = Field(None)
    serving_unit: Optional[str] = Field(None)
    calories: Optional[float] = Field(None)
    protein_g: Optional[float] = Field(None)
    carbs_g: Optional[float] = Field(None)
    fat_g: Optional[float] = Field(None)
    saturated_fat_g: Optional[float] = Field(None)
    sodium_mg: Optional[float] = Field(None)
    sugar_g: Optional[float] = Field(None)
    fiber_g: Optional[float] = Field(None)
    ingredients: Optional[str] = Field(None)
    allergens: Optional[List[str]] = Field(default_factory=list)
    image_url: Optional[str] = Field(None, description="Optional URL for front image")
    user_id: Optional[str] = Field(None, description="User who saved the product")


@app.post("/analyze-text")
async def analyze_nutrition_text(request: NutritionTextRequest):
    """
    Extract nutrition information from natural language text using API Ninjas.
    
    This endpoint uses AI to extract nutrition from:
    - Recipes (e.g., "2 cups flour, 3 eggs, 1 tbsp butter")
    - Menu items (e.g., "grilled chicken sandwich with fries")
    - Food descriptions (e.g., "1lb brisket and mashed potatoes")
    
    Automatically handles custom portions and multiple items.
    """
    try:
        logger.info(f"📝 Analyzing nutrition text: {request.query}")
        
        # Use API Ninjas to extract nutrition from text
        nutrition_items = data_agent.fetch_from_api_ninjas_text(request.query)
        
        if not nutrition_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not extract nutrition information from: {request.query}"
            )
        
        # Analyze each item
        user_profile = personalization_agent.get_user_profile(request.user_id)
        analyzed_items = []
        
        for item in nutrition_items:
            # Calculate health score
            evaluation = personalization_agent.evaluate_food_safety(item, user_profile)
            
            analyzed_items.append({
                "name": item.get("name"),
                "serving_size": f"{item.get('serving_size', 100)}{item.get('serving_unit', 'g')}",
                "nutrition": {
                    "calories": item.get("calories"),
                    "protein_g": item.get("protein_g"),
                    "carbs_g": item.get("carbs_g"),
                    "fat_g": item.get("fat_g"),
                    "saturated_fat_g": item.get("saturated_fat_g"),
                    "sugar_g": item.get("sugar_g"),
                    "fiber_g": item.get("fiber_g"),
                    "sodium_mg": item.get("sodium_mg"),
                    "potassium_mg": item.get("potassium_mg"),
                    "cholesterol_mg": item.get("cholesterol_mg")
                },
                "health_score": evaluation.get("health_score"),
                "verdict": evaluation.get("verdict"),
                "alerts": evaluation.get("alerts", []),
                "warnings": evaluation.get("warnings", [])
            })
        
        # Calculate total nutrition
        total_nutrition = {
            "calories": sum(item.get("calories", 0) for item in nutrition_items),
            "protein_g": sum(item.get("protein_g", 0) for item in nutrition_items),
            "carbs_g": sum(item.get("carbs_g", 0) for item in nutrition_items),
            "fat_g": sum(item.get("fat_g", 0) for item in nutrition_items),
            "sugar_g": sum(item.get("sugar_g", 0) for item in nutrition_items),
            "fiber_g": sum(item.get("fiber_g", 0) for item in nutrition_items),
            "sodium_mg": sum(item.get("sodium_mg", 0) for item in nutrition_items)
        }
        
        logger.info(f"✅ Extracted nutrition for {len(analyzed_items)} items")
        
        return {
            "query": request.query,
            "item_count": len(analyzed_items),
            "items": analyzed_items,
            "total_nutrition": total_nutrition,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze text: {str(e)}"
        )


@app.post("/save-product")
async def save_product(request: SaveProductRequest):
    """Save a product record submitted by the client (from OCR + parsing).

    The endpoint is intentionally permissive: if `barcode` is missing we generate
    a stable placeholder key and persist the record with `source='user'`.
    """
    try:
        # Choose barcode/key for DB primary key
        barcode = request.barcode or f"no-barcode-{int(datetime.utcnow().timestamp() * 1000)}"

        # Build normalized data mapping used by DataCollectionAgent._save_to_database
        data = {
            "barcode": barcode,
            "name": request.name,
            "brand": request.brand or "",
            "serving_size": request.serving_size or 100,
            "serving_unit": request.serving_unit or "g",
            "calories": request.calories or 0,
            "protein_g": request.protein_g or 0,
            "carbs_g": request.carbs_g or 0,
            "fat_g": request.fat_g or 0,
            "saturated_fat_g": request.saturated_fat_g or 0,
            "sodium_mg": request.sodium_mg or 0,
            "sugar_g": request.sugar_g or 0,
            "fiber_g": request.fiber_g or 0,
            "ingredients": request.ingredients or "",
            "allergens": request.allergens or [],
            "source": "user",
        }

        # Persist to database (DataCollectionAgent will no-op if DB not configured)
        try:
            data_agent._save_to_database(barcode, data)
        except Exception as db_e:
            logger.error(f"Failed to save product to DB: {db_e}")

        # Optionally respond with created barcode and any image_url sent
        return {"status": "saved", "barcode": barcode, "image_url": request.image_url}

    except Exception as e:
        logger.error(f"Save product failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post('/upload-front-image')
async def upload_front_image(request: Request, file: UploadFile = File(...)):
    """Upload a front image for a product and return an accessible URL. Limited to 3 concurrent uploads."""
    async with upload_semaphore:
        try:
            # sanitize filename
            base = os.path.basename(file.filename or 'front.jpg')
            filename = f"{int(datetime.utcnow().timestamp() * 1000)}_{base}"
            dest_path = os.path.join(UPLOADS_DIR, filename)

            # Write file to disk
            with open(dest_path, 'wb') as out_f:
                shutil.copyfileobj(file.file, out_f)

            image_url = f"{str(request.base_url).rstrip('/')}/static/uploads/{filename}"
            logger.info(f"Saved uploaded front image: {dest_path} -> {image_url}")
            return {"url": image_url}
        except Exception as e:
            logger.error(f"Front image upload failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/extract-text")
async def extract_text_from_image(file: UploadFile = File(...)):
    """
    Extract text from uploaded image using OCR.space.

    Supports JPEG, PNG images of food labels and nutrition information.
    """
    async with upload_semaphore:
        try:
            logger.info(f"📷 Extracting text from image: {file.filename}")

            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only JPEG, PNG, and WebP images are supported"
                )

            # Read content and check size (20MB limit)
            content = await file.read()
            file_size = len(content)
            if file_size > 20 * 1024 * 1024:  # 20MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image file too large. Maximum size is 20MB"
                )

            # First attempt: Google Cloud Vision (DOCUMENT_TEXT_DETECTION) if available
            extracted_text = ''
            processing_steps = ['preprocess_image']
            api_used = None
            usage_tracker = get_usage_tracker()

            if google_vision_available:
                # Check rate limit before calling Vision API
                can_use_vision, limit_msg = usage_tracker.can_make_request(units_needed=1)
                
                if can_use_vision:
                    try:
                        logger.info("Attempting OCR via Google Cloud Vision")
                        processing_steps.append('google_vision')
                        global vision_client
                        if vision_client is None:
                            vision_client = vision.ImageAnnotatorClient()

                        def call_vision():
                            image = vision.Image(content=content)
                            return vision_client.document_text_detection(image=image)

                        resp = await asyncio.to_thread(call_vision)
                        if getattr(resp, 'full_text_annotation', None) and getattr(resp.full_text_annotation, 'text', None):
                            extracted_text = resp.full_text_annotation.text or ''
                        elif getattr(resp, 'text_annotations', None) and len(resp.text_annotations) > 0:
                            extracted_text = resp.text_annotations[0].description or ''

                        if extracted_text.strip():
                            # Record successful Vision API usage (1 unit = 1 feature × 1 image)
                            usage_tracker.record_request(units=1, success=True)
                            api_used = 'google_vision'
                            logger.info(f"✅ Extracted {len(extracted_text)} characters of text via Google Vision")
                            
                            # Include usage stats in response
                            stats = usage_tracker.get_usage_stats()
                            return {
                                "filename": file.filename,
                                "extracted_text": extracted_text,
                                "word_count": len(extracted_text.split()),
                                "processing_steps": processing_steps,
                                "api_used": api_used,
                                "timestamp": datetime.utcnow().isoformat(),
                                "vision_usage": {
                                    "units_used": stats['units_used'],
                                    "units_remaining": stats['units_remaining'],
                                    "percentage_used": stats['percentage_used']
                                }
                            }
                    except Exception as e:
                        logger.warning(f"Google Vision extraction failed, falling back to OCR.space: {e}")
                else:
                    logger.warning(f"⚠️ Vision API rate limit: {limit_msg}")

            # Fallback: OCR.space
            try:
                processing_steps.append('ocr_space')
                ocr_result = ocr_space_extract(content)
                extracted_text = ocr_result.get('text', '')
                api_used = 'ocr_space'
            except Exception as e:
                logger.error(f"OCR.space extraction failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"OCR service failed: {str(e)}"
                )

            if not extracted_text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No text detected in the image. Please ensure the image contains readable text and is well-lit."
                )

            logger.info(f"✅ Extracted {len(extracted_text)} characters of text via {api_used}")

            return {
                "filename": file.filename,
                "extracted_text": extracted_text,
                "word_count": len(extracted_text.split()),
                "processing_steps": processing_steps,
                "api_used": api_used,
                "timestamp": datetime.utcnow().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OCR error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text: {str(e)}"
            )


@app.post("/detect-product")
async def detect_product_from_image(file: UploadFile = File(...)):
    """
    Detect product information from image using Vision API.
    
    Uses LABEL_DETECTION (1 unit) + WEB_DETECTION (1 unit) + TEXT_DETECTION for barcode (1 unit) = 3 units per image.
    Returns product categories, web entities (known products), barcode, and confidence scores.
    Useful for products page to identify and categorize items.
    """
    async with upload_semaphore:
        try:
            logger.info(f"🔍 Detecting product from image: {file.filename}")

            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only JPEG, PNG, and WebP images are supported"
                )

            # Read content and check size (20MB limit)
            content = await file.read()
            file_size = len(content)
            if file_size > 20 * 1024 * 1024:  # 20MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image file too large. Maximum size is 20MB"
                )

            if not google_vision_available:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Product detection requires Google Vision API (not available)"
                )

            usage_tracker = get_usage_tracker()
            # Product detection uses 3 features = 3 units (labels + web entities + text)
            can_use_vision, limit_msg = usage_tracker.can_make_request(units_needed=3)
            
            if not can_use_vision:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=limit_msg
                )

            try:
                logger.info("Calling Vision API for product detection (LABEL + WEB + TEXT for barcode)")
                global vision_client
                if vision_client is None:
                    vision_client = vision.ImageAnnotatorClient()

                def call_vision_detection():
                    image = vision.Image(content=content)
                    # Call label, web, and TEXT detection (3 units total, no logo)
                    label_response = vision_client.label_detection(image=image)
                    web_response = vision_client.web_detection(image=image)
                    text_response = vision_client.text_detection(image=image)
                    return label_response, web_response, text_response

                label_resp, web_resp, text_resp = await asyncio.to_thread(call_vision_detection)
                
                # Parse labels
                labels = []
                if label_resp.label_annotations:
                    for label in label_resp.label_annotations[:10]:  # Top 10 labels
                        labels.append({
                            'description': label.description,
                            'score': round(label.score, 3),
                            'confidence': f"{label.score * 100:.1f}%"
                        })
                
                # Parse web entities (known products/brands from Google's database)
                web_entities = []
                if web_resp.web_detection and web_resp.web_detection.web_entities:
                    for entity in web_resp.web_detection.web_entities[:10]:
                        if entity.description:  # Only include entities with descriptions
                            web_entities.append({
                                'description': entity.description,
                                'score': round(entity.score, 3) if entity.score else 0,
                                'confidence': f"{entity.score * 100:.1f}%" if entity.score else "N/A"
                            })
                
                # Extract barcode from text detection
                barcode = None
                detected_text = ''
                if text_resp.text_annotations:
                    # First annotation contains full detected text
                    detected_text = text_resp.text_annotations[0].description if text_resp.text_annotations else ''
                    
                    # Look for barcode patterns - improved to handle spaces, newlines, and various formats
                    import re
                    # Try multiple cleaning strategies
                    cleaned_text = detected_text.replace(' ', '').replace('\n', '').replace('\r', '').replace('-', '').replace('_', '')
                    
                    logger.info(f"Searching for barcode in text (length: {len(cleaned_text)} chars)")
                    logger.info(f"First 300 chars of cleaned text: {cleaned_text[:300]}")
                    
                    barcode_patterns = [
                        r'(\d{13})',  # EAN-13 (most common globally)
                        r'(\d{12})',  # UPC-A (North America)
                        r'(\d{14})',  # ITF-14 / GTIN-14
                        r'(\d{8})',   # EAN-8
                    ]
                    
                    all_found = []
                    for pattern in barcode_patterns:
                        matches = re.findall(pattern, cleaned_text)
                        if matches:
                            logger.info(f"Pattern {pattern} found {len(matches)} matches: {matches[:3]}")
                            all_found.extend(matches)
                    
                    # Find the most likely barcode
                    for match in all_found:
                        # Filter out common false positives
                        first_two = match[:2]
                        # Skip dates, years, phone-like numbers
                        if first_two in ['19', '20'] and len(match) <= 10:
                            continue
                        # Skip sequences of same digit (like 11111111)
                        if len(set(match)) == 1:
                            continue
                        # Valid barcode found
                        barcode = match
                        logger.info(f"✅ Selected barcode: {barcode}")
                        break
                    
                    if not barcode:
                        logger.warning(f"No valid barcode found. All digit sequences found: {all_found[:10]}")
                
                # Record usage (3 units: 1 for labels + 1 for web + 1 for text)
                usage_tracker.record_request(units=3, success=True)
                
                # Get usage stats
                stats = usage_tracker.get_usage_stats()
                
                logger.info(f"✅ Detected {len(labels)} labels, {len(web_entities)} web entities, barcode: {barcode or 'None'}")
                
                # Determine brand: prioritize web entities over labels
                detected_brand = None
                if web_entities and len(web_entities) > 0:
                    # Filter out generic terms
                    for entity in web_entities:
                        desc = entity['description'].lower()
                        if desc not in ['food', 'product', 'noodles', 'pasta', 'label', 'ingredient'] and len(desc) > 2:
                            detected_brand = entity['description']
                            break
                
                return {
                    "filename": file.filename,
                    "labels": labels,
                    "web_entities": web_entities,
                    "barcode": barcode,
                    "detected_text_preview": detected_text[:200] if detected_text else None,
                    "detected_text_full": detected_text if detected_text else None,
                    "primary_category": labels[0]['description'] if labels else None,
                    "detected_brand": detected_brand,
                    "features_used": ["LABEL_DETECTION", "WEB_DETECTION", "TEXT_DETECTION"],
                    "units_consumed": 3,
                    "vision_usage": {
                        "units_used": stats['units_used'],
                        "units_remaining": stats['units_remaining'],
                        "percentage_used": stats['percentage_used']
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Vision API product detection failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Product detection failed: {str(e)}"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Product detection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text: {str(e)}"
            )


class ProductSearchRequest(BaseModel):
    """Request model for product search by name"""
    product_name: str = Field(..., description="Product name extracted from OCR (e.g., 'Maggi Noodles', 'Britannia Marie')")
    max_results: int = Field(default=5, description="Maximum number of results to return per source")


class ProductSearchResponse(BaseModel):
    """Response model for product search"""
    success: bool
    found: bool
    results: List[Dict] = []
    total_found: int = 0
    sources_searched: List[str] = []
    error: Optional[str] = None


@app.post("/search-product-by-name", response_model=ProductSearchResponse)
async def search_product_by_name(request: ProductSearchRequest):
    """
    Search for product across Amazon India and BigBasket by name
    This is the NEW RELIABLE WAY to find products using OCR-extracted text
    
    Use this after extracting text from product image front label
    """
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔎 PRODUCT SEARCH BY NAME")
        logger.info(f"Product: {request.product_name}")
        logger.info(f"Max results per source: {request.max_results}")
        logger.info('='*60)
        
        # Import scrapers
        from scrapers import (
            search_amazon_india,
            search_bigbasket
        )
        
        all_results = []
        sources_searched = []
        
        # Search Amazon India
        logger.info("📦 Searching Amazon India...")
        try:
            amazon_results = search_amazon_india(request.product_name, request.max_results)
            if amazon_results:
                all_results.extend(amazon_results)
                sources_searched.append("Amazon India")
                logger.info(f"✅ Found {len(amazon_results)} results from Amazon")
        except Exception as e:
            logger.error(f"❌ Amazon search failed: {e}")
        
        # Search BigBasket
        logger.info("🛒 Searching BigBasket...")
        try:
            bigbasket_results = search_bigbasket(request.product_name, request.max_results)
            if bigbasket_results:
                all_results.extend(bigbasket_results)
                sources_searched.append("BigBasket")
                logger.info(f"✅ Found {len(bigbasket_results)} results from BigBasket")
        except Exception as e:
            logger.error(f"❌ BigBasket search failed: {e}")
        
        # Sort by confidence score
        all_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        logger.info(f"\n📊 TOTAL RESULTS: {len(all_results)} from {len(sources_searched)} sources")
        logger.info(f"Sources: {', '.join(sources_searched)}")
        
        if len(all_results) == 0:
            return ProductSearchResponse(
                success=True,
                found=False,
                results=[],
                total_found=0,
                sources_searched=sources_searched,
                error="Product not found in any source"
            )
        
        # Log top match
        if all_results:
            top_match = all_results[0]
            logger.info(f"\n🏆 TOP MATCH:")
            logger.info(f"   Product: {top_match.get('product_name', 'N/A')}")
            logger.info(f"   Brand: {top_match.get('brand', 'N/A')}")
            logger.info(f"   Price: ₹{top_match.get('price', 'N/A')}")
            logger.info(f"   Source: {top_match.get('source', 'N/A')}")
        
        # Auto-save scraped products to database
        try:
            if all_results and data_agent and data_agent.db_engine:
                logger.info("💾 Auto-saving scraped products to database...")
                save_result = await save_scraped_products(all_results)
                logger.info(f"✅ Auto-saved {save_result.get('saved_count', 0)} products to database")
        except Exception as e:
            logger.warning(f"⚠️ Failed to auto-save products: {e}")
        
        return ProductSearchResponse(
            success=True,
            found=True,
            results=all_results,
            total_found=len(all_results),
            sources_searched=sources_searched
        )
        
    except Exception as e:
        logger.error(f"❌ Product search error: {e}")
        return ProductSearchResponse(
            success=False,
            found=False,
            results=[],
            total_found=0,
            sources_searched=[],
            error=str(e)
        )


@app.post("/get-product-details")
async def get_product_details(product_url: str):
    """
    Get complete product details including nutrition from product page URL
    
    Args:
        product_url: Full URL to product page (Amazon or BigBasket)
    """
    try:
        logger.info(f"📦 Getting product details from: {product_url}")
        
        from scrapers import (
            get_amazon_product_details,
            get_bigbasket_product_details
        )
        
        product_details = None
        
        # Determine which scraper to use based on URL
        if 'amazon.in' in product_url:
            logger.info("Using Amazon scraper...")
            product_details = get_amazon_product_details(product_url)
        elif 'bigbasket.com' in product_url:
            logger.info("Using BigBasket scraper...")
            product_details = get_bigbasket_product_details(product_url)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported product URL. Only Amazon India and BigBasket are supported."
            )
        
        if not product_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not extract product details from URL"
            )
        
        logger.info(f"✅ Successfully extracted product details")
        if product_details.get('nutrition'):
            logger.info(f"✅ Nutrition info included: {list(product_details['nutrition'].keys())}")
        
        return {
            "success": True,
            "product": product_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product details: {str(e)}"
        )


class NutritionItemRequest(BaseModel):
    """Request model for single food item nutrition."""
    food_item: str = Field(..., description="Food item name (e.g., 'rice', 'chicken')")
    quantity: str = Field(..., description="Quantity with unit (e.g., '1 cup', '100g', '2 tbsp')")
    user_id: str = Field(..., description="User identifier")


@app.post("/analyze-item")
async def analyze_nutrition_item(request: NutritionItemRequest):
    """
    Get nutrition for a single food item with specific quantity.
    
    Supports various units:
    - Volume: cup, tbsp, tsp, ml, l
    - Weight: g, kg, oz, lb
    - Count: piece, slice, serving
    """
    try:
        logger.info(f"🍽️ Analyzing: {request.quantity} {request.food_item}")
        
        # Use API Ninjas to get nutrition for specific item and quantity
        nutrition_data = data_agent.fetch_from_api_ninjas_item(request.food_item, request.quantity)
        
        if not nutrition_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not find nutrition for: {request.quantity} {request.food_item}"
            )
        
        # Analyze health
        user_profile = personalization_agent.get_user_profile(request.user_id)
        evaluation = personalization_agent.evaluate_food_safety(nutrition_data, user_profile)
        
        logger.info(f"✅ Nutrition found for {request.quantity} {request.food_item}")
        
        return {
            "food_item": request.food_item,
            "quantity": request.quantity,
            "serving_size": f"{nutrition_data.get('serving_size', 100)}g",
            "nutrition": {
                "calories": nutrition_data.get("calories"),
                "protein_g": nutrition_data.get("protein_g"),
                "carbs_g": nutrition_data.get("carbs_g"),
                "fat_g": nutrition_data.get("fat_g"),
                "saturated_fat_g": nutrition_data.get("saturated_fat_g"),
                "sugar_g": nutrition_data.get("sugar_g"),
                "fiber_g": nutrition_data.get("fiber_g"),
                "sodium_mg": nutrition_data.get("sodium_mg"),
                "potassium_mg": nutrition_data.get("potassium_mg"),
                "cholesterol_mg": nutrition_data.get("cholesterol_mg")
            },
            "health_score": evaluation.get("health_score"),
            "verdict": evaluation.get("verdict"),
            "risk_level": evaluation.get("risk_level"),
            "alerts": evaluation.get("alerts", []),
            "warnings": evaluation.get("warnings", []),
            "suggestions": evaluation.get("suggestions", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Item analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze item: {str(e)}"
        )


# ==================== Startup/Shutdown Events ====================


class SaveProductCompleteRequest(BaseModel):
    barcode: Optional[str]
    product_name: str
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    region: Optional[str] = None
    weight: Optional[str] = None
    fssai_license: Optional[str] = None
    image_url: Optional[str] = None
    is_verified: Optional[bool] = False
    verified_by: Optional[str] = None
    # Nutrition facts (optional)
    nutrition: Optional[Dict[str, Optional[float]]] = None
    user_id: Optional[str] = None


def _upsert_product_and_insert_nutrition(engine, payload: SaveProductCompleteRequest):
    """Upsert product into `products` by barcode and insert a nutrition_facts row.

    Returns the product id (UUID string) if successful, else None.
    """
    if not engine:
        logger.warning("_upsert_product_and_insert_nutrition: No DB engine available")
        return None

    try:
        with engine.begin() as conn:
            # Upsert product by barcode (if barcode provided), otherwise insert new product
            params = {
                'barcode': payload.barcode,
                'product_name': payload.product_name,
                'brand': payload.brand,
                'manufacturer': payload.manufacturer,
                'region': payload.region,
                'weight': payload.weight,
                'fssai_license': payload.fssai_license,
                'image_url': payload.image_url,
                'is_verified': payload.is_verified,
                'verified_by': payload.verified_by
            }

            if payload.barcode:
                upsert_sql = text("""
                    INSERT INTO products (barcode, product_name, brand, manufacturer, region, weight, fssai_license, image_url, is_verified, verified_by, updated_at)
                    VALUES (:barcode, :product_name, :brand, :manufacturer, :region, :weight, :fssai_license, :image_url, :is_verified, :verified_by, CURRENT_TIMESTAMP)
                    ON CONFLICT (barcode) DO UPDATE SET
                        product_name = EXCLUDED.product_name,
                        brand = EXCLUDED.brand,
                        manufacturer = EXCLUDED.manufacturer,
                        region = EXCLUDED.region,
                        weight = EXCLUDED.weight,
                        fssai_license = EXCLUDED.fssai_license,
                        image_url = EXCLUDED.image_url,
                        is_verified = EXCLUDED.is_verified,
                        verified_by = EXCLUDED.verified_by,
                        updated_at = EXCLUDED.updated_at
                    RETURNING id
                """)
                res = conn.execute(upsert_sql, params)
                row = res.fetchone()
                product_id = str(row[0]) if row else None
            else:
                insert_sql = text("""
                    INSERT INTO products (product_name, brand, manufacturer, region, weight, fssai_license, image_url, is_verified, verified_by)
                    VALUES (:product_name, :brand, :manufacturer, :region, :weight, :fssai_license, :image_url, :is_verified, :verified_by)
                    RETURNING id
                """)
                res = conn.execute(insert_sql, params)
                row = res.fetchone()
                product_id = str(row[0]) if row else None

            # Insert nutrition facts if provided
            if payload.nutrition and product_id:
                nut = payload.nutrition
                nut_params = {
                    'product_id': product_id,
                    'serving_size': nut.get('serving_size'),
                    'servings_per_container': nut.get('servings_per_container'),
                    'calories': nut.get('calories'),
                    'total_fat': nut.get('total_fat'),
                    'saturated_fat': nut.get('saturated_fat'),
                    'trans_fat': nut.get('trans_fat'),
                    'cholesterol': nut.get('cholesterol'),
                    'sodium': nut.get('sodium'),
                    'total_carbohydrates': nut.get('total_carbohydrates'),
                    'dietary_fiber': nut.get('dietary_fiber'),
                    'total_sugars': nut.get('total_sugars'),
                    'added_sugars': nut.get('added_sugars'),
                    'protein': nut.get('protein'),
                    'confidence': nut.get('confidence')
                }

                insert_nut_sql = text("""
                    INSERT INTO nutrition_facts (
                        product_id, serving_size, servings_per_container, calories,
                        total_fat, saturated_fat, trans_fat, cholesterol, sodium,
                        total_carbohydrates, dietary_fiber, total_sugars, added_sugars,
                        protein, confidence, created_at
                    ) VALUES (
                        :product_id, :serving_size, :servings_per_container, :calories,
                        :total_fat, :saturated_fat, :trans_fat, :cholesterol, :sodium,
                        :total_carbohydrates, :dietary_fiber, :total_sugars, :added_sugars,
                        :protein, :confidence, CURRENT_TIMESTAMP
                    )
                """)
                conn.execute(insert_nut_sql, nut_params)

            return product_id

    except Exception as e:
        logger.error(f"DB upsert/insert error: {e}")
        return None

# @app.on_event("startup")
# async def startup_event():
#     """Run on application startup."""
#     logger.info("=" * 50)
#     logger.info("EatSmartly Backend Starting...")
#     logger.info(f"Debug Mode: {settings.DEBUG}")
#     logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
#     logger.info(f"Redis: {settings.REDIS_URL}")
#     logger.info("=" * 50)

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Run on application shutdown."""
#     logger.info("EatSmartly Backend Shutting Down...")


# Endpoint: Save complete product (upsert product + insert nutrition)
@app.post('/save-product-complete')
async def save_product_complete(payload: SaveProductCompleteRequest):
    """Save parsed product info and nutrition facts into the database.

    This upserts `products` by `barcode` and inserts a `nutrition_facts` record when provided.
    """
    try:
        if not data_agent or not data_agent.db_engine:
            logger.warning("save_product_complete: No DB engine configured; skipping DB save")
            return {"status": "no_db", "message": "Database not configured"}

        product_id = _upsert_product_and_insert_nutrition(data_agent.db_engine, payload)

        if product_id:
            return {"status": "saved", "product_id": product_id}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save product to DB")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"save_product_complete error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@app.get('/food-images')
async def list_food_images(limit: int = 200, offset: int = 0, image_type: Optional[str] = None):
    """Return food images from the `food_images` table. 
    Image URLs should already be complete from Supabase bucket. If DB not configured, return empty list."""
    try:
        if not data_agent or not data_agent.db_engine:
            return {"products": [], "total": 0, "image_types": []}

        # Build query with optional filters
        where_clauses = ["image_url IS NOT NULL"]
        params = {"limit": limit, "offset": offset}
        
        if image_type:
            where_clauses.append("image_type = :image_type")
            params["image_type"] = image_type
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Query food_images table only (no join with foods table for now)
        q = text(f"""
            SELECT 
                id,
                barcode,
                image_url,
                image_type,
                alt_text,
                uploaded_at,
                COALESCE(alt_text, 'Product') as product_name
            FROM food_images
            {where_sql}
            ORDER BY uploaded_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        # Get total count
        count_q = text(f"""
            SELECT COUNT(*) FROM food_images {where_sql}
        """)
        
        # Get unique image types for filters
        types_q = text("""
            SELECT DISTINCT image_type FROM food_images 
            WHERE image_type IS NOT NULL 
            ORDER BY image_type
        """)
        
        with data_agent.db_engine.connect() as conn:
            res = conn.execute(q, params)
            rows = []
            for r in res.fetchall():
                # Convert Row to dict using _mapping attribute
                row_dict = dict(r._mapping)
                rows.append(row_dict)
            
            # Get total count
            count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
            total = conn.execute(count_q, count_params).scalar()
            
            # Get filter options
            image_types = [row[0] for row in conn.execute(types_q).fetchall()]

        logger.info(f"Returning {len(rows)} products from food_images table")
        return {"products": rows, "total": total or 0, "image_types": image_types}
    except Exception as e:
        logger.error(f"list_food_images error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty result instead of raising exception to maintain compatibility
        return {"products": [], "total": 0, "image_types": [], "error": str(e)}


@app.post("/save-scraped-products")
async def save_scraped_products(products: List[Dict[str, Any]]):
    """Save scraped products to the database automatically."""
    try:
        saved_count = 0

        for product in products:
            try:
                # Prepare product data for database
                product_data = {
                    "product_name": product.get("product_name", product.get("name", "Unknown Product")),
                    "brand": product.get("brand"),
                    "manufacturer": product.get("manufacturer"),
                    "region": product.get("source", "India"),  # Default to India for scraped products
                    "weight": product.get("weight"),
                    "image_url": product.get("image_url"),
                    "is_verified": True,
                    "verified_by": "web_scraping_agent"
                }

                # Use the existing upsert function
                result = _upsert_product_and_insert_nutrition(data_agent.db_engine, SaveProductCompleteRequest(**product_data))

                if result:
                    saved_count += 1
                    logger.info(f"Saved scraped product: {product_data['product_name']}")

            except Exception as e:
                logger.error(f"Failed to save product {product}: {e}")
                continue

        return {
            "success": True,
            "saved_count": saved_count,
            "total_products": len(products),
            "message": f"Successfully saved {saved_count} out of {len(products)} products"
        }

    except Exception as e:
        logger.error(f"Error saving scraped products: {e}")
        return {
            "success": False,
            "error": str(e),
            "saved_count": 0,
            "total_products": len(products)
        }


# ==================== Products API ====================

@app.get('/products')
async def list_products(limit: int = 200, offset: int = 0, region: Optional[str] = None, brand: Optional[str] = None):
    """Return products from the database for the products page."""
    try:
        if not data_agent or not data_agent.db_engine:
            # Return scraped products as fallback
            scraped_products = [
                {
                    "id": "pasta-1",
                    "product_name": "DISANO Penne Pasta, 1Kg, 100% Durum Wheat, No Maida",
                    "brand": "DISANO",
                    "region": "India",
                    "weight": "1Kg",
                    "image_url": "https://m.media-amazon.com/images/I/71xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-2",
                    "product_name": "Del Monte Foodcraft Penne Pasta 1Kg | 100% Durum Wheat",
                    "brand": "Del Monte",
                    "region": "India",
                    "weight": "1Kg",
                    "image_url": "https://m.media-amazon.com/images/I/72xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-3",
                    "product_name": "DISANO Fusilli Pasta, 1Kg, 100% Durum Wheat, No Maida",
                    "brand": "DISANO",
                    "region": "India",
                    "weight": "1Kg",
                    "image_url": "https://m.media-amazon.com/images/I/73xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-4",
                    "product_name": "DISANO Elbows Pasta, 1Kg, 100% Durum Wheat, No Maida",
                    "brand": "DISANO",
                    "region": "India",
                    "weight": "1Kg",
                    "image_url": "https://m.media-amazon.com/images/I/74xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-5",
                    "product_name": "Chef's Basket Fusili Pasta 534 gm Pouch | 100% Durum Wheat",
                    "brand": "Chef's Basket",
                    "region": "India",
                    "weight": "534g",
                    "image_url": "https://m.media-amazon.com/images/I/75xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-6",
                    "product_name": "Bambino Vegetarian Pasta Macaroni 850g | Made from Durum Wheat",
                    "brand": "Bambino",
                    "region": "India",
                    "weight": "850g",
                    "image_url": "https://m.media-amazon.com/images/I/76xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-7",
                    "product_name": "MTR Penne Pasta 500g | Premium Quality Durum Wheat",
                    "brand": "MTR",
                    "region": "India",
                    "weight": "500g",
                    "image_url": "https://m.media-amazon.com/images/I/77xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-8",
                    "product_name": "Sunfeast Yippee Pasta Treat 75g | Fun Shaped Pasta",
                    "brand": "Sunfeast Yippee",
                    "region": "India",
                    "weight": "75g",
                    "image_url": "https://m.media-amazon.com/images/I/78xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-9",
                    "product_name": "Barilla Spaghetti Pasta 500g | Italian Quality",
                    "brand": "Barilla",
                    "region": "India",
                    "weight": "500g",
                    "image_url": "https://m.media-amazon.com/images/I/79xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-10",
                    "product_name": "San Remo Pasta Spirals 500g | Australian Durum Wheat",
                    "brand": "San Remo",
                    "region": "India",
                    "weight": "500g",
                    "image_url": "https://m.media-amazon.com/images/I/80xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-11",
                    "product_name": "Knorr Pasta Penne 75g | Quick Cook Pasta",
                    "brand": "Knorr",
                    "region": "India",
                    "weight": "75g",
                    "image_url": "https://m.media-amazon.com/images/I/81xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-12",
                    "product_name": "Wai Wai Quick Pasta Masala 85g | Instant Pasta",
                    "brand": "Wai Wai",
                    "region": "India",
                    "weight": "85g",
                    "image_url": "https://m.media-amazon.com/images/I/82xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-13",
                    "product_name": "Haldiram's Pasta 200g | Traditional Indian Taste",
                    "brand": "Haldiram's",
                    "region": "India",
                    "weight": "200g",
                    "image_url": "https://m.media-amazon.com/images/I/83xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-14",
                    "product_name": "Organic India Whole Wheat Pasta 500g | Organic & Healthy",
                    "brand": "Organic India",
                    "region": "India",
                    "weight": "500g",
                    "image_url": "https://m.media-amazon.com/images/I/84xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                },
                {
                    "id": "pasta-15",
                    "product_name": "Tasty Bite Pasta Penne 400g | Ready to Cook",
                    "brand": "Tasty Bite",
                    "region": "India",
                    "weight": "400g",
                    "image_url": "https://m.media-amazon.com/images/I/85xxxxx.jpg",
                    "is_verified": True,
                    "source": "web_scraping"
                }
            ]
            return {
                "products": scraped_products,
                "total": len(scraped_products),
                "regions": ["India"],
                "brands": ["DISANO", "Del Monte", "Chef's Basket", "Bambino", "MTR", "Sunfeast Yippee", "Barilla", "San Remo", "Knorr", "Wai Wai", "Haldiram's", "Organic India", "Tasty Bite"]
            }

        # Try to get products from database
        where_clauses = []
        params = {"limit": limit, "offset": offset}

        if region:
            where_clauses.append("region = :region")
            params["region"] = region
        if brand:
            where_clauses.append("brand ILIKE :brand")
            params["brand"] = f"%{brand}%"

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Query products table
        q = text(f"""
            SELECT
                id::text,
                barcode,
                product_name,
                brand,
                manufacturer,
                region,
                weight,
                fssai_license,
                image_url,
                is_verified,
                created_at
            FROM products
            {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        # Get total count
        count_q = text(f"""
            SELECT COUNT(*) FROM products {where_sql}
        """)

        # Get unique regions and brands
        regions_q = text("SELECT DISTINCT region FROM products WHERE region IS NOT NULL ORDER BY region")
        brands_q = text("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL ORDER BY brand")

        with data_agent.db_engine.connect() as conn:
            res = conn.execute(q, params)
            rows = res.fetchall()

            products = []
            for row in rows:
                products.append({
                    "id": row[0],
                    "barcode": row[1],
                    "product_name": row[2] or "Unknown Product",
                    "brand": row[3],
                    "manufacturer": row[4],
                    "region": row[5],
                    "weight": row[6],
                    "fssai_license": row[7],
                    "image_url": row[8],
                    "is_verified": row[9],
                    "created_at": row[10].isoformat() if row[10] else None
                })

            # Get total count
            total_res = conn.execute(count_q, params)
            total = total_res.scalar()

            # Get regions and brands
            regions_res = conn.execute(regions_q)
            regions = [row[0] for row in regions_res.fetchall()]

            brands_res = conn.execute(brands_q)
            brands = [row[0] for row in brands_res.fetchall()]

            # If no products in database, return the scraped ones
            if not products:
                scraped_products = [
                    {
                        "id": "pasta-1",
                        "product_name": "DISANO Penne Pasta, 1Kg, 100% Durum Wheat, No Maida",
                        "brand": "DISANO",
                        "region": "India",
                        "weight": "1Kg",
                        "image_url": "https://m.media-amazon.com/images/I/71xxxxx.jpg",
                        "is_verified": True,
                        "source": "web_scraping"
                    },
                    {
                        "id": "pasta-2",
                        "product_name": "Del Monte Foodcraft Penne Pasta 1Kg | 100% Durum Wheat",
                        "brand": "Del Monte",
                        "region": "India",
                        "weight": "1Kg",
                        "image_url": "https://m.media-amazon.com/images/I/72xxxxx.jpg",
                        "is_verified": True,
                        "source": "web_scraping"
                    },
                    {
                        "id": "pasta-3",
                        "product_name": "DISANO Fusilli Pasta, 1Kg, 100% Durum Wheat, No Maida",
                        "brand": "DISANO",
                        "region": "India",
                        "weight": "1Kg",
                        "image_url": "https://m.media-amazon.com/images/I/73xxxxx.jpg",
                        "is_verified": True,
                        "source": "web_scraping"
                    },
                    {
                        "id": "pasta-4",
                        "product_name": "DISANO Elbows Pasta, 1Kg, 100% Durum Wheat, No Maida",
                        "brand": "DISANO",
                        "region": "India",
                        "weight": "1Kg",
                        "image_url": "https://m.media-amazon.com/images/I/74xxxxx.jpg",
                        "is_verified": True,
                        "source": "web_scraping"
                    },
                    {
                        "id": "pasta-5",
                        "product_name": "Chef's Basket Fusili Pasta 534 gm Pouch | 100% Durum Wheat",
                        "brand": "Chef's Basket",
                        "region": "India",
                        "weight": "534g",
                        "image_url": "https://m.media-amazon.com/images/I/75xxxxx.jpg",
                        "is_verified": True,
                        "source": "web_scraping"
                    }
                ]
                return {
                    "products": scraped_products,
                    "total": len(scraped_products),
                    "regions": ["India"],
                    "brands": ["DISANO", "Del Monte", "Chef's Basket"]
                }

            return {
                "products": products,
                "total": total,
                "regions": regions,
                "brands": brands
            }

    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        # Return scraped products as fallback
        scraped_products = [
            {
                "id": "pasta-1",
                "product_name": "DISANO Penne Pasta, 1Kg, 100% Durum Wheat, No Maida",
                "brand": "DISANO",
                "region": "India",
                "weight": "1Kg",
                "image_url": "https://m.media-amazon.com/images/I/71xxxxx.jpg",
                "is_verified": True,
                "source": "web_scraping"
            },
            {
                "id": "pasta-2",
                "product_name": "Del Monte Foodcraft Penne Pasta 1Kg | 100% Durum Wheat",
                "brand": "Del Monte",
                "region": "India",
                "weight": "1Kg",
                "image_url": "https://m.media-amazon.com/images/I/72xxxxx.jpg",
                "is_verified": True,
                "source": "web_scraping"
            },
            {
                "id": "pasta-3",
                "product_name": "DISANO Fusilli Pasta, 1Kg, 100% Durum Wheat, No Maida",
                "brand": "DISANO",
                "region": "India",
                "weight": "1Kg",
                "image_url": "https://m.media-amazon.com/images/I/73xxxxx.jpg",
                "is_verified": True,
                "source": "web_scraping"
            },
            {
                "id": "pasta-4",
                "product_name": "DISANO Elbows Pasta, 1Kg, 100% Durum Wheat, No Maida",
                "brand": "DISANO",
                "region": "India",
                "weight": "1Kg",
                "image_url": "https://m.media-amazon.com/images/I/74xxxxx.jpg",
                "is_verified": True,
                "source": "web_scraping"
            },
            {
                "id": "pasta-5",
                "product_name": "Chef's Basket Fusili Pasta 534 gm Pouch | 100% Durum Wheat",
                "brand": "Chef's Basket",
                "region": "India",
                "weight": "534g",
                "image_url": "https://m.media-amazon.com/images/I/75xxxxx.jpg",
                "is_verified": True,
                "source": "web_scraping"
            }
        ]
        return {
            "products": scraped_products,
            "total": len(scraped_products),
            "regions": ["India"],
            "brands": ["DISANO", "Del Monte", "Chef's Basket"]
        }


# ==================== Ingredient Intelligence API ====================
# "We don't judge food. We decode labels and show you what regulators,
#  researchers, and public databases already say."

class DecodeIngredientsRequest(BaseModel):
    """Request to decode a product's ingredient list."""
    ingredients: str = Field(..., description="Ingredient list text (can be raw/OCR)")
    product_name: Optional[str] = Field(None, description="Product name for context")
    raw_ocr_text: Optional[str] = Field(None, description="Full OCR text if ingredients need auto-detection")


class CompareProductsRequest(BaseModel):
    """Request to compare two products' ingredient profiles."""
    product_a_ingredients: str = Field(..., description="Product A ingredient list")
    product_b_ingredients: str = Field(..., description="Product B ingredient list")
    product_a_name: str = Field(default="Product A", description="Product A name")
    product_b_name: str = Field(default="Product B", description="Product B name")


class IngredientLookupRequest(BaseModel):
    """Request to look up a single ingredient."""
    name: str = Field(..., description="Ingredient name or E-number")


class IngredientSearchRequest(BaseModel):
    """Request to search ingredients."""
    query: str = Field(..., description="Search query")


@app.post("/decode-ingredients", tags=["Ingredient Intelligence"])
async def decode_ingredients_endpoint(request: DecodeIngredientsRequest):
    """
    Decode a product's ingredient label into source-cited information.

    Parses the ingredient list, identifies each ingredient against our regulatory
    database (FSSAI, FDA, EFSA, CODEX), and returns plain-language explanations
    with full source citations.

    Every claim is traceable to a regulation, published study, or official document.
    """
    try:
        result = quick_decode(
            ingredient_text=request.ingredients,
            product_name=request.product_name or "",
        )
        return result
    except Exception as e:
        logger.error(f"Error decoding ingredients: {e}")
        raise HTTPException(status_code=500, detail=f"Error decoding ingredients: {str(e)}")


@app.post("/compare-products", tags=["Ingredient Intelligence"])
async def compare_products_endpoint(request: CompareProductsRequest):
    """
    Compare two products' ingredient profiles side by side.

    Shows common concerns, unique concerns per product, and which product
    has a simpler ingredient list.
    """
    try:
        result = compare_products(
            product_a_ingredients=request.product_a_ingredients,
            product_b_ingredients=request.product_b_ingredients,
            product_a_name=request.product_a_name,
            product_b_name=request.product_b_name,
        )
        return result
    except Exception as e:
        logger.error(f"Error comparing products: {e}")
        raise HTTPException(status_code=500, detail=f"Error comparing products: {str(e)}")


@app.post("/lookup-ingredient", tags=["Ingredient Intelligence"])
async def lookup_ingredient_endpoint(request: IngredientLookupRequest):
    """
    Look up detailed information about a single ingredient.

    Returns regulatory status across FSSAI/FDA/EFSA, health effects,
    concern level, ADI, and all source citations.
    """
    info = lookup_ingredient(request.name)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Ingredient '{request.name}' not found in our database. Try searching with /search-ingredients."
        )
    return info.to_dict()


@app.post("/search-ingredients", tags=["Ingredient Intelligence"])
async def search_ingredients_endpoint(request: IngredientSearchRequest):
    """
    Search for ingredients by partial name match.
    """
    results = search_ingredients(request.query)
    return {
        "query": request.query,
        "results": [r.to_dict() for r in results],
        "total": len(results),
    }


@app.get("/ingredient-database/stats", tags=["Ingredient Intelligence"])
async def ingredient_database_stats():
    """
    Get statistics about the ingredient knowledge base.
    """
    stats = get_database_stats()
    stats["description"] = (
        "EatSmartly Ingredient Intelligence Database. "
        "Every entry is source-cited from FSSAI, FDA, EFSA, CODEX, and PubMed."
    )
    stats["trust_model"] = (
        "We don't make health claims. We aggregate what regulators and "
        "researchers already say — with full citations."
    )
    return stats


@app.get("/ingredients/by-concern/{level}", tags=["Ingredient Intelligence"])
async def ingredients_by_concern_endpoint(level: str):
    """
    Get all ingredients at a specific concern level.
    Levels: none, low, moderate, high, controversial
    """
    try:
        concern = ConcernLevel(level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid concern level: {level}. Valid: none, low, moderate, high, controversial"
        )
    results = get_ingredients_by_concern(concern)
    return {
        "concern_level": level,
        "ingredients": [r.to_dict() for r in results],
        "total": len(results),
    }


@app.get("/ingredients/by-category/{category}", tags=["Ingredient Intelligence"])
async def ingredients_by_category_endpoint(category: str):
    """
    Get all ingredients of a specific category.
    Categories: preservative, colorant, sweetener, emulsifier, thickener, etc.
    """
    try:
        cat = IngredientCategory(category)
    except ValueError:
        valid = [c.value for c in IngredientCategory]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}. Valid: {', '.join(valid)}"
        )
    results = get_ingredients_by_category(cat)
    return {
        "category": category,
        "ingredients": [r.to_dict() for r in results],
        "total": len(results),
    }


# ===== RAG Document Indexing =====

@app.post("/admin/index-documents", tags=["Ingredient Intelligence"])
async def index_documents_endpoint(background_tasks: BackgroundTasks):
    """
    Trigger indexing of regulatory PDFs (FSSAI, IFCT) into the RAG vector store.
    Runs in background — PDFs are read, chunked, embedded, and saved.
    After indexing, unknown ingredients get auto-retrieved context from these docs.
    """
    import glob
    from pathlib import Path as _Path

    base = _Path(__file__).resolve().parent.parent
    backend = _Path(__file__).resolve().parent

    pdf_paths = []
    for search_dir in [base, backend, backend / "asset"]:
        for pdf in search_dir.glob("*.pdf"):
            if pdf.name not in [p.split("\\")[-1].split("/")[-1] for p in pdf_paths]:
                pdf_paths.append(str(pdf))

    if not pdf_paths:
        return {"status": "error", "message": "No PDF files found in project root or backend/asset/"}

    def _run_indexing():
        try:
            from knowledge.rag_pipeline import RAGPipeline
            import knowledge  # noqa: F401
            pipeline = RAGPipeline()
            pipeline.index_documents(pdf_paths=pdf_paths, include_kb=True)
            logger.info(f"Background indexing complete — {pipeline.store.size} chunks")
        except Exception as e:
            logger.error(f"Background indexing failed: {e}")

    background_tasks.add_task(_run_indexing)

    return {
        "status": "indexing_started",
        "pdfs_found": [_Path(p).name for p in pdf_paths],
        "message": "Indexing started in background. This may take a few minutes for large PDFs.",
    }


@app.get("/admin/rag-status", tags=["Ingredient Intelligence"])
async def rag_status_endpoint():
    """Check if the RAG vector store is indexed and ready."""
    from pathlib import Path as _Path
    store_path = _Path(__file__).resolve().parent / "data" / "vector_store.json"

    if not store_path.exists():
        return {
            "status": "not_indexed",
            "message": "Vector store not found. Run POST /admin/index-documents first.",
            "chunks": 0,
        }

    try:
        import json
        with open(store_path) as f:
            data = json.load(f)
        chunk_count = len(data.get("chunks", []))
        return {
            "status": "ready",
            "chunks": chunk_count,
            "store_path": str(store_path),
            "message": f"RAG pipeline ready with {chunk_count} searchable document chunks.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "chunks": 0}


@app.get("/rag-search", tags=["Ingredient Intelligence"])
async def rag_search_endpoint(query: str, top_k: int = 5):
    """
    Search the RAG vector store for regulatory information.
    Useful for ingredients not in the manual database.
    """
    try:
        from knowledge.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline()
        if not pipeline.is_ready:
            return {"found": False, "message": "RAG pipeline not indexed yet. Run POST /admin/index-documents first."}
        results = pipeline.retrieve(query, top_k=top_k)
        return {
            "query": query,
            "found": len(results) > 0,
            "results": [r.to_dict() for r in results],
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search error: {str(e)}")


# ===== AI-Powered Explanations (Ollama + Llama 3.1) =====

class AIExplainRequest(BaseModel):
    """Request for AI-powered ingredient explanation."""
    ingredient: str = Field(..., description="Ingredient name to explain")
    include_rag: bool = Field(default=True, description="Include RAG document context")


class AIProductSummaryRequest(BaseModel):
    """Request for AI-powered product summary."""
    ingredients: str = Field(..., description="Ingredient list text")
    product_name: str = Field(default="", description="Product name")


@app.post("/ai/explain-ingredient", tags=["AI Intelligence"])
async def ai_explain_ingredient_endpoint(request: AIExplainRequest):
    """
    Get an AI-generated, source-cited explanation of an ingredient.

    Uses Ollama (local Llama 3.1) to synthesize information from our
    regulatory database + FSSAI/IFCT PDFs into a plain-language explanation.
    Falls back to template if Ollama is not running.
    """
    from knowledge.llm_explainer import explain_ingredient
    from knowledge.regulatory_db import lookup_ingredient as kb_lookup

    # Get KB data
    kb_data = None
    info = kb_lookup(request.ingredient)
    if info:
        kb_data = info.to_dict()

    # Get RAG context
    rag_context = None
    if request.include_rag:
        try:
            from knowledge.rag_pipeline import RAGPipeline
            pipeline = RAGPipeline()
            if pipeline.is_ready:
                results = pipeline.retrieve(request.ingredient, top_k=3)
                rag_context = [r.to_dict() for r in results]
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")

    result = await explain_ingredient(request.ingredient, kb_data, rag_context)
    result["ingredient"] = request.ingredient
    result["in_database"] = info is not None
    return result


@app.post("/ai/summarize-product", tags=["AI Intelligence"])
async def ai_summarize_product_endpoint(request: AIProductSummaryRequest):
    """
    Get an AI-generated summary of a product's ingredient profile.

    Decodes all ingredients first, then uses Ollama to generate a
    natural-language summary highlighting concerns and notable ingredients.
    """
    from knowledge.llm_explainer import explain_product

    # First decode the ingredients
    decoded = quick_decode(request.ingredients, request.product_name)

    # Then get AI summary
    result = await explain_product(
        product_name=request.product_name or "This product",
        decoded_ingredients=decoded.get("decoded_ingredients", []),
    )
    result["decode"] = decoded
    return result


@app.get("/ai/status", tags=["AI Intelligence"])
async def ai_status_endpoint():
    """Check if the AI (Ollama) is available and which model is loaded."""
    from knowledge.llm_explainer import get_ollama_client
    client = get_ollama_client()
    available = await client.is_available()

    if available:
        return {
            "status": "ready",
            "provider": "ollama",
            "model": client.model,
            "url": client.base_url,
            "message": f"AI ready — using {client.model} via Ollama",
        }
    else:
        return {
            "status": "unavailable",
            "provider": "ollama",
            "model": client.model,
            "url": client.base_url,
            "message": (
                "Ollama not running. Install from https://ollama.com, then run: "
                f"ollama pull {client.model}"
            ),
            "fallback": "Template-based explanations are used when AI is unavailable.",
        }


# ==================== AI MEAL PLANNER ENDPOINTS ====================

@app.post("/meal-plan", response_model=MealPlanResponse, tags=["Meal Planning"])
async def generate_meal_plan(request: MealPlanRequest):
    """
    🍽️ GENERATE PERSONALIZED MEAL PLAN
    
    Creates a personalized meal plan based on:
    - Available ingredients at home
    - Nutritional goals (high protein, specific nutrients)
    - Dietary restrictions and preferences
    - Researched-backed recipes
    
    Example: POST /meal-plan with body:
    {
        "available_ingredients": ["chicken", "rice", "broccoli", "olive oil", "egg", "spinach"],
        "nutritional_goals": {"protein_g": 40, "calories": 2500},
        "meal_type": "high_protein",
        "num_meals": 5,
        "cooking_time_limit": 30,
        "dietary_restrictions": ["gluten_free"]
    }
    """
    try:
        logger.info(f"🍽️  Meal plan request: {request.meal_type} with {request.num_meals} meals")
        
        meal_planner = get_meal_planner()
        
        result = meal_planner.generate_meal_plan(
            available_ingredients=request.available_ingredients,
            nutritional_goals=request.nutritional_goals,
            dietary_restrictions=request.dietary_restrictions,
            cuisine_preferences=request.cuisine_preferences,
            meal_type=request.meal_type,
            num_meals=request.num_meals,
            cooking_time_limit=request.cooking_time_limit
        )
        
        return MealPlanResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Meal plan error: {e}")
        return MealPlanResponse(
            success=False,
            error=str(e)
        )


@app.post("/weekly-meal-plan", tags=["Meal Planning"])
async def generate_weekly_meal_plan(request: WeeklyMealPlanRequest):
    """
    📅 GENERATE 7-DAY MEAL PLAN

    Creates a complete weekly meal plan with:
    - All meals optimized for nutritional goals
    - Shopping list organized by category
    - Variety across cuisines and flavors
    - High protein focus
    - Researched-backed healthy recipes

    Example: POST /weekly-meal-plan with body:
    {
        "available_ingredients": ["chicken", "fish", "eggs", "rice", "vegetables"],
        "nutritional_goals": {"protein_g": 150, "calories": 14000},
        "dietary_restrictions": ["nut_allergy"]
    }
    """
    try:
        logger.info("📅 Generating 7-day meal plan...")

        meal_planner = get_meal_planner()

        result = meal_planner.generate_weekly_meal_plan(
            available_ingredients=request.available_ingredients,
            nutritional_goals=request.nutritional_goals,
            dietary_restrictions=request.dietary_restrictions,
            cuisine_preferences=request.cuisine_preferences
        )

        return result

    except Exception as e:
        logger.error(f"❌ Weekly meal plan error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/meal-chat", response_model=MealChatResponse, tags=["Meal Planning"])
async def meal_chat(request: MealChatRequest):
    """
    💬 CONVERSATIONAL MEAL PLANNING CHAT

    Chat naturally with the AI meal planning assistant.
    The assistant can help with:
    - Meal suggestions based on ingredients
    - Nutrition advice
    - Recipe ideas
    - Diet planning

    Example: POST /meal-chat with body:
    {
        "message": "I have chicken and rice, suggest a high protein meal",
        "history": [
            {"role": "user", "parts": ["Hello"]},
            {"role": "model", "parts": ["Hi! I can help you plan meals."]}
        ]
    }
    """
    try:
        logger.info(f"💬 Chat message: {request.message[:50]}...")

        meal_planner = get_meal_planner()

        response_text = meal_planner.chat(
            user_message=request.message,
            history=request.history,
            user_profile=request.user_profile  # Pass profile data
        )

        return MealChatResponse(
            success=True,
            response=response_text
        )

    except Exception as e:
        logger.error(f"❌ Meal chat error: {e}")
        return MealChatResponse(
            success=False,
            response="Sorry, I encountered an error. Please try again.",
            error=str(e)
        )


# ==================== COMPREHENSIVE HEALTH PROFILE ENDPOINTS ====================

@app.post("/user-profile", response_model=UserProfileResponse, tags=["User Profile"])
async def save_user_profile(profile: UserProfileRequest):
    """
    🏥 SAVE COMPREHENSIVE USER HEALTH PROFILE

    Save a complete user health profile including:
    - Body context (age, weight, activity level, goals)
    - Health context (conditions, allergies, medications)
    - Life context (cooking constraints, budget, equipment)

    The system automatically calculates BMR, TDEE, and macro targets.
    This profile data is used to personalize all meal recommendations.
    """
    try:
        logger.info("💾 Saving comprehensive user profile...")

        # Convert to dict for easy manipulation
        profile_data = profile.dict()

        # Calculate BMR, TDEE, and macro targets if body data is provided
        if all([profile.age, profile.gender, profile.weight_kg, profile.height_cm]):
            # BMR calculation using Mifflin-St Jeor equation
            if profile.gender == 'male':
                bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) + 5
            else:
                bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) - 161

            # TDEE calculation based on activity level
            activity_multipliers = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'active': 1.725,
                'very_active': 1.9
            }
            multiplier = activity_multipliers.get(profile.activity_level, 1.55)
            tdee = bmr * multiplier

            # Target calories based on goal
            goal_adjustments = {
                'lose_fat': -300,    # 300 cal deficit
                'gain_muscle': +200, # 200 cal surplus
                'bulk': +400,        # 400 cal surplus
                'recomp': 0,         # At maintenance
                'maintain': 0        # Maintain current
            }
            adjustment = goal_adjustments.get(profile.health_goal, 0)
            target_calories = tdee + adjustment

            # Macro calculation (protein priority approach)
            protein_multipliers = {
                'lose_fat': 2.2,     # High protein for muscle retention
                'gain_muscle': 2.0,  # High protein for growth
                'bulk': 1.8,         # Moderate protein
                'recomp': 2.2,       # High protein for body comp
                'maintain': 1.6      # General health
            }
            protein_mult = protein_multipliers.get(profile.health_goal, 1.6)
            target_protein = profile.weight_kg * protein_mult

            target_fat = target_calories * 0.25 / 9  # 25% calories from fat
            remaining_calories = target_calories - (target_protein * 4) - (target_fat * 9)
            target_carbs = remaining_calories / 4

            # Update profile data with calculated values
            profile_data.update({
                'bmr_calories': round(bmr, 2),
                'tdee_calories': round(tdee, 2),
                'target_calories': round(target_calories, 2),
                'target_protein_g': round(target_protein, 2),
                'target_carbs_g': round(target_carbs, 2),
                'target_fat_g': round(target_fat, 2)
            })

            logger.info(f"✅ Calculated targets: {int(target_calories)} cal, {int(target_protein)}g protein daily")

        return UserProfileResponse(
            success=True,
            message="Profile saved successfully with calculated nutrition targets",
            profile=UserProfileRequest(**profile_data)
        )

    except Exception as e:
        logger.error(f"❌ Profile save error: {e}")
        return UserProfileResponse(
            success=False,
            error=str(e)
        )


@app.get("/user-profile/{user_id}", response_model=UserProfileResponse, tags=["User Profile"])
async def get_user_profile(user_id: str):
    """
    📋 GET USER HEALTH PROFILE

    Retrieve a user's comprehensive health profile by user ID.
    Returns all profile data including calculated nutrition targets.
    """
    try:
        logger.info(f"🔍 Fetching profile for user: {user_id}")

        # TODO: Fetch from Supabase database when connected
        return UserProfileResponse(
            success=False,
            message="Profile retrieval not yet implemented - database connection needed"
        )

    except Exception as e:
        logger.error(f"❌ Profile fetch error: {e}")
        return UserProfileResponse(
            success=False,
            error=str(e)
        )


@app.post("/recipes", tags=["Meal Planning"])
async def get_recipe_suggestions(request: RecipeSuggestionRequest):
    """
    👨‍🍳 GET RECIPE SUGGESTIONS
    
    Find creative recipes using available ingredients with:
    - Researched-backed healthy options
    - Authenticated from credible recipe sources
    - Multiple cuisine options
    - Difficulty levels (beginner to advanced)
    - Complete nutritional information
    
    Example: POST /recipes with body:
    {
        "ingredients": ["pasta", "tomato", "garlic", "olive oil", "basil"],
        "cuisine": "italian",
        "skill_level": "intermediate",
        "dietary_needs": ["gluten_free", "high_protein"]
    }
    """
    try:
        logger.info(f"👨‍🍳 Getting recipes for {len(request.ingredients)} ingredients")
        
        meal_planner = get_meal_planner()
        
        result = meal_planner.get_recipe_suggestions(
            ingredients=request.ingredients,
            cuisine=request.cuisine,
            skill_level=request.skill_level,
            dietary_needs=request.dietary_needs
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Recipe suggestion error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/analyze-nutrition", tags=["Meal Planning"])
async def analyze_meal_nutrition(request: NutritionAnalysisRequest):
    """
    🔬 ANALYZE MEAL NUTRITION
    
    Get detailed nutritional breakdown of a meal using:
    - Verified nutritional databases
    - Research-backed analysis
    - Macronutrient and micronutrient data
    - Health benefits information
    
    Example: POST /analyze-nutrition with body:
    {
        "meal_description": "Grilled chicken breast (200g) with brown rice (150g) and steamed broccoli (100g)",
        "serving_size": "1 serving"
    }
    """
    try:
        logger.info(f"🔬 Analyzing nutrition: {request.meal_description[:50]}...")
        
        meal_planner = get_meal_planner()
        
        result = meal_planner.get_nutrition_analysis(
            meal_description=request.meal_description,
            serving_size=request.serving_size
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Nutrition analysis error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== BACKGROUND PRODUCT SCRAPER ENDPOINTS ====================

@app.post("/scraper/run-now", tags=["Background Scraper"])
async def run_scraper_now():
    """
    🛒 RUN SCRAPER IMMEDIATELY
    
    Manually trigger the product scraper to run now (instead of waiting for schedule).
    Scrapes Amazon and BigBasket across all product categories and adds to database.
    
    Returns results of the scrape operation.
    """
    try:
        logger.info("🛒 Manual scraper trigger requested")
        
        from agents.background_scraper import get_scraper
        
        scraper = get_scraper()
        result = await scraper.run_full_scrape_cycle()
        
        logger.info(f"✅ Manual scrape complete: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Scraper error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/scraper/status", tags=["Background Scraper"])
async def get_scraper_status():
    """
    📊 GET SCRAPER STATUS
    
    Get information about:
    - Whether scraper is running
    - Scheduled jobs
    - Last scrape result
    - Next scheduled run time
    """
    try:
        from knowledge.background_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        return {
            "success": True,
            "scheduler_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/scraper/last-result", tags=["Background Scraper"])
async def get_last_scrape_result():
    """
    📋 GET LAST SCRAPE RESULT
    
    Get the result of the last product scraping operation:
    - Products added
    - Products skipped (duplicates)
    - Breakdown by category
    - When it ran
    """
    try:
        from knowledge.background_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        result = scheduler.get_last_scrape_result()
        
        if result:
            return {
                "success": True,
                "last_result": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "last_result": None,
                "message": "No scraper runs yet"
            }
        
    except Exception as e:
        logger.error(f"❌ Error getting result: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/scraper/schedule", tags=["Background Scraper"])
async def schedule_scraper(interval_hours: int = 24):
    """
    ⏰ SCHEDULE SCRAPER
    
    Configure how often the scraper runs in the background.
    
    Args:
        interval_hours: Run scraper every N hours (default: 24 = daily)
    """
    try:
        from knowledge.background_scheduler import get_scheduler
        
        if interval_hours < 1 or interval_hours > 720:  # Max 30 days
            raise ValueError("interval_hours must be between 1 and 720")
        
        logger.info(f"⏰ Scheduling scraper to run every {interval_hours} hours")
        
        scheduler = get_scheduler()
        
        # Cancel existing scraper job
        try:
            scheduler.remove_job("background_product_scraper")
        except:
            pass
        
        # Schedule new one
        result = await scheduler.schedule_product_scraping(
            interval_hours=interval_hours,
            job_id="background_product_scraper"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error scheduling scraper: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/scraper/jobs", tags=["Background Scraper"])
async def get_scheduled_jobs():
    """
    📅 GET SCHEDULED JOBS
    
    List all background jobs currently scheduled.
    """
    try:
        from knowledge.background_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        return {
            "success": True,
            "jobs": jobs,
            "total_jobs": len(jobs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting jobs: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    from server_utils import find_free_port, print_server_info, check_port_available

    # Try to use port 8000, or find next available
    desired_port = 8000
    if not check_port_available(desired_port):
        print(f"⚠️  Port {desired_port} is in use, finding alternative...")
        port = find_free_port(start_port=8000)
        print(f"✅ Using port {port} instead")
    else:
        port = desired_port

    # Print connection information
    print_server_info("0.0.0.0", port)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Allow connections from network (not just localhost)
        port=port,
        reload=False,  # Disable reload to prevent shutdown issues
        log_level=settings.LOG_LEVEL.lower()
    )
