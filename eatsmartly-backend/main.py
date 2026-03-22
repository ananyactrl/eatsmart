"""
EatSmartly Backend - FastAPI Application with Multi-Agent System.
Main entry point for the barcode food analyzer API.
"""
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Request
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

from config import settings
from agents.data_collection import DataCollectionAgent
from agents.web_scraping import WebScrapingAgent
from agents.personalization import PersonalizationAgent
# from agents.autogen_orchestrator import AutoGenOrchestrator  # Temporarily disabled
from agents.utils import setup_logger
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
    logger.info("Agents disabled for testing")
except Exception as e:
    logger.warning(f"Agent initialization failed: {e}. OCR will still work.")
    data_agent = None
    scraping_agent = None
    personalization_agent = None

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
    global data_agent, scraping_agent, personalization_agent
    try:
        # Initialize DataCollectionAgent which will attempt DB and Redis connections
        data_agent = DataCollectionAgent()
        scraping_agent = WebScrapingAgent()
        personalization_agent = PersonalizationAgent()

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

    except Exception as e:
        logger.error(f"Startup initialization error: {e}")
        data_agent = None
        scraping_agent = None
        personalization_agent = None

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
    timestamp: str


class UserProfileRequest(BaseModel):
    """Request model for user profile."""
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    health_goal: Optional[str] = None
    allergies: Optional[List[str]] = []
    health_conditions: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []


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
        if data_agent and data_agent.db_engine:
            data_agent.db_engine.connect()
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        # Check Redis connection
        if data_agent and data_agent.redis_client:
            data_agent.redis_client.ping()
            redis_status = "connected"
        else:
            redis_status = "disconnected"
        
        # Determine overall health
        all_healthy = db_status == "connected" and redis_status == "connected"
        
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
        
        # Evaluate food safety
        evaluation = personalization_agent.evaluate_food_safety({
            "name": product_data.get("name"),
            "nutrition": nutrition,
            "ingredients": product_data.get("ingredients"),
            "allergens": product_data.get("allergens")
        }, user_profile)
        
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
        
        # Evaluate food safety
        evaluation = personalization_agent.evaluate_food_safety({
            "name": product_data.get("name"),
            "nutrition": nutrition,
            "ingredients": product_data.get("ingredients"),
            "allergens": product_data.get("allergens")
        }, user_profile)
        
        return {
            "product_name": product_data.get("name"),
            "brand": product_data.get("brand"),
            "nutrition": nutrition,
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



@app.get('/products')
async def list_products(limit: int = 50, offset: int = 0, region: Optional[str] = None, brand: Optional[str] = None):
    """Return recent products from the `products` table with optional filters. If DB not configured, return empty list."""
    try:
        if not data_agent or not data_agent.db_engine:
            return {"products": [], "total": 0, "regions": [], "brands": []}

        # Build query with optional filters
        where_clauses = []
        params = {"limit": limit, "offset": offset}
        
        if region:
            where_clauses.append("region = :region")
            params["region"] = region
        
        if brand:
            where_clauses.append("brand ILIKE :brand")
            params["brand"] = f"%{brand}%"
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        q = text(f"""
            SELECT id, barcode, product_name, brand, manufacturer, region, weight, 
                   fssai_license, image_url, is_verified, created_at, updated_at
            FROM products
            {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        # Get total count
        count_q = text(f"""
            SELECT COUNT(*) FROM products {where_sql}
        """)
        
        # Get unique regions and brands for filters
        regions_q = text("""
            SELECT DISTINCT region FROM products WHERE region IS NOT NULL ORDER BY region
        """)
        
        brands_q = text("""
            SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL ORDER BY brand LIMIT 100
        """)
        
        with data_agent.db_engine.connect() as conn:
            res = conn.execute(q, params)
            rows = []
            for r in res.fetchall():
                # SQLAlchemy RowMapping may not be serializable, convert to dict
                try:
                    rows.append({k: v for k, v in r.items()})
                except Exception:
                    # Fallback for older SQLAlchemy row tuples
                    rows.append(dict(r))
            
            # Get total count
            total = conn.execute(count_q, {k: v for k, v in params.items() if k not in ['limit', 'offset']}).scalar()
            
            # Get filter options
            regions = [r[0] for r in conn.execute(regions_q).fetchall()]
            brands = [r[0] for r in conn.execute(brands_q).fetchall()]

        return {"products": rows, "total": total or 0, "regions": regions, "brands": brands}
    except Exception as e:
        logger.error(f"list_products error: {e}")
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


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Allow connections from network (not just localhost)
        port=3000,
        reload=False,  # Disable reload to prevent shutdown issues
        log_level=settings.LOG_LEVEL.lower()
    )
