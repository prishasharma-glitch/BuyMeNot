# ============================================================
# BUY ME NOT COMPATIBILITY ENGINE
# ============================================================


def check_compatibility(
    specifications,
    requirements,
    product_name=""
):
    """
    Compare user requirements against structured product specifications
    and the product title/name.

    Returns:
        compatible: True / False
        violations: list of failed requirements
        checked_requirements: list of requirements checked
    """

    violations = []
    checked_requirements = []
    product_name_lower = (product_name or "").strip().lower()

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
        # 1. Requirement does not exist in product specs table
        #    Check if it is present in the product name/title
        # ----------------------------------------------------

        if requirement_key not in specifications:

            required_str = str(required_value).strip().lower()
            found_in_title = False

            # Check if required value (e.g., "blue") is in the title
            if required_str and required_str not in ["true", "yes"]:
                if required_str in product_name_lower:
                    found_in_title = True
            # Or if requirement key itself (e.g., "blue") is in the title
            elif requirement_key in product_name_lower or requirement.strip().lower() in product_name_lower:
                found_in_title = True

            if found_in_title:
                # Satisfied via product name
                continue

            violations.append({
                "requirement":
                    requirement_key,

                "required":
                    required_value,

                "actual":
                    None,

                "reason":
                    "The required specification was not found in the "
                    "specifications table or the product title."
            })

            continue

        actual_value = specifications[
            requirement_key
        ]

        # ----------------------------------------------------
        # 2. Boolean requirements
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
                        "The product does not satisfy the required condition."
                })

        # ----------------------------------------------------
        # 3. Numeric requirements
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
                            "The product specification is below the required value."
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
                        "The product specification could not be compared numerically."
                })

        # ----------------------------------------------------
        # 4. Text requirements (supports partial & title matches)
        # ----------------------------------------------------

        else:

            required_text = str(
                required_value
            ).strip().lower()

            actual_text = str(
                actual_value
            ).strip().lower()

            # Pass if exact match, if required text is inside the spec (e.g. "Shock Blue"),
            # or if it appears in the product title.
            if required_text != actual_text and required_text not in actual_text:
                if required_text not in product_name_lower:
                    violations.append({
                        "requirement":
                            requirement_key,

                        "required":
                            required_value,

                        "actual":
                            actual_value,

                        "reason":
                            "The product specification does not match the requirement."
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