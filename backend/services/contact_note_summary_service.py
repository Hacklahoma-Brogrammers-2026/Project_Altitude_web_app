
from backend.config import config
from backend.repos.contact_note_repo import list_contact_notes_for_contact
from database.models import Contact, User

from langchain.chat_models import init_chat_model

model = init_chat_model(model=config.llm_model_name)


def get_contact_important_info(user: User, contact: Contact) -> str:
    notes = list_contact_notes_for_contact(
        user_id=user.user_id,
        contact_id=contact.contact_id,
        limit=100
    )

    messages = [{"role": "system", "content": f"Your job is to help {user.username} recall important information about {contact.first_name}, {contact.last_name}, just before {user.username} has a conversation with them. I will show you fact about {contact.first_name}, and you will need to create one concise sentence to prime {user.username} with the information he needs to know. Focus on the important things, like their name, if available. Keep your response short. No more than a sentence. For example, 'This is so and so. You saw them at a party last week'."}, {"role": "user", "content": str(notes)}]

    model_response = model.invoke(messages)
    return str(model_response.content)

     