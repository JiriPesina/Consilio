import requests

def verify_redmine_credentials(api_key: str, username: str, password: str) -> requests.Response:
    """
    Ověří uživatele v Redmine na adrese /my/account.json
    - Použijeme HTTP Basic Auth (username/password).
    - Jako parametr do query stringu dáme 'key' = api_key.
    - Vrátíme requests.Response, aby si volající zkontroloval status_code a data.
    """
    url = "https://projects.olc.cz/my/account.json"
    try:
        # Redmine očekává klíč jako query-parametr 'key', nikoli 'api_key'.
        # Autentizace se provádí Basic Auth: (username, password).
        response = requests.get(
            url,
            params={'key': api_key},
            auth=(username, password),
            timeout=10
        )
        return response
    except requests.RequestException as e:
        # Pro RequestException (timeout, spojení, DNS atp.) můžeme rovnou předat dál.
        raise