import os
import time
import json
import logging
import numpy as np
import onnxruntime as ort
from typing import Tuple, Optional, List, Dict
from huggingface_hub import hf_hub_download

logger = logging.getLogger("PRIVACY68.VoiceAuth")

APPDATA_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "SANA")
MODELS_DIR = os.path.join(APPDATA_DIR, "models")
PROFILE_PATH = os.path.join(APPDATA_DIR, "voice_profile.npy")
PROFILE_META_PATH = os.path.join(APPDATA_DIR, "voice_profile_meta.json")

os.makedirs(MODELS_DIR, exist_ok=True)


class VoiceAuthenticator:
    """
    State-of-the-art Speaker Verification biometrics using ECAPA-TDNN (ONNX).
    Extracts 192-dimensional speaker embeddings and computes cosine similarity
    against enrolled master voice profile.
    """
    def __init__(self, sample_rate: int = 16000, n_mels: int = 80, frame_length: float = 25.0, frame_shift: float = 10.0):
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.win_len = int(sample_rate * frame_length / 1000)  # 400 samples
        self.hop_len = int(sample_rate * frame_shift / 1000)   # 160 samples
        self.n_fft = 512
        
        self.session: Optional[ort.InferenceSession] = None
        self.is_ready = False
        
        # Enrolled master embedding vector (192-d)
        self.master_embedding: Optional[np.ndarray] = None
        self.temp_enrollment_samples: List[np.ndarray] = []
        
        # Precompute Kaldi Povey window and Mel filterbank matrix once for sub-2ms speed
        self._precompute_kaldi_filters()
        
        # Initialize model session
        self._init_model()
        
        # Load existing profile if available
        self.load_profile()

    def _precompute_kaldi_filters(self):
        """Precomputes exact Kaldi-compliant Povey window and Mel filterbank matrix."""
        # Povey Window (Hamming^0.85)
        i = np.arange(self.win_len)
        self.window = ((0.5 - 0.5 * np.cos(2 * np.pi * i / (self.win_len - 1))) ** 0.85).astype(np.float32)
        
        # Kaldi Mel Filterbank (Natural logarithm formula: 1127.01048 * ln(1 + f / 700))
        low_freq = 20.0
        high_freq = self.sample_rate / 2.0  # 8000 Hz
        
        low_mel = 1127.01048 * np.log(1.0 + low_freq / 700.0)
        high_mel = 1127.01048 * np.log(1.0 + high_freq / 700.0)
        mel_points = np.linspace(low_mel, high_mel, self.n_mels + 2)
        hz_points = 700.0 * (np.exp(mel_points / 1127.01048) - 1.0)
        fft_bin_points = np.floor((self.n_fft + 1) * hz_points / self.sample_rate).astype(int)
        
        fbank = np.zeros((self.n_mels, self.n_fft // 2 + 1), dtype=np.float32)
        for m in range(1, self.n_mels + 1):
            left = fft_bin_points[m - 1]
            center = fft_bin_points[m]
            right = fft_bin_points[m + 1]
            for k in range(left, center):
                if center > left:
                    fbank[m - 1, k] = (k - left) / (center - left)
            for k in range(center, right):
                if right > center:
                    fbank[m - 1, k] = (right - k) / (right - center)
                    
        self.mel_filterbank = fbank.T.astype(np.float32)

    def _init_model(self):
        """Loads ECAPA-TDNN ONNX model, downloading if necessary."""
        try:
            model_path = os.path.join(MODELS_DIR, "voxceleb_ECAPA512_LM.onnx")
            if not os.path.exists(model_path):
                logger.info("Downloading ECAPA-TDNN Speaker Recognition ONNX model (~80MB)...")
                downloaded_path = hf_hub_download(
                    repo_id="Wespeaker/wespeaker-ecapa-tdnn512-LM",
                    filename="voxceleb_ECAPA512_LM.onnx",
                    local_dir=MODELS_DIR
                )
                if os.path.exists(downloaded_path) and downloaded_path != model_path:
                    try:
                        import shutil
                        shutil.copy2(downloaded_path, model_path)
                    except Exception:
                        model_path = downloaded_path

            opts = ort.SessionOptions()
            opts.inter_op_num_threads = 1
            opts.intra_op_num_threads = 2
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.session = ort.InferenceSession(model_path, sess_options=opts, providers=['CPUExecutionProvider'])
            self.is_ready = True
            logger.info("ECAPA-TDNN Voice Authenticator initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Voice Authenticator model: {e}")
            self.is_ready = False

    def compute_fbank(self, audio: np.ndarray) -> np.ndarray:
        """
        Extracts 80-channel Kaldi Log-Mel Filterbanks matching WeSpeaker's training pipeline.
        Processes audio array and returns (num_frames, 80) feature matrix.
        """
        waveform = audio.flatten().astype(np.float32)
        
        # Scale float [-1.0, 1.0] to standard 16-bit PCM integer range [-32768, 32767] expected by Kaldi
        if np.max(np.abs(waveform)) <= 1.5:
            waveform = waveform * 32768.0

        if len(waveform) < self.win_len:
            waveform = np.pad(waveform, (0, self.win_len - len(waveform)))

        # Pre-emphasis (0.97)
        waveform = np.append(waveform[0] - 0.97 * waveform[0], waveform[1:] - 0.97 * waveform[:-1])

        # Framing
        num_frames = max(1, int(np.floor((len(waveform) - self.win_len) / self.hop_len)) + 1)
        frames = np.lib.stride_tricks.as_strided(
            waveform,
            shape=(num_frames, self.win_len),
            strides=(waveform.strides[0] * self.hop_len, waveform.strides[0])
        ).copy()

        # Povey Window & Real FFT Power Spectrum
        frames *= self.window
        fft_complex = np.fft.rfft(frames, n=self.n_fft)
        power_spectrum = np.abs(fft_complex) ** 2

        # Mel Filterbank dot product
        mel_energy = np.dot(power_spectrum, self.mel_filterbank)
        mel_energy = np.maximum(mel_energy, np.finfo(np.float32).eps)
        log_mel = np.log(mel_energy)

        # Cepstral Mean Normalization (CMVN)
        log_mel -= np.mean(log_mel, axis=0, keepdims=True)
        return log_mel.astype(np.float32)

    def extract_embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        """
        Extracts a 192-dimensional unit-normalized speaker embedding vector from 16kHz audio.
        """
        if not self.is_ready or self.session is None:
            return None

        try:
            feats = self.compute_fbank(audio)
            feats_batch = np.expand_dims(feats, axis=0)  # Shape: (1, T, 80)
            
            output = self.session.run(None, {'feats': feats_batch})
            emb = output[0][0].astype(np.float32)
            
            # L2 Unit Normalization
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            return emb
        except Exception as e:
            logger.error(f"Error extracting voice embedding: {e}")
            return None

    def enroll_sample(self, audio: np.ndarray) -> Dict:
        """
        Records an enrollment audio sample into temporary buffer.
        Returns the current sample count and sample status.
        """
        emb = self.extract_embedding(audio)
        if emb is None:
            return {"success": False, "message": "Failed to extract voice embedding from sample.", "count": len(self.temp_enrollment_samples)}

        self.temp_enrollment_samples.append(emb)
        logger.info(f"Voice enrollment sample {len(self.temp_enrollment_samples)} recorded successfully.")
        return {
            "success": True,
            "message": f"Sample {len(self.temp_enrollment_samples)} recorded successfully.",
            "count": len(self.temp_enrollment_samples),
            "max": 3
        }

    def save_profile(self, owner_name: str = "Owner") -> bool:
        """
        Averages all recorded enrollment sample embeddings into a master profile vector
        and saves it to disk.
        """
        if not self.temp_enrollment_samples:
            logger.warning("Cannot save voice profile: No enrollment samples recorded.")
            return False

        try:
            # Centroid vector computation
            stacked = np.array(self.temp_enrollment_samples)
            centroid = np.mean(stacked, axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm

            self.master_embedding = centroid.astype(np.float32)
            np.save(PROFILE_PATH, self.master_embedding)

            meta = {
                "owner_name": owner_name,
                "samples_count": len(self.temp_enrollment_samples),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": "ECAPA-TDNN-512-192d",
                "dim": 192
            }
            with open(PROFILE_META_PATH, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            self.temp_enrollment_samples.clear()
            logger.info(f"Master voice profile saved for '{owner_name}' at {PROFILE_PATH}")
            return True
        except Exception as e:
            logger.error(f"Failed to save voice profile: {e}")
            return False

    def load_profile(self) -> bool:
        """Loads master voice embedding from disk if it exists."""
        if os.path.exists(PROFILE_PATH):
            try:
                self.master_embedding = np.load(PROFILE_PATH).astype(np.float32)
                logger.info("Loaded master voice profile from disk.")
                return True
            except Exception as e:
                logger.warning(f"Could not load voice profile: {e}")
        self.master_embedding = None
        return False

    def clear_profile(self) -> bool:
        """Deletes master voice profile and resets enrollment state."""
        self.master_embedding = None
        self.temp_enrollment_samples.clear()
        try:
            if os.path.exists(PROFILE_PATH):
                os.remove(PROFILE_PATH)
            if os.path.exists(PROFILE_META_PATH):
                os.remove(PROFILE_META_PATH)
            logger.info("Voice profile cleared.")
            return True
        except Exception as e:
            logger.error(f"Error clearing voice profile: {e}")
            return False

    def verify_speaker(self, audio: np.ndarray, threshold: float = 0.72) -> Tuple[bool, float]:
        """
        Compares live audio snippet against master voice embedding using Cosine Similarity.
        Returns: (is_authorized: bool, score: float)
        """
        if self.master_embedding is None:
            # If no voice profile is enrolled yet, allow open access
            return True, 1.0

        live_emb = self.extract_embedding(audio)
        if live_emb is None:
            return False, 0.0

        # Cosine similarity between two unit-normalized vectors is their dot product
        score = float(np.dot(self.master_embedding, live_emb))
        is_authorized = bool(score >= threshold)
        
        logger.info(f"Voice Verification: Score = {score:.3f} | Threshold = {threshold:.2f} | Authorized = {is_authorized}")
        return is_authorized, score

    def get_status(self) -> Dict:
        """Returns the current state of voice biometrics."""
        is_enrolled = self.master_embedding is not None and os.path.exists(PROFILE_PATH)
        meta = {}
        if is_enrolled and os.path.exists(PROFILE_META_PATH):
            try:
                with open(PROFILE_META_PATH, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass

        return {
            "model_ready": self.is_ready,
            "is_enrolled": is_enrolled,
            "temp_samples_count": len(self.temp_enrollment_samples),
            "owner_name": meta.get("owner_name", "User"),
            "created_at": meta.get("created_at", None),
        }


# Global singleton instance
voice_authenticator = VoiceAuthenticator()
