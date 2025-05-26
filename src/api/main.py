from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload
import pyotp
import stripe
import os
from pydantic import BaseModel, EmailStr, constr, validator

from . import models, auth
from .database import get_db, init_db
from .research import research_service
from .routers import subscription
from .cache import cache, cache_response
from .monitoring import setup_monitoring, monitor_endpoint, StructuredLogger
from .config import settings
from .services.email import EmailService

# Add ADK router import
from .routers import adk
# Add health router import  
from .routers import health
# Add monitoring integration
from .monitoring.cloud_monitoring import CloudMonitoringService
from .monitoring.monitoring_middleware import setup_request_monitoring

# Configure Stripe
stripe.api_key = settings["stripe"]["secret_key"]
stripe.api_version = "2023-10-16"  # Use latest stable version

# Pydantic models for payment/subscription
class SubscriptionPlanCreate(BaseModel):
    name: str
    description: str
    price: float
    interval: str
    features: Dict[str, Any]

    @validator("interval")
    def validate_interval(cls, v):
        if v not in ["month", "year"]:
            raise ValueError("interval must be 'month' or 'year'")
        return v

class PaymentMethodCreate(BaseModel):
    payment_method_id: str
    set_default: bool = False

class SubscriptionCreate(BaseModel):
    plan_id: int
    payment_method_id: Optional[str] = None

class WebhookEvent(BaseModel):
    type: str
    data: Dict[str, Any]

