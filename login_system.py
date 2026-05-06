import json
import os
import hashlib
import re
from datetime import datetime, timedelta
import budget_tracker  # This imports your FINA main app!

DB_FILE = "users.json"
LOGIN_ATTEMPTS_FILE = "login_attempts.json"
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_MINUTES = 5

# --- SECURITY: PASSWORD HASHING ---
def hash_password(password):
    """Hashes password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- SECURITY: USERNAME VALIDATION ---
def is_valid_username(username):
    """
    Validates username to prevent path traversal and injection attacks.
    Only allows alphanumeric characters, underscores, and hyphens.
    Length: 3-20 characters.
    """
    if not username or len(username) < 3 or len(username) > 20:
        return False
    # Only allow safe characters
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))

# --- QUALITY OF LIFE HELPER FUNCTIONS ---
def clear_screen():
    """Clears the terminal screen for a cleaner UI."""
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    """Pauses the program so the user can read messages before the screen clears."""
    input("\nPress Enter to continue...")

# --- DATABASE FUNCTIONS WITH ERROR HANDLING ---
def init_db():
    """Initializes the user database with error handling."""
    try:
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w") as f:
                json.dump({}, f)
    except Exception as e:
        print(f"⚠️  Critical Error: Could not initialize database. {e}")
        return False
    return True

def load_users():
    """Loads users from JSON with corruption handling."""
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # If file doesn't exist, create it
        init_db()
        return {}
    except json.JSONDecodeError:
        # JSON CORRUPTION HANDLER
        print("⚠️  WARNING: User database is corrupted!")
        backup_file = f"{DB_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            # Backup the corrupted file
            if os.path.exists(DB_FILE):
                os.rename(DB_FILE, backup_file)
                print(f"Corrupted file backed up as: {backup_file}")
        except:
            pass
        # Create fresh database
        init_db()
        print("✅ Created fresh database. Previous accounts are lost (if any).")
        pause()
        return {}
    except Exception as e:
        print(f"⚠️  Unexpected error loading users: {e}")
        return {}

def save_users(users):
    """Saves users to JSON with error handling."""
    try:
        # Create backup before saving
        if os.path.exists(DB_FILE):
            backup_file = f"{DB_FILE}.temp"
            with open(backup_file, "w") as f:
                json.dump(users, f, indent=4)
            # If successful, replace original
            os.replace(backup_file, DB_FILE)
        else:
            with open(DB_FILE, "w") as f:
                json.dump(users, f, indent=4)
        return True
    except Exception as e:
        print(f"⚠️  Error saving users: {e}")
        return False

# --- LOGIN ATTEMPT TRACKING (SECURITY FEATURE) ---
def load_login_attempts():
    """Loads login attempt tracking data."""
    try:
        if os.path.exists(LOGIN_ATTEMPTS_FILE):
            with open(LOGIN_ATTEMPTS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_login_attempts(attempts):
    """Saves login attempt data."""
    try:
        with open(LOGIN_ATTEMPTS_FILE, "w") as f:
            json.dump(attempts, f, indent=4)
    except:
        pass

def is_account_locked(username):
    """Checks if account is temporarily locked due to failed attempts."""
    attempts = load_login_attempts()
    
    if username not in attempts:
        return False, None
    
    user_attempts = attempts[username]
    
    # Check if user has failed attempts
    if user_attempts.get("failed_count", 0) >= MAX_LOGIN_ATTEMPTS:
        lockout_time = datetime.fromisoformat(user_attempts["lockout_until"])
        
        if datetime.now() < lockout_time:
            # Still locked
            remaining = (lockout_time - datetime.now()).seconds // 60 + 1
            return True, remaining
        else:
            # Lockout expired, reset
            attempts[username] = {"failed_count": 0, "lockout_until": None}
            save_login_attempts(attempts)
            return False, None
    
    return False, None

def record_failed_login(username):
    """Records a failed login attempt."""
    attempts = load_login_attempts()
    
    if username not in attempts:
        attempts[username] = {"failed_count": 0, "lockout_until": None}
    
    attempts[username]["failed_count"] += 1
    
    # Lock account if max attempts reached
    if attempts[username]["failed_count"] >= MAX_LOGIN_ATTEMPTS:
        lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        attempts[username]["lockout_until"] = lockout_until.isoformat()
    
    save_login_attempts(attempts)
    
    remaining = MAX_LOGIN_ATTEMPTS - attempts[username]["failed_count"]
    return remaining

def reset_login_attempts(username):
    """Resets login attempts after successful login."""
    attempts = load_login_attempts()
    if username in attempts:
        attempts[username] = {"failed_count": 0, "lockout_until": None}
        save_login_attempts(attempts)

# --- CORE FUNCTIONS ---
def register():
    clear_screen()
    users = load_users()
    
    print("=" * 60)
    print("                         REGISTER")
    print("=" * 60)
    print("Username Requirements:")
    print("  • 3-20 characters long")
    print("  • Letters, numbers, underscores (_), hyphens (-) only")
    print("  • No spaces or special characters")
    print("-" * 60)
    
    username = input("Enter username: ").strip()
    
    # SECURITY: Validate username
    if not is_valid_username(username):
        print("\n❌ Invalid username!")
        print("Must be 3-20 characters: letters, numbers, _ or - only.")
        pause()
        return

    if username in users:
        print("\n❌ Username already exists! Try logging in instead.")
        pause()
        return

    password = input("Enter password: ").strip()
    
    # INPUT VALIDATION: Password length
    if not password or len(password) < 4:
        print("\n❌ Password must be at least 4 characters long!")
        pause()
        return
    
    if len(password) > 128:
        print("\n❌ Password too long! Maximum 128 characters.")
        pause()
        return

    # Confirm password
    confirm_password = input("Confirm password: ").strip()
    
    if password != confirm_password:
        print("\n❌ Passwords do not match!")
        pause()
        return

    # SECURITY: Hash the password before storing
    users[username] = {
        "password": hash_password(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if save_users(users):
        print("\n✅ User registered successfully! You can now log in.")
        print("🔐 Your password is encrypted and secure.")
    else:
        print("\n❌ Registration failed. Please try again.")
    
    pause()

def login():
    clear_screen()
    users = load_users()

    print("=" * 60)
    print("                          LOGIN")
    print("=" * 60)
    
    username = input("Enter username: ").strip()
    
    # SECURITY: Check if account is locked
    locked, remaining_minutes = is_account_locked(username)
    if locked:
        print(f"\n🔒 Account temporarily locked due to multiple failed attempts!")
        print(f"Please try again in {remaining_minutes} minute(s).")
        pause()
        return
    
    password = input("Enter password: ").strip()

    # SECURITY: Hash input password and compare
    if username in users and users[username]["password"] == hash_password(password):
        print(f"\n✅ Login Successful! Welcome to FINA, {username}!")
        
        # Reset failed login attempts
        reset_login_attempts(username)
        
        pause()
        
        # --- THE CONNECTION POINT ---
        # This calls the main() function in budget_tracker.py and passes the username
        try:
            budget_tracker.main(username)
        except KeyboardInterrupt:
            print("\n\nSession interrupted by user.")
            pause()
        except Exception as e:
            print(f"\n⚠️  An error occurred in the main application: {e}")
            pause()
    else:
        # SECURITY: Record failed attempt
        if username in users:
            remaining = record_failed_login(username)
            if remaining > 0:
                print(f"\n❌ Invalid password!")
                print(f"⚠️  {remaining} attempt(s) remaining before account lockout.")
            else:
                print(f"\n❌ Invalid password!")
                print(f"🔒 Account locked for {LOCKOUT_MINUTES} minutes due to multiple failures.")
        else:
            print("\n❌ Invalid username or password! Please try again.")
        
        pause()

def show_system_info():
    """Shows system information and security features."""
    clear_screen()
    print("=" * 60)
    print("                    SYSTEM INFORMATION")
    print("=" * 60)
    print("\nSECURITY FEATURES:")
    print("  • Encrypted password storage (SHA-256 hashing)")
    print(f"  • Login attempt limiting ({MAX_LOGIN_ATTEMPTS} attempts)")
    print(f"  • Temporary lockout ({LOCKOUT_MINUTES} minutes)")
    print("  • Username validation (prevents injection attacks)")
    print("  • Automatic database corruption recovery")
    print("\nAPPLICATION FEATURES:")
    print("  • Multi-user support with isolated data")
    print("  • Daily budget tracking and alerts")
    print("  • Visual spending analytics (graphs)")
    print("  • Smart financial insights")
    print("  • CSV export capabilities")
    print("  • Built-in financial calculator")
    print("\nDATA STORAGE:")
    print(f"  • User Database: {DB_FILE}")
    print(f"  • Budget Data: budget_data_[username].json")
    print("  • Automatic backups on corruption")
    print("\nDEVELOPMENT TEAM:")
    print("  • GROUP 2 - * Mark Droeid Mendoza")
    print("                * Jhon Mark Unico")
    print("                * Pauleen Pusta")
    print("                * Jhared Louise Chavez")
    print("                * Chyzza Malou Edulza")
    print("                * Janeah Angeles")
    print("                * Ghinger Kaye Reyes")
    print("=" * 60)
    pause()

# --- MAIN MENU LOOP ---
def main():
    if not init_db():
        print("Critical error: Cannot start application.")
        return
    
    while True:
        clear_screen()
        print("=" * 68)
        print(" 💰 FINA: Terminal Based Financial Insights Navigation Assistant 💰")
        print("                      User Authentication System")
        print("=" * 68)
        print("\n1. Register New Account")
        print("2. Login to Existing Account")
        print("3. System Information")
        print("4. Exit Application")
        print("\n" + "=" * 68)

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            show_system_info()
        elif choice == "4":
            clear_screen()
            print("\n" + "=" * 68)
            print("  Thank you for using FINA!")
            print("  Your financial data is safe and encrypted.")
            print("=" * 68)
            print("\n  Developed by GROUP 2 | BSIT-1203 | 2025-2026")
            print()
            break
        else:
            print("\n❌ Invalid choice. Please select 1, 2, 3, or 4.")
            pause()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n⚠️  Critical error: {e}")
        print("Please contact support if this persists.")