import json
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pydantic import BaseModel
import uuid

# --- Data Model ---
class Person(BaseModel):
    id: str
    name: str = "Unknown"
    age: Optional[int] = None
    image_path: str
    # We store the encoding list to avoid re-processing images on startup
    encoding: Optional[List[float]] = None 

# --- Interface ---
class PersonRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Person]:
        """Retrieve all stored people."""
        pass

    @abstractmethod
    def add_person(self, person: Person) -> None:
        """Add a new person to storage."""
        pass

    @abstractmethod
    def update_person(self, person_id: str, updates: Dict) -> Optional[Person]:
        """Update fields of an existing person."""
        pass
    
    @abstractmethod
    def get_person(self, person_id: str) -> Optional[Person]:
        pass

# --- JSON Implementation ---
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

    def get_all(self) -> List[Person]:
        raw_data = self._load_data()
        return [Person(**item) for item in raw_data]

    def add_person(self, person: Person) -> None:
        data = self._load_data()
        data.append(person.dict())
        self._save_data(data)

    def update_person(self, person_id: str, updates: Dict) -> Optional[Person]:
        data = self._load_data()
        updated_person = None
        
        for item in data:
            if item["id"] == person_id:
                # Update fields
                for key, value in updates.items():
                    if key in item and key != "id": # Prevent ID change
                        item[key] = value
                updated_person = Person(**item)
                break
        
        if updated_person:
            self._save_data(data)
            
        return updated_person

    def get_person(self, person_id: str) -> Optional[Person]:
        people = self.get_all()
        for p in people:
            if p.id == person_id:
                return p
        return None