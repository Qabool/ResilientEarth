"""On-demand web search using Serper. Results are leads, not verified official warnings."""
import requests

URL = "https://google.serper.dev/search"


def search(query, api_key, num=8, timeout=20):
    if not api_key:
        raise ValueError("SERPER_API_KEY is not configured in Streamlit Secrets.")
    response = requests.post(
        URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": num, "gl": "pk", "hl": "en"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("organic", [])
