import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from xgboost import XGBClassifier


# ============================================================
# LOAD DATASET
# ============================================================

print("\n========== LOADING DATASET ==========")

train_path = "dataset/train.csv"
test_path = "dataset/test.csv"

train_df = pd.read_csv(train_path)
test_df = pd.read_csv(test_path)

print("Train shape:", train_df.shape)
print("Test shape:", test_df.shape)


# ============================================================
# BASIC DATASET INFORMATION
# ============================================================

print("\n========== DATASET INFORMATION ==========")

print("\nColumns:")
print(train_df.columns.tolist())

print("\nData types:")
print(train_df.dtypes)

print("\nMissing values:")
print(train_df.isnull().sum())

print("\nDuplicate rows:")
print(train_df.duplicated().sum())


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print("\n========== TARGET DISTRIBUTION ==========")

print(train_df["returned"].value_counts())
print(train_df["returned"].value_counts(normalize=True))


# ============================================================
# CATEGORICAL FEATURES
# ============================================================

categorical_columns = [
    "device_type",
    "product_category",
    "shipping_method",
    "payment_method"
]

print("\n========== CATEGORICAL FEATURES ==========")

for column in categorical_columns:
    print(f"\n{column}:")
    print(train_df[column].value_counts())


# ============================================================
# NUMERICAL FEATURES
# ============================================================

numerical_columns = [
    "customer_age",
    "product_price",
    "discount_percent",
    "product_rating",
    "past_purchase_count",
    "past_return_rate",
    "delivery_delay_days",
    "session_length_minutes",
    "num_product_views",
    "used_coupon"
]

print("\n========== NUMERICAL FEATURES ==========")

print(
    train_df[numerical_columns].describe().T
)


# ============================================================
# CHECK SUSPICIOUS VALUES
# ============================================================

print("\n========== SUSPICIOUS VALUES ==========")

print(
    "Negative product prices:",
    (train_df["product_price"] < 0).sum()
)

print(
    "Invalid discount percentages:",
    (
        (train_df["discount_percent"] < 0)
        | (train_df["discount_percent"] > 100)
    ).sum()
)

print(
    "Invalid product ratings:",
    (
        (train_df["product_rating"] < 1)
        | (train_df["product_rating"] > 5)
    ).sum()
)

print(
    "Invalid past return rates:",
    (
        (train_df["past_return_rate"] < 0)
        | (train_df["past_return_rate"] > 1)
    ).sum()
)

print(
    "Negative delivery delays:",
    (train_df["delivery_delay_days"] < 0).sum()
)

print(
    "Negative session lengths:",
    (train_df["session_length_minutes"] < 0).sum()
)

print(
    "Negative product views:",
    (train_df["num_product_views"] < 0).sum()
)


# ============================================================
# CLEAN INVALID VALUES
# ============================================================

print("\n========== CLEANING DATA ==========")

train_df.loc[
    train_df["product_price"] < 0,
    "product_price"
] = np.nan

train_df.loc[
    (train_df["discount_percent"] < 0)
    | (train_df["discount_percent"] > 100),
    "discount_percent"
] = np.nan

train_df.loc[
    (train_df["product_rating"] < 1)
    | (train_df["product_rating"] > 5),
    "product_rating"
] = np.nan

train_df.loc[
    (train_df["past_return_rate"] < 0)
    | (train_df["past_return_rate"] > 1),
    "past_return_rate"
] = np.nan

train_df.loc[
    train_df["session_length_minutes"] < 0,
    "session_length_minutes"
] = np.nan

train_df.loc[
    train_df["num_product_views"] < 0,
    "num_product_views"
] = np.nan


print("Invalid values converted to missing values.")


# ============================================================
# FEATURE SELECTION
# ============================================================

feature_columns = [
    "customer_age",
    "product_price",
    "discount_percent",
    "product_rating",
    "past_purchase_count",
    "past_return_rate",
    "session_length_minutes",
    "num_product_views",
    "device_type",
    "product_category",
    "shipping_method",
    "payment_method",
    "used_coupon"
]

X = train_df[feature_columns]
y = train_df["returned"]


# ============================================================
# TRAIN / VALIDATION SPLIT
# ============================================================

print("\n========== TRAIN / VALIDATION SPLIT ==========")

X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training samples:", len(X_train))
print("Validation samples:", len(X_valid))

print(
    "\nTraining target distribution:"
)
print(y_train.value_counts(normalize=True))

print(
    "\nValidation target distribution:"
)
print(y_valid.value_counts(normalize=True))


# ============================================================
# PREPROCESSING
# ============================================================

numerical_features = [
    "customer_age",
    "product_price",
    "discount_percent",
    "product_rating",
    "past_purchase_count",
    "past_return_rate",
    "session_length_minutes",
    "num_product_views",
    "used_coupon"
]

categorical_features = [
    "device_type",
    "product_category",
    "shipping_method",
    "payment_method"
]


numerical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        )
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore"
            )
        )
    ]
)


preprocessor = ColumnTransformer(
    transformers=[
        (
            "numerical",
            numerical_pipeline,
            numerical_features
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        )
    ]
)


# ============================================================
# FIT PREPROCESSOR
# ============================================================

print("\n========== PREPROCESSING ==========")

X_train_processed = preprocessor.fit_transform(
    X_train
)

X_valid_processed = preprocessor.transform(
    X_valid
)

print(
    "Processed training shape:",
    X_train_processed.shape
)

print(
    "Processed validation shape:",
    X_valid_processed.shape
)


# ============================================================
# MODEL EVALUATION FUNCTION
# ============================================================

