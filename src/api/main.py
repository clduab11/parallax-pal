from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pyotp
import stripe
from pydantic import BaseModel, EmailStr, constr, validator

from . import models, auth
from .database import get_db, init_db
from .research import research_service
from .cache import cache, cache_response
from .monitoring import setup_monitoring, monitor_endpoint, StructuredLogger
from .config import settings

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
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Set up monitoring and logging
logger = setup_monitoring(app)
structured_logger = StructuredLogger("parallax-pal-api")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Events
@app.on_event("startup")
async def startup_event():
    """Initialize database and monitoring on startup"""
    init_db()
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
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    refresh_token = auth.create_refresh_token(data={"sub": user.username})
    
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
    
    # Generate verification token
    verification_token = auth.create_access_token(data={"sub": new_user.username}, expires_delta=timedelta(hours=24))
    
    # Send verification email
    await send_verification_email(new_user.email, verification_token)
    
    return {"message": "Registration successful. Please check your email to verify your account."}

@app.get("/verify", tags=["authentication"],
    summary="Verify user account",
    description="Verify user account using the verification token")
async def verify(token: str, db: Session = Depends(get_db)):
    payload = auth.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.is_active:
        return {"message": "Account already verified"}
    user.is_active = True
    db.commit()
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
async def reset_password_request(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate reset token
    reset_token = auth.create_access_token(data={"sub": user.username}, expires_delta=timedelta(hours=24))

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
    plans = db.query(models.SubscriptionPlan)\
        .filter(models.SubscriptionPlan.is_active == True)\
        .all()
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

@app.post("/api/subscription/cancel",
    response_model=Dict[str, str],
    tags=["subscription"],
    summary="Cancel subscription",
    description="Cancel the current subscription")
@monitor_endpoint("cancel_subscription")
async def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get active subscription
    subscription = db.query(models.Subscription)\
        .filter(models.Subscription.user_id == current_user.id)\
        .filter(models.Subscription.status == models.SubscriptionStatus.ACTIVE)\
        .first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Cancel subscription in Stripe
    stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        cancel_at_period_end=True
    )
    
    # Update local subscription
    subscription.cancel_at_period_end = True
    db.commit()
    
    return {"message": "Subscription will be canceled at the end of the billing period"}

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
    subscription = db.query(models.Subscription)\
        .filter(models.Subscription.user_id == current_user.id)\
        .filter(models.Subscription.status == models.SubscriptionStatus.ACTIVE)\
        .first()
    
    if not subscription:
        return {
            "has_subscription": False,
            "subscription": None
        }
    
    return {
        "has_subscription": True,
        "subscription": {
            "plan": subscription.plan,
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
        # Attach payment method to Stripe customer
        stripe.PaymentMethod.attach(
            payment_method.payment_method_id,
            customer=current_user.stripe_customer_id
        )

        # Get payment method details
        pm = stripe.PaymentMethod.retrieve(payment_method.payment_method_id)

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
            # Set all other payment methods as non-default
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

        db.add(db_payment_method)
        db.commit()
        db.refresh(db_payment_method)

        return db_payment_method
    except stripe.error.StripeError as e:
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
    # TODO: Implement email sending logic here
    print(f"Sending verification email to {email} with token {token}")
    # For example, you can use the following code:
    # from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    # conf = ConnectionConfig(
    #     MAIL_USERNAME=settings.EMAIL_USERNAME,
    #     MAIL_PASSWORD=settings.EMAIL_PASSWORD,
    #     MAIL_FROM=settings.EMAIL_FROM,
    #     MAIL_PORT=settings.EMAIL_PORT,
    #     MAIL_SERVER=settings.EMAIL_HOST,
    #     MAIL_STARTTLS=True,
    #     MAIL_SSL_TLS=False,
    #     USE_CREDENTIALS=True,
    #     VALIDATE_CERTS=True
    # )
    # message = MessageSchema(
    #     subject="Account Verification",
    #     recipients=[email],
    #     body=f"Please click on the following link to verify your account: {settings.FRONTEND_URL}/verify?token={token}",
    #     subtype="html"
    # )
    # fm = FastMail(conf)
    # await fm.send_message(message)
    pass

async def send_reset_email(email: str, token: str):
    # TODO: Implement email sending logic here
    print(f"Sending reset email to {email} with token {token}")
    # Implementation similar to send_verification_email
    pass

# GPU and Model Management Endpoints
@app.get("/api/gpu-status",
    response_model=Dict[str, Any],
    tags=["gpu"],
    summary="Get GPU status",
    description="Get current GPU status and model recommendations")
@monitor_endpoint("get_gpu_status")
async def get_gpu_status():
    from .llm_wrapper import llm
    return llm.get_gpu_status()

@app.post("/api/update-model",
    response_model=Dict[str, str],
    tags=["gpu"],
    summary="Update Ollama model",
    description="Update the Ollama model being used")
@monitor_endpoint("update_model")
async def update_model(model_data: Dict[str, str]):
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
    try:
        db = next(get_db())
        db.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "database": db_status,
            "cache": redis_status
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
    uvicorn.run(app, host="0.0.0.0", port=8000)