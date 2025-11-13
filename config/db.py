import mysql.connector
from ../config/settings import Config
# Establish a connection
try:
    cnx = mysql.connector.connect(
        host= Config.DB_HOSTNAME,
        user=Config.DB_USERNAME,
        password=Config.DB_PASSWORD,
        database=Config.DB_DATNAME,
        port = Config.DB_PORT
    )

    # Create a cursor object
    cursor = cnx.cursor()

    # Execute a query
    cursor.execute("SELECT * FROM your_table")

    # Fetch results
    for row in cursor:
        print(row)

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    # Close the cursor and connection
    if 'cursor' in locals() and cursor is not None:
        cursor.close()
    if 'cnx' in locals() and cnx.is_connected():
        cnx.close()
