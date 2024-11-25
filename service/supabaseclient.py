from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Initialize Supabase client
url: str = os.getenv("SUPABASE_URL")  # Get URL from .env
key: str = os.getenv("SUPABASE_KEY")  # Get Key from .env
supabase: Client = create_client(url, key)

def sign_in_with_password(email: str, password: str):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user
    except Exception as e:
        print(f"Error signing in: {str(e)}")
        return None

def get_user():
    return supabase.auth.get_user()

def fetch_user_profile(user_id: str):
    try:
        response = supabase.table('profiles').select('roles').eq('id', user_id).execute()
        return response
    except Exception as e:
        print(f"Error fetching user profile: {str(e)}")
        return None

def fetch_user_email(user_id: str):
    return supabase.table('profiles').select('name').eq('id', user_id).execute()

def sign_out():
    return supabase.auth.sign_out()  # Log out the user

def fetch_images_data():
    # Fetch specific fields from the images table where status is 'pending'
    response = supabase.table('images').select('id, status, image_url, price').eq('status', 'pending').execute()
    return response.data  # Return the data from the response

def fetch_user_name(user_id):
    # Fetch the user's name from the profiles table using the user ID
    response = supabase.table('profiles').select('name').eq('id', user_id).execute()
    return response.data[0]['name'] if response.data else None

def fetch_user_withdrawals():
    try:
        # Fetch amount, success, id from withdraw table where success is false
        withdrawals_response = supabase.table('withdraw').select('id, user_id, amount, success').eq('success', False).execute()
        
        withdrawals = withdrawals_response.data
        
        # Fetch upi_id for each withdrawal based on user_id
        for withdrawal in withdrawals:
            user_id = withdrawal['user_id']
            profile_response = supabase.table('profiles').select('upi_id').eq('id', user_id).execute()
            withdrawal['upi_id'] = profile_response.data[0]['upi_id'] if profile_response.data else None
        
        return withdrawals  # Return the filtered withdrawals with upi_id
    except Exception as e:
        print(f"Error fetching user withdrawals: {str(e)}")
        return None

def update_withdrawal_status(withdrawal_id: str, success: bool):
    try:
        # Update the success status of the withdrawal
        response = supabase.table('withdraw').update({'success': success}).eq('id', withdrawal_id).execute()
        return response.data  # Return the response data
    except Exception as e:
        print(f"Error updating withdrawal: {str(e)}")
        return None

def fetch_delivery_partners():
    try:
        # Fetch delivery partner profiles
        profiles_response = supabase.table('profiles').select('id, name, zomato_id, upi_id, phone, bann, email').eq('roles', 'delivery').execute()
        profiles = profiles_response.data

        # For each profile, fetch their images
        for profile in profiles:
            images_response = supabase.table('images').select('*').eq('user_id', profile['id']).execute()
            profile['images'] = images_response.data

        return profiles
    except Exception as e:
        print(f"Error fetching delivery partners: {str(e)}")
        return None

def update_delivery_partner_bann(user_id: str, bann: bool):
    try:
        # Update the bann status of the delivery partner
        response = supabase.table('profiles').update({'bann': bann}).eq('id', user_id).eq('roles', 'delivery').execute()
        return response.data
    except Exception as e:
        print(f"Error updating bann status: {str(e)}")
        return None
