from pydantic import BaseModel, Field
from backend.repos.contact_note_repo import create_contact_note
from database.models import Contact, ContactNote, User
from backend.services.audio_transcription_service import Utterance, process_audio
from langchain.agents import create_agent
from backend.config import config

class NotableFact(BaseModel):
    label: str = Field(..., description="Label for the fact, such as 'birthday' or 'occupation'")
    content: str = Field(default=..., description="Content for the fact.")

class ListOfNotableFacts(BaseModel):
    notable_facts: list[NotableFact] = Field(..., description="The list of notable facts. If there are no notable facts, return an empty list.")

agent = create_agent(config.llm_model_name, response_format=ListOfNotableFacts)


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

def notable_facts_to_contact_note(notable_facts: list[NotableFact], user: User, contact: Contact) -> list[ContactNote]:
    outputs = []
    for notable_fact in notable_facts:
        contact_note = create_contact_note(user.user_id, contact.contact_id, notable_fact.label, notable_fact.content)

        outputs.append(contact_note)

    return outputs

def extract_contact_facts_from_conversation(conversation: list[ConversationEntry], user: User, contact: Contact) -> list[ContactNote]:
    system_prompt = f"""
    You are a helpful AI assistant that listens to {user.username} conversations with people they are connected to. Your job is to help them remember important information from their conversations that will be useful in the future. Important information includes small things like a birthday or other significant dates, occupation, names of family members, contact information, stories, a plan to meet up later, etc. For the conversation snippet you are given, extract these relevant facts. Remember that these facts will be stored in long-term storage, so don't record everything. Just record things that would be good to remember in the long term. It is okay to response with no extracted facts."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": str(conversation)}
    ]

    result = agent.invoke({"messages": messages}) # type: ignore

    extracted_facts: ListOfNotableFacts = result['structured_response']
    print(extracted_facts)
    content_notes = notable_facts_to_contact_note(
        notable_facts=extracted_facts.notable_facts,
        user=user,
        contact=contact
    )

    return content_notes


if __name__ == "__main__":
    pass 
    # user = User(
    #     user_id='afa',
    #     username='Noah',
    #     email='noah@gmail.com',
    #     password_hash='asfasfdsfasf',
    #     audio_sample_path="./backend/data/noah_audio_sample.wav"
        
    # )
    # utterances = process_audio("./backend/data/noah_and_k_data.wav", user)
    # conversation = conversation = utterances_to_conversation_entries(utterances, user)

    # extract_contact_facts_from_conversation(
    #     conversation=conversation,
    #     user=user,
    #     contact=
    # )

    


