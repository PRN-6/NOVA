"""
Diagnostic: Compare our compute_fbank vs correct Kaldi order.
Tests how sensitive embeddings are to feature extraction changes.
"""
import sys, os
sys.path.insert(0, os.path.abspath("."))
import numpy as np
from speech.voice_auth import voice_authenticator

va = voice_authenticator
sr = 16000

def compute_fbank_fixed(audio):
    """Correct Kaldi-order fbank: Stride -> DC offset -> Per-frame pre-emphasis -> Window -> FFT"""
    waveform = audio.flatten().astype(np.float32)
    
    # Scale to 16-bit PCM
    if np.max(np.abs(waveform)) <= 1.5:
        waveform = waveform * 32768.0
    
    win_len = va.win_len   # 400
    hop_len = va.hop_len   # 160
    n_fft = va.n_fft       # 512
    
    if len(waveform) < win_len:
        waveform = np.pad(waveform, (0, win_len - len(waveform)))
    
    # 1. Frame the raw waveform (snip_edges=True) 
    num_frames = max(1, (len(waveform) - win_len) // hop_len + 1)
    frames = np.lib.stride_tricks.as_strided(
        waveform,
        shape=(num_frames, win_len),
        strides=(waveform.strides[0] * hop_len, waveform.strides[0])
    ).copy()
    
    # 2. Remove DC offset per frame (Kaldi default: remove_dc_offset=True)
    frames -= np.mean(frames, axis=1, keepdims=True)
    
    # 3. Per-frame pre-emphasis (replicate-pad left, matching torchaudio exactly)
    #    For each frame [s0, s1, s2, ...] -> [s0-0.97*s0, s1-0.97*s0, s2-0.97*s1, ...]
    padded = np.concatenate([frames[:, :1], frames], axis=1)  # (num_frames, win_len+1)
    frames = frames - 0.97 * padded[:, :-1]
    
    # 4. Apply Povey window
    frames *= va.window
    
    # 5. FFT power spectrum
    fft_complex = np.fft.rfft(frames, n=n_fft)
    power_spectrum = np.abs(fft_complex) ** 2
    
    # 6. Mel filterbank
    mel_energy = np.dot(power_spectrum, va.mel_filterbank)
    mel_energy = np.maximum(mel_energy, np.finfo(np.float32).eps)
    log_mel = np.log(mel_energy)
    
    # 7. CMVN
    log_mel -= np.mean(log_mel, axis=0, keepdims=True)
    return log_mel.astype(np.float32)


def extract_fixed(audio):
    from speech.voice_auth import trim_speech
    clean = trim_speech(audio, sample_rate=sr)
    feats = compute_fbank_fixed(clean)
    feats_batch = np.expand_dims(feats, axis=0)
    output = va.session.run(None, {'feats': feats_batch})
    emb = output[0][0].astype(np.float32)
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm
    return emb


# Test 1: Identical signal determinism
t = np.linspace(0, 2.0, 2*sr)
voice = (0.3*np.sin(2*np.pi*150*t) + 0.2*np.sin(2*np.pi*500*t) + 0.1*np.sin(2*np.pi*1500*t)).astype(np.float32)

e1_old = va.extract_embedding(voice)
e1_new = extract_fixed(voice)

# Test 2: Robustness to tiny noise
noise = np.random.randn(len(voice)).astype(np.float32) * 0.001
voice_noisy = voice + noise

e2_old = va.extract_embedding(voice_noisy)
e2_new = extract_fixed(voice_noisy)

print("=== OLD compute_fbank (global pre-emphasis, no DC offset removal) ===")
print(f"  Clean vs Noisy: {float(np.dot(e1_old, e2_old)):.4f}")

print("=== NEW compute_fbank (per-frame pre-emphasis + DC offset removal) ===")
print(f"  Clean vs Noisy: {float(np.dot(e1_new, e2_new)):.4f}")

# Test 3: Different durations of same signal
voice_short = voice[:int(1.5*sr)]
e3_old_short = va.extract_embedding(voice_short)
e3_new_short = extract_fixed(voice_short)

print(f"\n  OLD 2.0s vs 1.5s same signal: {float(np.dot(e1_old, e3_old_short)):.4f}")
print(f"  NEW 2.0s vs 1.5s same signal: {float(np.dot(e1_new, e3_new_short)):.4f}")

# Test 4: Signal with silence padding (simulating real mic capture)
silence_before = np.zeros(int(0.3*sr), dtype=np.float32)
silence_after = np.zeros(int(1.5*sr), dtype=np.float32)
voice_padded = np.concatenate([silence_before, voice, silence_after])

e4_old = va.extract_embedding(voice_padded)
e4_new = extract_fixed(voice_padded)

print(f"\n  OLD clean vs silence-padded: {float(np.dot(e1_old, e4_old)):.4f}")
print(f"  NEW clean vs silence-padded: {float(np.dot(e1_new, e4_new)):.4f}")
