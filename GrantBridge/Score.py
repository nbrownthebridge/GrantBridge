from pymongo import MongoClient

# Connect to MongoDB
connection_string = 'mongodb+srv://allenfoss42:Drpepper5463@hackathongrants.ul3qy.mongodb.net/hackathon_db?retryWrites=true&w=majority'
client = MongoClient(connection_string)
db = client['hackathon_db']
grants_collection = db['Gov Active Grants']  # Collection with grant details
profiles_collection = db['profiles']  # Collection with user profiles
grant_scores_collection = db['GrantScores']  # Collection to store profile-grant scores

def calculate_score(user_profile, grant):
    score = 0

    # Helper function for rough matching across all fields
    def rough_match(text, keywords):
        if not keywords or not isinstance(text, str):
            return False
        text_lower = text.lower()
        keywords_lower = [keyword.lower() for keyword in keywords]
        return any(keyword in text_lower for keyword in keywords_lower)

    # Extract profile data with default values
    program_focus_keywords = user_profile.get('Program Focus', '').split()
    organization_description_keywords = user_profile.get('Organization Description', '').split()
    grant_type_keywords = [user_profile.get('Grant Type', '').lower()]
    award_floor = user_profile.get('AWARD Floor', 0)
    award_ceiling = user_profile.get('AWARD Ceiling', float('inf'))
    geographic_area_city = user_profile.get('Geographic Area City', '').lower()
    geographic_area_state = user_profile.get('Geographic Area State', '').lower()

    # Check for rough matches in the grant fields
    fields_to_check = [
        'title', 'description', 'type', 'geographic_area', 'agency', 'agencyCode', 'cfdaList'
    ]
    
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

    # Additional checks for award amounts
    if (grant.get('award_floor', 0) >= award_floor and
        grant.get('award_ceiling', float('inf')) <= award_ceiling):
        score += 7

    return score

def update_scores():
    # Retrieve all profiles
    profiles = profiles_collection.find()
    # Retrieve all grants
    grants = grants_collection.find()

    # For each profile, calculate scores for all grants
    for profile in profiles:
        profile_id = profile['_id']
        profile_organization = profile.get('Organization', 'Unknown Organization')
        for grant in grants:
            grant_id = grant.get('id', 'Unknown Grant ID')
            grant_title = grant.get('opportunityTitle', 'Unknown Grant Title')
            score = calculate_score(profile, grant)
            grant_scores_collection.update_one(
                {'profile_id': profile_id, 'grant_id': grant_id},
                {'$set': {
                    'score': score,
                    'grant_title': grant_title,
                    'profile_title': profile_organization
                }},
                upsert=True  # Create a new document if it does not exist
            )

    print("Scores updated successfully in GrantScores collection.")

update_scores()
