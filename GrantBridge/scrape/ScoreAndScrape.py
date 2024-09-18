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

def rough_match(text, keywords):
    """Helper function for rough matching across all fields."""
    if not keywords or not isinstance(text, str):
        return False
    text_lower = text.lower()
    keywords_lower = [keyword.lower() for keyword in keywords]
    return any(keyword in text_lower for keyword in keywords_lower)

def calculate_score(user_profile, grant):
    score = 0

    # Extract profile data with default values
    program_focus_keywords = user_profile.get('Program Focus', '').split()
    organization_description_keywords = user_profile.get('Organization Description', '').split()
    grant_type_keywords = [user_profile.get('Grant Type', '').lower()]
    award_floor = user_profile.get('AWARD Floor', 0)
    award_ceiling = user_profile.get('AWARD Ceiling', float('inf'))
    geographic_area_city = user_profile.get('Geographic Area City', '').lower()
    geographic_area_state = user_profile.get('Geographic Area State', '').lower()

    # Fields to check for matching
    fields_to_check = ['title', 'description', 'type', 'geographic_area', 'agency']
    
    # Check each field for rough matches
    for field in fields_to_check:
        field_value = grant.get(field, '')
        if rough_match(field_value, program_focus_keywords):
            score += 10
        if rough_match(field_value, organization_description_keywords):
            score += 5
        if rough_match(field_value, grant_type_keywords):
            score += 8
        if rough_match(field_value, [geographic_area_city]):
            score += 5
        if rough_match(field_value, [geographic_area_state]):
            score += 5

    # Check award range
    if (grant.get('award_floor', 0) >= award_floor and
        grant.get('award_ceiling', float('inf')) <= award_ceiling):
        score += 7

    return score

def filter_grant_fields(grant):
    """Filter the grant data to only the fields of interest."""
    return {
        'ID': grant.get('id'),
        'Title': grant.get('title'),
        'Description': grant.get('synopsis', {}).get('synopsisDesc'),
        'Agency': grant.get('agency'),
        'Agency Code': grant.get('agencyCode'),
        'Agency Detail': grant.get('agencyDetail'),
        'Open Date': grant.get('openDate'),
        'Close Date': grant.get('closeDate'),
        'Opportunity Category': grant.get('opportunityCategory'),
        'Opportunity Category Object': grant.get('opportunityCategoryObject'),
        'Synopsis': {
            'Agency Name': grant.get('synopsis', {}).get('agencyName'),
            'Agency Phone': grant.get('synopsis', {}).get('agencyPhone'),
            'Synopsis Description': grant.get('synopsis', {}).get('synopsisDesc'),
            'Award Floor': grant.get('synopsis', {}).get('awardFloor'),
            'Award Ceiling': grant.get('synopsis', {}).get('awardCeiling')
        }
    }

def fetch_and_update_grants_with_scores(profile, rows=10):
    """Fetch multiple grants and update detailed information for each with embedded scores."""
    print(f"Starting fetch_and_update_grants_with_scores for {rows} grants...")

    # MongoDB connection
    connection_string = 'mongodb+srv://allenfoss42:Drpepper5463@hackathongrants.ul3qy.mongodb.net/hackathon_db?retryWrites=true&w=majority'
    client = MongoClient(connection_string)
    db = client['hackathon_db']
    grants_collection = db['Gov Active Grants']  # Collection for grants
    profiles_collection = db['profiles']  # Collection for user profiles

    url = "https://apply07.grants.gov/grantsws/rest/opportunities/search/"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "fundingInstruments": "G",
        "sortBy": "openDate|desc",
        "rows": rows,  # Fetch multiple records
        "oppStatuses": "forecasted|posted"
    }

    try:
        print("Sending POST request for search results...")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        print("Received response with status code:", response.status_code)
        
        grants_data = response.json().get('oppHits', [])
        print(f"Fetched {len(grants_data)} grants.")
        filtered_grants = []
        # Updating database with grant details and embedded scores
        for grant in grants_data:
            opp_id = grant.get('id')
            
            # Skip grants with no 'id' field
            if not opp_id:
                print(f"Skipping grant with missing 'id': {grant}")
                continue

            # Fetch detailed information about the grant
            grant_details = fetch_grant_details(opp_id)

            # Combine the search results and detailed information into one object
            combined_data = grant.copy()  # Start with the initial grant data
            if grant_details:
                combined_data.update(grant_details)  # Merge detailed data into the initial data

            # Filter the grant fields
            filtered_grant = filter_grant_fields(combined_data)

            # Embed scores for each profile into the grant document
            filtered_grant['scores'] = []
            score = calculate_score(profile, filtered_grant)
            # if score == 0:
            #     continue
            profile_score_data = {
                'profile_id': profile['_id'],
                'organization': profile.get('Organization', 'Unknown Organization'),
                'score': score
            }
            filtered_grant['scores'].append(profile_score_data)
            filtered_grants.append(filtered_grant)
        result = []
        for record in filtered_grants:
            record['_id'] = str(record['_id'])  # Convert ObjectId to string for JSON serialization
            record['scores'][0]['profile_id'] = str(record['scores'][0]['profile_id'])
            result.append(record)
        # print(filtered_grants)
        return filtered_grants

        #print(f"Database updated successfully with {len(grants_data)} grants and embedded scores.")
    
    except requests.RequestException as e:
        print(f"Failed to fetch data from grants.gov: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the combined function, specify the number of grants you want to fetch (e.g., 10, 20, 50)
# fetch_and_update_grants_with_scores(rows=150)
