from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from service.supabaseclient import sign_in_with_password, get_user, fetch_user_profile, fetch_user_email, sign_out, supabase, fetch_images_data, fetch_user_name, fetch_user_withdrawals, update_withdrawal_status, fetch_delivery_partners
from dotenv import load_dotenv
import os
import requests
from functools import wraps

load_dotenv()  # Load environment variables from .env file

app: Flask = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Set a secret key for session management from .env file

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in to access this page.', 'danger')
            return redirect(url_for('login'))  # Redirect to login page
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('customer/home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/dashboard.html')

@app.route('/dashboard/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = sign_in_with_password(email, password)
        if user:
            user_profile = fetch_user_profile(user.id)
            if user_profile and user_profile.data and len(user_profile.data) > 0:
                user_role = user_profile.data[0]['roles']
                if user_role in ['staff', 'admin']:
                    session['user_id'] = user.id  # Store user ID in session
                    session['user_role'] = user_role  # Store user role in session
                    return redirect(url_for('dashboard'))  # Redirect to dashboard
                else:
                    flash('You do not have permission to access this area.', 'danger')
            else:
                flash('User profile not found.', 'danger')
        else:
            flash('Login failed. Please check your credentials.', 'danger')
    
    return render_template('dashboard/login.html')

@app.route('/logout')
def logout():
    sign_out()  # Log out the user from Supabase
    session.pop('user_id', None)  # Remove user ID from session
    flash('You have been logged out successfully.', 'success')  # Flash logout message
    return redirect(url_for('login'))  # Redirect to login page

@app.route('/order_approve')
@login_required
def order_approve():
    images = fetch_images_data()  # Fetch images from the database
    return render_template('dashboard/orderapprove.html', images=images)  # Pass images to the template

@app.route('/withdraw')
@login_required
def withdraw():
    withdrawals = fetch_user_withdrawals()  # Fetch all withdrawals where success is false
    return render_template('dashboard/withdraw.html', withdrawals=withdrawals)  # Pass withdrawals to the template

@app.route('/delivery_partners')
@login_required
def delivery_partners():
    partners = fetch_delivery_partners()  # Fetch delivery partners from the database
    return render_template('dashboard/delivery_partners.html', profiles=partners)  # Pass profiles to the template

@app.route('/approve_image/<int:id>', methods=['POST'])
def approve_image(id):
    try:
        # Update the image status to 'approved' in the database
        response = supabase.table('images').update({'status': 'approved'}).eq('id', id).execute()
        
        # Check if the update was successful
        if response.data:  # If response.data is not empty, the update was successful
            flash('Image approved successfully!', 'success')
        else:
            flash('Failed to approve image. Please try again.', 'danger')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('order_approve'))  # Redirect back to the order approval page

@app.route('/update_withdrawal/<int:withdrawal_id>', methods=['POST'])
def update_withdrawal(withdrawal_id):
    success = request.form.get('success') == 'true'  # Get the success status from the form
    result = update_withdrawal_status(withdrawal_id, success)  # Call the renamed update function

    if result:
        flash('Withdrawal updated successfully!', 'success')
    else:
        flash('Failed to update withdrawal. Please try again.', 'danger')

    return redirect(url_for('withdraw'))  # Redirect back to the withdraw page

@app.route('/partner')
def partner():
    response = requests.get("https://api.github.com/repos/theitruler/GNMEarning/releases/latest")
    if response.status_code == 200:
        latest_release = response.json()
        download_url = latest_release['assets'][0]['browser_download_url']  # Get the download URL from the first asset
    else:
        download_url = "#"  # Fallback URL or handle error appropriately

    return render_template('partner/partner.html', download_url=download_url)  # Pass the download URL to the template

@app.route('/offer')
def offer():
    return render_template('customer/offer.html')

@app.route('/toggle_bann', methods=['POST'])
@login_required
def toggle_bann():
    if session.get('user_role') == 'admin':
        try:
            # Update the bann field to true for users with the delivery role
            response = supabase.table('profiles').update({'bann': True}).eq('roles', 'delivery').execute()
            if response.data:
                return jsonify({'message': 'Users updated successfully!'}), 200
            else:
                return jsonify({'message': 'No users found with the delivery role.'}), 404
        except Exception as e:
            return jsonify({'message': f'An error occurred: {str(e)}'}), 500
    else:
        return jsonify({'message': 'Unauthorized access.'}), 403

@app.route('/toggle_bann_off', methods=['POST'])
@login_required
def toggle_bann_off():
    if session.get('user_role') == 'admin':
        try:
            # Update the bann field to false for users with the delivery role
            response = supabase.table('profiles').update({'bann': False}).eq('roles', 'delivery').execute()
            if response.data:
                return jsonify({'message': 'Users updated successfully!'}), 200
            else:
                return jsonify({'message': 'No users found with the delivery role.'}), 404
        except Exception as e:
            return jsonify({'message': f'An error occurred: {str(e)}'}), 500
    else:
        return jsonify({'message': 'Unauthorized access.'}), 403

@app.route('/dashboard/orderapprove/reject/<int:image_id>', methods=['POST'])
@login_required
def reject_image(image_id):
    reason = request.form.get('reason')  # Get the rejection reason from the form
    try:
        # Update the image status to 'rejected' in the database
        response = supabase.table('images').update({'status': 'rejected', 'reason': reason}).eq('id', image_id).execute()
        
        # Check if the update was successful
        if response.data:  # If response.data is not empty, the update was successful
            flash(f'Image rejected successfully! Reason: {reason}', 'danger')  # Flash rejection message with reason
        else:
            flash('Failed to reject image. Please try again.', 'danger')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('order_approve'))  # Redirect back to the order approval page

# ... other routes ...

if __name__ == '__main__':
    if os.getenv('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)