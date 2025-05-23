from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
import pandas as pd
import anthropic
import secrets
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Make sure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Claude client
from dotenv import load_dotenv
load_dotenv()
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_quickbooks_data(filepath):
    """Process QuickBooks CSV export"""
    try:
        print(f"Starting to process: {filepath}")
        # Try reading with different encodings
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                print(f"Trying encoding: {encoding}")
                df = pd.read_csv(filepath, encoding=encoding)
                print(f"Successfully read file with {encoding} encoding")
                break
            except UnicodeDecodeError:
                if encoding == encodings[-1]:  # If this was the last encoding to try
                    raise  # Re-raise the exception
                continue
        
        # Basic data processing
        print(f"Processing data: {len(df)} rows, columns: {df.columns}")
        report_data = {
            'total_records': len(df),
            'columns': list(df.columns),
            'sample_data': df.head(5).to_dict('records'),
            # Add more processed data as needed
        }
        print("Report data created successfully")
        
        return df, report_data
    except Exception as e:
        print(f"Error in process_quickbooks_data: {e}")
        return None, None
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file upload"""
    if request.method == 'POST':
        print("POST request received")
        print("Files in request:", request.files)
        print("File in request:", 'file' in request.files)
        
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            print(f"About to process file: {filepath}")
            df, report_data = process_quickbooks_data(filepath)
            print(f"Process result: df = {type(df)}, report_data = {type(report_data)}")
            if df is not None:
                # Store in session for display
                session['report_data'] = report_data
                
                return redirect(url_for('results'))
            else:
                flash('Error processing file')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a CSV file.')
            return redirect(request.url)
    
    # If not a POST request or if something went wrong, show the upload form
    return render_template('index.html')

@app.route('/results')
def results():
    """Display results page"""
    report_data = session.get('report_data', None)
    
    if report_data is None:
        return redirect(url_for('index'))
    
    return render_template('results.html', report_data=report_data)
@app.route('/test-upload', methods=['GET', 'POST'])
def test_upload():
    """Test file upload functionality"""
    if request.method == 'POST':
        print("POST request received in test-upload")
        print("Files in request:", request.files)
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Save the file
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                return f"File '{filename}' uploaded successfully! <a href='/'>Back to home</a>"
            return "No file selected"
        return "No file part in the request"
    
    # Simple HTML form for testing
    html = '''
    <!DOCTYPE html>
    <html>
    <head><title>Test Upload</title></head>
    <body>
        <h1>Test File Upload</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <button type="submit">Upload</button>
        </form>
    </body>
    </html>
    '''
    return html
if __name__ == '__main__':
    app.run(debug=True)
def process_existing_file(filename):
    """Process an existing file in the uploads folder"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        # Process the file
        df, report_data = process_quickbooks_data(filepath)
        
        if df is not None:
            # Store in session for display
            session['report_data'] = report_data
            
            return redirect(url_for('results'))
        else:
            return "Error processing file"
    else:
        return f"File {filename} not found in uploads folder"@app.route('/list-files')
def list_files():
    """List files in the uploads folder"""
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_list = "<h1>Files in uploads folder:</h1><ul>"
    for file in files:
        file_list += f"<li><a href='/process-file/{file}'>{file}</a></li>"
    file_list += "</ul>"
    return file_list

@app.route('/process-file/<filename>')
def process_file(filename):
    """Process a specific file in the uploads folder"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        # Process the file
        df, report_data = process_quickbooks_data(filepath)
        
        if df is not None:
            # Store in session for display
            session['report_data'] = report_data
            
            return redirect(url_for('results'))
        else:
            return f"Error processing file: {filepath}"
    else:
        return f"File not found: {filepath}"