"""Order business logic: shipping, tax, estimated delivery, wilaya validation."""

from datetime import datetime, timedelta

from django.utils import timezone

# Wilaya codes and names (Algeria) - exact list from spec
WILAYAS = {
    "01": "Adrar",
    "02": "Chlef",
    "03": "Laghouat",
    "04": "Oum El Bouaghi",
    "05": "Batna",
    "06": "Béjaïa",
    "07": "Biskra",
    "08": "Béchar",
    "09": "Blida",
    "10": "Bouira",
    "11": "Tamanrasset",
    "12": "Tébessa",
    "13": "Tlemcen",
    "14": "Tiaret",
    "15": "Tizi Ouzou",
    "16": "Alger",
    "17": "Djelfa",
    "18": "Jijel",
    "19": "Sétif",
    "20": "Saïda",
    "21": "Skikda",
    "22": "Sidi Bel Abbès",
    "23": "Annaba",
    "24": "Guelma",
    "25": "Constantine",
    "26": "Médéa",
    "27": "Mostaganem",
    "28": "M'Sila",
    "29": "Mascara",
    "30": "Ouargla",
    "31": "Oran",
    "32": "El Bayadh",
    "33": "Illizi",
    "34": "Bordj Bou Arréridj",
    "35": "Boumerdès",
    "36": "El Tarf",
    "37": "Tindouf",
    "38": "Tissemsilt",
    "39": "El Oued",
    "40": "Khenchela",
    "41": "Souk Ahras",
    "42": "Tipaza",
    "43": "Mila",
    "44": "Aïn Defla",
    "45": "Naâma",
    "46": "Aïn Témouchent",
    "47": "Ghardaïa",
    "48": "Relizane",
    "49": "El M'Ghair",
    "50": "El Meniaa",
    "51": "Ouled Djellal",
    "52": "Bordj Badji Mokhtar",
    "53": "Béni Abbès",
    "54": "Timimoun",
    "55": "Touggourt",
    "56": "Djanet",
    "57": "In Salah",
    "58": "In Guezzam",
}

SHIPPING_COSTS = {
    "standard": 0,
    "express": 500,
    "sameday": 1000,
}

TAX_RATE = 0.05  # 5%


def is_valid_wilaya(wilaya):
    """Validate wilaya - accepts code (01-58) or name (Adrar, etc.)."""
    if not wilaya:
        return False
    wilaya_str = str(wilaya).strip()
    # by code
    if wilaya_str in WILAYAS:
        return True
    # by name (case-insensitive)
    wilaya_lower = wilaya_str.lower()
    return any(
        wilaya_lower == name.lower() or wilaya_str == code
        for code, name in WILAYAS.items()
    )


def get_shipping_cost(method):
    return SHIPPING_COSTS.get(method, 0)


def calculate_tax(subtotal):
    """5% of subtotal, rounded to integer."""
    return round(float(subtotal) * TAX_RATE)


def add_business_days(dt, days):
    """Add business days (excluding weekends)."""
    result = dt
    added = 0
    while added < days:
        result += timedelta(days=1)
        if result.weekday() < 5:  # Mon=0, Fri=4
            added += 1
    return result


def get_estimated_delivery(shipping_method):
    """Compute estimated delivery datetime."""
    now = timezone.now()
    if shipping_method == "standard":
        return add_business_days(now, 5)
    elif shipping_method == "express":
        return add_business_days(now, 2)
    elif shipping_method == "sameday":
        if now.hour < 12:
            return now.replace(hour=23, minute=59, second=59, microsecond=0)
        return add_business_days(now.replace(hour=0, minute=0, second=0, microsecond=0), 1)
    return add_business_days(now, 5)
