import pandas as pd

def maxplate():
    # Load the CSV file into a DataFrame
    file_path = r"pipeline\test_interpolated.csv"  # Replace with your file path
    df = pd.read_csv(file_path)

    # Convert 'license_number_score' to numeric in case of invalid data
    df['license_number_score'] = pd.to_numeric(df['license_number_score'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    # Group by 'car_id' and find the row with the maximum 'license_number_score' for each group
    max_score_per_car = df.loc[df.groupby('car_id')['license_number_score'].idxmax()]

    # Select relevant columns (license number, timestamp, and car_id)
    result = max_score_per_car[['car_id', 'license_number', 'timestamp']]

    # Display the result
    print(result)

    # Save the result to a new CSV file
    output_file_path = r"pipeline\license_and_timestamp.csv"  # Specify your output file path
    result.to_csv(output_file_path, index=False)
