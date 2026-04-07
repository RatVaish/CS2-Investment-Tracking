"""
Payments — Stripe subscription management.
"""

import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

FREE_TIER_INVESTMENT_LIMIT = 10


class CheckoutRequest(BaseModel):
    price_id: str
    success_url: str = f"{settings.FRONTEND_URL}/app/billing?success=true"
    cancel_url: str = f"{settings.FRONTEND_URL}/app/billing?canceled=true"


def _get_or_create_stripe_customer(user: User, db: Session) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        name=user.display_name or user.username,
        metadata={"user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    db.commit()
    return customer.id


def _apply_subscription_status(user: User, subscription, db: Session) -> None:
    """Update user tier from a Stripe subscription object (new SDK uses attributes not dict)."""
    # New Stripe SDK: use attribute access, fall back to dict-style for safety
    try:
        sub_status = subscription.status
        sub_id = subscription.id
    except AttributeError:
        sub_status = subscription.get("status", "")
        sub_id = subscription.get("id")

    user.stripe_subscription_id = sub_id
    user.subscription_status = sub_status

    if sub_status in ("active", "trialing"):
        user.tier = "pro"
    else:
        user.tier = "free"

    db.commit()
    logger.info(f"User {user.id} subscription updated: status={sub_status} tier={user.tier}")


def _get_customer_id(data) -> str:
    """Extract customer ID from Stripe event data object or dict."""
    try:
        return data.customer
    except AttributeError:
        return data.get("customer")


@router.post("/create-checkout-session")
def create_checkout_session(
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_prices = {settings.STRIPE_MONTHLY_PRICE_ID, settings.STRIPE_ANNUAL_PRICE_ID}
    if body.price_id not in allowed_prices:
        raise HTTPException(status_code=400, detail="Invalid price ID")
    if current_user.tier == "pro":
        raise HTTPException(status_code=400, detail="Already subscribed. Use the billing portal to manage your plan.")

    customer_id = _get_or_create_stripe_customer(current_user, db)

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": body.price_id, "quantity": 1}],
            mode="subscription",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={"user_id": str(current_user.id)},
            subscription_data={"metadata": {"user_id": str(current_user.id)}},
            allow_promotion_codes=True,
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe checkout error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

    return {"url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.errors.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]
    logger.info(f"Stripe webhook received: {event_type}")

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        customer_id = _get_customer_id(data)
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"No user found for Stripe customer {customer_id}")
            return JSONResponse({"received": True})
        _apply_subscription_status(user, data, db)

    elif event_type == "customer.subscription.deleted":
        customer_id = _get_customer_id(data)
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.tier = "free"
            user.subscription_status = "canceled"
            user.stripe_subscription_id = None
            db.commit()
            logger.info(f"User {user.id} downgraded to free")

    elif event_type == "invoice.payment_failed":
        customer_id = _get_customer_id(data)
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = "past_due"
            db.commit()
            logger.info(f"User {user.id} payment failed — marked past_due")

    return JSONResponse({"received": True})


@router.get("/billing-portal")
def billing_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found. Please subscribe first.")
    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/app/billing",
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe portal error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to open billing portal")
    return {"url": session.url}


@router.get("/status")
def subscription_status(current_user: User = Depends(get_current_user)):
    return {
        "tier": current_user.tier,
        "subscription_status": current_user.subscription_status,
        "stripe_customer_id": current_user.stripe_customer_id,
        "investment_limit": FREE_TIER_INVESTMENT_LIMIT if current_user.tier == "free" else None,
    }