# Initialize FastAPI app with enhanced metadata
app = FastAPI(
    title="Parallax Pal API",
    description="""
    Parallax Pal API - Research and Analytics Integration Platform
    
    Features:
    * Secure authentication with JWT
    * Research task management
    * Real-time progress tracking
    * Analytics integration
    * Admin dashboard
    * ADK-based agent system integration
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Include routers
app.include_router(subscription.router)
# Add ADK router
app.include_router(adk.router)
# Add health router
app.include_router(health.router)

# Set up monitoring and logging
logger = setup_monitoring(app)
structured_logger = StructuredLogger("parallax-pal-api")

# Initialize Cloud Monitoring service
monitoring_service = CloudMonitoringService()
# Setup request monitoring middleware
setup_request_monitoring(app, monitoring_service)

# Configure CORS with enhanced security
allowed_origins = []

# Add frontend URL from settings
if settings.get('frontend', {}).get('url'):
    allowed_origins.append(settings['frontend']['url'])

# For development environments, add localhost origins
if settings.get('environment') == 'development':
    allowed_origins.extend([
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ])
# For production, ensure we have at least one origin
elif not allowed_origins:
    # Fallback to safe default if no frontend URL is configured
    allowed_origins = ["https://app.parallaxanalytics.com"]

# Configure CORS middleware with specific allowed methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "Accept"],
    expose_headers=["Content-Disposition"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Import WebSocket implementation
from .websocket import setup_websocket
# Import ADK WebSocket manager
from .websocket_adk import adk_websocket_manager

# ADK configuration
ADK_ENABLED = os.getenv("ADK_ENABLED", "false").lower() == "true"
ADK_BASE_URL = os.getenv("ADK_ORCHESTRATOR_URL", "http://localhost:8080")

# Startup Events
@app.on_event("startup")
async def startup_event():
    """Initialize database, monitoring, WebSockets, and ADK on startup"""
    # Initialize database
    init_db()
    
    # Set up WebSockets
    setup_websocket(app)
    
    # Initialize ADK WebSocket manager if enabled
    if ADK_ENABLED:
        try:
            await adk_websocket_manager.initialize(ADK_BASE_URL)
            structured_logger.log("info", "ADK WebSocket manager initialized",
                                 adk_base_url=ADK_BASE_URL)
        except Exception as e:
            structured_logger.log("error", "Failed to initialize ADK WebSocket manager", 
                                 error=str(e))
    
    # Log successful startup
    structured_logger.log("info", "Application started successfully")

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

# Authentication Endpoints
@app.post("/token", 
    response_model=Dict[str, str],
    tags=["authentication"],
    summary="Obtain JWT access token",
    description="Authenticate user credentials and return JWT token for API access")
@monitor_endpoint("login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = await auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        structured_logger.log("warning", "Failed login attempt", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with appropriate expiration
    access_token_expires = timedelta(minutes=settings['security']['access_token_expire_minutes'])
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Create refresh token with appropriate expiration
    refresh_token_expires = timedelta(days=settings['security']['refresh_token_expire_days'])
    refresh_token = auth.create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )
    
    # Store refresh token in database
    db_refresh_token = models.RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings['security']['refresh_token_expire_days'])
    )
    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)

    structured_logger.log("info", "Successful login", username=user.username)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/register", response_model=Dict[str, Any],
    tags=["authentication"],
    summary="Register a new user",
    description="Create a new user account")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate verification token with purpose claim for extra security
    verification_token = auth.create_access_token(
        data={
            "sub": new_user.username, 
            "purpose": "email_verification",
            "email": new_user.email  # Include email to prevent token reuse for different email
        }, 
        expires_delta=timedelta(hours=24)
    )
    
    # Send verification email
    await send_verification_email(new_user.email, verification_token)
    
    return {"message": "Registration successful. Please check your email to verify your account."}

@app.get("/verify", tags=["authentication"],
    summary="Verify user account",
    description="Verify user account using the verification token")
async def verify(token: str, db: Session = Depends(get_db)):
    """
    Verify user account using email verification token
    
    Args:
        token: JWT verification token
        db: Database session
    
    Returns:
        dict: Message indicating verification status
    """
    # Use a generic error message to prevent information disclosure
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification token"
    )
    
    # Decode and validate the token
    payload = auth.decode_token(token)
    if not payload:
        structured_logger.log("warning", "Invalid verification token used")
        raise invalid_token_exception
    
    # Extract username and check token purpose
    username: str = payload.get("sub")
    token_purpose = payload.get("purpose")
    
    # Validate token has required claims
    if not username or token_purpose != "email_verification":
        structured_logger.log("warning", "Verification token missing required claims")
        raise invalid_token_exception
    
    # Use ORM's constant-time comparison to find the user
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        # Don't reveal that user doesn't exist
        structured_logger.log("warning", "User not found during verification")
        raise invalid_token_exception
    
    # Check if account already verified
    if user.is_active:
        return {"message": "Account already verified"}
    
    # Update user and log activity
    user.is_active = True
    user.verified_at = datetime.utcnow()
    db.commit()
    
    structured_logger.log("info", "User account verified", user_id=user.id)
    
    # Send welcome email
    try:
        await EmailService.send_welcome_email(user.email, user.username)
    except Exception as e:
        # Log error but continue - welcome email is not critical
        logger.error(f"Error sending welcome email: {str(e)}")
    
    return {"message": "Account verified successfully"}

@app.post("/generate_mfa_secret", tags=["authentication"],
    summary="Generate MFA secret",
    description="Generate a new MFA secret for the user")
async def generate_mfa_secret(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Generate new MFA secret
    totp = pyotp.TOTP(pyotp.random_base32())
    secret = totp.secret()

    # Store secret in database
    current_user.mfa_secret = secret
    db.commit()

    # Return secret
    return {"secret": secret}

@app.post("/verify_mfa", tags=["authentication"],
    summary="Verify MFA code",
    description="Verify the MFA code provided by the user")
async def verify_mfa(code: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up for this user"
        )
    
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code"
        )
    
    return {"message": "MFA verification successful"}

@app.post("/refresh_token",
    response_model=Dict[str, str],
    tags=["authentication"],
    summary="Refresh JWT access token",
    description="Use refresh token to obtain a new JWT access token")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    payload = auth.decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.query(models.User)
        .filter(models.User.username == username)
        .filter(models.User.is_active == True)
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if refresh token exists and is valid
    db_refresh_token = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == refresh_token)
        .filter(models.RefreshToken.user_id == user.id)
        .filter(models.RefreshToken.expires_at > datetime.utcnow())
        .first()
    )
    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    # Rotate refresh token
    new_refresh_token = auth.create_refresh_token(data={"sub": user.username})
    db_new_refresh_token = models.RefreshToken(
        token=new_refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings['security']['refresh_token_expire_days'])
    )
    db.add(db_new_refresh_token)
    db.commit()
    db.refresh(db_new_refresh_token)

    # Invalidate old refresh token
    db_refresh_token.replaced_by = db_new_refresh_token.id
    db.commit()

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@app.post("/reset_password_request", tags=["authentication"],
    summary="Request password reset",
    description="Request a password reset link to be sent to the user's email address")
async def reset_password_request(email: str, db: Session = Depends(get_db), request: Request = None):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate reset token with purpose claim for extra security
    reset_token = auth.create_access_token(
        data={
            "sub": user.username,
            "purpose": "password_reset",
            "email": user.email,  # Include email to prevent token reuse for different email
            "jti": f"{datetime.utcnow().timestamp()}-{os.urandom(8).hex()}"  # Unique ID for one-time use
        },
        expires_delta=timedelta(hours=1)  # Shorter expiry for security
    )

    # Record reset request in audit log
    auth.log_auth_activity(
        db=db,
        user=user,
        action="password_reset_requested",
        ip_address=request.client.host if request else None,
        details="Password reset email sent"
    )

    # Send reset email
    await send_reset_email(email, reset_token)

    return {"message": "Password reset link sent to your email address"}

# Payment and Subscription Endpoints
@app.post("/api/subscription/plans",
    response_model=Dict[str, Any],
    tags=["subscription"],
    summary="Create subscription plan",
    description="Create a new subscription plan (admin only)")
@monitor_endpoint("create_subscription_plan")
async def create_subscription_plan(
    plan: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_admin_role)
):
    # Create Stripe product and price
    stripe_product = stripe.Product.create(
        name=plan.name,
        description=plan.description,
        metadata={"features": str(plan.features)}
    )
    
    stripe_price = stripe.Price.create(
        product=stripe_product.id,
        unit_amount=int(plan.price * 100),  # Convert to cents
        currency="usd",
        recurring={"interval": plan.interval}
    )
    
    # Create plan in database
    db_plan = models.SubscriptionPlan(
        name=plan.name,
        description=plan.description,
        price=plan.price,
        interval=plan.interval,
        stripe_price_id=stripe_price.id,
        features=plan.features
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    
    return db_plan

@app.get("/api/subscription/plans",
    response_model=List[Dict[str, Any]],
    tags=["subscription"],
    summary="List subscription plans",
    description="Get list of available subscription plans")
@monitor_endpoint("list_subscription_plans")
@cache_response(timeout=300)  # Cache for 5 minutes
async def list_subscription_plans(
    db: Session = Depends(get_db)
):
    # Optimized query that selects only needed columns and adds ordering for consistency
    plans = db.query(models.SubscriptionPlan)\
        .filter(models.SubscriptionPlan.is_active == True)\
        .order_by(models.SubscriptionPlan.price.asc())\
        .all()
    
    # Note: We're not selecting specific columns because the response_model needs the full object
    # In a real optimization, we'd create a specific Pydantic model for the response
    # that only includes the fields we need to return
    
    return plans

@app.post("/api/subscription/checkout",
    response_model=Dict[str, str],
    tags=["subscription"],
    summary="Create checkout session",
    description="Create a Stripe checkout session for subscription")
@monitor_endpoint("create_checkout_session")
async def create_checkout_session(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    plan = db.query(models.SubscriptionPlan)\
        .filter(models.SubscriptionPlan.id == plan_id)\
        .filter(models.SubscriptionPlan.is_active == True)\
        .first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Create or get Stripe customer
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id}
        )
        current_user.stripe_customer_id = customer.id
        db.commit()
    
    # Create checkout session
    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': plan.stripe_price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f"{settings['frontend']['url']}/subscription/success",
        cancel_url=f"{settings['frontend']['url']}/subscription/cancel",
        metadata={
            "user_id": current_user.id,
            "plan_id": plan.id
        }
    )
    
    return {"session_id": session.id}

@app.post("/api/subscription/webhook",
    tags=["subscription"],
    summary="Stripe webhook handler",
    description="Handle Stripe webhook events")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(...),
    db: Session = Depends(get_db)
):
    # Get raw request body
    payload = await request.body()
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings["stripe"]["webhook_secret"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event.type == "checkout.session.completed":
        session = event.data.object
        user_id = session.metadata.get("user_id")
        plan_id = session.metadata.get("plan_id")
        
        # Create subscription record
        subscription = models.Subscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_subscription_id=session.subscription,
            status=models.SubscriptionStatus.ACTIVE,
            current_period_start=datetime.fromtimestamp(session.subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(session.subscription.current_period_end)
        )
        db.add(subscription)
        db.commit()
    
    elif event.type == "customer.subscription.updated":
        subscription = event.data.object
        db_subscription = db.query(models.Subscription)\
            .filter(models.Subscription.stripe_subscription_id == subscription.id)\
            .first()
        if db_subscription:
            db_subscription.status = subscription.status
            db_subscription.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            db_subscription.cancel_at_period_end = subscription.cancel_at_period_end
            db.commit()
    
    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        db_subscription = db.query(models.Subscription)\
            .filter(models.Subscription.stripe_subscription_id == subscription.id)\
            .first()
        if db_subscription:
            db_subscription.status = models.SubscriptionStatus.CANCELED
            db_subscription.canceled_at = datetime.now()
            db.commit()

    return {"status": "success"}

class CancellationOptions(BaseModel):
    immediate: bool = False

@app.post("/api/subscription/cancel",
    response_model=Dict[str, str],
    tags=["subscription"],
    summary="Cancel subscription",
    description="Cancel the current subscription")
@monitor_endpoint("cancel_subscription")
async def cancel_subscription(
    options: CancellationOptions = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if options is None:
        options = CancellationOptions()
        
    structured_logger.log("info", "Subscription cancellation requested", 
        user_id=current_user.id, immediate=options.immediate)
    
    # Get active subscription with plan in a single optimized query
    subscription = db.query(models.Subscription)\
        .options(selectinload(models.Subscription.plan))\
        .filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        )\
        .first()
    
    if not subscription:
        structured_logger.log("warning", "No active subscription found for cancellation", user_id=current_user.id)
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    try:
        # Begin a transaction for atomicity
        # Note: We already have an implicit transaction with db.commit() later
        
        # Cancel subscription in Stripe
        try:
            if options.immediate:
                # Cancel immediately
                stripe_sub = stripe.Subscription.delete(
                    subscription.stripe_subscription_id
                )
                structured_logger.log("info", "Subscription canceled immediately in Stripe", 
                    subscription_id=subscription.stripe_subscription_id)
                
                # Update local subscription to canceled status
                subscription.status = models.SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.utcnow()
                end_date = datetime.utcnow()
            else:
                # Cancel at period end
                stripe_sub = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                structured_logger.log("info", "Subscription set to cancel at period end in Stripe", 
                    subscription_id=subscription.stripe_subscription_id)
                
                # Update local subscription
                subscription.cancel_at_period_end = True
                end_date = subscription.current_period_end
                
        except stripe.error.StripeError as e:
            structured_logger.log("error", "Stripe error during subscription cancellation", 
                error=str(e), user_id=current_user.id)
            raise HTTPException(status_code=400, detail=f"Payment provider error: {str(e)}")
        
        # Commit database changes
        db.commit()
        
        # Send cancellation email asynchronously (with correct end date)
        try:
            # Use plan data we already loaded with selectinload
            await EmailService.send_subscription_canceled(
                email=current_user.email,
                plan_name=subscription.plan.name,
                end_date=end_date
            )
        except Exception as email_error:
            # Log error but don't fail the operation - email is non-critical
            structured_logger.log("error", "Failed to send cancellation email", 
                error=str(email_error), user_id=current_user.id)
        
        # Log cancellation event for analytics
        auth.log_auth_activity(
            db=db,
            user=current_user,
            action="subscription_canceled",
            details=f"Plan: {subscription.plan.name}, End date: {end_date}, Immediate: {options.immediate}"
        )
        
        structured_logger.log("info", "Subscription successfully canceled", 
            user_id=current_user.id, 
            plan=subscription.plan.name,
            end_date=end_date.isoformat() if end_date else None,
            immediate=options.immediate)
        
        if options.immediate:
            return {"message": "Subscription has been canceled immediately"}
        else:
            return {"message": "Subscription will be canceled at the end of the billing period"}
    
    except Exception as e:
        # Handle unexpected errors
        db.rollback()  # Roll back the transaction
        structured_logger.log("error", "Unexpected error during subscription cancellation", 
            error=str(e), error_type=type(e).__name__, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/api/subscription/reactivate",
    response_model=Dict[str, str],
    tags=["subscription"],
    summary="Reactivate subscription",
    description="Reactivate a subscription that was previously set to cancel at period end")
@monitor_endpoint("reactivate_subscription")
async def reactivate_subscription(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    structured_logger.log("info", "Subscription reactivation requested", user_id=current_user.id)
    
    # Get subscription that is marked for cancellation at period end
    subscription = db.query(models.Subscription)\
        .options(selectinload(models.Subscription.plan))\
        .filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status == models.SubscriptionStatus.ACTIVE,
            models.Subscription.cancel_at_period_end == True
        )\
        .first()
    
    if not subscription:
        structured_logger.log("warning", "No subscription eligible for reactivation found", user_id=current_user.id)
        raise HTTPException(status_code=404, detail="No subscription eligible for reactivation found")
    
    try:
        # Reactivate subscription in Stripe
        try:
            stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )
            structured_logger.log("info", "Subscription reactivated in Stripe", 
                subscription_id=subscription.stripe_subscription_id)
        except stripe.error.StripeError as e:
            structured_logger.log("error", "Stripe error during subscription reactivation", 
                error=str(e), user_id=current_user.id)
            raise HTTPException(status_code=400, detail=f"Payment provider error: {str(e)}")
        
        # Update local subscription
        subscription.cancel_at_period_end = False
        db.commit()
        
        # Send reactivation email asynchronously
        try:
            await EmailService.send_subscription_reactivated(
                email=current_user.email,
                plan_name=subscription.plan.name,
                next_billing_date=subscription.current_period_end
            )
        except Exception as email_error:
            # Log error but don't fail the operation - email is non-critical
            structured_logger.log("error", "Failed to send reactivation email", 
                error=str(email_error), user_id=current_user.id)
        
        # Log reactivation event for analytics
        auth.log_auth_activity(
            db=db,
            user=current_user,
            action="subscription_reactivated",
            details=f"Plan: {subscription.plan.name}"
        )
        
        structured_logger.log("info", "Subscription successfully reactivated", 
            user_id=current_user.id, 
            plan=subscription.plan.name)
        
        return {"message": "Your subscription has been reactivated"}
    
    except Exception as e:
        # Handle unexpected errors
        db.rollback()  # Roll back the transaction
        structured_logger.log("error", "Unexpected error during subscription reactivation", 
            error=str(e), error_type=type(e).__name__, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.get("/api/subscription/status",
    response_model=Dict[str, Any],
    tags=["subscription"],
    summary="Get subscription status",
    description="Get current user's subscription status")
@monitor_endpoint("get_subscription_status")
@cache_response(timeout=60)  # Cache for 1 minute
async def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Use a join to efficiently fetch subscription with plan details in a single query
    # This avoids the N+1 query problem when accessing subscription.plan
    subscription = db.query(models.Subscription)\
        .options(
            selectinload(models.Subscription.plan)  # Eager load the plan relationship
        )\
        .filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        )\
        .first()
    
    if not subscription:
        return {
            "has_subscription": False,
            "subscription": None
        }
    
    # Extract only the needed plan data to avoid serializing the entire object
    plan_data = {
        "id": subscription.plan.id,
        "name": subscription.plan.name,
        "description": subscription.plan.description,
        "price": subscription.plan.price,
        "interval": subscription.plan.interval,
        "features": subscription.plan.features,
        "allows_ollama": subscription.plan.allows_ollama
    }
    
    return {
        "has_subscription": True,
        "subscription": {
            "plan": plan_data,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end
        }
    }

# Payment Method Endpoints
@app.post("/api/payment-methods",
    response_model=Dict[str, Any],
    tags=["payment"],
    summary="Add payment method",
    description="Add a new payment method for the user")
@monitor_endpoint("add_payment_method")
async def add_payment_method(
    payment_method: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        # Check if customer exists in Stripe
        if not current_user.stripe_customer_id:
            # Create customer if needed
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            # We'll commit this change along with other database operations later
        
        # Attach payment method to Stripe customer in a single API call
        # and retrieve payment method details in the same call
        try:
            # First attach payment method
            stripe.PaymentMethod.attach(
                payment_method.payment_method_id,
                customer=current_user.stripe_customer_id
            )
            
            # Then retrieve payment method details
            pm = stripe.PaymentMethod.retrieve(payment_method.payment_method_id)
        except stripe.error.StripeError as e:
            # Handle specific Stripe errors with better error messages
            error_message = str(e)
            if "No such payment_method" in error_message:
                error_message = "Invalid payment method ID"
            elif "No such customer" in error_message:
                error_message = "Customer account not found in payment system"
            
            structured_logger.log("error", "Payment method attachment failed",
                               user_id=current_user.id,
                               error_message=error_message)
            raise HTTPException(status_code=400, detail=error_message)

        # Begin transaction to ensure all database operations succeed or fail together
        try:
            # Create payment method record
            db_payment_method = models.PaymentMethod(
                user_id=current_user.id,
                stripe_payment_method_id=pm.id,
                type=pm.type,
                last4=pm.card.last4,
                exp_month=pm.card.exp_month,
                exp_year=pm.card.exp_year,
                is_default=payment_method.set_default
            )
            
            if payment_method.set_default:
                # Set all other payment methods as non-default in single query
                db.query(models.PaymentMethod)\
                    .filter(models.PaymentMethod.user_id == current_user.id)\
                    .update({"is_default": False})
                
                # Update default payment method in Stripe
                stripe.Customer.modify(
                    current_user.stripe_customer_id,
                    invoice_settings={
                        "default_payment_method": payment_method.payment_method_id
                    }
                )
            
            # Add new payment method to database
            db.add(db_payment_method)
            
            # Commit all changes at once (customer ID update, payment method flags, new payment method)
            db.commit()
            db.refresh(db_payment_method)
            
            # Log successful operation
            structured_logger.log("info", "Payment method added successfully",
                                user_id=current_user.id,
                                payment_method_id=pm.id,
                                is_default=payment_method.set_default)
            
            return db_payment_method
        except Exception as db_error:
            # Rollback transaction on database error
            db.rollback()
            
            # Log the database error
            structured_logger.log("error", "Database error adding payment method",
                               user_id=current_user.id,
                               error_message=str(db_error))
            
            # Try to detach the payment method from Stripe to clean up
            try:
                stripe.PaymentMethod.detach(payment_method.payment_method_id)
            except stripe.error.StripeError:
                # Ignore errors during cleanup
                pass
                
            raise HTTPException(status_code=500, detail="Failed to save payment method")
            
    except stripe.error.StripeError as e:
        # Handle other Stripe errors
        structured_logger.log("error", "Stripe error adding payment method",
                           user_id=current_user.id,
                           error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/payment-methods",
    response_model=List[Dict[str, Any]],
    tags=["payment"],
    summary="List payment methods",
    description="Get list of user's payment methods")
@monitor_endpoint("list_payment_methods")
async def list_payment_methods(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    payment_methods = db.query(models.PaymentMethod)\
        .filter(models.PaymentMethod.user_id == current_user.id)\
        .all()
    return payment_methods

@app.delete("/api/payment-methods/{payment_method_id}",
    response_model=Dict[str, str],
    tags=["payment"],
    summary="Delete payment method",
    description="Delete a payment method")
@monitor_endpoint("delete_payment_method")
async def delete_payment_method(
    payment_method_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get payment method from database
    payment_method = db.query(models.PaymentMethod)\
        .filter(models.PaymentMethod.user_id == current_user.id)\
        .filter(models.PaymentMethod.stripe_payment_method_id == payment_method_id)\
        .first()
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    try:
        # Detach payment method from Stripe customer
        stripe.PaymentMethod.detach(payment_method_id)
        
        # Delete from database
        db.delete(payment_method)
        db.commit()
        
        return {"message": "Payment method deleted successfully"}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/payment-methods/{payment_method_id}/set-default",
    response_model=Dict[str, str],
    tags=["payment"],
    summary="Set default payment method",
    description="Set a payment method as default")
@monitor_endpoint("set_default_payment_method")
async def set_default_payment_method(
    payment_method_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get payment method from database
    payment_method = db.query(models.PaymentMethod)\
        .filter(models.PaymentMethod.user_id == current_user.id)\
        .filter(models.PaymentMethod.stripe_payment_method_id == payment_method_id)\
        .first()
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    try:
        # Update default payment method in Stripe
        stripe.Customer.modify(
            current_user.stripe_customer_id,
            invoice_settings={
                "default_payment_method": payment_method_id
            }
        )
        
        # Update in database
        db.query(models.PaymentMethod)\
            .filter(models.PaymentMethod.user_id == current_user.id)\
            .update({"is_default": False})
        
        payment_method.is_default = True
        db.commit()
        
        return {"message": "Default payment method updated successfully"}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

async def send_verification_email(email: str, token: str):
    """
    Send verification email using the EmailService
    
    Args:
        email: User's email address 
        token: Verification token (JWT)
    """
    try:
        # Log email sending attempt without showing the token
        structured_logger.log("info", "Sending verification email", email=email)
        
        # Use the EmailService to send the verification email securely
        await EmailService.send_verification_email(email, token)
        
        structured_logger.log("info", "Verification email sent successfully", email=email)
    except Exception as e:
        # Log the error without exposing sensitive information
        structured_logger.log("error", "Failed to send verification email", 
                             error_type=type(e).__name__)
        logger.error(f"Error sending verification email: {str(e)}")
        # Don't raise the exception to prevent exposing sensitive information

async def send_reset_email(email: str, token: str):
    """
    Send password reset email using the EmailService
    
    Args:
        email: User's email address
        token: Reset token (JWT)
    """
    try:
        # Log email sending attempt without showing the token
        structured_logger.log("info", "Sending password reset email", email=email)
        
        # Use the EmailService to send the password reset email securely
        await EmailService.send_password_reset_email(email, token)
        
        structured_logger.log("info", "Password reset email sent successfully", email=email)
    except Exception as e:
        # Log the error without exposing sensitive information
        structured_logger.log("error", "Failed to send password reset email", 
                             error_type=type(e).__name__)
        logger.error(f"Error sending password reset email: {str(e)}")
        # Don't raise the exception to prevent exposing sensitive information

# GPU and Model Management Endpoints
@app.get("/api/gpu-status",
    response_model=Dict[str, Any],
    tags=["gpu"],
    summary="Get GPU status",
    description="Get current GPU status and model recommendations")
@monitor_endpoint("get_gpu_status")
async def get_gpu_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Check subscription features
    subscription = db.query(models.Subscription)\
        .filter(models.Subscription.user_id == current_user.id)\
        .filter(models.Subscription.status == models.SubscriptionStatus.ACTIVE)\
        .first()

    if not subscription or subscription.plan.price < 79.99:  # Pro plan check
        return {"error": "GPU acceleration requires a Pro subscription"}

    from .llm_wrapper import llm
    return llm.get_gpu_status()

@app.post("/api/update-model",
    response_model=Dict[str, str],
    tags=["gpu"],
    summary="Update Ollama model",
    description="Update the Ollama model being used")
@monitor_endpoint("update_model")
async def update_model(
    model_data: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Check subscription features
    subscription = db.query(models.Subscription)\
        .filter(models.Subscription.user_id == current_user.id)\
        .filter(models.Subscription.status == models.SubscriptionStatus.ACTIVE)\
        .first()

    if not subscription or not subscription.plan.allows_ollama:
        raise HTTPException(status_code=403, detail="Ollama access requires a Pro subscription")

    from .llm_wrapper import llm
    try:
        llm.update_ollama_model(model_data["model"])
        return {"message": f"Successfully updated model to {model_data['model']}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Research Endpoints
@app.post("/api/research/tasks",
    response_model=Dict[str, Any],
    tags=["research"],
    summary="Create new research task",
    description="Submit a new research query for processing")
@monitor_endpoint("create_research_task")
async def create_research_task(
    query: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # For ADK enabled systems, redirect to ADK research
    if ADK_ENABLED:
        structured_logger.log("info", "Redirecting to ADK research", user_id=current_user.id)
        # Create a simple forwarding to the ADK router
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/api/adk/research")
    
    # Standard research process
    task = models.ResearchTask(
        query=query,
        owner_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Process task asynchronously
    background_tasks.add_task(
        research_service.process_research_task,
        db,
        task.id,
        query
    )
    
    structured_logger.log("info", "Research task created",
        task_id=task.id,
        user_id=current_user.id
    )
    
    return {"task_id": task.id, "status": task.status}

@app.get("/api/research/tasks/{task_id}",
    response_model=Dict[str, Any],
    tags=["research"],
    summary="Get research task details",
    description="Retrieve status and results of a specific research task")
@monitor_endpoint("get_research_task")
@cache_response(timeout=300)  # Cache for 5 minutes
async def get_research_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = await research_service.get_task_status(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check task ownership
    db_task = db.query(models.ResearchTask).filter(models.ResearchTask.id == task_id).first()
    if db_task.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        structured_logger.log("warning", "Unauthorized task access attempt",
            task_id=task_id,
            user_id=current_user.id
        )
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
        
    return task

@app.get("/api/research/tasks",
    response_model=List[Dict[str, Any]],
    tags=["research"],
    summary="List research tasks",
    description="Get paginated list of research tasks for current user")
@monitor_endpoint("list_research_tasks")
@cache_response(timeout=60)  # Cache for 1 minute
async def list_research_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    tasks = db.query(models.ResearchTask)\
        .filter(models.ResearchTask.owner_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return tasks

# Admin Endpoints
@app.get("/api/admin/tasks",
    response_model=List[Dict[str, Any]],
    tags=["admin"],
    summary="Admin: List all tasks",
    description="Get paginated list of all research tasks (admin only)")
@monitor_endpoint("admin_list_tasks")
@cache_response(timeout=60)
async def admin_list_all_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.check_admin_role)
):
    tasks = db.query(models.ResearchTask)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return tasks

# Health Check Endpoints
@app.get("/",
    tags=["health"],
    summary="Basic health check",
    description="Simple health check endpoint")
@monitor_endpoint("health_check")
async def root():
    return {"status": "online", "service": "Parallax Pal API"}

@app.get("/api/health",
    tags=["health"],
    summary="Detailed health check",
    description="Get detailed health status of the API and its dependencies")
@monitor_endpoint("detailed_health_check")
async def health_check():
    redis_status = "healthy" if cache.client.ping() else "unhealthy"
    db_status = "healthy"
    adk_status = "disabled"
    
    try:
        db = next(get_db())
        db.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"
    
    # Check ADK status if enabled
    if ADK_ENABLED:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{ADK_BASE_URL}/health", timeout=2) as response:
                    if response.status == 200:
                        adk_status = "healthy"
                    else:
                        adk_status = "unhealthy"
        except Exception:
            adk_status = "unhealthy"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "database": db_status,
            "cache": redis_status,
            "adk": adk_status
        }
    }

# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    structured_logger.log("error", "HTTP error",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    structured_logger.log("error", "Unexpected error",
        error_type=type(exc).__name__,
        error_details=str(exc),
        path=request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Custom OpenAPI Schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Use environment variable for host binding, default to localhost for security
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    
    # In production, this should be handled by a proper ASGI server
    uvicorn.run(app, host=host, port=port)