from pydantic import BaseModel
from database.models import User
from services.audio_transcription_service import Utterance
from langchain.chat_models import init_chat_model
from config import config

model = init_chat_model(config.llm_model_name)

class ConversationEntry(BaseModel):
    speaker: str
    content: str

def utterances_to_conversation_entries(utterances: list[Utterance], user: User) -> list[ConversationEntry]:

    output = []
    for utterance in utterances:
        if utterance.speaker_id == 'user':
            output.append(ConversationEntry(
                speaker=user.username,
                content=utterance.text
            ))
        else:
            output.append(ConversationEntry(
                speaker=utterance.speaker_id,
                content=utterance.text
            ))
    return output

def extract_contact_facts_from_conversation(conversation: list[ConversationEntry], user: User)


