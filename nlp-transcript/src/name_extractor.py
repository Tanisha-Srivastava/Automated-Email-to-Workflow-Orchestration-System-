import re

def extract_names(lines):
    names = set()

    for line in lines:
        match = re.match(r"^([A-Z][a-zA-Z]+):", line)
        if match:
            names.add(match.group(1))

    return sorted(names)
