import csv

import requests

# Define the MGNIFY API endpoint for retrieving runss
# api_url = "https://www.ebi.ac.uk/metagenomics/api/latest/"
api_url = "https://www.ebi.ac.uk/metagenomics/api/v1/"


# Function to fetch runs accession identifiers from MGNIFY
def fetch_runs_accession_ids(outfile):
    runs_accession_ids = []
    endpoint = f"{api_url}runs"
    params = {
        'page_size': 100,  # Number of results per page (handle pagination)
        'page': 1  # Start with the first page
    }
    mypage_count = 0
    while True:
        response = requests.get(endpoint, params = params)
        data = response.json()
        local_runs_accession_ids =[]

        # Check if there are any results
        if 'data' in data:
            for runs in data['data']:
                # Check if the runs has an accession identifier
                if 'accession' in runs['attributes']:
                    runs_accession_ids.append(runs['attributes']['accession'])
                    local_runs_accession_ids.append(runs['attributes']['accession'])

        # Pagination logic
        if 'links' in data and 'next' in data['links'] and data['links']['next']:
            endpoint = data['links']['next']
        else:
            break

        print(".", end="")
        mypage_count += 1
        for accession_id in local_runs_accession_ids:
            outfile.write(f"{accession_id}\n")
        # break
    return runs_accession_ids


# Fetch all runs accession identifiers
outfilename ="runs_accession_ids.txt"
print(f"Writing to {outfilename}")
outfile = open(outfilename, 'w')

runs_accession_ids = fetch_runs_accession_ids(outfile)
print(f"Found {len(runs_accession_ids)} runs accession identifiers")


#print(runs_accession_ids)
outfile.close()