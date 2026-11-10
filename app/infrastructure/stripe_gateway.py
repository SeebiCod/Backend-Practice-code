# app/infrastructure/stripe_gateway.py
import stripe
from app.domain.exceptions import PermissionDeniedError
from app.infrastructure.config import STRIPE_SECRET_KEY

class StripePaymentGateway:
    def __init__(self):
        stripe.api_key = STRIPE_SECRET_KEY

    def create_checkout(self, user_id: int, email: str, amount_cents: int) -> str:
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_email=email,
                client_reference_id=str(user_id),
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {"name": "Pro plan"},
                    },
                    "quantity": 1,
                }],
                success_url="http://localhost:8000/success",
                cancel_url="http://localhost:8000/cancel",
            )
        except stripe.StripeError as exc:
            raise PermissionDeniedError(str(exc)) from exc  # turn Stripe's error into OUR error
        return session.url