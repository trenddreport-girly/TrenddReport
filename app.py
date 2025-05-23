from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import traceback
import os
from datetime import datetime
from data_processor import analyze_dormant_customers, analyze_dormant_customers_by_range

# Create Flask app
app = Flask(__name__)
app.secret_key = "trendd_secret_key"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to store current analysis results
current_results = None

@app.route('/')
def index():
    return render_template('index.html', start_date='', end_date='')

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_results
    
    # Debug: Print all form data
    print("Form data received:")
    for key, value in request.form.items():
        print(f"  {key}: {value}")
    print("Files received:")
    for key, file in request.files.items():
        print(f"  {key}: {file.filename if file else 'None'}")
    
    if 'file' not in request.files:
        flash('No file part in request')
        return redirect('/')
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected. Please choose a file.')
        return redirect('/')
    
    # Get date range from form
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    
    print(f"FORM DEBUG: start_date_str='{start_date_str}', end_date_str='{end_date_str}'")
    print(f"Date range: {start_date_str} to {end_date_str}")
    
    if not start_date_str or not end_date_str:
        flash('Please select both start and end dates.')
        return redirect('/')
    
    # Validate dates
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        print(f"PARSED DATES: start_date={start_date}, end_date={end_date}")
        
        if start_date >= end_date:
            flash('Start date must be before end date')
            return redirect('/')
            
    except ValueError:
        flash('Invalid date format')
        return redirect('/')
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"File saved successfully: {filepath}")
        
        try:
            # Pass the actual date range to the analysis function
            print(f"CALLING analyze_dormant_customers_by_range with dates {start_date} to {end_date}")
            result = analyze_dormant_customers_by_range(filepath, start_date, end_date)
            print(f"RESULT KEYS: {result.keys()}")   
             
            
            # Store results for customer details page
            current_results = result
            return render_template('results.html', result=result, report_type="dormant_customers")
            
        except ValueError as ve:
            # Handle our custom date range validation error
            flash(str(ve))
            return render_template('index.html', start_date=start_date_str, end_date=end_date_str)
        except Exception as e:
            traceback.print_exc()  # Print detailed error
            flash(f'Error processing file: {str(e)}')
            return render_template('index.html', start_date=start_date_str, end_date=end_date_str)

@app.route('/customer_details/<customer_name>')
def customer_details(customer_name):
    # Access the global results
    global current_results
    
    if not current_results or customer_name not in current_results['dormant_customers']:
        flash("Customer information not found")
        return redirect('/')
    
    # Get customer data
    customer_data = current_results['dormant_customers'][customer_name]
    
    # Format order date
    from datetime import datetime
    if isinstance(customer_data['last_order_date'], datetime):
        order_date = customer_data['last_order_date'].strftime('%m/%d/%Y')
    else:
        order_date = str(customer_data['last_order_date'])
    
    # Get items
    items = customer_data.get('last_order_items', [])
    
    return render_template('customer_details.html', 
                          customer_name=customer_name, 
                          order_date=order_date,
                          items=items,
                          total_orders=customer_data['total_orders'],
                          lifetime_sales=customer_data['total_spent'],
                          customer_data=customer_data)

if __name__ == '__main__':
    app.run(debug=True)