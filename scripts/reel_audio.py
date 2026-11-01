"""Narration, the music bed and loudness (see build_reel.py for the rules)."""

from reel_common import *  # noqa: F401,F403

TRIM_FILTER = (
    # Trim leading/trailing silence from every narration file, TTS or
    # supplied, so beat joins keep the 0.15s gap and nothing longer, and cap
    # pauses inside the narration at about 0.25s (the spec allows no gap over
    # 0.3s). -40 dB catches TTS pauses that sit just above digital silence;
    # tested on the Binance preview.
    "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,"
    "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse,"
    "silenceremove=start_periods=0:stop_periods=-1:stop_duration=0.15:"
    "stop_threshold=-40dB:stop_silence=0.12")


def narrate(scene, raw_out, wav_out, tts, voice):
    """Speak (or take the supplied 'audio') and trim one beat's narration."""
    raw = scene.get("audio")
    if not raw:
        raw = raw_out
        cmd = [tts, "speak", "--text", scene.get("narration", ""),
               "--format", "mp3", "--output", raw]
        if voice:
            cmd += ["--voice", voice]
        run(cmd)
    run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", TRIM_FILTER, wav_out])
    return wav_out


def pad_audio(src, dur, out):
    """One beat's narration padded (or silence) to exactly dur seconds,
    48 kHz stereo."""
    if src:
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", "apad",
             "-ar", "48000", "-ac", "2", "-t", f"{dur:.4f}", out])
    else:
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
             "anullsrc=r=48000:cl=stereo", "-t", f"{dur:.4f}", out])
    return out


def concat_list(paths, listing):
    with open(listing, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
    return listing


SFX = {
    # Generated accents (no copyrighted SFX), mixed well under the voice: a
    # low hit lands with a stat's figure. Wipes stay silent (the user's call).
    "hit": ("sine=frequency=55:duration=0.6:sample_rate=48000",
            "volume=1.6,afade=t=out:st=0.02:d=0.55:curve=exp,volume=0.55"),
}


def sfx_track(cues, total, work):
    """One stereo track of the accents at their cue times: [(name, seconds)]."""
    inputs, chains = [], []
    for n, (name, t) in enumerate(cues):
        src, filt = SFX[name]
        inputs += ["-f", "lavfi", "-i", src]
        ms = max(0, int(round(t * 1000)))
        chains.append(f"[{n}:a]{filt},aformat=sample_rates=48000:channel_layouts=stereo,"
                      f"adelay={ms}|{ms}[s{n}]")
    out = os.path.join(work, "sfx.wav")
    mixin = "".join(f"[s{n}]" for n in range(len(cues)))
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
         ";".join(chains) + f";{mixin}amix=inputs={len(cues)}:normalize=0,apad,"
         f"atrim=0:{total:.3f}[x]", "-map", "[x]", "-ar", "48000", "-ac", "2", out])
    return out


def mix(beat_audio, total, work, music_bed=True, cues=None):
    """Join the beats' audio, add the music bed and the sound accents
    (cues: [(name, seconds)]), compress and normalise. Returns the path of
    the finished 48 kHz stereo WAV."""
    joined = os.path.join(work, "audio_only.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", concat_list(beat_audio, os.path.join(work, "audios.txt")), "-c", "copy", joined])
    cues = [c for c in (cues or []) if 0 <= c[1] < total]
    if cues:
        fx = sfx_track(cues, total, work)
        with_fx = os.path.join(work, "voice_fx.wav")
        run(["ffmpeg", "-y", "-v", "error", "-i", joined, "-i", fx, "-filter_complex",
             "[0:a][1:a]amix=inputs=2:normalize=0:duration=first[a]", "-map", "[a]", with_fx])
        joined = with_fx
    if music_bed:
        # Original sine-pad music bed (no copyrighted music), mixed low and
        # kept under 400 Hz, so the voice sits clearly on top.
        music = os.path.join(work, "music.wav")
        run(["ffmpeg", "-y", "-v", "error",
             "-f", "lavfi", "-i", f"sine=frequency=110:duration={total:.2f}",
             "-f", "lavfi", "-i", f"sine=frequency=164.8:duration={total:.2f}",
             "-filter_complex",
             "[0:a]volume=0.05[a0];[1:a]volume=0.03[a1];[a0][a1]amix=inputs=2:normalize=0,"
             "lowpass=f=400,afade=t=in:st=0:d=1,"
             f"afade=t=out:st={max(0, total - 1):.2f}:d=1,aformat=sample_rates=48000:channel_layouts=stereo[m]",
             "-map", "[m]", music])
        mixed = os.path.join(work, "mixed.wav")
        run(["ffmpeg", "-y", "-v", "error", "-i", joined, "-i", music,
             "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]",
             "-map", "[a]", mixed])
        joined = mixed
    # loudnorm alone stopped short of -14 LUFS on true-peak limiting, so a
    # gentle compressor runs first.
    norm = os.path.join(work, "audio_norm.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", joined, "-af",
         "acompressor=threshold=-28dB:ratio=12:attack=5:release=100:makeup=12dB,"
         "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", norm])
    return norm


def encode(wav, out):
    """The finished audio as AAC, encoded once. The final mux copies this
    stream unchanged, so re-muxing after a video-only fix leaves the audio
    bit-identical (checked by checksum). 192k: the default bitrate
    overshot true peak above 0 dB."""
    run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-ac", "2", out])
    return out


def loudness(path):
    r = run(["ffmpeg", "-i", path, "-af", "ebur128", "-f", "null", "-"], check=False)
    vals = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(vals[-1]) if vals else None
