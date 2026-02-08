import os
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # quick workaround if needed

import numpy as np
from speechbrain.inference.speaker import SpeakerRecognition
from speechbrain.dataio import audio_io  # type: ignore

verifier: SpeakerRecognition = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa",
)  # type: ignore

def init_audio_service():
    os.makedirs("data/audio_samples", exist_ok=True)

def are_audio_samples_from_same_speaker(path1: str, path2: str) -> bool:
    signal1, fs = audio_io.load(path1)
    signal2, fs = audio_io.load(path2)
    score, prediction = verifier.verify_batch(signal1, signal2)
    return prediction.squeeze(0)[0].item()

if __name__ == "__main__":
    print("Running")
    print(are_audio_samples_from_same_speaker("./data/noah_audio_sample.wav", "./data/noah_audio_sample.wav"))
