def format_address(address_data, with_country=False):
    # Safely extract fields from the dictionary with defaults
    street1 = address_data.get("Street1", "")
    street2 = address_data.get("Street2", "")
    unit_number = address_data.get("UnitNumber", "")
    city = address_data.get("City", "")
    state = address_data.get("State", "")
    postal_code = address_data.get("PostalCode", "")
    country_name = address_data.get("CountryName", "")
    # Create the address line
    line1 = f"{street1} {street2}".strip()
    if unit_number:
        line1 += f" #{unit_number}"
    # Combine the other parts of the address
    line2 = f"{city} {state} {postal_code}".strip()
    line3 = country_name if with_country else None
    # Construct the full address and remove empty lines
    address_as_list = [line1, line2, line3]
    address_as_list = [line for line in address_as_list if line]  # Remove None or empty strings
    return "\n".join(address_as_list)