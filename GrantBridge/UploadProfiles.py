import pandas as pd
from pymongo import MongoClient

# MongoDB connection

connection_string = 'mongodb+srv://allenfoss42:Drpepper5463@hackathongrants.ul3qy.mongodb.net/hackathon_db?retryWrites=true&w=majority'
client = MongoClient(connection_string)
db = client['hackathon_db']

# Load the Excel file
excel_file = "/Users/allenfoss/Desktop/Hackathon Excel.xlsx"

# Load the profile sheet into a pandas DataFrame
profile_df = pd.read_excel(excel_file, sheet_name='Profile')

# Convert Timestamp columns to string/ISO format and handle NaT values
def convert_to_json_serializable(df):
    return df.applymap(lambda x: x.isoformat() if isinstance(x, pd.Timestamp) else None if pd.isna(x) else x)

profile_df = convert_to_json_serializable(profile_df)

# Convert DataFrame to JSON
profile_json = profile_df.to_dict(orient='records')

# Insert JSON data into MongoDB
db['profiles'].insert_many(profile_json)

print("Profile data conversion and MongoDB insertion completed!")