def evaluate_model(
    model_name,
    model,
    X_train_data,
    X_valid_data
):

    print(
        f"\n========== {model_name.upper()} =========="
    )

    model.fit(
        X_train_data,
        y_train
    )

    predictions = model.predict(
        X_valid_data
    )

    accuracy = accuracy_score(
        y_valid,
        predictions
    )

    precision = precision_score(
        y_valid,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_valid,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_valid,
        predictions,
        zero_division=0
    )

    print(
        f"Accuracy : {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall   : {recall:.4f}"
    )

    print(
        f"F1 Score : {f1:.4f}"
    )

    return {
        "model": model_name,
        "model_object": model,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


# ============================================================
# LOGISTIC REGRESSION
# ============================================================

logistic_model = LogisticRegression(
    max_iter=1000,
    random_state=42
)

logistic_result = evaluate_model(
    "Logistic Regression",
    logistic_model,
    X_train_processed,
    X_valid_processed
)


# ============================================================
# RANDOM FOREST
# ============================================================

random_forest_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

random_forest_result = evaluate_model(
    "Random Forest",
    random_forest_model,
    X_train_processed,
    X_valid_processed
)


# ============================================================
# XGBOOST
# ============================================================

xgb_model = XGBClassifier(
    n_estimators=150,
    max_depth=8,
    learning_rate=0.1,
    random_state=42,
    eval_metric="logloss"
)

xgb_result = evaluate_model(
    "XGBoost",
    xgb_model,
    X_train_processed,
    X_valid_processed
)


# ============================================================
# MODEL COMPARISON
# ============================================================

results = [
    logistic_result,
    random_forest_result,
    xgb_result
]

comparison_df = pd.DataFrame(
    [
        {
            "Model": result["model"],
            "Accuracy": result["accuracy"],
            "Precision": result["precision"],
            "Recall": result["recall"],
            "F1": result["f1"]
        }
        for result in results
    ]
)

print("\n========== MODEL COMPARISON ==========")

print(
    comparison_df.to_string(
        index=False
    )
)


# ============================================================
# SELECT BEST MODEL BY F1
# ============================================================

best_result = max(
    results,
    key=lambda result: result["f1"]
)

best_model = best_result["model_object"]

print(
    "\n========== BEST MODEL =========="
)

print(
    "Best model:",
    best_result["model"]
)

print(
    f"Best F1 score: {best_result['f1']:.4f}"
)


# ============================================================
# REAL VALIDATION SAMPLE
# ============================================================

print(
    "\n========== REAL DATASET SAMPLE =========="
)

sample_index = X_valid.index[0]

sample = X_valid.loc[
    [sample_index]
]

actual_result = y_valid.loc[
    sample_index
]

print("\nSample features:")

print(
    sample.to_string(
        index=False
    )
)

print(
    "\nActual return label:",
    actual_result
)


# ============================================================
# PREPROCESS REAL SAMPLE
# ============================================================

sample_processed = preprocessor.transform(
    sample
)


# ============================================================
# TEST SAMPLE WITH ALL MODELS
# ============================================================

print(
    "\n========== SAMPLE MODEL COMPARISON =========="
)


for result in results:

    model_name = result["model"]
    model = result["model_object"]

    prediction = model.predict(
        sample_processed
    )[0]

    probability = model.predict_proba(
        sample_processed
    )[0][1]

    print(
        f"\n{model_name}"
    )

    print(
        "Prediction:",
        prediction
    )

    print(
        f"Return probability: {probability:.4f}"
    )

    if prediction == 1:
        print(
            "Result: HIGHER RETURN RISK"
        )
    else:
        print(
            "Result: LOWER RETURN RISK"
        )


# ============================================================
# CHECK WHETHER MODELS AGREE
# ============================================================

print(
    "\n========== SAMPLE CONSENSUS =========="
)

sample_predictions = []

for result in results:

    prediction = result["model_object"].predict(
        sample_processed
    )[0]

    sample_predictions.append(
        prediction
    )


if len(set(sample_predictions)) == 1:

    print(
        "All three models agree on the prediction."
    )

else:

    print(
        "The models disagree on the prediction."
    )


# ============================================================
# FEATURE IMPORTANCE FOR XGBOOST
# ============================================================

print(
    "\n========== XGBOOST FEATURE IMPORTANCE =========="
)

feature_names = (
    preprocessor
    .get_feature_names_out()
)

importance_values = (
    xgb_model.feature_importances_
)

feature_importance_df = pd.DataFrame(
    {
        "feature": feature_names,
        "importance": importance_values
    }
)

feature_importance_df = (
    feature_importance_df
    .sort_values(
        "importance",
        ascending=False
    )
)

print(
    feature_importance_df.head(15).to_string(
        index=False
    )
)


# ============================================================
# SAVE BEST MODEL
# ============================================================

print(
    "\n========== SAVING BEST MODEL =========="
)

joblib.dump(
    best_model,
    "buy_me_not_xgboost.pkl"
)

joblib.dump(
    preprocessor,
    "buy_me_not_preprocessor.pkl"
)

print(
    "Best model saved as:",
    "buy_me_not_xgboost.pkl"
)

print(
    "Preprocessor saved as:",
    "buy_me_not_preprocessor.pkl"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print(
    "\n========== FINAL SUMMARY =========="
)

print(
    f"Selected model: {best_result['model']}"
)

print(
    f"Accuracy : {best_result['accuracy']:.4f}"
)

print(
    f"Precision: {best_result['precision']:.4f}"
)

print(
    f"Recall   : {best_result['recall']:.4f}"
)

print(
    f"F1 Score : {best_result['f1']:.4f}"
)

print(
    "\nModel comparison and sample testing completed."
)