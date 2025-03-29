# Import necessary libraries
import pandas as pd 
import numpy as np
from pandas import json_normalize
from pymongo import MongoClient
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

# Stage 1: Importing Data

# Load Complaints CSV file
complaints_path = r'C:\Users\zakar\OneDrive\Desktop\DB\BI\project\data\complaints.csv'
df_complaints = pd.read_csv(complaints_path)

# Connect to MongoDB (Demographics data)
mongo_uri = "mongodb://localhost:27017/"
client = MongoClient(mongo_uri)

# Select the database and collection
db = client['demographics']
collection = db['us_demo']

# Define the fields to extract from MongoDB
projection_template = {
    "state": 1,  # Include 'state' field
    "county": 1, # Include 'county' field
    "_id": 0    # Exclude the MongoDB document ID
}

# Specify desired fields with years
fields = [
    "unemployment.employed",
    "unemployment.unemployed",
    "population_by_age.total.18_over",
    "population_by_age.total.65_over",
]

# Add fields for each year from 2011 to 2020
years = range(2011, 2021)
for field in fields:
    for year in years:
        projection_template[f"{field}.{year}"] = 1

# Query MongoDB and convert to DataFrame
cursor = collection.find({}, projection_template)
df_demo = pd.DataFrame(list(cursor))

# Flatten nested JSON structure
df_demo_flat = json_normalize(df_demo.to_dict(orient='records'))
df_demo = df_demo_flat.copy()  # Backup the cleaned DataFrame

# Stage 2: Data Transformation

# Clean and prepare the complaints dataset
def clean_complaints(df):
    # Drop unnecessary columns
    df.drop(columns=['Tags', 'ZIP code'], inplace=True)

    # Convert 'Date received' to datetime format
    df['Date received'] = pd.to_datetime(df['Date received'], errors='coerce')

    # Fill missing values with random existing values in specific columns
    columns_to_replace = ['State', 'Consumer disputed?', 'Company response to consumer',
                          'Timely response?', 'Submitted via']

    for col in columns_to_replace:
        nan_mask = df[col].isna()
        if nan_mask.any():
            random_values = np.random.choice(df[col].dropna(), nan_mask.sum())
            df.loc[nan_mask, col] = random_values

    # Filter data to include only complaints between 2011 and 2020
    df = df[(df['Date received'] >= '2011-01-01') & (df['Date received'] <= '2020-12-31')]

    # Handle missing values by filling them with unique combinations
    unique_combinations = df[['Product', 'Sub-product', 'Issue', 'Sub-issue']].drop_duplicates()

    for index, row in df[df.isna().any(axis=1)].iterrows():
        nan_columns = row.index[row.isna()]
        for col in nan_columns:
            if col in unique_combinations.columns:
                df.at[index, col] = np.random.choice(unique_combinations[col].values)

    # Convert binary columns ('Yes'/'No') to numeric (1/0)
    binary_columns = ['Timely response?', 'Consumer disputed?']
    df[binary_columns] = df[binary_columns].map({'Yes': 1, 'No': 0})

    return df

# Apply cleaning function to complaints dataset
df_complaints_clean = clean_complaints(df_complaints)

# Clean and prepare the demographics dataset
def clean_demographics(df):
    # Remove columns related to 'census'
    df = df[df.columns[~df.columns.str.contains('census', case=False)]]

    # Unpivot the DataFrame to make it long-form (melt operation)
    melted_df = pd.melt(df, id_vars=['state', 'county'], var_name='category', value_name='population')

    # Extract 'year' and clean 'category'
    melted_df[['category', 'year']] = melted_df['category'].str.rsplit('.', n=1, expand=True)

    # Standardize category names
    melted_df['category'] = melted_df['category'].replace({
        'unemployment.employed': 'unemployment_employed',
        'unemployment.unemployed': 'unemployment_unemployed'
    })

    # Convert year to integer
    melted_df['year'] = melted_df['year'].astype(int)

    # Pivot back to wide-form with each category as a column
    pivot_df = melted_df.pivot_table(index=['state', 'county', 'year'],
                                     columns='category', values='population', aggfunc='first').reset_index()

    # Handle missing values
    for col in pivot_df.select_dtypes(include='number').columns:
        pivot_df[col].fillna(pivot_df.groupby('county')[col].transform('median'), inplace=True)

    for col in pivot_df.select_dtypes(include='object').columns:
        pivot_df[col].fillna(pivot_df.groupby('county')[col].transform(lambda x: x.mode().iloc[0]), inplace=True)

    # Drop 'county' as it's not required in the final dataset
    pivot_df.drop(columns='county', inplace=True)

    return pivot_df

# Apply cleaning function to demographics dataset
df_demo_clean = clean_demographics(df_demo)

# Stage 3: Transferring Data

# PostgreSQL connection parameters
username = 'postgres'
password = 'root'
host = 'localhost'
port = '5432'
database = 'test1'

# Encode password and create the connection URI
encoded_password = quote(password)
db_uri = f'postgresql://{username}:{encoded_password}@{host}:{port}/{database}'

# Initialize the SQLAlchemy engine
engine = create_engine(db_uri, pool_size=10, max_overflow=20)

try:
    # Test database connection
    connection = engine.connect()
    print("Connected to the database.")
    connection.close()
except OperationalError as e:
    print(f"Failed to connect to the database: {e}")

# Load cleaned datasets into PostgreSQL
df_complaints_clean.to_sql('complaints', engine, index=False, if_exists='replace')
df_demo_clean.to_sql('demographics', engine, index=False, if_exists='replace')

print('Data has been successfully transferred.')
