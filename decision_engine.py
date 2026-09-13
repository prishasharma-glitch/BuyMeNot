# ============================================================
# BUY ME NOT DECISION ENGINE
# ============================================================


# ============================================================
# REVIEW SENTIMENT SCORE
# ============================================================

def calculate_review_score(aspects):
    """
    Calculate a review sentiment score.

    Positive aspect  = +1
    Neutral aspect   =  0
    Negative aspect  = -1

    The final score is normalized
    between 0 and 1.

    0.0 = completely negative
    0.5 = neutral / mixed
    1.0 = completely positive
    """

    if not aspects:

        return 0.5

    score = 0

    for aspect in aspects:

        sentiment = (
            aspect.get("sentiment", "")
            .lower()
        )

        if sentiment == "positive":

            score += 1

        elif sentiment == "negative":

            score -= 1

    max_score = len(aspects)

    normalized_score = (
        (score + max_score)
        / (2 * max_score)
    )

    return normalized_score


# ============================================================
# RETURN-RISK SCORE
# ============================================================

def calculate_return_risk_score(
    return_probability
):
    """
    Convert return probability into a
    positive suitability score.

    Lower return probability = higher score.

    Example:

    return_probability = 0.20
    return_risk_score = 0.80
    """

    if return_probability is None:

        return None

    return 1 - return_probability


# ============================================================
# FINAL DECISION
# ============================================================

def make_buy_me_not_decision(
    compatibility,
    aspects=None,
    return_probability=None
):
    """
    Generate the final Buy Me Not decision.

    Compatibility is treated as a HARD GATE.

    If compatibility fails:
        DON'T BUY

    If compatibility passes:

        Gemini + ML available
            -> HYBRID mode

        Gemini available only
            -> GEMINI_ONLY mode

        ML available only
            -> ML_ONLY mode

        Neither available
            -> No reliable decision

    Hybrid score:

        0.5 * Review Score
        +
        0.5 * Return-Risk Score

    Decision thresholds:

        >= 0.65 -> BUY
        >= 0.40 -> MAYBE
        <  0.40 -> DON'T BUY
    """

    # ========================================================
    # HARD COMPATIBILITY GATE
    # ========================================================

    if compatibility is False:

        return {

            "decision":
                "DON'T BUY",

            "score":
                0.0,

            "reason":
                "The product does not satisfy "
                "a required compatibility condition.",

            "mode":
                "COMPATIBILITY_FAIL"
        }

    # ========================================================
    # DETERMINE AVAILABLE SIGNALS
    # ========================================================

    gemini_available = (
        aspects is not None
    )

    ml_available = (
        return_probability is not None
    )

    # ========================================================
    # CALCULATE GEMINI REVIEW SCORE
    # ========================================================

    review_score = None

    if gemini_available:

        review_score = calculate_review_score(
            aspects
        )

    # ========================================================
    # CALCULATE ML RETURN-RISK SCORE
    # ========================================================

    return_risk_score = None

    if ml_available:

        return_risk_score = (
            calculate_return_risk_score(
                return_probability
            )
        )

    # ========================================================
    # DETERMINE DECISION MODE
    # ========================================================

    if (
        gemini_available
        and ml_available
    ):

        mode = "HYBRID"

    elif gemini_available:

        mode = "GEMINI_ONLY"

    elif ml_available:

        mode = "ML_ONLY"

    else:

        return {

            "decision":
                "UNAVAILABLE",

            "score":
                None,

            "reason":
                "Neither review analysis nor "
                "return-risk prediction is available.",

            "mode":
                "NO_SIGNAL"
        }

    # ========================================================
    # HYBRID MODE
    # ========================================================

    if mode == "HYBRID":

        final_score = (

            0.5 * review_score

            +

            0.5 * return_risk_score
        )

    # ========================================================
    # GEMINI-ONLY MODE
    # ========================================================

    elif mode == "GEMINI_ONLY":

        final_score = review_score

    # ========================================================
    # ML-ONLY MODE
    # ========================================================

    else:

        final_score = return_risk_score

    # ========================================================
    # FINAL DECISION
    # ========================================================

    if final_score >= 0.65:

        decision = "BUY"

    elif final_score >= 0.40:

        decision = "MAYBE"

    else:

        decision = "DON'T BUY"

    # ========================================================
    # EXPLANATION
    # ========================================================

    if mode == "HYBRID":

        if decision == "BUY":

            reason = (
                "The product has generally favorable "
                "review sentiment and relatively lower "
                "return risk."
            )

        elif decision == "MAYBE":

            reason = (
                "The product has mixed suitability "
                "signals. Review sentiment and return "
                "risk do not strongly support or reject "
                "the purchase."
            )

        else:

            reason = (
                "The product has unfavorable suitability "
                "signals based on review sentiment and "
                "return risk."
            )

    elif mode == "GEMINI_ONLY":

        if decision == "BUY":

            reason = (
                "The product has generally favorable "
                "customer review sentiment."
            )

        elif decision == "MAYBE":

            reason = (
                "The product has mixed customer review "
                "sentiment."
            )

        else:

            reason = (
                "The product has unfavorable customer "
                "review sentiment."
            )

    else:

        if decision == "BUY":

            reason = (
                "The product has a relatively lower "
                "model-estimated return risk."
            )

        elif decision == "MAYBE":

            reason = (
                "The product has an intermediate "
                "model-estimated return risk."
            )

        else:

            reason = (
                "The product has a relatively higher "
                "model-estimated return risk."
            )

    # ========================================================
    # RESPONSE
    # ========================================================

    result = {

        "decision":
            decision,

        "score":
            round(
                final_score,
                4
            ),

        "reason":
            reason,

        "mode":
            mode
    }

    # ========================================================
    # ADD GEMINI SCORE
    # ========================================================

    if review_score is not None:

        result["review_score"] = round(
            review_score,
            4
        )

    # ========================================================
    # ADD ML SCORE
    # ========================================================

    if return_risk_score is not None:

        result["return_risk_score"] = round(
            return_risk_score,
            4
        )

    # ========================================================
    # ADD RETURN PROBABILITY
    # ========================================================

    if return_probability is not None:

        result["return_probability"] = round(
            return_probability,
            4
        )

    # ========================================================
    # ADD HYBRID SCORE
    # ========================================================

    if mode == "HYBRID":

        result["hybrid_score"] = round(
            final_score,
            4
        )

    return result