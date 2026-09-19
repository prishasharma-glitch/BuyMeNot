from decision_engine import make_buy_me_not_decision
from compatibility_engine import check_compatibility

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
from typing import List

from specifications import extract_specifications
from user_profile import UserProfile

import json
import os
import joblib
import pandas as pd

from pathlib import Path


# ============================================================
# ENVIRONMENT / CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. "
        "Please make sure the .env file exists in the BuyMeNot folder."
    )

client = genai.Client(
    api_key=api_key
)

# Real Gemini review analysis is enabled.
USE_MOCK_AI = False


# ============================================================
# LOAD ML MODEL
# ============================================================

ML_MODEL_PATH = (
    BASE_DIR
    / "ML"
    / "buy_me_not_xgboost.pkl"
)

ML_PREPROCESSOR_PATH = (
    BASE_DIR
    / "ML"
    / "buy_me_not_preprocessor.pkl"
)

return_risk_model = joblib.load(
    ML_MODEL_PATH
)

return_risk_preprocessor = joblib.load(
    ML_PREPROCESSOR_PATH
)

print(
    "Return-risk ML model loaded successfully."
)

print(
    "Return-risk preprocessor loaded successfully."
)


# ============================================================
# PYDANTIC MODELS
# ============================================================

class Aspect(BaseModel):
    aspect: str
    sentiment: str
    reason: str
    evidence: List[str]


class ReviewAnalysis(BaseModel):
    aspects: List[Aspect]


class ReturnRiskRequest(BaseModel):

    # User / session information
    user_profile: UserProfile

    # Current product information
    # These values may be unavailable on some product pages.
    product_price: float | None = None
    discount_percent: float | None = None
    product_rating: float | None = None
    product_category: str | None = None


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Buy Me Not backend is running!"
    }


# ============================================================
# RETURN-RISK PREDICTION
# ============================================================

@app.post("/predict-return-risk")
def predict_return_risk(
    request: ReturnRiskRequest
):

    # --------------------------------------------------------
    # Convert UserProfile to dictionary
    # --------------------------------------------------------

    user_data = request.user_profile.model_dump()

    # --------------------------------------------------------
    # Combine user + product information
    # --------------------------------------------------------

    model_input = {

        "customer_age":
            user_data["customer_age"],

        "product_price":
            request.product_price,

        "discount_percent":
            request.discount_percent,

        "product_rating":
            request.product_rating,

        "past_purchase_count":
            user_data["past_purchase_count"],

        "past_return_rate":
            user_data["past_return_rate"],

        "session_length_minutes":
            user_data["session_length_minutes"],

        "num_product_views":
            user_data["num_product_views"],

        "device_type":
            user_data["device_type"],

        "product_category":
            request.product_category,

        "shipping_method":
            user_data["shipping_method"],

        "payment_method":
            user_data["payment_method"],

        "used_coupon":
            user_data["used_coupon"]
    }

    # --------------------------------------------------------
    # Feature order
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    try:

        sample = pd.DataFrame(
            [model_input],
            columns=feature_columns
        )

    except Exception:

        return {
            "error": "Invalid input data."
        }

    # --------------------------------------------------------
    # Preprocess
    # --------------------------------------------------------

    try:

        sample_processed = (
            return_risk_preprocessor.transform(
                sample
            )
        )

    except Exception as e:

        print(
            "Preprocessing error:",
            str(e)
        )

        return {
            "error":
                "Unable to preprocess the supplied data."
        }

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    try:

        prediction = (
            return_risk_model
            .predict(sample_processed)[0]
        )

        probability = (
            return_risk_model
            .predict_proba(
                sample_processed
            )[0][1]
        )

    except Exception as e:

        print(
            "Prediction error:",
            str(e)
        )

        return {
            "error":
                "Unable to generate return-risk prediction."
        }

    # --------------------------------------------------------
    # Human-readable risk
    # --------------------------------------------------------

    if prediction == 1:

        risk = "HIGHER RETURN RISK"

    else:

        risk = "LOWER RETURN RISK"

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "return_prediction":
            int(prediction),

        "return_probability":
            round(
                float(probability),
                4
            ),

        "risk":
            risk,

        "model":
            "XGBoost"
    }


