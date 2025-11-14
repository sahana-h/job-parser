"""Token encryption/decryption for storing Gmail OAuth tokens securely."""

import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Generate a key for encryption and decryption
# In a real application, this key should be loaded from a secure environment variable
# and never hardcoded or committed to version control.
# For development, you can generate one with: Fernet.generate_key().decode()
_ENCRYPTION_KEY_STR = os.getenv('ENCRYPTION_KEY', None)

if _ENCRYPTION_KEY_STR:
    # Use provided key
    try:
        _ENCRYPTION_KEY = _ENCRYPTION_KEY_STR.encode('utf-8')
        _f = Fernet(_ENCRYPTION_KEY)
    except Exception as e:
        print(f"ERROR: Invalid ENCRYPTION_KEY format. Generating a new one for this session.")
        print(f"   To fix: Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        print(f"   Then set it in your .env file as: ENCRYPTION_KEY=your_generated_key")
        # Generate a temporary key for this session (will be different each time!)
        _ENCRYPTION_KEY = Fernet.generate_key()
        _f = Fernet(_ENCRYPTION_KEY)
        print("WARNING: Using temporary encryption key. Tokens encrypted now won't be decryptable after restart!")
else:
    # No key provided - generate a temporary one
    print("WARNING: No ENCRYPTION_KEY set. Generating a temporary key for this session.")
    print("   To fix: Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    print("   Then set it in your .env file as: ENCRYPTION_KEY=your_generated_key")
    _ENCRYPTION_KEY = Fernet.generate_key()
    _f = Fernet(_ENCRYPTION_KEY)
    print("WARNING: Using temporary encryption key. Tokens encrypted now won't be decryptable after restart!")

def encrypt_token(token_bytes: bytes) -> bytes:
    """Encrypts a token."""
    return _f.encrypt(token_bytes)

def decrypt_token(encrypted_token_bytes):
    """
    Decrypts an encrypted token.
    
    Args:
        encrypted_token_bytes: Encrypted token as bytes or string (from database)
    
    Returns:
        Decrypted token as bytes, or None if decryption fails
    """
    try:
        # Handle both bytes and string (PostgreSQL Text column returns string)
        if isinstance(encrypted_token_bytes, str):
            # Convert string back to bytes (Fernet tokens are base64-encoded)
            encrypted_token_bytes = encrypted_token_bytes.encode('utf-8')
        
        return _f.decrypt(encrypted_token_bytes)
    except Exception as e:
        print(f"Error decrypting token: {e}")
        return None

