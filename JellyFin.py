import requests

class JellyFin:
    server_url = ""
    auth_token = ""

    @staticmethod
    def load_credentials():
        """
        Loads the server URL and auth token from the 'CREDENTIALS.txt' file.
        The file should have the server URL on the first line and the auth token on the second line.
        """
        try:
            with open("CREDENTIALS.txt", "r") as file:
                lines = file.readlines()
                if len(lines) < 2:
                    raise ValueError("CREDENTIALS.txt must contain at least two lines: server URL and auth token.")
                JellyFin.server_url = lines[0].strip()
                JellyFin.auth_token = lines[1].strip()
        except FileNotFoundError:
            print("CREDENTIALS.txt file not found.")
        except Exception as e:
            print(f"An error occurred while loading credentials: {e}")

    @staticmethod
    def Refresh():
        """
        Sends a POST request to the Jellyfin server to refresh all libraries.

        :return: None
        """
        if not JellyFin.server_url or not JellyFin.auth_token:
            print("Credentials not loaded. Please ensure CREDENTIALS.txt is present and properly formatted.")
            return

        api_endpoint = f"{JellyFin.server_url}/Library/Refresh"

        # Headers required for the API request
        headers = {
            "X-Emby-Authorization": f'MediaBrowser Client="Jellyfin", Device="PythonScript", DeviceId="12345", Version="10.9.9", Token="{JellyFin.auth_token}"',
            "Content-Type": "application/json"
        }

        # Send POST request to refresh libraries
        response = requests.post(api_endpoint, headers=headers)

        # Check response status code
        if response.status_code == 204:
            print("Library refresh triggered successfully!")
        elif response.status_code == 401:
            print("Unauthorized. Check your API token.")
        else:
            print(f"Failed to refresh libraries. Status code: {response.status_code}")


# Load credentials from CREDENTIALS.txt and trigger library refresh
JellyFin.load_credentials()
JellyFin.Refresh()