# ============================================================
# EVIDENCE VALIDATION
# ============================================================

def validate_evidence(
    analysis,
    reviews
):

    original_review_text = " ".join(

        review.get("text", "")

        for review in reviews

        if review.get("text")
    ).lower()

    for aspect in analysis.get(
        "aspects",
        []
    ):

        valid_evidence = []

        for evidence in aspect.get(
            "evidence",
            []
        ):

            evidence_clean = (
                evidence
                .strip()
                .lower()
            )

            if (
                evidence_clean
                and evidence_clean
                in original_review_text
            ):

                valid_evidence.append(
                    evidence
                )

        aspect["evidence"] = (
            valid_evidence
        )

    return analysis


# ============================================================
# DECISION ENGINE HELPER
# ============================================================

def generate_decision(
    product,
    analysis,
    compatibility_result
):
    """
    Generate the final Buy Me Not decision.

    Compatibility is treated as a hard constraint.

    Return risk is calculated using the trained
    XGBoost model.

    Review sentiment comes from the review analysis.

    Missing product values are passed to the trained
    preprocessing pipeline as missing values so that
    its existing imputation strategy can handle them.

    Missing user profile information is never
    fabricated.
    """

    # --------------------------------------------------------
    # Check compatibility first
    # --------------------------------------------------------

    if compatibility_result is not None:

        if not compatibility_result.get(
            "compatible",
            True
        ):

            # ------------------------------------------------
            # Hard compatibility failure
            # ------------------------------------------------

            return {
                "decision": "DON'T BUY",
                "score": 0.0,
                "reason":
                    "The product does not satisfy "
                    "one or more required conditions.",
                "compatibility":
                    compatibility_result
            }

    # --------------------------------------------------------
    # Check for user profile
    # --------------------------------------------------------

    user_profile_data = product.get(
        "user_profile"
    )

    if not user_profile_data:

        return None

    # --------------------------------------------------------
    # Validate UserProfile
    # --------------------------------------------------------

    try:

        user_profile = UserProfile(
            **user_profile_data
        )

    except Exception as e:

        print(
            "User profile validation error:",
            str(e)
        )

        return None

    # --------------------------------------------------------
    # Prepare ML features
    # --------------------------------------------------------

    user_data = user_profile.model_dump()

    # --------------------------------------------------------
    # Missing numeric product values
    #
    # Do NOT invent values such as 0.
    #
    # NaN allows the trained numerical imputer
    # to replace missing values using the statistics
    # learned during training.
    # --------------------------------------------------------

    product_price = product.get(
        "product_price"
    )

    discount_percent = product.get(
        "discount_percent"
    )

    product_rating = product.get(
        "product_rating"
    )

    if product_price is None:
        product_price = float("nan")

    if discount_percent is None:
        discount_percent = float("nan")

    if product_rating is None:
        product_rating = float("nan")

    # --------------------------------------------------------
    # Missing categorical value
    # --------------------------------------------------------

    product_category = product.get(
        "product_category"
    )

    if not product_category:
        product_category = "unknown"

    # --------------------------------------------------------
    # Build model input
    # --------------------------------------------------------

    model_input = {

        "customer_age":
            user_data["customer_age"],

        "product_price":
            product_price,

        "discount_percent":
            discount_percent,

        "product_rating":
            product_rating,

        "past_purchase_count":
            user_data["past_purchase_count"],

        "past_return_rate":
            user_data["past_return_rate"],

        "session_length_minutes":
            user_data["session_length_minutes"],

        "num_product_views":
            user_data["num_product_views"],

        "device_type":
            user_data["device_type"],

        "product_category":
            product_category,

        "shipping_method":
            user_data["shipping_method"],

        "payment_method":
            user_data["payment_method"],

        "used_coupon":
            user_data["used_coupon"]
    }

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

    # --------------------------------------------------------
    # Create DataFrame + preprocess
    # --------------------------------------------------------

    try:

        sample = pd.DataFrame(
            [model_input],
            columns=feature_columns
        )

        sample_processed = (
            return_risk_preprocessor.transform(
                sample
            )
        )

    except Exception as e:

        print(
            "Decision engine preprocessing error:",
            str(e)
        )

        return None

    # --------------------------------------------------------
    # Predict return probability
    # --------------------------------------------------------

    try:

        return_probability = float(
            return_risk_model
            .predict_proba(
                sample_processed
            )[0][1]
        )

    except Exception as e:

        print(
            "Decision engine prediction error:",
            str(e)
        )

        return None

    # --------------------------------------------------------
    # Extract aspects
    # --------------------------------------------------------

    aspects = analysis.get(
        "aspects",
        []
    )

    # --------------------------------------------------------
    # Final Buy Me Not decision
    # --------------------------------------------------------

    decision = make_buy_me_not_decision(

        compatibility=True,

        aspects=aspects,

        return_probability=
            return_probability
    )

    # --------------------------------------------------------
    # Add compatibility information
    # --------------------------------------------------------

    if compatibility_result is not None:

        decision["compatibility"] = (
            compatibility_result
        )

    # --------------------------------------------------------
    # Add return-risk information
    # --------------------------------------------------------

    decision["return_probability"] = round(
        return_probability,
        4
    )

    decision["return_risk"] = (
        "HIGHER RETURN RISK"
        if return_probability >= 0.5
        else
        "LOWER RETURN RISK"
    )

    decision["model"] = "XGBoost"

    return decision


