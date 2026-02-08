import json
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from database.models import Contact
from repos import contact_repo

# --- Interface ---
class PersonRepository(ABC):
    @abstractmethod
    def get_all(self, user_id: str = None) -> List[Contact]:
        """Retrieve all stored people/contacts."""
        pass

    @abstractmethod
    def add_person(self, person: Contact) -> None:
        """Add a new person to storage."""
        pass

    @abstractmethod
    def update_person(self, person_id: str, updates: Dict) -> Optional[Contact]:
        """Update fields of an existing person."""
        pass
    
    @abstractmethod
    def get_person(self, person_id: str) -> Optional[Contact]:
        pass

# --- MongoDB Implementation (Unified) ---
class DatabasePersonRepository(PersonRepository):
    def get_all(self, user_id: str = None) -> List[Contact]:
        if not user_id:
            return [] 
        return contact_repo.get_all_contacts_for_user(user_id)

    def add_person(self, person: Contact) -> None:
        # Assumes owner_user_id is set
        contact_repo.save_contact_to_database(person)

    def update_person(self, person_id: str, updates: Dict) -> Optional[Contact]:
        contact = contact_repo.get_contact_by_id(person_id)
        if not contact:
            return None
        
        # Apply updates
        contact_dict = contact.model_dump()
        for key, value in updates.items():
             if key in contact_dict and key != "contact_id":
                 contact_dict[key] = value
        
        # Mapping for 'name' update which might be ambiguous with first/last name
        if 'name' in updates:
            # Simple heuristic: split by space
            parts = updates['name'].split(' ', 1)
            contact_dict['first_name'] = parts[0]
            contact_dict['last_name'] = parts[1] if len(parts) > 1 else ""

        updated_contact = Contact(**contact_dict)
        return contact_repo.update_contact(updated_contact)

    def get_person(self, person_id: str) -> Optional[Contact]:
        return contact_repo.get_contact_by_id(person_id)


# --- Legacy JSON Implementation (Deprecated / Fallback) ---
class Person(BaseModel):
    # Backward compatibility shim using Contact structure where possible
    id: str
    name: str = "Unknown"
    age: Optional[int] = None
    image_path: str
    encoding: Optional[List[float]] = None 

class JsonPersonRepository(PersonRepository):
    def __init__(self, data_file: str = "data/people.json"):
        self.data_file = data_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        directory = os.path.dirname(self.data_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)

    def _load_data(self) -> List[Dict]:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_data(self, data: List[Dict]):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_all(self, user_id: str = None) -> List[Contact]:
        # Convert JSON structure to Contact objects
        raw_data = self._load_data()
        contacts = []
        for item in raw_data:
            # Map legacy Person fields to Contact
            name_parts = item.get("name", "Unknown").split(' ', 1)
            fname = name_parts[0]
            lname = name_parts[1] if len(name_parts) > 1 else ""
            
            c = Contact(
                contact_id=item["id"],
                owner_user_id=user_id or "legacy_json_user",
                first_name=fname,
                last_name=lname,
                age=item.get("age"),
                image_path=item.get("image_path"),
                encoding=item.get("encoding")
                # Notes and dates might be missing
            )
            contacts.append(c)
        return contacts

    def add_person(self, person: Contact) -> None:
        data = self._load_data()
        # Map Contact back to legacy dict structure
        p_dict = {
            "id": person.contact_id,
            "name": person.name,
            "age": person.age,
            "image_path": person.image_path,
            "encoding": person.encoding,
        }
        data.append(p_dict)
        self._save_data(data)

    def update_person(self, person_id: str, updates: Dict) -> Optional[Contact]:
        data = self._load_data()
        updated_contact = None
        
        for item in data:
            if item["id"] == person_id:
                for key, value in updates.items():
                    if key in item and key != "id":
                        item[key] = value
                
                # Convert updated item to Contact to return
                name_parts = item.get("name", "Unknown").split(' ', 1)
                updated_contact = Contact(
                    contact_id=item["id"],
                    owner_user_id="legacy",
                    first_name=name_parts[0],
                    last_name=name_parts[1] if len(name_parts) > 1 else "",
                    age=item.get("age"),
                    image_path=item.get("image_path"),
                    encoding=item.get("encoding")
                )
                break
        
        if updated_contact:
            self._save_data(data)
            
        return updated_contact

    def get_person(self, person_id: str) -> Optional[Contact]:
        data = self._load_data()
        for item in data:
            if item["id"] == person_id:
                  name_parts = item.get("name", "Unknown").split(' ', 1)
                  return Contact(
                    contact_id=item["id"],
                    owner_user_id="legacy",
                    first_name=name_parts[0],
                    last_name=name_parts[1] if len(name_parts) > 1 else "",
                    age=item.get("age"),
                    image_path=item.get("image_path"),
                    encoding=item.get("encoding")
                )
        return None