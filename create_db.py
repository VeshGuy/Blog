import mysql.connector

# Establishing the connection
mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Sarvesh12'
)

# Creating a cursor object
my_cursor = mydb.cursor()

# Creating the database if it doesn't exist
my_cursor.execute("CREATE DATABASE IF NOT EXISTS our_users")

# Listing all databases
my_cursor.execute('SHOW DATABASES')
for db in my_cursor:
    print(db)
