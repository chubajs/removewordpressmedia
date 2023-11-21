import mysql.connector
import os
import re

# Database configuration
config = {
    'user': 'wordpress',
    'password': '[PASSWORD]',
    'host': 'localhost',
    'database': 'wordpress',
    'raise_on_warnings': True
}

# Path to WordPress uploads
wp_uploads_path = '/var/www/html/wp-content/uploads/'

# File size constant (in bytes)
FILE_SIZE = 84888

# Connect to the database
try:
    conn = mysql.connector.connect(**config)
    # Using buffered=True for the cursors
    select_cursor = conn.cursor(buffered=True)
    delete_cursor = conn.cursor(buffered=True)
    print("Connected to the database.")
except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit(1)

# Query to get image metadata
query = "SELECT post_id, meta_value FROM wp_postmeta WHERE meta_key = '_wp_attached_file';"

select_cursor.execute(query)
print("Query executed, checking for files...")

total_files_checked = 0
total_files_deleted = 0

for (post_id, meta_value) in select_cursor:
    file_path = os.path.join(wp_uploads_path, meta_value)
    file_dir = os.path.dirname(file_path)
    file_base = os.path.basename(file_path)
    file_name, file_ext = os.path.splitext(file_base)

    # Check the size of the original file
    if os.path.exists(file_path) and os.path.getsize(file_path) == FILE_SIZE:
        print(f"Original file {file_path} matches the specified size. Deleting file and its variants.")

        # Regex to match files with the same base name (handles different sizes)
        pattern = re.compile(rf'^{re.escape(file_name)}(-\d+x\d+)?{re.escape(file_ext)}$')

        for file in os.listdir(file_dir):
            if pattern.match(file):
                full_path = os.path.join(file_dir, file)
                print(f"Deleting file {full_path}")
                os.remove(full_path)
                total_files_deleted += 1

        # Delete database record for the original image
        delete_cursor.execute("DELETE FROM wp_postmeta WHERE post_id = %s", (post_id,))
        delete_cursor.execute("DELETE FROM wp_posts WHERE ID = %s", (post_id,))

    total_files_checked += 1

# Commit changes and close connection
conn.commit()
select_cursor.close()
delete_cursor.close()
conn.close()
print(f"Database connection closed. Total files checked: {total_files_checked}, Total files deleted: {total_files_deleted}")
