
from backend.repos.contact_note_repo import save_contact_note_to_database
from backend.repos.contact_repo import get_contact_by_contact_id
from backend.repos.user_repo import create_user, get_user_by_user_id
from backend.services.audio_transcription_service import process_audio
from backend.services.information_extractor_service import extract_contact_facts_from_conversation, utterances_to_conversation_entries


def take_notes(file_path: str, user_id: str, contact_id: str):
    user = get_user_by_user_id(user_id)
    if user is None:
        raise ValueError("Invalid user id - user not found")
    contact = get_contact_by_contact_id(contact_id)
    if contact is None:
        raise ValueError("Invalid contact id - contact not found")

    labeled_utterances = process_audio(file_path, user)
    conversation = utterances_to_conversation_entries(labeled_utterances, user)
    contact_notes = extract_contact_facts_from_conversation(
        conversation=conversation,
        user=user,
        contact=contact
    )

    for contact_note in contact_notes:
        save_contact_note_to_database(contact_note)
