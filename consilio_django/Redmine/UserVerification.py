import requests

# Ověří přihlašovací údaje do Redmine pomocí poskytnutého API klíče, uživatelského jména a hesla.

def verify_redmine_credentials(api_key: str, username: str, password: str) -> requests.Response:
    url = "https://projects.olc.cz/my/account.json"
    try:
        # Odešle GET požadavek na Redmine REST API.
        response = requests.get(
            url,
            params={'key': api_key},
            auth=(username, password),
            timeout=10
        )
        return response
    except requests.RequestException as e:
        raise