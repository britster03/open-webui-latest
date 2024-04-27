from itsdangerous import URLSafeTimedSerializer as Serializer
import time

# Configuration
SECRET_KEY = "a9354d435ecbe043fde4ef6f92b65d32a9e5cc7ec8be8e117823453f627c6ad1"
SALT = "email-verify"
EXPIRATION = 3600  # Token expiration time in seconds

def generate_token(email):
    serializer = Serializer(SECRET_KEY)
    token = serializer.dumps(email, salt=SALT)
    return token

def verify_token(token, expiration=EXPIRATION):
    serializer = Serializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=SALT, max_age=expiration)
        return email
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

# Test the process
if __name__ == "__main__":
    test_email = "ronitvirwani1@gmail.com"
    print(f"Generating token for: {test_email}")
    
    token = generate_token(test_email)
    print(f"Generated token: {token}")

    # Verify the token immediately
    result = verify_token(token)
    print(f"Immediate verification result: {result}")

    # Verify with an invalid token
    invalid_token = "thisisnotavalidtoken"
    print(f"Verifying invalid token: {invalid_token}")
    result = verify_token(invalid_token)
    print(f"Verification result for invalid token: {result}")

    # Verify after waiting for the token to expire (for demonstration, we'll use a shorter expiration)
    print("Waiting for token to expire...")
    time.sleep(5)  # Wait for 5 seconds; adjust as needed for your expiration test

    expired_token = generate_token(test_email)
    result = verify_token(expired_token, expiration=1)  # Assuming the token is set to expire after 1 second
    print(f"Verification result after expiration: {result}")
