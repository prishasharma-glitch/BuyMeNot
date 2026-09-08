import joblib
import pandas as pd


# ============================================================
# LOAD SAVED MODEL
# ============================================================

model = joblib.load("buy_me_not_xgboost.pkl")
preprocessor = joblib.load("buy_me_not_preprocessor.pkl")

print("Model loaded successfully.")
print("Preprocessor loaded successfully.")


# ============================================================
# SAMPLE INPUT
# ============================================================

sample = pd.DataFrame([
    {
        "customer_age": 25,
        "product_price": 50.0,
        "discount_percent": 20.0,
        "product_rating": 4.2,
        "past_purchase_count": 8,
        "past_return_rate": 0.15,
        "session_length_minutes": 60.0,
        "num_product_views": 10,
        "device_type": "mobile",
        "product_category": "electronics",
        "shipping_method": "standard",
        "payment_method": "credit_card",
        "used_coupon": 0
    }
])


# ============================================================
# PREPROCESS INPUT
# ============================================================

sample_processed = preprocessor.transform(sample)


# ============================================================
# MAKE PREDICTION
# ============================================================

prediction = model.predict(sample_processed)[0]

probability = model.predict_proba(sample_processed)[0][1]


# ============================================================
# DISPLAY RESULT
# ============================================================

print("\n========== PREDICTION ==========")

print("Return prediction:", int(prediction))
print("Return probability:", round(float(probability), 4))

if prediction == 1:
    print("Result: HIGHER RETURN RISK")
else:
    print("Result: LOWER RETURN RISK")