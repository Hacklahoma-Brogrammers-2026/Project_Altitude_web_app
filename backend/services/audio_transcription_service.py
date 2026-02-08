# example.py
import os
from dotenv import load_dotenv
from io import BytesIO
import requests
from elevenlabs.client import ElevenLabs

from database.models import User


import os
import tempfile
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field, computed_field

import torch
from pydub import AudioSegment
from speechbrain.inference.speaker import SpeakerRecognition
from speechbrain.dataio import audio_io  # type: ignore


from typing import Literal
from pydantic import BaseModel, Field, computed_field

load_dotenv()

TokenType = Literal["word", "spacing", "audio_event"]

class Token(BaseModel):
    text: str
    start: float
    end: float
    type: TokenType
    speaker_id: str | None = None

class Utterance(BaseModel):
    speaker_id: str
    text: str = Field(..., description="Concatenated text for this utterance.")
    start: float
    end: float

    @computed_field  # pydantic v2
    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

from collections.abc import Iterable


def tokens_to_utterances(
    tokens: Iterable[Token],
    *,
    break_on_silence_s: float | None = 1.2,
    include_audio_events: bool = False,
) -> list[Utterance]:
    out: list[Utterance] = []

    cur_speaker: str | None = None
    cur_parts: list[str] = []
    cur_start: float | None = None
    cur_end: float | None = None
    last_end: float | None = None

    def flush() -> None:
        nonlocal cur_speaker, cur_parts, cur_start, cur_end
        if cur_speaker is None:
            return
        text = "".join(cur_parts).strip()
        if text:
            out.append(Utterance(
                speaker_id=cur_speaker,
                text=text,
                start=float(cur_start or 0.0),
                end=float(cur_end or (cur_start or 0.0)),
            ))
        cur_speaker = None
        cur_parts = []
        cur_start = None
        cur_end = None

    for t in tokens:
        spk = t.speaker_id
        if not spk:
            # drop un-attributed tokens
            last_end = t.end
            continue

        if t.type == "audio_event" and not include_audio_events:
            last_end = t.end
            continue

        # optional silence boundary split
        if (
            break_on_silence_s is not None
            and last_end is not None
            and (t.start - last_end) >= break_on_silence_s
        ):
            flush()

        # speaker change split
        if cur_speaker is not None and spk != cur_speaker:
            flush()

        # start new utterance if needed
        if cur_speaker is None:
            cur_speaker = spk
            cur_start = t.start

        cur_parts.append(t.text)
        cur_end = t.end
        last_end = t.end

    flush()
    return out


elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)


def convert_raw_audio_to_utterances(audio_path: str) -> list[Utterance]:
    with open(audio_path, "rb") as f:
        transcription = elevenlabs.speech_to_text.convert(
            file=f,
            model_id="scribe_v2", # Model to use
            tag_audio_events=True, # Tag audio events like laughter, applause, etc.
            language_code="eng", # Language of the audio file. If set to None, the model will detect the language automatically.
            diarize=True, # Whether to annotate who is speaking
        )
        tokens = [eleven_word_to_token(w) for w in transcription.words] # type: ignore
        utterances = tokens_to_utterances(tokens, break_on_silence_s=1.2, include_audio_events=True)

        return utterances




# ---------- SpeechBrain verifier ----------
verifier: SpeakerRecognition = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa",
)  # type: ignore

def to_mono_batch(wav: torch.Tensor) -> torch.Tensor:
    """
    Accepts wav shaped [T], [C, T], or [B, T].
    Returns [1, T] mono batch.
    """
    if wav.ndim == 2:
        # Treat as channels-first if C is small (like 2 for stereo)
        if wav.shape[0] <= 8:
            wav = wav.mean(dim=0)  # [T]
        # else assume already [B, T] and leave it
    elif wav.ndim != 1:
        raise ValueError(f"Unexpected wav shape: {wav.shape}")

    if wav.ndim == 1:
        wav = wav.unsqueeze(0)  # [1, T]

    return wav

def _clip_utterance_to_temp_wav(
    full_audio: AudioSegment,
    start_s: float,
    end_s: float,
) -> str:
    """
    Export [start_s, end_s] from full_audio to a temporary WAV file, return path.
    """
    start_ms = int(max(0.0, start_s) * 1000)
    end_ms = int(max(0.0, end_s) * 1000)
    seg = full_audio[start_ms:end_ms]

    # Guard: avoid tiny segments that produce unstable speaker decisions
    if len(seg) < 300:  # type: ignore
        raise ValueError("segment too short")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    seg.export(tmp.name, format="wav") # type: ignore
    return tmp.name


