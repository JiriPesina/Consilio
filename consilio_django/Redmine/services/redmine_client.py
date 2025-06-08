import requests

class RedmineClient:
    """
    Jednoduchý HTTP klient pro volání Redmine JSON API přes requests.Session,
    aby se sdílely hlavičky a TCP keep-alive.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-Redmine-API-Key": self.api_key,
            "Content-Type": "application/json",
        })

    def fetch(self, endpoint: str):
        """
        GET https://projects.olc.cz/{endpoint}.json
        Vrátí data z klíče endpoint (např. 'users', 'projects', 'issues') nebo raw JSON.
        """
        url = f"https://projects.olc.cz/{endpoint}.json"
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data.get(endpoint, data)
