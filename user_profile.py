from pydantic import BaseModel


class UserProfile(BaseModel):
    customer_age: int

    past_purchase_count: int

    past_return_rate: float

    session_length_minutes: float

    num_product_views: int

    device_type: str

    shipping_method: str

    payment_method: str

    used_coupon: int