def _score_paths_with_verify_batch(ref_path: str, utt_path: str) -> float:
    signal_ref, _ = audio_io.load(ref_path)
    signal_utt, _ = audio_io.load(utt_path)
    signal_ref = to_mono_batch(signal_ref)
    signal_utt = to_mono_batch(signal_utt)
    # print(signal_ref.shape)
    # print(signal_utt.shape)

    with torch.inference_mode():
        score, prediction = verifier.verify_batch(signal_ref, signal_utt)

    # score can be:
    # - scalar tensor: [[x]] or [x]
    # - 2-element tensor: [[a, b]] or [a, b] (two-class)
    s = score.detach().cpu().squeeze()

    if s.numel() == 1:
        return float(s.item())

    if s.numel() == 2:
        # We need to decide which element corresponds to "same speaker".
        # SpeechBrain's prediction is the authoritative label; pick the score matching it.
        # prediction is typically [[0]] or [[1]] (or shape that squeezes to scalar).
        pred = int(prediction.detach().cpu().squeeze().item())

        # If pred==1 means "same speaker", use s[1], else use s[0].
        # If SpeechBrain uses the opposite convention in your install, this still ranks correctly
        # across utterances for the same reference because pred is derived from these scores.
        return float(s[pred].item())

    # Unexpected shape: fall back to mean (still provides a sortable scalar)
    return float(s.float().mean().item())



def score_speakers_against_reference(
    *,
    full_audio_path: str,
    utterances: list[Utterance],
    reference_sample_path: str,
    min_utt_s: float = 0.6,
    max_utts_per_speaker: int = 15,
) -> tuple[str, list[tuple[str, float]]]:
    """
    Compute a score for each diarized speaker_id vs the reference sample.

    Returns:
      best_speaker_id,
      scores_sorted_desc = [(speaker_id, mean_score), ...]

    Scoring strategy:
      - clip N utterances per speaker from full audio
      - score each clip vs reference using verifier.verify_batch
      - average scores per speaker
    """
    full_audio = AudioSegment.from_file(full_audio_path)

    # group utterances by diarized speaker_id
    by_speaker: dict[str, list[Utterance]] = defaultdict(list)
    for u in utterances:
        if u.duration >= min_utt_s:
            by_speaker[u.speaker_id].append(u)

    tmp_paths: list[str] = []
    speaker_scores: list[tuple[str, float]] = []

    try:
        for speaker_id, utts in by_speaker.items():
            utts = utts[:max_utts_per_speaker]

            scores: list[float] = []
            for u in utts:
                try:
                    clip_path = _clip_utterance_to_temp_wav(full_audio, u.start, u.end)
                    tmp_paths.append(clip_path)
                    scores.append(_score_paths_with_verify_batch(reference_sample_path, clip_path))
                except ValueError:
                    continue

            if not scores:
                continue

            mean_score = sum(scores) / len(scores)
            speaker_scores.append((speaker_id, mean_score))

        speaker_scores.sort(key=lambda x: x[1], reverse=True)

        if not speaker_scores:
            raise RuntimeError("No usable utterances to score (all too short or failed to load).")

        best_speaker_id = speaker_scores[0][0]
        return best_speaker_id, speaker_scores

    finally:
        for p in tmp_paths:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass

def eleven_word_to_token(w) -> Token:
    return Token(
        text=w.text,
        start=float(w.start),
        end=float(w.end),
        type=w.type,              # "word" / "spacing" / "audio_event"
        speaker_id=w.speaker_id,  # "speaker_0", "speaker_1"
    )

def relabel_utterances_with_user(
    utterances: list[Utterance],
    user_voice_speaker_id: str,
) -> list[Utterance]:
    """
    Relabel utterances so that:
      - user_voice_speaker_id -> "user"
      - all other speaker_ids -> "user_contact_N" (stable mapping)

    Returns a NEW list of Utterance objects.
    """
    contact_map: dict[str, str] = {}
    next_contact_idx = 1

    relabeled: list[Utterance] = []

    for u in utterances:
        if u.speaker_id == user_voice_speaker_id:
            new_speaker = "user"
        else:
            if u.speaker_id not in contact_map:
                contact_map[u.speaker_id] = f"user_contact_{next_contact_idx}"
                next_contact_idx += 1
            new_speaker = contact_map[u.speaker_id]

        relabeled.append(
            Utterance(
                speaker_id=new_speaker,
                text=u.text,
                start=u.start,
                end=u.end,
            )
        )

    return relabeled





def process_audio(file_path: str, user: User) -> list[Utterance]:
    utterances = convert_raw_audio_to_utterances(file_path)

    if user.audio_sample_path is None:
        raise ValueError("Speaker needs to have an audio sample")
    speaker_reference_file = user.audio_sample_path
    best_label, scores = score_speakers_against_reference(
        full_audio_path=file_path,
        utterances=utterances,
        reference_sample_path=speaker_reference_file
    )

    relabeled_utterances = relabel_utterances_with_user(
        utterances=utterances,
        user_voice_speaker_id=best_label
    )

    return relabeled_utterances






if __name__ == "__main__":
    user = User(
        user_id='afa',
        username='afasfa',
        email='noah@gmail.com',
        password_hash='asfasfdsfasf',
        audio_sample_path="./backend/data/noah_audio_sample.wav"
        
    )
    print(process_audio("./backend/data/noah_and_k_data.wav", user))