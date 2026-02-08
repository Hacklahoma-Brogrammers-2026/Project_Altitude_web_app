import sys
import os
from pathlib import Path
import random
import uuid
from datetime import datetime, timezone

# --- PATH CONFIGURATION ---
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent

if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from backend.config import config
from database.db import init_db, get_db_collections
from database.models import Contact, ContactNote
from repos.contact_note_repo import create_contact_note, save_contact_note_to_database

# Initialize DB
print(f"Connecting to database: {config.db_name}...")
init_db(config.mongo_url, config.db_name)

# --- CONSTANTS ---
RANDOM_NOTES = [
    "Met at the conference last year.",
    "High school friend.",
    "Work colleague from the marketing department.",
    "Neighbor from down the street.",
    "Met at the gym.", 
    "Family friend.",
    "Unknown connection."
]
RANDOM_NOTE_LABELS = ["Meeting", "Personal", "Work", "Reminder", "Important", "Idea"]
RANDOM_FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ian", "Julia"]
RANDOM_LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

# --- HELPER FUNCTIONS ---
def get_random_value(field):
    if field == "age": return random.randint(18, 90)
    if field == "note": return random.choice(RANDOM_NOTES)
    if field == "note_label": return random.choice(RANDOM_NOTE_LABELS)
    if field == "first_name": return random.choice(RANDOM_FIRST_NAMES)
    if field == "last_name": return random.choice(RANDOM_LAST_NAMES)
    if field == "last_modified": return datetime.now(timezone.utc)
    if field == "contact_id": return str(uuid.uuid4())
    return f"Random-{uuid.uuid4().hex[:8]}"

def generate_dummy_data(user_id, count=5):
    """Creates new dummy contacts."""
    contacts_coll = get_db_collections().contacts
    created_count = 0
    print(f"\nGenerating {count} dummy contacts for user {user_id}...")
    
    for _ in range(count):
        fname = get_random_value("first_name")
        lname = get_random_value("last_name")
        
        contact = Contact(
            contact_id=str(uuid.uuid4()),
            owner_user_id=user_id,
            first_name=fname,
            last_name=lname,
            age=get_random_value("age"),
            note=get_random_value("note"),
            created_at=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc)
        )
        
        try:
            contacts_coll.insert_one(contact.model_dump())
            print(f"  [+] Created: {fname} {lname}")
            created_count += 1
        except Exception as e:
            print(f"  [-] Error creating {fname}: {e}")

    print(f"Done. {created_count} contacts added.")

def generate_dummy_notes(user_id):
    """Generates dummy ContactNotes for ALL existing contacts of a user."""
    contacts_coll = get_db_collections().contacts
    
    cursor = contacts_coll.find({"owner_user_id": user_id})
    contacts = list(cursor)
    
    if not contacts:
        print("No contacts found for this user.")
        return

    print(f"\nFound {len(contacts)} contacts. Generating notes...")
    
    # Options
    print("1. Add 1 note per contact")
    print("2. Add random number (1-3) of notes per contact")
    choice = input("Choice: ").strip()
    
    created_count = 0
    
    for doc in contacts:
        c_id = doc["contact_id"]
        c_name = f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip()
        
        num_notes = 1
        if choice == '2':
            num_notes = random.randint(1, 3)
            
        for _ in range(num_notes):
            try:
                note = create_contact_note(
                    user_id=user_id,
                    contact_id=c_id,
                    label=get_random_value("note_label"),
                    content=get_random_value("note"),
                )
                save_contact_note_to_database(note)
                created_count += 1
            except Exception as e:
                print(f"  [-] Error creating note for {c_name}: {e}")
                
        print(f"  [+] Added {num_notes} note(s) for {c_name}")

    print(f"Done. {created_count} total notes created.")

def update_contacts_field(user_id):
    contacts_coll = get_db_collections().contacts
    
    # Define available fields
    fields = ["note", "age", "first_name", "last_name", "image_path", "relation", "group", "last_modified"]
    
    print("\n--- Field Selection ---")
    for i, f in enumerate(fields):
        print(f"{i+1}. {f}")
    
    try:
        f_idx = int(input("\nSelect number of field to update: ")) - 1
        if not (0 <= f_idx < len(fields)): raise ValueError
        field = fields[f_idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    print(f"\nUpdating field: '{field}' for ALL contacts of this user.")
    print("1. Enter a specific value (Apply same value to all)")
    print("2. Generate random values (Different random value for each)")
    print("3. Clear field (Set to Null)")

    choice = input("Choice: ").strip()
    
    update_type = "static"
    value_to_set = None

    if choice == '1':
        val = input(f"Enter value for '{field}': ")
        # Basic Type conversion
        if field == "age":
            try: val = int(val)
            except: val = 0
        value_to_set = val
        update_type = "static"

    elif choice == '2':
        update_type = "random"
    
    elif choice == '3':
        value_to_set = None
        update_type = "clear"

    else:
        print("Invalid choice.")
        return

    confirm = input(f"Are you sure you want to update '{field}' for ALL contacts? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    # Execute
    cursor = contacts_coll.find({"owner_user_id": user_id})
    updated_count = 0
    
    print(f"\nProcessing updates for field '{field}'...")
    for doc in cursor:
        c_id = doc["contact_id"]
        
        final_val = value_to_set
        if update_type == "random":
            final_val = get_random_value(field)
            
        contacts_coll.update_one(
            {"contact_id": c_id},
            {"$set": {
                field: final_val, 
                "last_modified": datetime.now(timezone.utc)
            }}
        )
        # Show partial preview
        display_val = str(final_val)[:30] + "..." if final_val and len(str(final_val)) > 30 else final_val
        print(f"  -> {doc.get('first_name', 'Unknown')} {doc.get('last_name', '')}: {display_val}")
        updated_count += 1
        
    print(f"Done. Updated {updated_count} contacts.")

# --- MAIN LOOP ---
if __name__ == "__main__":
    while True:
        try:
            # 1. Fetch Users (Refresh list each time)
            users_coll = get_db_collections().users
            users = list(users_coll.find({}, {"user_id": 1, "username": 1, "email": 1}))
            
            if not users:
                print("No users found in database! Please register a user first via the API or Frontend.")
                break

            # 2. Select User
            print("\n--- User Select ---")
            for idx, u in enumerate(users):
                print(f"{idx + 1}. {u.get('username')} ({u.get('email')})")
            print("q. Quit")
                
            selection = input("\nEnter user number: ")
            if selection.lower() == 'q':
                break
                
            idx = int(selection) - 1
            if not (0 <= idx < len(users)):
                print("Invalid selection.")
                continue
                
            target_user_id = users[idx]['user_id']
            username = users[idx]['username']

            # 3. Action Menu
            while True:
                print(f"\n--- Managing: {username} ---")
                print("1. Update specific field for ALL existing contacts")
                print("2. Create NEW dummy contacts")
                print("3. Generate dummy NOTES for existing contacts")
                print("b. Back to User Select")
                
                action = input("Selection: ").strip()
                
                if action == '1':
                    update_contacts_field(target_user_id)
                
                elif action == '2':
                    count_input = input("How many new contacts? (default 5): ")
                    count = int(count_input) if count_input.isdigit() else 5
                    generate_dummy_data(target_user_id, count)
                    
                elif action == '3':
                    generate_dummy_notes(target_user_id)
                    
                elif action.lower() == 'b':
                    break
                else:
                    print("Invalid option.")

        except ValueError:
            print("Invalid input.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
