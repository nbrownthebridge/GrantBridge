import datetime
from flask import Flask, jsonify, request
from scrape import ScoreAndScrape as ss
from pymongo import MongoClient

import scrape.ScoreAndScrape

app = Flask(__name__)
connection_string = 'mongodb+srv://allenfoss42:Drpepper5463@hackathongrants.ul3qy.mongodb.net/hackathon_db?retryWrites=true&w=majority'

@app.route('/saveProfile', methods=['POST'])
def save_profile():
    print(request.json)
    request_data = request.json
    profile_record = {
        'organizationName': request_data.get('organizationName', 'NotProvided'),
        'organizationDesc': request_data.get('organizationDesc', 'NotProvided'),
        'email': request_data.get('email', 'NotProvided'),
        'grantType': request_data.get('grantType', 'NotProvided'),
        'state': request_data.get('state', 'NotProvided'),
        'city': request_data.get('city', 'NotProvided'),
        'creationDate': datetime.utcnow().isoformat(),
    }
    client = MongoClient(connection_string)
    db = client['hackathon_db']
    db_insert_result = db['profiles'].insert_one(profile_record)
    return jsonify({'inserted_record_id': str(db_insert_result.inserted_id)}), 201

@app.route('/scrapeAndScore', methods=['GET'])
def scrape_and_score():
    print(request.json)
    organizationId = request.args.get('orgId')
    query = {}
    if organizationId:
        query['organizationId'] = organizationId
    client = MongoClient(connection_string)
    db = client['hackathon_db']
    existing_records = db['grants'].find(query)
    if existing_records is not None:
        return existing_records
    else:
        ss.fetch_and_update_grants_with_scores(rows=500)
    return
