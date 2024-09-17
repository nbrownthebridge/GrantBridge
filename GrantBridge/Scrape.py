
import requests
from pymongo import MongoClient

def fetch_grant_details(opp_id):
    """Fetch detailed information about a grant using its oppId."""
    url = "https://apply07.grants.gov/grantsws/rest/opportunity/details"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        "oppId": opp_id
    }

    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        return response.json()  # Return the detailed grant information
    except requests.RequestException as e:
        print(f"Failed to fetch grant details for oppId {opp_id}: {e}")
        return None

def fetch_and_update_grants():
    """Fetch the list of grants, then fetch and update detailed information for each."""
    print("Starting fetch_and_update_grants...")
    url = "https://apply07.grants.gov/grantsws/rest/opportunities/search/"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "fundingInstruments": "G",
        "sortBy": "openDate|desc",
        "rows": 1,  # Fetch a number of records
        "oppStatuses": "forecasted|posted"
    }

    try:
        print("Sending POST request for search results...")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        print("Received response with status code:", response.status_code)
        
        # Debug: Print the full response for inspection
        print("Response Headers:", response.headers)
        print("Response Content:", response.text)

        grants_data = response.json().get('oppHits', [])
        print(f"Fetched {len(grants_data)} grants.")

        # Connect to MongoDB
        connection_string = 'mongodb+srv://allenfoss42:Drpepper5463@hackathongrants.ul3qy.mongodb.net/hackathon_db?retryWrites=true&w=majority'
        client = MongoClient(connection_string)
        db = client['hackathon_db']
        collection = db['Gov Active Grants']  # Updated to the single collection

        print("Updating database...")
        for grant in grants_data:
            opp_id = grant.get('id')
            if opp_id:
                # Fetch detailed information about the grant
                grant_details = fetch_grant_details(opp_id)
                
                # Combine the search results and detailed information into one object
                combined_data = grant.copy()  # Start with the initial grant data
                if grant_details:
                    combined_data.update(grant_details)  # Merge detailed data into the initial data
                
                # Insert or update the combined grant information in MongoDB
                collection.update(
                    {"id": opp_id},
                    {"$set": combined_data},
                    upsert=True
                )
        
        print("Database updated successfully.")
    except requests.RequestException as e:
        print(f"Failed to fetch data from grants.gov: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function
fetch_and_update_grants()

