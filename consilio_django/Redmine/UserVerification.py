import requests

def verify_redmine_credentials(api_key: str, username: str, password: str) -> requests.Response:
    url = "https://projects.olc.cz/my/account.json"
    try:
        response = requests.get(
            url,
            params={'key': api_key},
            auth=(username, password),
            timeout=10
        )
        return response
    except requests.RequestException as e:
        raise