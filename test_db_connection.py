import psycopg2

try:
    # Establish the connection to PostgreSQL
    conn = psycopg2.connect(
        dbname="postgres",        # Database name
        user="postgres",          # Database user (or 'sunkevenkateswarlu' if you use that user)
        password="postgres",      # Database password
        host="localhost",         # Host name, usually 'localhost'
        port="5432"               # PostgreSQL default port
    )

    print("Connection successful")  # Print this if connection is successful

except Exception as e:
    print(f"Error: {e}")  # Print error message if something goes wrong

finally:
    if conn:
        conn.close()  # Close the connection
