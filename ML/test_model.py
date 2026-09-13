import os
import joblib
import pandas as pd

MODEL_PATH = "buy_me_not_pipeline.pkl"
USER_HISTORY_PATH = "user_history.csv"

def predict_return_probability(product_data: dict) -> float:
    pipeline = joblib.load(MODEL_PATH)
    df = pd.DataFrame([product_data])
    # Returns the probability of Class 1 (returned)
    prob = pipeline.predict_proba(df)[0][1]
    return float(prob)

def log_user_order_outcome(order_data: dict):
    """
    Appends a new order outcome (returned=0 or returned=1)
    to user_history.csv so future training runs include it.
    """
    df = pd.DataFrame([order_data])
    header = not os.path.exists(USER_HISTORY_PATH)
    df.to_csv(USER_HISTORY_PATH, mode="a", header=header, index=False)
    print("Logged order outcome to user_history.csv.")

if __name__ == "__main__":
    # Test a sample prediction
    sample_product = {
        "customer_age": 25,
        "product_price": 49.99,
        "discount_percent": 15.0,
        "product_rating": 4.1,
        "past_purchase_count": 5,
        "past_return_rate": 0.20,  # Recalculated dynamically per user
        "session_length_minutes": 12.0,
        "num_product_views": 4,
        "device_type": "desktop",
        "product_category": "clothing",
        "shipping_method": "standard",
        "payment_method": "credit_card",
        "used_coupon": 1
    }

    probability = predict_return_probability(sample_product)
    print(f"Return Probability: {probability * 100:.2f}%")