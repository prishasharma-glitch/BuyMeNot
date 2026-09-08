from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
from typing import List
from specifications import extract_specifications
import json
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

USE_MOCK_AI = True


class Aspect(BaseModel):
    aspect: str
    sentiment: str
    reason: str
    evidence: List[str]


class ReviewAnalysis(BaseModel):
    aspects: List[Aspect]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Buy Me Not backend is running!"
    }


def validate_evidence(analysis, reviews):

    original_review_text = " ".join(
        review.get("text", "")
        for review in reviews
        if review.get("text")
    ).lower()

    for aspect in analysis.get("aspects", []):
        valid_evidence = []
        for evidence in aspect.get("evidence", []):
            evidence_clean = evidence.strip().lower()
            if evidence_clean and evidence_clean in original_review_text:
                valid_evidence.append(evidence)
        aspect["evidence"] = valid_evidence

    return analysis


@app.post("/analyze")
def analyze_product(product: dict):

    raw_specifications = product.get("specifications", "")
    structured_specifications = extract_specifications(raw_specifications)
    product["structured_specifications"] = structured_specifications

    reviews = product.get("reviews", [])

    if USE_MOCK_AI:
        analysis = {
            "aspects": [
                {
                    "aspect": "Price / Value",
                    "sentiment": "positive",
                    "reason": "Sample development result.",
                    "evidence": ["Sample evidence for development."]
                },
                {
                    "aspect": "Build Quality",
                    "sentiment": "neutral",
                    "reason": "Sample development result.",
                    "evidence": ["Sample evidence for development."]
                }
            ]
        }

        return {
            "product": {
                "name": product.get("name"),
                "asin": product.get("asin")
            },
            "review_count": len(reviews),
            "analysis": analysis,
            "structured_specifications": structured_specifications,
            "mode": "mock"
        }

    review_text = "\n\n".join(
        f"REVIEW {index + 1}:\n{review.get('text', '')}"
        for index, review in enumerate(reviews)
        if review.get("text")
    )

    prompt = f"""
You are an e-commerce review analysis assistant.

Analyze ONLY the customer reviews provided below.

Identify the important product aspects mentioned across the reviews
and map them to one of these standardized categories:

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
combine them into a single result and use "neutral" as the sentiment.

For every aspect provide:

1. sentiment
2. a short reason explaining the sentiment
3. up to 3 evidence snippets from the actual reviews

IMPORTANT RULES FOR EVIDENCE:

- Evidence MUST come directly from the supplied reviews.
- Do NOT invent evidence.
- Do NOT write a general statement and present it as evidence.
- Keep evidence short and relevant to the aspect.
- Evidence should preserve the original wording from the review as much
  as possible.
- If there is no useful evidence for an aspect, return an empty list.
- Evidence must not contain information that is not present in the reviews.

Sentiment must be one of:
- positive
- negative
- neutral

Customer reviews:

{review_text}
"""

    response_schema = {
        "type": "object",
        "properties": {
            "aspects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "aspect": {"type": "string"},
                        "sentiment": {
                            "type": "string",
                            "enum": ["positive", "negative", "neutral"]
                        },
                        "reason": {"type": "string"},
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["aspect", "sentiment", "reason", "evidence"]
                }
            }
        },
        "required": ["aspects"]
    }

    try:
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": response_schema
            }
        )

        analysis = json.loads(interaction.output_text)
        analysis = validate_evidence(analysis, reviews)

    except Exception as e:
        error_message = str(e)
        if "429" in error_message or "quota" in error_message.lower():
            return {"error": "Gemini API rate limit reached. Please try again in a moment."}
        return {"error": "Gemini API error. Please try again."}

    return {
        "product": {
            "name": product.get("name"),
            "asin": product.get("asin")
        },
        "review_count": len(reviews),
        "analysis": analysis,
        "structured_specifications": structured_specifications,
        "mode": "gemini"
    }