# ============================================================
# COMPATIBILITY HELPER
# ============================================================

def generate_compatibility(
    product,
    structured_specifications
):
    """
    Extract user requirements from the product
    request and compare them against the
    structured product specifications and product name.
    """

    requirements = product.get(
        "user_requirements"
    )

    # --------------------------------------------------------
    # No requirements supplied
    # --------------------------------------------------------

    if not requirements:

        return {
            "compatible": True,
            "violations": [],
            "checked_requirements": []
        }

    # --------------------------------------------------------
    # Extract product name / title
    # --------------------------------------------------------

    product_name = (
        product.get("name")
        or product.get("title")
        or ""
    )

    # --------------------------------------------------------
    # Run generic compatibility engine
    # --------------------------------------------------------

    try:

        result = check_compatibility(

            specifications=
                structured_specifications,

            requirements=
                requirements,

            product_name=
                product_name
        )

        return result

    except Exception as e:

        print(
            "Compatibility error:",
            str(e)
        )

        return {
            "compatible": False,

            "violations": [
                {
                    "requirement":
                        "compatibility_check",

                    "required":
                        True,

                    "actual":
                        None,

                    "reason":
                        "Compatibility could not "
                        "be verified."
                }
            ],

            "checked_requirements": []
        }


# ============================================================
# PRODUCT ANALYSIS
# ============================================================

@app.post("/analyze")
def analyze_product(
    product: dict
):

    # --------------------------------------------------------
    # Extract structured specifications
    # --------------------------------------------------------

    raw_specifications = product.get(
        "specifications",
        ""
    )

    structured_specifications = (
        extract_specifications(
            raw_specifications
        )
    )

    product[
        "structured_specifications"
    ] = structured_specifications

    # --------------------------------------------------------
    # Reviews
    # --------------------------------------------------------

    reviews = product.get(
        "reviews",
        []
    )

    # --------------------------------------------------------
    # Compatibility
    # --------------------------------------------------------

    compatibility_result = (
        generate_compatibility(
            product,
            structured_specifications
        )
    )

    # ========================================================
    # MOCK AI MODE
    # ========================================================

    if USE_MOCK_AI:

        analysis = {

            "aspects": [

                {
                    "aspect":
                        "Price / Value",

                    "sentiment":
                        "positive",

                    "reason":
                        "Sample development result.",

                    "evidence": [
                        "Sample evidence for development."
                    ]
                },

                {
                    "aspect":
                        "Build Quality",

                    "sentiment":
                        "neutral",

                    "reason":
                        "Sample development result.",

                    "evidence": [
                        "Sample evidence for development."
                    ]
                }
            ]
        }

        # ----------------------------------------------------
        # Generate decision
        # ----------------------------------------------------

        decision = generate_decision(

            product,

            analysis,

            compatibility_result
        )

        response = {

            "product": {

                "name":
                    product.get("name"),

                "asin":
                    product.get("asin")
            },

            "review_count":
                len(reviews),

            "analysis":
                analysis,

            "structured_specifications":
                structured_specifications,

            "compatibility":
                compatibility_result,

            "mode":
                "mock"
        }

        # ----------------------------------------------------
        # Add decision when available
        # ----------------------------------------------------

        if decision is not None:

            response["decision"] = decision

        return response

    # ========================================================
    # PREPARE REVIEW TEXT
    # ========================================================

    review_text = "\n\n".join(

        f"REVIEW {index + 1}:\n"
        f"{review.get('text', '')}"

        for index, review
        in enumerate(reviews)

        if review.get("text")
    )

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are an e-commerce review analysis assistant.

