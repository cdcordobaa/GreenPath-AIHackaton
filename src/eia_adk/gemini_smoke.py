import os
from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY not set. Put it in .env")

    client = genai.Client(api_key=api_key)
    model = "gemini-1.5-flash"
    prompt = "Say hello from Gemini in one short sentence."

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    print(resp.text.strip())


if __name__ == "__main__":
    main()
