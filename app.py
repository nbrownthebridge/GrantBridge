from datetime import datetime, timezone
from flask import Flask, jsonify, request
from scrape import ScoreAndScrape as ss
from pymongo import MongoClient

app = Flask(__name__)
connection_string = 'mongodb+srv://allenfoss42:Drpepper5463@hackathongrants.ul3qy.mongodb.net/hackathon_db?retryWrites=true&w=majority'

@app.route('/saveProfile', methods=['POST'])
def save_profile():
    print(request.json)
    client = MongoClient(connection_string)
    db = client['hackathon_db']

    request_data = request.json
    profile_record = {
        'FirstName': request_data.get('fname', 'NotProvided'),
        'LastName': request_data.get('lname', 'NotProvided'),
        'Organization': request_data.get('orgname', 'NotProvided'),
        'OrganizationDescription': request_data.get('orgdesc', 'NotProvided'),
        'Email': request_data.get('email', 'NotProvided'),
        'Address1': request_data.get('streetaddress', 'NotProvided'),
        'Address2': request_data.get('address2', 'NotProvided'),
        'City': request_data.get('city', 'NotProvided'),
        'State': request_data.get('state', 'NotProvided'),
        'Zip': request_data.get('zip', 'NotProvided'),
        'Country': request_data.get('country', 'NotProvided'),
        'AwardCeiling': 100000,
        'AwardFloor': 3000,
        'CreationDate': datetime.now(timezone.utc)
    }

    db_insert_result = db['profiles'].insert_one(profile_record)
    return jsonify({'inserted_record_id': str(db_insert_result.inserted_id)}), 201

@app.route('/scrapeAndScore', methods=['GET'])
def scrape_and_score():
    organizationId = request.args.get('orgId')
    query = {}
    if organizationId:
        query['OrganizationId'] = organizationId
    print(query)
    client = MongoClient(connection_string)
    db = client['hackathon_db']
    profile = db['profiles'].find_one(query)
    result = []
    if profile is not None:
        grants = ss.fetch_and_update_grants_with_scores(profile, rows=100)
        return jsonify(grants)
    else:
        return jsonify({'Result': 'No organization with that ID exists.'})
    return
