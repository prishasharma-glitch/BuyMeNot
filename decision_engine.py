# ============================================================
# BUY ME NOT DECISION ENGINE
# ============================================================


# ============================================================
# REVIEW SENTIMENT SCORE
# ============================================================

def calculate_review_score(aspects):
    """
    Calculate a simple review sentiment score.

    Positive aspect  = +1
    Neutral aspect   =  0
    Negative aspect  = -1

    The final score is normalized to a value
    between 0 and 1.
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
    """

    return 1 - return_probability


# ============================================================
# FINAL DECISION
# ============================================================

def make_buy_me_not_decision(
    compatibility,
    aspects,
    return_probability
):
    """
    Combine compatibility, review sentiment,
    and return risk into a preliminary
    Buy Me Not decision.
    """

    # --------------------------------------------------------
    # HARD COMPATIBILITY CHECK
    # --------------------------------------------------------

    if compatibility is False:

        return {
            "decision": "DON'T BUY",
            "score": 0.0,
            "reason":
                "The product does not satisfy "
                "a required compatibility condition."
        }

    # --------------------------------------------------------
    # Review score
    # --------------------------------------------------------

    review_score = calculate_review_score(
        aspects
    )

    # --------------------------------------------------------
    # Return-risk score
    # --------------------------------------------------------

    return_risk_score = (
        calculate_return_risk_score(
            return_probability
        )
    )

    # --------------------------------------------------------
    # Combine soft signals
    # --------------------------------------------------------

    final_score = (
        0.5 * review_score
        + 0.5 * return_risk_score
    )

    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    if final_score >= 0.65:

        decision = "BUY"

    elif final_score >= 0.40:

        decision = "MAYBE"

    else:

        decision = "DON'T BUY"

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    if decision == "BUY":

        reason = (
            "The product has generally favorable "
            "review sentiment and relatively lower "
            "return risk."
        )

    elif decision == "MAYBE":

        reason = (
            "The product has mixed suitability signals. "
            "Review sentiment and return risk do not "
            "strongly support or reject the purchase."
        )

    else:

        reason = (
            "The product has unfavorable suitability "
            "signals based on review sentiment and "
            "return risk."
        )

    return {

        "decision":
            decision,

        "score":
            round(
                final_score,
                4
            ),

        "review_score":
            round(
                review_score,
                4
            ),

        "return_risk_score":
            round(
                return_risk_score,
                4
            ),

        "reason":
            reason
    }