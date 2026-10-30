import re

TIME_UNITS = {
    "s":1,
    "m":60,
    "h":3600,
    "d":86400
}

def parse_delay(value: str) -> int :

    value = value.lower().replace(" ","")

    #plain number to seconds
    if value.isdigit():
        return int(value)

    pattern = r"(\d+)([smhd])"

    matches = re.findall(pattern , value)

    if not matches:
        raise ValueError("Invalid time format.")

    total_seconds= 0 

    for amount , unit in matches:
        total_seconds += int(amount) *TIME_UNITS[unit]


    return total_seconds