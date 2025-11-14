"""Script to clear Gmail tokens from all users (forces reconnection)."""

from database import DatabaseManager

def clear_all_tokens():
    """Clear Gmail tokens from all users."""
    db = DatabaseManager()
    
    try:
        users = db.get_all_users()
        print(f"Found {len(users)} users")
        
        cleared = 0
        for user in users:
            if user.gmail_token:
                user.gmail_token = None
                cleared += 1
                print(f"  - Cleared token for user: {user.email}")
        
        db.session.commit()
        print(f"\n✅ Cleared Gmail tokens from {cleared} users")
        print("Users will need to reconnect Gmail to scan emails.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    clear_all_tokens()

