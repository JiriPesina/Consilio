import requests

#modul obsahuje implementaci jednoduchého klienta pro komunikaci se serverem Redmine.
class RedmineClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-Redmine-API-Key": self.api_key,
            "Content-Type": "application/json",
        })

    #Získá data z daného endpointu Redmine
    def fetch(self, endpoint: str):
        url = f"https://projects.olc.cz/{endpoint}.json"
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data.get(endpoint, data)
