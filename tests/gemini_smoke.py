import os
from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_GENAI_API_KEY not set. Put it in .env")

    client = genai.Client(api_key=api_key)
    model = os.getenv("EIA_MODEL_PRIMARY", "gemini-2.5-flash")
    prompt = "Say hello from Gemini in one short sentence."

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    print(resp.text.strip())


if __name__ == "__main__":
    main()
