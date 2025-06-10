"""
US State license plate definitions and utilities.
This module contains state-specific information for license plate detection.
"""

# State name variations for text cleaning
STATE_NAMES = {
    "ALABAMA": "AL",
    "ALASKA": "AK", 
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY"
}

# Common prefixes/suffixes to filter out
COMMON_WORDS = [
    "STATE", "OF", "THE", "SUNSHINE", "GOLDEN", "EMPIRE", "GARDEN", 
    "VOLUNTEER", "PEACH", "KEYSTONE", "FIRST", "LAST", "FRONTIER", 
    "GRAND", "CANYON", "TREASURE", "ALOHA", "GREAT", "LAKES"
]

# Dealership and frame text to filter out
DEALER_FRAME_WORDS = [
    # Dealership names and types
    "DEALER", "DEALERSHIP", "AUTO", "GROUP", "MOTORS", "AUTOMOTIVE", "SALES", "SERVICE",
    "TOYOTA", "HONDA", "FORD", "CHEVROLET", "CHEVY", "NISSAN", "HYUNDAI", "KIA", 
    "SUBARU", "DODGE", "JEEP", "LEXUS", "AUDI", "BMW", "MERCEDES", "VOLKSWAGEN",
    "VOLVO", "MAZDA", "ACURA", "INFINITI", "CADILLAC", "LINCOLN", "BUICK", "GMC",
    "CHRYSLER", "FIAT", "TESLA", "PORSCHE", "FERRARI", "LAMBORGHINI", "MASERATI",
    
    # Services and departments
    "PARTS", "COLLISION", "REPAIR", "CENTER", "FINANCING", "LEASE", "LEASING",
    "RENTAL", "USED", "NEW", "CERTIFIED", "PRE-OWNED", "WARRANTY", "MAINTENANCE",
    
    # Educational institutions
    "UNIVERSITY", "COLLEGE", "SCHOOL", "ALUMNI", "PROUD", "SUPPORT", "OWNER",
    "GRADUATE", "STUDENT", "EDUCATION", "ACADEMY", "INSTITUTE",
    
    # Contact and web information
    "VISIT", "CALL", "WWW", "HTTP", "HTTPS", ".COM", ".NET", ".ORG", ".EDU",
    "PHONE", "EMAIL", "CONTACT", "INFO", "WEBSITE", "ONLINE",
    
    # Location and directions
    "DRIVE", "DRIVING", "ROAD", "STREET", "AVE", "AVENUE", "BLVD", "BOULEVARD",
    "HWY", "HIGHWAY", "ROUTE", "EXIT", "NORTH", "SOUTH", "EAST", "WEST",
    
    # Frame and plate related
    "TAG", "FRAME", "HOLDER", "LICENSE", "PLATE", "REGISTRATION", "TAGS",
    "BRACKET", "MOUNT", "COVER", "PROTECTOR",
    
    # Generic promotional text
    "PROUD", "OWNER", "MEMBER", "CUSTOMER", "SATISFACTION", "QUALITY", "BEST",
    "AWARD", "WINNING", "FAMILY", "FRIENDLY", "COMMUNITY", "LOCAL", "HOMETOWN"
]

# State slogans and mottos to filter out
STATE_SLOGANS = [
    # Common state slogans that appear on plates
    "LONE STAR STATE", "GOLDEN STATE", "SUNSHINE STATE", "EMPIRE STATE",
    "GARDEN STATE", "KEYSTONE STATE", "VOLUNTEER STATE", "PEACH STATE",
    "FIRST STATE", "LAST FRONTIER", "GRAND CANYON STATE", "TREASURE STATE",
    "ALOHA STATE", "GREAT LAKES STATE", "LAND OF LINCOLN", "SHOW ME STATE",
    "BLUEGRASS STATE", "PELICAN STATE", "PINE TREE STATE", "OLD LINE STATE",
    "BAY STATE", "WOLVERINE STATE", "NORTH STAR STATE", "MAGNOLIA STATE",
    "BIG SKY COUNTRY", "CORNHUSKER STATE", "SILVER STATE", "LIVE FREE OR DIE",
    "OCEAN STATE", "PALMETTO STATE", "MOUNT RUSHMORE STATE", "VOLUNTEER STATE",
    "BEEHIVE STATE", "GREEN MOUNTAIN STATE", "OLD DOMINION", "EVERGREEN STATE",
    "MOUNTAIN STATE", "BADGER STATE", "EQUALITY STATE"
]