Analyze ONLY the customer reviews provided below.

Identify the important product aspects mentioned across
the reviews and map them to one of these standardized
categories:

- Price / Value
- Build Quality
- Performance
- Durability
- Usability
- Compatibility
- Safety
- Customer Support
- Features
- Utility

Do not create new aspect categories.
Use the closest matching category from the list above.

Each category must appear only once in the final output.

If a category has both positive and negative opinions,
combine them into a single result and use "neutral" as
the sentiment.

For every aspect provide:

1. sentiment
2. a short reason explaining the sentiment
3. up to 3 evidence snippets from the actual reviews

IMPORTANT RULES FOR EVIDENCE:

- Evidence MUST come directly from the supplied reviews.
- Do NOT invent evidence.
- Do NOT write a general statement and present it as evidence.
- Keep evidence short and relevant to the aspect.
- Evidence should preserve the original wording from the
  review as much as possible.
- If there is no useful evidence for an aspect, return an
  empty list.
- Evidence must not contain information that is not present
  in the reviews.

Sentiment must be one of:
- positive
- negative
- neutral

Customer reviews:

{review_text}
"""

    # --------------------------------------------------------
    # Gemini response schema
    # --------------------------------------------------------

    response_schema = {

        "type":
            "object",

        "properties": {

            "aspects": {

                "type":
                    "array",

                "items": {

                    "type":
                        "object",

                    "properties": {

                        "aspect": {

                            "type":
                                "string"
                        },

                        "sentiment": {

                            "type":
                                "string",

                            "enum": [
                                "positive",
                                "negative",
                                "neutral"
                            ]
                        },

                        "reason": {

                            "type":
                                "string"
                        },

                        "evidence": {

                            "type":
                                "array",

                            "items": {

                                "type":
                                    "string"
                            }
                        }
                    },

                    "required": [
                        "aspect",
                        "sentiment",
                        "reason",
                        "evidence"
                    ]
                }
            }
        },

        "required": [
            "aspects"
        ]
    }

    # --------------------------------------------------------
    # Gemini request
    # --------------------------------------------------------

    try:

        interaction = client.interactions.create(

            model="gemini-3.6-flash",

            input=prompt,

            response_format={

                "type":
                    "text",

                "mime_type":
                    "application/json",

                "schema":
                    response_schema
            }
        )

        analysis = json.loads(
            interaction.output_text
        )

        analysis = validate_evidence(
            analysis,
            reviews
        )

    except Exception as e:

        error_message = str(e)

        print(
            "Gemini API error:",
            error_message
        )

        if (
            "429" in error_message
            or "quota"
            in error_message.lower()
        ):

            return {

                "error":
                    "Gemini API rate limit reached. "
                    "Please try again in a moment."
            }

        return {

            "error":
                "Gemini API error. Please try again."
        }

    # --------------------------------------------------------
    # Buy Me Not Decision
    # --------------------------------------------------------

    decision = generate_decision(

        product,

        analysis,

        compatibility_result
    )

    # --------------------------------------------------------
    # Gemini response
    # --------------------------------------------------------

    response = {

        "product": {

            "name":
                product.get("name"),

            "asin":
                product.get("asin")
        },

        "review_count":
            len(reviews),

        "analysis":
            analysis,

        "structured_specifications":
            structured_specifications,

        "compatibility":
            compatibility_result,

        "mode":
            "gemini"
    }

    # --------------------------------------------------------
    # Add decision when available
    # --------------------------------------------------------

    if decision is not None:

        response["decision"] = decision

    return response