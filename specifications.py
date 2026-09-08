def extract_specifications(raw_text):

    specifications = {}

    lines = raw_text.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Amazon specifications are usually separated by tabs
        parts = line.split("\t")

        if len(parts) < 2:
            continue

        key = parts[0].strip().lower()
        value = parts[1].strip()

        # --------------------------------
        # MATERIAL
        # --------------------------------

        if key == "material":
            specifications["material"] = value

        # --------------------------------
        # CAPACITY
        # --------------------------------

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
                    pass

        # --------------------------------
        # DIMENSIONS
        # --------------------------------

        elif key == "product dimensions":
            specifications["dimensions"] = value

        # --------------------------------
        # WEIGHT
        # --------------------------------

        elif key == "item weight":
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
                    pass

        # --------------------------------
        # COATING
        # --------------------------------

        elif key == "coating description":
            specifications["coating"] = value

    return specifications