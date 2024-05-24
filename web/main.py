from flask import Flask, render_template, make_response, request
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime


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
    filtered_df = filtered_df[(filtered_df[col] >= lower_bound) & (filtered_df[col] <= upper_bound)]
  return filtered_df

def get_formatted_data(**kwargs):

    last_hours = kwargs['last_hours'] if 'last_hours' in kwargs else 24
    
    df = db_to_dataframe('../air.db', 'meteo_samples')
    one_hour = (60 * 60)
    hours_delay = last_hours * one_hour

    howback_date = datetime.timestamp(datetime.now()) - hours_delay

    df = df[df['date'] > howback_date]

    df['date'] = df['date'].apply(datetime.fromtimestamp)
    df.set_index('date', inplace=True)

    df_reshaped = df.pivot_table(values='value', index='date', columns='metric')

    cols = ['temperature','relative_humidity', 'gas', 'pressure', 'altitude']
    df_no_outliers = remove_iqr_outliers_multi(df_reshaped, cols, threshold=1.5)
    cols.insert(0, 'aqi')
    df_no_outliers['aqi'] = np.log(df_no_outliers['gas']) + 0.04 * df_no_outliers['relative_humidity']
    ret = {}
    for _col in cols:
        ret[_col] = df_no_outliers[_col]
        ret[_col] = ret[_col].reset_index()
        ret[_col]['date'] = ret[_col]['date'].astype(str)
        ret[_col] = ret[_col].to_dict(orient='records')
        ret[_col] = [{'x': item['date'], 'y': item[_col]} for item in ret[_col]]

    return ret

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/meteo_data.js')
def meteo_data():

    last_hours = request.args.get('last_hours', 24)

    datasets = get_formatted_data(last_hours = int(last_hours))
    resp = make_response(json.dumps(datasets), 200)
    resp.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    resp.headers['Server'] = 'Pizza/0.1'
    return resp

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)




