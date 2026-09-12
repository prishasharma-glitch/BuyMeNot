# ============================================================
# BUY ME NOT COMPATIBILITY ENGINE
# ============================================================


def check_compatibility(
    specifications,
    requirements
):
    """
    Compare user requirements against structured
    product specifications.

    Returns:
        compatible: True / False
        violations: list of failed requirements
        checked_requirements: list of requirements checked
    """

    violations = []
    checked_requirements = []

    if not requirements:
        return {
            "compatible": True,
            "violations": [],
            "checked_requirements": []
        }

    for requirement, required_value in requirements.items():

        requirement_key = (
            requirement
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        checked_requirements.append(
            requirement_key
        )

        # ----------------------------------------------------
        # Requirement does not exist in product specs
        # ----------------------------------------------------

        if requirement_key not in specifications:

            violations.append({
                "requirement":
                    requirement_key,

                "required":
                    required_value,

                "actual":
                    None,

                "reason":
                    "The required specification "
                    "was not found for this product."
            })

            continue

        actual_value = specifications[
            requirement_key
        ]

        # ----------------------------------------------------
        # Boolean requirements
        # ----------------------------------------------------

        if isinstance(required_value, bool):

            if actual_value != required_value:

                violations.append({
                    "requirement":
                        requirement_key,

                    "required":
                        required_value,

                    "actual":
                        actual_value,

                    "reason":
                        "The product does not satisfy "
                        "the required condition."
                })

        # ----------------------------------------------------
        # Numeric requirements
        # ----------------------------------------------------

        elif isinstance(
            required_value,
            (int, float)
        ):

            try:

                if float(actual_value) < float(
                    required_value
                ):

                    violations.append({
                        "requirement":
                            requirement_key,

                        "required":
                            required_value,

                        "actual":
                            actual_value,

                        "reason":
                            "The product specification "
                            "is below the required value."
                    })

            except (
                TypeError,
                ValueError
            ):

                violations.append({
                    "requirement":
                        requirement_key,

                    "required":
                        required_value,

                    "actual":
                        actual_value,

                    "reason":
                        "The product specification "
                        "could not be compared numerically."
                })

        # ----------------------------------------------------
        # Text requirements
        # ----------------------------------------------------

        else:

            required_text = str(
                required_value
            ).strip().lower()

            actual_text = str(
                actual_value
            ).strip().lower()

            if required_text != actual_text:

                violations.append({
                    "requirement":
                        requirement_key,

                    "required":
                        required_value,

                    "actual":
                        actual_value,

                    "reason":
                        "The product specification "
                        "does not match the requirement."
                })

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {

        "compatible":
            len(violations) == 0,

        "violations":
            violations,

        "checked_requirements":
            checked_requirements
    }