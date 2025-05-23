from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import traceback
import os
from data_processor import analyze_dormant_customers

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
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_results
    
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"File saved successfully: {filepath}")
        
        # Process the file for dormant customer analysis
        target_month = request.form.get('target_month', '2024-05')
        print(f"Target month: {target_month}")
        try:
            result = analyze_dormant_customers(filepath, target_month)
            # Store results for customer details page
            current_results = result
            return render_template('results.html', result=result, report_type="dormant_customers")
        except Exception as e:
            traceback.print_exc()  # Print detailed error
            flash(f'Error processing file: {str(e)}')
            return redirect('/')

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
                          lifetime_sales=customer_data['total_spent'])

if __name__ == '__main__':
    app.run(debug=True)