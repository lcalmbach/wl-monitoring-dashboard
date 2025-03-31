from pathlib import Path
import pandas as pd
import urllib.parse
from datetime import datetime

datapath = Path("./data")
identifier = "100064"
csv_data_file = datapath / f"{identifier}.csv"
parquet_data_file = datapath / f"{identifier}.parquet"
parquet_final_data_file = datapath / f"{identifier}_final.parquet"
csv_station_file = datapath / f"{identifier}_stations.csv"
parquet_station_file = datapath / f"{identifier}_stations.parquet"

base_url = "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100164/exports/csv"
params = {
    "lang": "de",
    "timezone": "Europe/Zurich",
    "use_labels": "false",
    "delimiter": ";",
    "select": "timestamp,stationnr,stationname,value,lat,lon",
    "where": "timestamp >= '1976-01-01' and timestamp <'1977-01-01'",
}
station_fields = ["stationnr", "stationname", "lat", "lon"]
value_fields = ["timestamp", "stationnr", "value"]
query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
full_url = f"{base_url}?{query_string}"


def get_data():
    """
    Fetches and processes data for a range of years, saving the results to files.

    This function retrieves data from a remote source for each year starting from 1976 
    up to the current year. The data is fetched using HTTP requests, processed, and 
    saved in both Parquet and CSV formats.

    Steps:
    1. Iterates through each year in the range.
    2. Constructs a query string with date filters for the specific year.
    3. Fetches the data from the remote source using the constructed URL.
    4. Processes the data by converting timestamps and formatting station numbers.
    5. Concatenates data from all years into a single DataFrame.
    6. Extracts unique station information and saves it separately.
    7. Writes the processed data and station information to Parquet and CSV files.

    Outputs:
    - A Parquet file containing the processed data for all years.
    - A CSV file containing the processed data for all years.
    - A Parquet file containing unique station information.
    - A CSV file containing unique station information.

    Note:
    - The function assumes the existence of certain global variables such as `params`, 
      `base_url`, `station_fields`, `value_fields`, `parquet_data_file`, 
      `csv_data_file`, `parquet_station_file`, and `csv_station_file`.
    - The function uses pandas for data manipulation and urllib for URL encoding.

    Raises:
    - Any exceptions related to HTTP requests or file I/O operations.
    - ValueErrors if the data processing steps encounter unexpected formats.
    """
    data = []
    years = range(1976, datetime.now().year + 1)
    for year in years:
        print(f"reading year {year}")
        params["where"] = f"timestamp >= '{year}-01-01' and timestamp <'{year+1}-01-01'"
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        full_url = f"{base_url}?{query_string}"
        df = pd.read_csv(full_url, sep=";", low_memory=False)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["stationnr"] = df["stationnr"].astype(str)
        data.append(df)
    df_all_years = pd.concat(data, ignore_index=True)
    df_stations = df_all_years[station_fields].drop_duplicates()
    print(f"writing data files: {parquet_data_file.name}")
    df_all_years[value_fields].to_parquet(parquet_data_file)
    df_all_years[value_fields].to_csv(csv_data_file, sep=";")

    print(f"writing station files: {parquet_station_file.name}")
    df_stations.to_csv(csv_station_file, sep=";")
    df_stations.to_parquet(parquet_station_file)


def fix_station_codes():
    """
    Fixes the station codes in the dataset by ensuring they are 10 characters long,
    padded with zeros on the left if necessary. The function processes two datasets:
    station data and yearly data, and updates them accordingly.

    Steps:
    1. Reads the station data from a Parquet file.
    2. Ensures the "stationnr" column in the station data is 10 characters long by
       padding with zeros on the left.
    3. Removes duplicate rows in the station data based on the "stationnr" column,
       keeping the last occurrence.
    4. Saves the updated station data back to the Parquet file.
    5. Reads the yearly data from a Parquet file.
    6. Ensures the "stationnr" column in the yearly data is 10 characters long by
       padding with zeros on the left.
    7. Saves the updated yearly data to both a Parquet file and a CSV file.

    Note:
    - The function assumes the existence of the following global variables:
      - `parquet_station_file`: Path to the Parquet file containing station data.
      - `parquet_data_file`: Path to the Parquet file containing yearly data.
      - `csv_data_file`: Path to the CSV file for saving yearly data.
      - `value_fields`: List of column names to be saved in the yearly data files.
    - The CSV file is saved with a semicolon (;) as the delimiter.
    """
    # if the column stationnr is smalle then 10 characters, fill iwth on the left with 0
    df_stations = pd.read_parquet(parquet_station_file)
    df_stations["stationnr"] = df_stations["stationnr"].str.zfill(10)
    df_stations = df_stations.drop_duplicates(subset="stationnr", keep="last")
    df_stations.to_parquet(parquet_station_file)

    df_all_years = pd.read_parquet(parquet_data_file)
    df_all_years["stationnr"] = df_all_years["stationnr"].str.zfill(10)
    df_all_years[value_fields].to_parquet(parquet_data_file)
    df_all_years[value_fields].to_csv(csv_data_file, sep=";")


def summerize_data():
    """
    Summarizes data by calculating the average values for each station in the dataset.

    This function reads a Parquet file containing data, processes it to extract
    temporal information (year, month, date, and day of the year), and calculates
    the mean values grouped by station number, year, month, and date. The summarized
    data is then saved to a new Parquet file.

    Steps:
    1. Reads the input Parquet file into a DataFrame.
    2. Converts the 'timestamp' column to datetime and extracts year, month, date,
       and day of the year.
    3. Drops the 'timestamp' column after extracting the necessary information.
    4. Groups the data by 'stationnr', 'year', 'month', and 'date', and calculates
       the mean for each group.
    5. Saves the summarized data to a specified Parquet file.

    Note:
        - The input and output file paths are expected to be defined as global
          variables `parquet_data_file` and `parquet_final_data_file`, respectively.
        - The function uses the 'pyarrow' engine for writing the Parquet file.

    Raises:
        FileNotFoundError: If the input Parquet file does not exist.
        ValueError: If the DataFrame is empty or contains invalid data.

    """
    # calculate averave value for each station in the data dataframe
    df_all_years = pd.read_parquet(parquet_data_file)
    df_all_years["timestamp"] = pd.to_datetime(df_all_years["timestamp"])
    df_all_years["year"] = df_all_years["timestamp"].dt.year
    df_all_years["month"] = df_all_years["timestamp"].dt.month
    df_all_years["date"] = df_all_years["timestamp"].dt.date
    df_all_years["day_in_year"] = df_all_years["timestamp"].dt.dayofyear.astype(int)
    df_all_years = df_all_years.drop(columns=["timestamp"])
    df_all_years = (
        df_all_years.groupby(["stationnr", "year", "month", "date"])
        .mean()
        .reset_index()
    )
    print(f"writing final data files: {parquet_final_data_file.name}")
    df_all_years.to_parquet(parquet_final_data_file, engine="pyarrow")


get_data()
fix_station_codes()
summerize_data()
