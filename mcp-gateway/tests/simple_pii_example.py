import requests

# Your OAuth Access Token
access_token = "gho_16C7e42F292c6912E7710c838347Ae178B4a"
# The API URL you want to access (e.g., to get user information)
api_url = "https://api.github.com/user"
email_address = "user@example.com"
credit_card = "4580253103936543"
non_valid_credit_card = "3456393013520854"
# Set up the headers with the access token
headers = {
    "Authorization": f"token {access_token}",
    "Accept": "application/vnd.github.v3+json",
}
# Make the GET request to the specified API URL
response = requests.get(api_url, headers=headers)
# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    user_data = response.json()
    print("User data retrieved successfully:")
    print(user_data)
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
