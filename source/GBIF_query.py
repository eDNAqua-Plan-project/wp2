import requests

# attempt at script to mine
# Define the GBIF API endpoint for datasets
datasets_url = "https://api.gbif.org/v1/dataset"


# Function to fetch all dataset keys from GBIF
def fetch_dataset_keys(api_url):
    print("Fetching dataset keys...")
    dataset_keys = []
    params = {
        'limit': 100,  # Limit the number of results (for pagination)
        'offset': 0  # Offset for pagination
    }

    count = 0
    max_count = 3
    while True:
        print(f"Fetching dataset keys for {api_url} and params={params}")
        response = requests.get(api_url, params = params)

        data = response.json()

        # Check if there are any results
        if 'results' in data:
            for dataset in data['results']:
                dataset_keys.append(dataset['key'])

        # Pagination logic
        if 'endOfRecords' in data and data['endOfRecords']:
            break
        params['offset'] += params['limit']
        count += 1
        if count > max_count:
            break

    return dataset_keys


# Function to fetch occurrence records from GBIF for a specific dataset
def fetch_occurrences(api_url, dataset_key):
    sequence_accession_ids = []
    params = {
        'datasetKey': dataset_key,
        'limit': 100,  # Limit the number of results (for pagination)
        'offset': 0  # Offset for pagination
    }
    fetch_count = 0
    while True:
        if fetch_count % 100 == 0:
            print(f"\n{fetch_count}) _", end="")
        else:
            print("_", end="")
        fetch_count = fetch_count + 1
        response = requests.get(api_url, params = params)
        data = response.json()

        # Check if there are any results
        if 'results' in data:
            for occurrence in data['results']:
                # Check if the occurrence has a sequence accession identifier
                if 'sequenceAccession' in occurrence:
                    sequence_accession_ids.append(occurrence['sequenceAccession'])
                    print(f"+{occurrence['sequenceAccession']}+")

        # Pagination logic
        if 'endOfRecords' in data and data['endOfRecords']:
            break
        params['offset'] += params['limit']

    return sequence_accession_ids


# Fetch all dataset keys
all_dataset_keys = fetch_dataset_keys(datasets_url)
print(f"Found {len(all_dataset_keys)} datasets")

all_dataset_keys = all_dataset_keys[:100]

# Define the GBIF API endpoint for occurrence search
occurrences_url = "https://api.gbif.org/v1/occurrence/search"

# Aggregate sequence accession identifiers from all datasets
all_sequence_accession_ids = []

# Fetch sequence accession identifiers for each dataset
for dataset_key in all_dataset_keys:
    print(".", end="", flush=True)
    sequence_accession_ids = fetch_occurrences(occurrences_url, dataset_key)
    all_sequence_accession_ids.extend(sequence_accession_ids)

print(f"Found {len(all_sequence_accession_ids)} sequence accession identifiers")




