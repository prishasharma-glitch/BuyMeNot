# ============================================================
# BUY ME NOT - SPECIFICATION EXTRACTOR
# ============================================================


def clean_text(value):
    """
    Clean common whitespace and invisible characters.
    """

    if value is None:
        return ""

    return (
        value
        .replace("\u200e", "")
        .replace("\u200f", "")
        .replace("\u202a", "")
        .replace("\u202b", "")
        .replace("\u202c", "")
        .replace("\u202d", "")
        .replace("\u202e", "")
        .replace("\u2060", "")
        .replace("\u00a0", " ")
        .strip()
    )


def normalize_key(key):
    """
    Convert a specification name into
    the format used by user requirements.
    """

    key = clean_text(key).lower()

    key = (
        key
        .replace("-", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )

    return key


def convert_value(value):
    """
    Convert common specification values
    into useful Python data types.
    """

    value = clean_text(value)

    if not value:
        return value

    # Boolean values

    if value.lower() in {
        "yes",
        "true",
        "available",
        "compatible"
    }:
        return True

    if value.lower() in {
        "no",
        "false",
        "not available",
        "incompatible"
    }:
        return False

    # Numeric values

    try:
        return float(value)

    except ValueError:
        pass

    # Normal text

    return value


def extract_specifications(raw_text):

    specifications = {}

    if not raw_text:
        return specifications

    lines = raw_text.splitlines()

    for line in lines:

        line = clean_text(line)

        if not line:
            continue

        # Amazon commonly uses:
        #
        # Language : English
        # Item Weight : 300 g
        # Dimensions : 21 x 14 x 3 cm

        if ":" in line:

            parts = line.split(":", 1)

            key = parts[0].strip()
            value = parts[1].strip()

        # Some product data may use tabs.

        elif "\t" in line:

            parts = line.split("\t", 1)

            key = parts[0].strip()
            value = parts[1].strip()

        else:
            continue

        key = normalize_key(key)
        value = clean_text(value)

        if not key or not value:
            continue

        # ----------------------------------------------------
        # SPECIALIZED SPECIFICATIONS
        # ----------------------------------------------------

        if key == "material":

            specifications["material"] = value

        elif key == "capacity":

            value_lower = value.lower()

            if "liter" in value_lower:

                number = (
                    value_lower
                    .replace("liters", "")
                    .replace("liter", "")
                    .strip()
                )

                try:
                    specifications["capacity_liters"] = float(number)

                except ValueError:
                    specifications["capacity"] = value

            else:
                specifications["capacity"] = value

        elif key == "product_dimensions":

            specifications["dimensions"] = value

        elif key == "item_weight":

            value_lower = value.lower()

            if "kilogram" in value_lower:

                number = (
                    value_lower
                    .replace("kilograms", "")
                    .replace("kilogram", "")
                    .strip()
                )

                try:
                    specifications["weight_kg"] = float(number)

                except ValueError:
                    specifications["weight"] = value

            elif "kg" in value_lower:

                number = (
                    value_lower
                    .replace("kg", "")
                    .strip()
                )

                try:
                    specifications["weight_kg"] = float(number)

                except ValueError:
                    specifications["weight"] = value

            else:
                specifications["weight"] = value

        elif key == "is_oven_safe":

            value_lower = value.lower()

            if value_lower == "yes":

                specifications["oven_safe"] = True

            elif value_lower == "no":

                specifications["oven_safe"] = False

            else:

                specifications["oven_safe"] = value

        elif key == "coating_description":

            specifications["coating"] = value

        elif "induction" in key:

            specifications["induction_compatible"] = (
                value.lower() == "yes"
            )

        elif (
            "gas" in key
            and "stove" in key
        ):

            specifications["gas_stove_compatible"] = (
                value.lower() == "yes"
            )

        # ----------------------------------------------------
        # GENERIC SPECIFICATION
        # ----------------------------------------------------

        else:

            specifications[key] = convert_value(value)

    return specifications