import sqlite3
import argparse


def print_tables_or_data(db_file, table_name=None):
    """
    Either prints a list of all tables in a SQLite database,
    or prints all rows from a specific table.

    Args:
        db_file (str): Path to the SQLite database file.
        table_name (str, optional): Name of the table to print (default: None).
    """

    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        if table_name is None:
            # Get a list of all tables in the database
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]

            if not tables:
                print(f"No tables found in database '{db_file}'.")
            else:
                print(f"List of tables in '{db_file}':")
                print(*tables, sep='\n')
        else:
            # Execute a query to select all rows from the specified table
            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()

            if not rows:
                print(f"No rows found in table '{table_name}'.")
            else:
                # Optionally, uncomment the code to print column names
                # column_names = [desc[0] for desc in cur.description]
                # print(", ".join(column_names))

                # Print each row
                for row in rows:
                    print(row)

        conn.close()

    except sqlite3.Error as e:
        print(f"Error connecting to database or reading table: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print tables or data from a SQLite database.")
    parser.add_argument("db_file", help="Path to the SQLite database file")
    parser.add_argument("-t", "--table", help="Name of the table to print (optional)")
    args = parser.parse_args()

    print_tables_or_data(args.db_file, args.table)

