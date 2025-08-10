import os
import boto3
import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL Configuration from environment variables (will come from K8s secrets)
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'mysql-service')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'password')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'employees')

mysql = MySQL(app)

# Get configuration from environment variables (will come from ConfigMap)
GROUP_NAME = os.environ.get('GROUP_NAME', 'Default Group')
GROUP_SLOGAN = os.environ.get('GROUP_SLOGAN', 'Default Slogan')
BACKGROUND_IMAGE_URL = os.environ.get('BACKGROUND_IMAGE_URL', '')

# AWS Configuration for S3 access
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN', '')

def download_background_image():
    """Download background image from S3 and store locally"""
    if not BACKGROUND_IMAGE_URL:
        logger.warning("No background image URL provided")
        return None
    
    try:
        # Parse S3 URL to extract bucket and key
        # Expected format: s3://bucket-name/path/to/image.jpg
        if BACKGROUND_IMAGE_URL.startswith('s3://'):
            s3_path = BACKGROUND_IMAGE_URL[5:]  # Remove 's3://'
            bucket_name = s3_path.split('/')[0]
            object_key = '/'.join(s3_path.split('/')[1:])
            
            # Initialize S3 client with credentials
            s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                aws_session_token=AWS_SESSION_TOKEN
            )
            
            # Download the image
            local_image_path = os.path.join('static', 'background.jpg')
            s3_client.download_file(bucket_name, object_key, local_image_path)
            
            logger.info(f"Successfully downloaded background image from: {BACKGROUND_IMAGE_URL}")
            return 'background.jpg'
        else:
            logger.error("Invalid S3 URL format")
            return None
            
    except Exception as e:
        logger.error(f"Error downloading background image: {str(e)}")
        return None

@app.route('/')
def index():
    # Download background image on each request (in production, you might want to cache this)
    background_image = download_background_image()
    
    # Log the background image URL
    logger.info(f"Background image URL: {BACKGROUND_IMAGE_URL}")
    
    return render_template('index.html', 
                         group_name=GROUP_NAME, 
                         group_slogan=GROUP_SLOGAN,
                         background_image=background_image)

@app.route('/employees')
def employees():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees")
        data = cur.fetchall()
        cur.close()
        return render_template('employees.html', employees=data)
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return f"Database error: {str(e)}"

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        try:
            name = request.form['name']
            position = request.form['position']
            department = request.form['department']
            
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO employees (name, position, department) VALUES (%s, %s, %s)", 
                       (name, position, department))
            mysql.connection.commit()
            cur.close()
            
            return redirect(url_for('employees'))
        except Exception as e:
            logger.error(f"Error adding employee: {str(e)}")
            return f"Error adding employee: {str(e)}"
    
    return render_template('add_employee.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)
