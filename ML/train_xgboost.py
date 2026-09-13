import os
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from xgboost import XGBClassifier

# Get the directory where this script is located (D:\buyMeNot\ML)
ML_DIR = Path(__file__).resolve().parent

def train_model(
    data_path=ML_DIR / "dataset" / "train.csv", 
    user_data_path=ML_DIR / "user_history.csv"
):
    print(f"Loading base dataset from {data_path}...")
    df = pd.read_csv(data_path)

    # 1. Continuous Learning: Append new user order outcomes if they exist
    if os.path.exists(user_data_path):
        print("Found user order history. Appending new samples...")
        user_df = pd.read_csv(user_data_path)
        df = pd.concat([df, user_df], ignore_index=True)

    # 2. Clean invalid bounds
    df.loc[df["product_price"] < 0, "product_price"] = np.nan
    df.loc[(df["discount_percent"] < 0) | (df["discount_percent"] > 100), "discount_percent"] = np.nan
    df.loc[(df["product_rating"] < 1) | (df["product_rating"] > 5), "product_rating"] = np.nan
    df.loc[(df["past_return_rate"] < 0) | (df["past_return_rate"] > 1), "past_return_rate"] = np.nan
    df.loc[df["session_length_minutes"] < 0, "session_length_minutes"] = np.nan
    df.loc[df["num_product_views"] < 0, "num_product_views"] = np.nan

    feature_columns = [
        "customer_age", "product_price", "discount_percent", "product_rating",
        "past_purchase_count", "past_return_rate", "session_length_minutes",
        "num_product_views", "device_type", "product_category", "shipping_method",
        "payment_method", "used_coupon"
    ]

    X = df[feature_columns]
    y = df["returned"]

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 3. Fit Preprocessor
    numerical_features = [
        "customer_age", "product_price", "discount_percent", "product_rating",
        "past_purchase_count", "past_return_rate", "session_length_minutes",
        "num_product_views", "used_coupon"
    ]
    categorical_features = [
        "device_type", "product_category", "shipping_method", "payment_method"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("numerical", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), numerical_features),
            ("categorical", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))
            ]), categorical_features)
        ]
    )

    print("Fitting preprocessor and transforming features...")
    X_train_processed = preprocessor.fit_transform(X_train)

    # 4. Train XGBoost
    print("Training XGBoost...")
    model = XGBClassifier(
        n_estimators=150,
        max_depth=8,
        learning_rate=0.1,
        random_state=42,
        objective="binary:logistic",
        eval_metric="logloss"
    )
    model.fit(X_train_processed, y_train)

    # 5. Save directly inside D:\buyMeNot\ML\
    model_file = ML_DIR / "buy_me_not_xgboost.pkl"
    preprocessor_file = ML_DIR / "buy_me_not_preprocessor.pkl"

    joblib.dump(model, model_file)
    joblib.dump(preprocessor, preprocessor_file)
    print(f"Successfully generated:\n - {model_file}\n - {preprocessor_file}")

if __name__ == "__main__":
    train_model()