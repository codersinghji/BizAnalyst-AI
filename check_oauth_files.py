
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

for filename in ["credentials.json", "token.json"]:

    file_path = BASE_DIR / filename

    print(f"\nChecking: {filename}")

    if not file_path.exists():
        print("STATUS: File does not exist.")
        continue

    print("File size:", file_path.stat().st_size, "bytes")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        print("STATUS: Valid JSON")
        print("JSON keys:", list(data.keys()))

        if filename == "credentials.json":
            if "installed" in data:
                print("OAuth type: Desktop application")
            elif "web" in data:
                print("OAuth type: Web application")
            else:
                print("WARNING: Expected installed or web OAuth configuration.")

    except Exception as error:
        print("STATUS: INVALID JSON")
        print("ERROR:", type(error).__name__, str(error))
