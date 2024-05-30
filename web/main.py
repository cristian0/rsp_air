from flask import Flask, render_template, make_response, request
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def db_to_dataframe(db_file, table_name):
    """
    Prints all rows from a specific table.

    Args:
        db_file (str): Path to the SQLite database file.
        table_name (str): Name of the table to print.
    """

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        # Execute a query to select all rows from the specified table
        cur.execute(f"SELECT * FROM {table_name}")
        res = cur.execute("SELECT * FROM meteo_samples")
        df = pd.DataFrame(res.fetchall(), columns=[i[0] for i in cur.description])
        conn.close()
        return df

    except sqlite3.Error as e:
        print(f"Error connecting to database or reading table: {e}")


def remove_iqr_outliers_multi(df, columns_to_check, threshold=1.1):
    """
    Removes outliers from multiple columns in a DataFrame based on IQR.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        columns_to_check (list): A list of column names to check for outliers.
        threshold (float, optional): The IQR multiplier for outlier detection (default: 1.5).

    Returns:
        pd.DataFrame: A new DataFrame with outliers removed from the specified columns.
    """

    filtered_df = df.copy()  # Copy the DataFrame to avoid modifying the original
    for col in columns_to_check:
        Q1 = filtered_df[col].quantile(0.10)
        Q3 = filtered_df[col].quantile(0.90)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        filtered_df = filtered_df[
            (filtered_df[col] >= lower_bound) & (filtered_df[col] <= upper_bound)
        ]
    return filtered_df


def get_formatted_data(**kwargs):
    # Define constants
    SECONDS_IN_HOUR = 3600
    DEFAULT_LAST_HOURS = 24

    # Get the number of hours to look back, defaulting to 24 if not provided
    last_hours = kwargs.get("last_hours", DEFAULT_LAST_HOURS)
    hours_delay = last_hours * SECONDS_IN_HOUR

    # Load data from the database into a DataFrame
    df = db_to_dataframe("../air.db", "meteo_samples")

    # Determine the sampling rate based on the hours_delay
    if hours_delay > 10 * SECONDS_IN_HOUR:
        sample_rate = ('1H', 'One hour')
    elif hours_delay > 2 * SECONDS_IN_HOUR:
        sample_rate = False
    else:
        sample_rate = False

    # Filter the DataFrame to include only rows within the specified time range
    cutoff_time = datetime.now() - timedelta(seconds=hours_delay)
    df = df[df["date"] > datetime.timestamp(cutoff_time)]

    # Convert the 'date' column from timestamps to datetime objects and set it as the index
    df["date"] = pd.to_datetime(df["date"], unit='s')
    df.set_index("date", inplace=True)

    # Reshape the DataFrame to have 'date' as the index and 'metric' as columns with 'value' as data
    df_reshaped = df.pivot_table(values="value", index="date", columns="metric")

    # Resample the reshaped DataFrame based on the sample rate
    df_reshaped = df_reshaped.resample(sample_rate[0]).mean()

    # List of columns to process
    cols = ["temperature", "relative_humidity", "pressure", "gas"]

    # Remove outliers from the DataFrame
    df_no_outliers = remove_iqr_outliers_multi(df_reshaped, cols, threshold=1.5)

    # Calculate AQI and add it to the DataFrame
    df_no_outliers["aqi"] = np.log(df_no_outliers["gas"]) + 0.04 * df_no_outliers["relative_humidity"]
    cols.insert(3, "aqi")

    # Prepare the final return dictionary
    ret = {
        col: [
            {"x": item["date"].isoformat(), "y": item[col]} 
            for item in df_no_outliers[[col]].reset_index().to_dict(orient="records")
        ] 
        for col in cols
    }

    return {'datasets': ret, 'sample_rate_applied': sample_rate}


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/meteo_data.js")
def meteo_data():

    last_hours = request.args.get("last_hours", 24)

    datasets = get_formatted_data(last_hours=int(last_hours))
    resp = make_response(json.dumps(datasets), 200)
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    resp.headers["Server"] = "Pizza/0.1"
    return resp


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