# State-specific regex patterns for validation
# Format: [regex pattern, description]
STATE_PATTERNS = {
    "AL": [r"[0-9]{1,7}", "1-7 digits"],
    "AK": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "AZ": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "AR": [r"[0-9]{3}[A-Z]{3}", "3 digits followed by 3 letters"],
    "CA": [r"[0-9][A-Z]{3}[0-9]{3}|[A-Z][0-9]{7}", "1 digit, 3 letters, 3 digits OR 1 letter followed by 7 digits"],
    "CO": [r"[A-Z]{3}-[0-9]{3}", "3 letters, hyphen, 3 digits"],
    "CT": [r"[0-9]{1,3}[A-Z]{3}", "1-3 digits followed by 3 letters"],
    "DE": [r"[0-9]{1,6}", "1-6 digits"],
    "DC": [r"[A-Z]{2}[0-9]{4}", "2 letters followed by 4 digits"],
    "FL": [r"[A-Z]{3}[0-9]{3}|[A-Z]{3}-[0-9]{3}", "3 letters followed by 3 digits"],
    "GA": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "HI": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "ID": [r"[A-Z][0-9]{6}|[0-9][A-Z]{6}", "1 letter followed by 6 digits OR 1 digit followed by 6 letters"],
    "IL": [r"[A-Z]{1,3}[0-9]{1,4}", "1-3 letters followed by 1-4 digits"],
    "IN": [r"[A-Z]{3}[0-9]{3}|[0-9]{3}[A-Z]{3}", "3 letters followed by 3 digits OR 3 digits followed by 3 letters"],
    "IA": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "KS": [r"[0-9]{3}[A-Z]{3}", "3 digits followed by 3 letters"],
    "KY": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "LA": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "ME": [r"[0-9]{4}[A-Z]{2}", "4 digits followed by 2 letters"],
    "MD": [r"[A-Z]{1}[0-9]{2}[A-Z]{3}|[0-9]{7}", "1 letter, 2 digits, 3 letters OR 7 digits"],
    "MA": [r"[0-9]{1,6}|[A-Z]{1,6}", "1-6 digits OR 1-6 letters"],
    "MI": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "MN": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "MS": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "MO": [r"[A-Z]{2}[0-9]{1}[A-Z]{1}[0-9]{3}", "2 letters, 1 digit, 1 letter, 3 digits"],
    "MT": [r"[0-9]{1,7}|[A-Z]{1,7}", "1-7 digits OR 1-7 letters"],
    "NE": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "NV": [r"[0-9]{3}[A-Z]{3}", "3 digits followed by 3 letters"],
    "NH": [r"[0-9]{1,7}", "1-7 digits"],
    "NJ": [r"[A-Z]{1}[0-9]{2}[A-Z]{3}", "1 letter, 2 digits, 3 letters"],
    "NM": [r"[A-Z]{3}[0-9]{3,4}", "3 letters followed by 3-4 digits"],
    "NY": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "NC": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "ND": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "OH": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "OK": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "OR": [r"[0-9]{1,6}", "1-6 digits"],
    "PA": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "RI": [r"[0-9]{1,6}", "1-6 digits"],
    "SC": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "SD": [r"[0-9]{1,6}[A-Z]{1,2}", "1-6 digits followed by 1-2 letters"],
    "TN": [r"[A-Z]{1,3}[0-9]{1,4}", "1-3 letters followed by 1-4 digits"],
    "TX": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "UT": [r"[A-Z]{1,3}[0-9]{2,5}", "1-3 letters followed by 2-5 digits"],
    "VT": [r"[A-Z]{3}[0-9]{3}", "3 letters followed by 3 digits"],
    "VA": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "WA": [r"[A-Z]{3}[0-9]{4}", "3 letters followed by 4 digits"],
    "WV": [r"[0-9]{1,6}", "1-6 digits"],
    "WI": [r"[A-Z]{3}[0-9]{3,4}", "3 letters followed by 3-4 digits"],
    "WY": [r"[0-9]{1,6}", "1-6 digits"]
}

# Special plate indicators
SPECIAL_PLATES = {
    "DEALER": ["DLR", "DEALER", "DLRS"],
    "TEMPORARY": ["TEMP", "TEMPORARY", "TMP"],
    "COMMERCIAL": ["CMV", "COM", "COMM", "COMMERCIAL"],
    "FARM": ["FARM", "FRM"],
    "MOTORCYCLE": ["MC", "MOTO", "MOTORCYCLE"],
    "DISABLED": ["DV", "DISABLED", "HANDICAP"],
    "VETERAN": ["VET", "VETERAN"],
    "PERSONALIZED": ["VANITY", "PERSONAL", "CUSTOM"]
}

def get_state_from_text(text):
    """
    Attempt to identify state from text.
    
    Args:
        text: Text that might contain a state name
        
    Returns:
        Two-letter state code or None if no state identified
    """
    text = text.upper()
    
    # Check for exact state names
    for state_name, state_code in STATE_NAMES.items():
        if state_name in text:
            return state_code
            
    # Check for state codes
    for state_code in STATE_NAMES.values():
        if f" {state_code} " in f" {text} ":  # Add spaces to avoid partial matches
            return state_code
            
    return None

def get_state_pattern(state_code):
    """
    Get the regex pattern for a specific state.
    
    Args:
        state_code: Two-letter state code
        
    Returns:
        Regex pattern string or None if state not found
    """
    if state_code in STATE_PATTERNS:
        return STATE_PATTERNS[state_code][0]
    return None