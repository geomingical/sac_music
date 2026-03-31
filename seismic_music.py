# pyright: reportMissingImports=false, reportMissingTypeStubs=false

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import random
from typing import cast

import numpy as np
from numpy.typing import NDArray
import pretty_midi
import soundfile as sf
from obspy import read
from obspy.signal.trigger import classic_sta_lta, trigger_onset
from scipy.signal import butter, fftconvolve, hilbert, savgol_filter, sosfilt


# --- Constants ---
BASE_DIR = Path(__file__).resolve().parent
SAC_PATH = BASE_DIR / "TQ07_HHZ_20240403_UTC8.sac"
CSV_PATH = BASE_DIR / "C0H9C0-2024-04-03.csv"
OUTPUT_DIR = BASE_DIR / "output"
SF2_PATH = BASE_DIR / "soundfonts" / "GeneralUser-GS.sf2"
MIDI_PATH = OUTPUT_DIR / "hualien_earthquake_music.mid"
WAV_PATH = OUTPUT_DIR / "hualien_earthquake_music.wav"

TARGET_MUSIC_DURATION_SEC = 180.0
TARGET_BPM = 90.0
BEAT_SEC = 60.0 / TARGET_BPM
NOTE_RATE_PER_SEC = TARGET_BPM / 60.0
HOURS_PER_DAY = 24
SECONDS_PER_HOUR_IN_MUSIC = TARGET_MUSIC_DURATION_SEC / HOURS_PER_DAY
EARTHQUAKE_HOUR = 7.97  # UTC+8 07:58:11
EARTHQUAKE_MUSIC_TIME = EARTHQUAKE_HOUR * SECONDS_PER_HOUR_IN_MUSIC
QUIET_ZONE_END = EARTHQUAKE_MUSIC_TIME - 5.0
PHASE_2_END = EARTHQUAKE_MUSIC_TIME + 60.0

FADE_IN_SECONDS = 3.0
FADE_OUT_SECONDS = 5.0

PENTATONIC_C_MINOR = [48, 51, 53, 55, 58, 60, 63, 65, 67, 70]

PIANO_PROGRAM = 0
PAD_PROGRAM = 89

VELOCITY_MIN = 30
VELOCITY_MAX = 120
PAD_VELOCITY_MIN = 40
PAD_VELOCITY_MAX = 90

EVENT_TRIGGER_ON = 5.0
EVENT_TRIGGER_OFF = 2.5
STA_SECONDS = 1.0
LTA_SECONDS = 30.0

FS_WAV = 44100
DRONE_PROGRAM = 95

# --- Brainwave Entrainment Constants ---
ALPHA_FREQ = 10.0  # Hz
THETA_FREQ = 6.0  # Hz
RELAXATION_BPM_ALPHA = 72.0
RELAXATION_BPM_THETA = 60.0


@dataclass
class WeatherRow:
    obs_time: int
    pressure: float
    temperature: float
    wind_speed: float


@dataclass
class StyleConfig:
    name: str
    scale: list[int]
    piano_program: int
    pad_program: int
    use_drums: bool
    drum_hits_strong: list[tuple[int, float]]
    drum_hits_medium: list[tuple[int, float]]
    drum_hits_weak: list[tuple[int, float]]
    bpm: float
    pad_velocity_min: int
    pad_velocity_max: int
    velocity_min: int
    velocity_max: int


@dataclass
class EntrainmentConfig:
    name: str
    entrainment_freq_start: float
    entrainment_freq_end: float
    isochronic_depth: float


def make_dark_ambient() -> StyleConfig:
    return StyleConfig(
        name="dark_ambient",
        scale=[48, 51, 53, 55, 58, 60, 63, 65, 67, 70],
        piano_program=0,
        pad_program=89,
        use_drums=True,
        drum_hits_strong=[(36, 0.18), (51, 0.25)],
        drum_hits_medium=[(38, 0.18)],
        drum_hits_weak=[(42, 0.12)],
        bpm=90.0,
        pad_velocity_min=40,
        pad_velocity_max=90,
        velocity_min=30,
        velocity_max=120,
    )


def make_ethereal() -> StyleConfig:
    return StyleConfig(
        name="ethereal",
        scale=[62, 64, 66, 69, 71, 74, 76, 78, 81, 83],
        piano_program=9,
        pad_program=48,
        use_drums=True,
        drum_hits_strong=[(84, 0.5)],
        drum_hits_medium=[(81, 0.4)],
        drum_hits_weak=[(80, 0.3)],
        bpm=72.0,
        pad_velocity_min=30,
        pad_velocity_max=70,
        velocity_min=25,
        velocity_max=90,
    )


def make_cinematic() -> StyleConfig:
    return StyleConfig(
        name="cinematic",
        scale=[45, 48, 50, 52, 53, 55, 57, 59, 60, 64],
        piano_program=48,
        pad_program=60,
        use_drums=True,
        drum_hits_strong=[(36, 0.3), (49, 0.4)],
        drum_hits_medium=[(47, 0.25)],
        drum_hits_weak=[(41, 0.15)],
        bpm=85.0,
        pad_velocity_min=45,
        pad_velocity_max=100,
        velocity_min=35,
        velocity_max=127,
    )


def make_lofi_chill() -> StyleConfig:
    return StyleConfig(
        name="lofi_chill",
        scale=[51, 53, 55, 58, 60, 63, 65, 67, 70, 72],
        piano_program=4,
        pad_program=89,
        use_drums=True,
        drum_hits_strong=[(36, 0.15), (51, 0.3)],
        drum_hits_medium=[(40, 0.12)],
        drum_hits_weak=[(42, 0.08)],
        bpm=70.0,
        pad_velocity_min=35,
        pad_velocity_max=75,
        velocity_min=25,
        velocity_max=85,
    )


def make_glitch() -> StyleConfig:
    return StyleConfig(
        name="glitch",
        scale=[48, 50, 52, 54, 56, 58, 60, 62, 64, 66],
        piano_program=81,
        pad_program=88,
        use_drums=True,
        drum_hits_strong=[(36, 0.1), (39, 0.08)],
        drum_hits_medium=[(40, 0.08)],
        drum_hits_weak=[(42, 0.06), (37, 0.05)],
        bpm=110.0,
        pad_velocity_min=40,
        pad_velocity_max=95,
        velocity_min=30,
        velocity_max=127,
    )


def make_alpha_relax() -> tuple[StyleConfig, EntrainmentConfig]:
    style = StyleConfig(
        name="alpha_relax",
        scale=[60, 62, 64, 67, 69],
        piano_program=4,
        pad_program=89,
        use_drums=False,
        drum_hits_strong=[],
        drum_hits_medium=[],
        drum_hits_weak=[],
        bpm=RELAXATION_BPM_ALPHA,
        pad_velocity_min=25,
        pad_velocity_max=50,
        velocity_min=25,
        velocity_max=55,
    )
    entrainment = EntrainmentConfig(
        name="alpha_relax",
        entrainment_freq_start=ALPHA_FREQ,
        entrainment_freq_end=ALPHA_FREQ,
        isochronic_depth=0.22,
    )
    return style, entrainment


def make_theta_meditation() -> tuple[StyleConfig, EntrainmentConfig]:
    style = StyleConfig(
        name="theta_meditation",
        scale=[60, 62, 67, 69, 72],
        piano_program=89,
        pad_program=92,
        use_drums=False,
        drum_hits_strong=[],
        drum_hits_medium=[],
        drum_hits_weak=[],
        bpm=RELAXATION_BPM_THETA,
        pad_velocity_min=20,
        pad_velocity_max=45,
        velocity_min=20,
        velocity_max=50,
    )
    entrainment = EntrainmentConfig(
        name="theta_meditation",
        entrainment_freq_start=THETA_FREQ,
        entrainment_freq_end=THETA_FREQ,
        isochronic_depth=0.25,
    )
    return style, entrainment


def make_progressive_relax() -> tuple[StyleConfig, EntrainmentConfig]:
    style = StyleConfig(
        name="progressive_relax",
        scale=[62, 65, 67, 69, 72],
        piano_program=4,
        pad_program=92,
        use_drums=False,
        drum_hits_strong=[],
        drum_hits_medium=[],
        drum_hits_weak=[],
        bpm=66.0,
        pad_velocity_min=22,
        pad_velocity_max=48,
        velocity_min=22,
        velocity_max=52,
    )
    entrainment = EntrainmentConfig(
        name="progressive_relax",
        entrainment_freq_start=ALPHA_FREQ,
        entrainment_freq_end=THETA_FREQ,
        isochronic_depth=0.23,
    )
    return style, entrainment


# --- Helpers ---
def normalize_array(values: NDArray[np.float64]) -> NDArray[np.float64]:
    if values.size == 0:
        return values
    v_min = float(np.min(values))
    v_max = float(np.max(values))
    if np.isclose(v_max, v_min):
        return np.full_like(values, 0.5, dtype=np.float64)
    return (values - v_min) / (v_max - v_min)


def map_range(
    value: float, src_min: float, src_max: float, dst_min: float, dst_max: float
) -> float:
    if np.isclose(src_max, src_min):
        return (dst_min + dst_max) * 0.5
    ratio = (value - src_min) / (src_max - src_min)
    ratio_clamped = float(np.clip(ratio, 0.0, 1.0))
    return dst_min + ratio_clamped * (dst_max - dst_min)


def ensure_input_files() -> None:
    if not SAC_PATH.exists():
        raise FileNotFoundError(f"SAC 檔案不存在: {SAC_PATH}")
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV 檔案不存在: {CSV_PATH}")


def read_weather_csv(csv_path: Path) -> list[WeatherRow]:
    rows: list[WeatherRow] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        next(handle, None)
        reader = csv.DictReader(handle)
        for row in reader:
            if row is None:
                continue
            obs_text = (row.get("ObsTime") or "").strip()
            pressure_text = (row.get("StnPres") or "").strip()
            temp_text = (row.get("Temperature") or "").strip()
            wind_text = (row.get("WS") or "").strip()
            if not obs_text or not pressure_text or not temp_text or not wind_text:
                continue
            rows.append(
                WeatherRow(
                    obs_time=int(obs_text),
                    pressure=float(pressure_text),
                    temperature=float(temp_text),
                    wind_speed=float(wind_text),
                )
            )
    if not rows:
        raise ValueError("CSV 無有效天氣資料列")
    return rows


def load_and_process_sac(sac_path: Path) -> tuple[NDArray[np.float64], float]:
    stream = read(str(sac_path))
    if len(stream) == 0:
        raise ValueError("SAC 檔案沒有可用 trace")

    trace = stream[0].copy()
    trace.detrend("linear")
    trace.filter("bandpass", freqmin=0.5, freqmax=10.0, corners=4, zerophase=True)

    sampling_rate = float(trace.stats.sampling_rate)
    data = np.asarray(trace.data, dtype=np.float64)
    if data.size == 0:
        raise ValueError("SAC 波形資料為空")
    return data, sampling_rate


def compute_envelope(signal_data: NDArray[np.float64]) -> NDArray[np.float64]:
    analytic = hilbert(signal_data)
    envelope = np.abs(cast(NDArray[np.complex128], cast(object, analytic)))

    window = min(1001, envelope.size if envelope.size % 2 == 1 else envelope.size - 1)
    if window < 5:
        return envelope

    smoothed = savgol_filter(envelope, window_length=window, polyorder=3, mode="interp")
    return cast(NDArray[np.float64], smoothed)


def build_piano_track(
    envelope: NDArray[np.float64],
    sampling_rate: float,
    total_source_seconds: float,
    style: StyleConfig,
) -> tuple[pretty_midi.Instrument, int]:
    piano = pretty_midi.Instrument(program=style.piano_program, name="Seismic Piano")

    beat_sec = 60.0 / style.bpm
    note_rate_per_sec = style.bpm / 60.0

    target_note_count = max(int(TARGET_MUSIC_DURATION_SEC * note_rate_per_sec), 1)
    sample_indices = np.linspace(
        0, envelope.size - 1, num=target_note_count, dtype=np.int64
    )
    sampled_env = envelope[sample_indices]

    q05 = float(np.percentile(sampled_env, 5))
    q95 = float(np.percentile(sampled_env, 95))
    env_for_map = np.clip(sampled_env, q05, q95)
    env_norm = normalize_array(env_for_map)

    note_duration = beat_sec * 0.95
    source_to_music = TARGET_MUSIC_DURATION_SEC / total_source_seconds
    rng = np.random.default_rng(seed=42)
    quiet_keep_probability = 0.5 / note_rate_per_sec

    note_count = 0
    for idx, source_index in enumerate(sample_indices):
        src_time_sec = float(source_index) / sampling_rate
        start_time = src_time_sec * source_to_music
        end_time = min(start_time + note_duration, TARGET_MUSIC_DURATION_SEC)
        if end_time <= start_time:
            continue

        level = float(env_norm[idx])

        if start_time < EARTHQUAKE_MUSIC_TIME:
            if float(rng.random()) > quiet_keep_probability:
                continue

            quiet_index_base = int(round(level * 4.0))
            quiet_jitter = int(rng.integers(-1, 2))
            pitch_index = int(np.clip(quiet_index_base + quiet_jitter, 0, 4))
            quiet_velocity_max = min(style.velocity_max, style.velocity_min + 20)
            velocity = int(
                round(
                    map_range(
                        level,
                        0.0,
                        1.0,
                        float(style.velocity_min),
                        float(quiet_velocity_max),
                    )
                )
            )
        elif start_time <= PHASE_2_END:
            pitch_index = int(round(level * (len(style.scale) - 1)))
            velocity = int(
                round(
                    map_range(
                        level,
                        0.0,
                        1.0,
                        float(style.velocity_min),
                        float(style.velocity_max),
                    )
                )
            )
        else:
            decay_progress = map_range(
                start_time,
                PHASE_2_END,
                TARGET_MUSIC_DURATION_SEC,
                0.0,
                1.0,
            )
            max_pitch_index = int(
                round(map_range(decay_progress, 0.0, 1.0, len(style.scale) - 1, 4.0))
            )
            pitch_index = int(round(level * max_pitch_index))
            decay_velocity_floor = max(20.0, float(style.velocity_min) * 0.8)
            decay_velocity_ceiling = max(
                decay_velocity_floor + 5.0,
                min(float(style.velocity_max), float(style.velocity_min) + 25.0),
            )
            velocity_floor = map_range(
                decay_progress,
                0.0,
                1.0,
                float(style.velocity_min),
                decay_velocity_floor,
            )
            velocity_ceiling = map_range(
                decay_progress,
                0.0,
                1.0,
                float(style.velocity_max),
                decay_velocity_ceiling,
            )
            velocity = int(
                round(map_range(level, 0.0, 1.0, velocity_floor, velocity_ceiling))
            )

        pitch = style.scale[pitch_index]

        piano.notes.append(
            pretty_midi.Note(
                velocity=int(np.clip(velocity, style.velocity_min, style.velocity_max)),
                pitch=pitch,
                start=float(start_time),
                end=float(end_time),
            )
        )
        note_count += 1

    return piano, note_count


def pressure_to_chord(pressure_norm: float) -> list[int]:
    if pressure_norm < 0.33:
        return [57, 60, 64] if pressure_norm < 0.165 else [62, 65, 69]
    if pressure_norm > 0.67:
        return [48, 52, 55] if pressure_norm < 0.835 else [53, 57, 60]
    return [48, 53, 55]


def build_pad_track(
    weather_rows: list[WeatherRow],
    style: StyleConfig,
) -> tuple[pretty_midi.Instrument, int]:
    pad = pretty_midi.Instrument(program=style.pad_program, name="Weather Pad")

    pressures = np.array([row.pressure for row in weather_rows], dtype=np.float64)
    pressures_norm = normalize_array(pressures)
    wind_speeds = np.array([row.wind_speed for row in weather_rows], dtype=np.float64)
    wind_min = float(np.min(wind_speeds))
    wind_max = float(np.max(wind_speeds))

    chord_note_count = 0
    for index, row in enumerate(weather_rows):
        start_time = index * SECONDS_PER_HOUR_IN_MUSIC
        end_time = min(
            start_time + SECONDS_PER_HOUR_IN_MUSIC, TARGET_MUSIC_DURATION_SEC
        )
        if end_time <= start_time:
            continue

        chord = pressure_to_chord(float(pressures_norm[index]))
        if row.temperature < 7.0:
            chord = [pitch - 12 for pitch in chord]

        velocity = int(
            round(
                map_range(
                    row.wind_speed,
                    wind_min,
                    wind_max,
                    style.pad_velocity_min,
                    style.pad_velocity_max,
                )
            )
        )

        hour_index = float(index)
        if hour_index < 8.0:
            intro_progress = map_range(hour_index, 0.0, 7.0, 0.0, 1.0)
            intro_floor = max(20.0, float(style.pad_velocity_min) * 0.6)
            velocity = int(
                round(
                    map_range(
                        intro_progress,
                        0.0,
                        1.0,
                        intro_floor,
                        float(velocity),
                    )
                )
            )
        elif hour_index >= 17.0:
            decay_progress = map_range(hour_index, 17.0, 23.0, 0.0, 1.0)
            decay_floor = max(22.0, float(style.pad_velocity_min) * 0.75)
            velocity = int(
                round(
                    map_range(
                        decay_progress,
                        0.0,
                        1.0,
                        float(velocity),
                        decay_floor,
                    )
                )
            )

        velocity_clamped = int(
            np.clip(velocity, style.pad_velocity_min, style.pad_velocity_max)
        )

        for pitch in chord:
            pad.notes.append(
                pretty_midi.Note(
                    velocity=velocity_clamped,
                    pitch=int(pitch),
                    start=float(start_time),
                    end=float(end_time),
                )
            )
            chord_note_count += 1

    return pad, chord_note_count


def build_drum_track(
    signal_data: NDArray[np.float64],
    sampling_rate: float,
    total_source_seconds: float,
    style: StyleConfig,
) -> tuple[pretty_midi.Instrument | None, int]:
    if not style.use_drums:
        return None, 0

    sta_n = max(int(STA_SECONDS * sampling_rate), 1)
    lta_n = max(int(LTA_SECONDS * sampling_rate), sta_n + 1)

    cft = classic_sta_lta(signal_data, sta_n, lta_n)
    onsets = trigger_onset(cft, EVENT_TRIGGER_ON, EVENT_TRIGGER_OFF)
    if onsets.size == 0:
        print("警告: STA/LTA 未偵測到事件，將略過鼓組軌")
        return None, 0

    drum = pretty_midi.Instrument(program=0, is_drum=True, name="Seismic Drums")
    source_to_music = TARGET_MUSIC_DURATION_SEC / total_source_seconds

    event_strengths: list[float] = []
    events: list[tuple[int, int, float]] = []
    for onset in onsets:
        start_idx = int(onset[0])
        end_idx = int(onset[1])
        if end_idx <= start_idx:
            continue
        segment = np.abs(signal_data[start_idx:end_idx])
        if segment.size == 0:
            continue
        strength = float(np.max(segment))
        event_strengths.append(strength)
        events.append((start_idx, end_idx, strength))

    if not events:
        print("警告: 事件分段為空，將略過鼓組軌")
        return None, 0

    strengths = np.array(event_strengths, dtype=np.float64)
    p75 = float(np.percentile(strengths, 75))
    p50 = float(np.percentile(strengths, 50))
    s_min = float(np.min(strengths))
    s_max = float(np.max(strengths))

    event_count = 0
    last_event_time = -1.0
    for start_idx, _end_idx, strength in events:
        start_time = (start_idx / sampling_rate) * source_to_music
        if start_time < QUIET_ZONE_END:
            continue
        if start_time - last_event_time < 0.15:
            continue
        if start_time >= TARGET_MUSIC_DURATION_SEC:
            continue

        velocity = int(round(map_range(strength, s_min, s_max, 40, 100)))

        if start_time < EARTHQUAKE_MUSIC_TIME:
            ramp = map_range(
                start_time,
                QUIET_ZONE_END,
                EARTHQUAKE_MUSIC_TIME,
                0.0,
                1.0,
            )
            velocity = int(round(velocity * ramp))

        velocity_clamped = int(np.clip(velocity, 30, 127))

        drum_hits: list[tuple[int, float]] = []
        if strength >= p75:
            drum_hits = style.drum_hits_strong
        elif strength >= p50:
            drum_hits = style.drum_hits_medium
        else:
            drum_hits = style.drum_hits_weak

        for pitch, hit_duration in drum_hits:
            end_time = min(start_time + hit_duration, TARGET_MUSIC_DURATION_SEC)
            if end_time <= start_time:
                continue
            drum.notes.append(
                pretty_midi.Note(
                    velocity=velocity_clamped,
                    pitch=pitch,
                    start=float(start_time),
                    end=float(end_time),
                )
            )
        last_event_time = start_time
        event_count += 1

    if event_count == 0:
        print("警告: 事件都超出音樂時間範圍，將略過鼓組軌")
        return None, 0

    return drum, event_count


def build_relaxation_piano_track(
    envelope: NDArray[np.float64],
    sampling_rate: float,
    total_source_seconds: float,
    style: StyleConfig,
) -> tuple[pretty_midi.Instrument, int]:
    piano = pretty_midi.Instrument(program=style.piano_program, name="Relaxation Piano")

    smooth_env = np.asarray(envelope, dtype=np.float64).copy()

    first_window = min(
        501, smooth_env.size if smooth_env.size % 2 == 1 else smooth_env.size - 1
    )
    if first_window >= 5:
        smooth_env = cast(
            NDArray[np.float64],
            savgol_filter(
                smooth_env, window_length=first_window, polyorder=2, mode="interp"
            ),
        )

    source_to_music = TARGET_MUSIC_DURATION_SEC / total_source_seconds
    music_to_source = total_source_seconds / TARGET_MUSIC_DURATION_SEC
    quake_start_source = QUIET_ZONE_END * music_to_source
    quake_end_source = PHASE_2_END * music_to_source
    quake_start_idx = max(0, int(round(quake_start_source * sampling_rate)))
    quake_end_idx = min(smooth_env.size, int(round(quake_end_source * sampling_rate)))
    quake_segment = smooth_env[quake_start_idx:quake_end_idx]
    second_window = min(
        2001,
        quake_segment.size if quake_segment.size % 2 == 1 else quake_segment.size - 1,
    )
    if second_window >= 5 and quake_segment.size > 0:
        smooth_env[quake_start_idx:quake_end_idx] = cast(
            NDArray[np.float64],
            savgol_filter(
                quake_segment, window_length=second_window, polyorder=2, mode="interp"
            ),
        )

    note_rate = style.bpm / 60.0
    target_note_count = max(int(TARGET_MUSIC_DURATION_SEC * note_rate), 1)
    sample_indices = np.linspace(
        0, smooth_env.size - 1, num=target_note_count, dtype=np.int64
    )
    sampled_env = smooth_env[sample_indices]

    q05 = float(np.percentile(sampled_env, 5))
    q95 = float(np.percentile(sampled_env, 95))
    env_for_map = np.clip(sampled_env, q05, q95)
    env_norm = normalize_array(env_for_map)

    trigger_threshold = float(np.mean(env_norm) + 1.5 * np.std(env_norm))
    env_std = float(np.std(env_norm))
    if env_std < 1e-6:
        return piano, 0
    max_scale_index = min(4, len(style.scale) - 1)

    note_count = 0
    next_allowed_time = 0.0
    for idx, source_index in enumerate(sample_indices):
        source_time = float(source_index) / sampling_rate
        start_time = source_time * source_to_music
        if start_time < next_allowed_time:
            continue

        level = float(env_norm[idx])
        if level < trigger_threshold:
            continue

        duration = map_range(level, 0.0, 1.0, 5.0, 2.0)
        end_time = min(start_time + duration, TARGET_MUSIC_DURATION_SEC)
        if end_time <= start_time:
            continue

        pitch_idx = int(round(level * max_scale_index))
        pitch_idx = max(0, min(pitch_idx + random.randint(-1, 1), max_scale_index))
        velocity = int(
            round(
                map_range(
                    level,
                    0.0,
                    1.0,
                    float(style.velocity_min),
                    float(style.velocity_max),
                )
            )
        )

        piano.notes.append(
            pretty_midi.Note(
                velocity=int(np.clip(velocity, 1, 127)),
                pitch=style.scale[pitch_idx],
                start=float(start_time),
                end=float(end_time),
            )
        )
        note_count += 1
        next_allowed_time = start_time + 5.0

    return piano, note_count


def build_relaxation_pad_track(
    weather_rows: list[WeatherRow],
    style: StyleConfig,
) -> tuple[pretty_midi.Instrument, int]:
    pad = pretty_midi.Instrument(program=style.pad_program, name="Relaxation Pad")

    RELAX_CHORDS: list[list[int]] = [
        [48, 55, 60],
        [48, 50, 55],
        [48, 53, 55],
        [48, 55, 59],
        [45, 52, 57],
    ]

    grouped_rows: list[list[WeatherRow]] = []
    for index in range(0, len(weather_rows), 2):
        grouped_rows.append(weather_rows[index : index + 2])

    grouped_pressures = np.array(
        [
            float(np.mean([row.pressure for row in row_group]))
            for row_group in grouped_rows
            if row_group
        ],
        dtype=np.float64,
    )
    pressures_norm = normalize_array(grouped_pressures)

    wind_speeds = np.array([row.wind_speed for row in weather_rows], dtype=np.float64)
    wind_min = float(np.min(wind_speeds))
    wind_max = float(np.max(wind_speeds))

    chord_note_count = 0
    for group_index, row_group in enumerate(grouped_rows):
        if not row_group:
            continue

        start_hour = row_group[0].obs_time
        start_time = start_hour * SECONDS_PER_HOUR_IN_MUSIC
        end_time = min(
            start_time + (2.0 * SECONDS_PER_HOUR_IN_MUSIC) + 3.0,
            TARGET_MUSIC_DURATION_SEC,
        )
        if end_time <= start_time:
            continue

        pressure_bucket = int(min(float(pressures_norm[group_index]) * 5.0, 4.0))
        chord = RELAX_CHORDS[pressure_bucket]

        avg_temp = float(np.mean([row.temperature for row in row_group]))
        avg_wind = float(np.mean([row.wind_speed for row in row_group]))
        if avg_temp < 7.0:
            chord = [pitch - 12 for pitch in chord]

        velocity = map_range(
            avg_wind,
            wind_min,
            wind_max,
            float(style.pad_velocity_min),
            float(style.pad_velocity_max),
        )

        hour_index = float(start_hour)
        if hour_index <= 7.0:
            intro_progress = map_range(hour_index, 0.0, 7.0, 0.0, 1.0)
            intro_floor = max(15.0, float(style.pad_velocity_min) * 0.5)
            velocity = map_range(intro_progress, 0.0, 1.0, intro_floor, velocity)
        elif hour_index >= 17.0:
            decay_progress = map_range(hour_index, 17.0, 23.0, 0.0, 1.0)
            decay_floor = max(18.0, float(style.pad_velocity_min) * 0.6)
            velocity = map_range(decay_progress, 0.0, 1.0, velocity, decay_floor)

        velocity_clamped = int(
            np.clip(round(velocity), style.pad_velocity_min, style.pad_velocity_max)
        )
        for pitch in chord:
            pad.notes.append(
                pretty_midi.Note(
                    velocity=velocity_clamped,
                    pitch=int(pitch),
                    start=float(start_time),
                    end=float(end_time),
                )
            )
            chord_note_count += 1

    return pad, chord_note_count


def build_relaxation_drone_track(
    weather_rows: list[WeatherRow],
    style: StyleConfig,
) -> tuple[pretty_midi.Instrument, int]:
    drone = pretty_midi.Instrument(program=DRONE_PROGRAM, name="Relaxation Drone")

    RELAX_CHORDS: list[list[int]] = [
        [48, 55, 60],
        [48, 50, 55],
        [48, 53, 55],
        [48, 55, 59],
        [45, 52, 57],
    ]

    grouped_rows: list[list[WeatherRow]] = []
    for index in range(0, len(weather_rows), 2):
        grouped_rows.append(weather_rows[index : index + 2])

    grouped_pressures = np.array(
        [
            float(np.mean([row.pressure for row in row_group]))
            for row_group in grouped_rows
            if row_group
        ],
        dtype=np.float64,
    )
    pressures_norm = normalize_array(grouped_pressures)

    note_count = 0
    for group_index, row_group in enumerate(grouped_rows):
        if not row_group:
            continue

        start_hour = row_group[0].obs_time
        start_time = start_hour * SECONDS_PER_HOUR_IN_MUSIC
        if group_index + 1 < len(grouped_rows) and grouped_rows[group_index + 1]:
            next_start_hour = grouped_rows[group_index + 1][0].obs_time
            next_start_time = next_start_hour * SECONDS_PER_HOUR_IN_MUSIC
            end_time = min(next_start_time + 3.0, TARGET_MUSIC_DURATION_SEC)
        else:
            end_time = TARGET_MUSIC_DURATION_SEC

        if end_time <= start_time:
            continue

        pressure_bucket = int(min(float(pressures_norm[group_index]) * 5.0, 4.0))
        chord = RELAX_CHORDS[pressure_bucket]
        root_pitch = int(chord[0] - 24)

        drone.notes.append(
            pretty_midi.Note(
                velocity=style.pad_velocity_min,
                pitch=root_pitch,
                start=float(start_time),
                end=float(end_time),
            )
        )
        note_count += 1

    return drone, note_count


# --- Brainwave Entrainment ---
def apply_isochronic_modulation(
    audio: NDArray[np.float64],
    fs: int,
    entrainment_config: EntrainmentConfig,
) -> NDArray[np.float64]:
    if audio.size == 0:
        return audio

    num_samples = audio.shape[0]
    t = np.arange(num_samples, dtype=np.float64) / float(fs)
    depth = float(np.clip(entrainment_config.isochronic_depth, 0.0, 1.0))

    if np.isclose(
        entrainment_config.entrainment_freq_start,
        entrainment_config.entrainment_freq_end,
    ):
        phase = 2.0 * np.pi * float(entrainment_config.entrainment_freq_start) * t
    else:
        freq_array = np.linspace(
            float(entrainment_config.entrainment_freq_start),
            float(entrainment_config.entrainment_freq_end),
            num_samples,
            dtype=np.float64,
        )
        cycles = np.concatenate(([0.0], np.cumsum(freq_array[:-1] / float(fs))))
        phase = 2.0 * np.pi * cycles

    envelope = 1.0 - depth * (0.5 - 0.5 * np.cos(phase))
    if audio.ndim == 1:
        return cast(NDArray[np.float64], audio * envelope)
    return cast(NDArray[np.float64], audio * envelope[:, np.newaxis])


def generate_pink_noise_floor(
    duration_seconds: float,
    fs: int,
    volume: float = 0.03,
) -> NDArray[np.float64]:
    num_samples = int(duration_seconds * fs)
    if num_samples <= 0:
        return np.zeros(0, dtype=np.float64)

    rng = np.random.default_rng(seed=2024)
    white = rng.standard_normal(num_samples)

    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(len(white), d=1.0 / fs)
    freqs[0] = 1.0
    fft *= 1.0 / np.sqrt(freqs)
    pink = np.fft.irfft(fft, n=len(white))

    sos = butter(4, 200.0, btype="low", fs=fs, output="sos")
    pink = cast(NDArray[np.float64], sosfilt(sos, pink))

    peak = float(np.max(np.abs(pink)))
    if peak > 0.0:
        pink = pink / peak * volume

    t = np.arange(len(pink)) / fs
    lfo = 0.7 + 0.3 * np.sin(2.0 * np.pi * 0.1 * t)
    pink *= lfo
    return cast(NDArray[np.float64], pink)


def apply_reverb_tail(
    audio: NDArray[np.float64],
    fs: int,
    decay_seconds: float = 12.0,
) -> NDArray[np.float64]:
    if audio.size == 0:
        return audio

    ir_length = int(decay_seconds * fs)
    if ir_length <= 0:
        return audio

    ir = np.random.default_rng(seed=42).standard_normal(ir_length)
    decay_curve = np.exp(-3.0 * np.arange(ir_length) / ir_length)
    ir *= decay_curve

    ir_peak = float(np.max(np.abs(ir)))
    if ir_peak > 0.0:
        ir = ir / ir_peak

    sos = butter(2, 3000.0, btype="low", fs=fs, output="sos")
    ir = cast(NDArray[np.float64], sosfilt(sos, ir))

    wet = cast(NDArray[np.float64], fftconvolve(audio, ir, mode="full")[: audio.size])
    mix_ratio = 0.4
    result = (1.0 - mix_ratio) * audio + mix_ratio * wet
    return cast(NDArray[np.float64], result)


def synthesize_and_write_audio(
    midi: pretty_midi.PrettyMIDI,
    wav_path: Path,
    entrainment: EntrainmentConfig | None = None,
    is_relaxation: bool = False,
) -> None:
    if SF2_PATH.exists():
        print(f"使用 SoundFont: {SF2_PATH.name}")
        audio = midi.fluidsynth(fs=FS_WAV, synthesizer=str(SF2_PATH))
    else:
        print("警告: SoundFont 不存在，使用內建音色")
        audio = midi.synthesize(fs=FS_WAV)
    if audio.size == 0:
        raise ValueError("合成音訊為空")

    if is_relaxation:
        audio_f64 = np.asarray(audio, dtype=np.float64)
        audio_f64 = apply_reverb_tail(audio_f64, FS_WAV, decay_seconds=12.0)

        pink = generate_pink_noise_floor(
            duration_seconds=float(audio_f64.size) / float(FS_WAV),
            fs=FS_WAV,
            volume=0.03,
        )
        if pink.size > audio_f64.size:
            pink = pink[: audio_f64.size]
        elif pink.size < audio_f64.size:
            pink = np.pad(pink, (0, audio_f64.size - pink.size))

        audio_f64 += pink
        audio = audio_f64

    fade_in_samples = min(int(round(FADE_IN_SECONDS * FS_WAV)), audio.size)
    if fade_in_samples > 0:
        fade_in_curve = np.linspace(0.0, 1.0, num=fade_in_samples, endpoint=True)
        audio[:fade_in_samples] *= fade_in_curve

    fade_out_samples = min(int(round(FADE_OUT_SECONDS * FS_WAV)), audio.size)
    if fade_out_samples > 0:
        fade_out_curve = np.linspace(1.0, 0.0, num=fade_out_samples, endpoint=True)
        audio[-fade_out_samples:] *= fade_out_curve

    peak = float(np.max(np.abs(audio)))
    if peak > 0.0:
        audio = 0.98 * (audio / peak)

    if entrainment is not None:
        audio_f64 = np.asarray(audio, dtype=np.float64)
        audio_f64 = apply_isochronic_modulation(audio_f64, FS_WAV, entrainment)

        fade_in_n = min(int(round(FADE_IN_SECONDS * FS_WAV)), audio_f64.size)
        if fade_in_n > 0:
            audio_f64[:fade_in_n] *= np.linspace(0.0, 1.0, num=fade_in_n, endpoint=True)

        fade_out_n = min(int(round(FADE_OUT_SECONDS * FS_WAV)), audio_f64.size)
        if fade_out_n > 0:
            audio_f64[-fade_out_n:] *= np.linspace(
                1.0, 0.0, num=fade_out_n, endpoint=True
            )

        peak = float(np.max(np.abs(audio_f64)))
        if peak > 0.0:
            audio_f64 = 0.98 * (audio_f64 / peak)
        audio = audio_f64

    sf.write(str(wav_path), audio, FS_WAV)


def main() -> None:
    ensure_input_files()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    weather_rows = read_weather_csv(CSV_PATH)
    if len(weather_rows) < HOURS_PER_DAY:
        print(f"警告: 天氣資料少於 24 筆，實際筆數: {len(weather_rows)}")

    signal_data, sampling_rate = load_and_process_sac(SAC_PATH)
    total_source_seconds = len(signal_data) / sampling_rate
    if total_source_seconds <= 0.0:
        raise ValueError("無效的 SAC 時長")

    envelope = compute_envelope(signal_data)

    styles = [
        make_dark_ambient(),
        make_ethereal(),
        make_cinematic(),
        make_lofi_chill(),
        make_glitch(),
    ]

    def describe_track(track_name: str, instrument: pretty_midi.Instrument) -> str:
        notes = sorted(instrument.notes, key=lambda note: note.start)
        note_count = len(notes)
        if note_count == 0:
            return f"- {track_name}: notes=0"

        first_slice = notes[:5]
        last_slice = notes[-5:]
        first_start = first_slice[0].start
        first_end = first_slice[-1].end
        last_start = last_slice[0].start
        last_end = last_slice[-1].end
        return (
            f"- {track_name}: notes={note_count}, "
            f"first5={first_start:.2f}-{first_end:.2f}s, "
            f"last5={last_start:.2f}-{last_end:.2f}s"
        )

    for style in styles:
        print(f"\n{'=' * 50}")
        print(f"生成風格: {style.name}")
        print(f"{'=' * 50}")

        piano_track, piano_notes = build_piano_track(
            envelope,
            sampling_rate,
            total_source_seconds,
            style,
        )
        pad_track, pad_notes = build_pad_track(weather_rows, style)
        drum_track, detected_events = build_drum_track(
            signal_data,
            sampling_rate,
            total_source_seconds,
            style,
        )

        midi = pretty_midi.PrettyMIDI(initial_tempo=style.bpm)
        midi.instruments.append(piano_track)
        midi.instruments.append(pad_track)
        if drum_track is not None:
            midi.instruments.append(drum_track)

        midi_path = OUTPUT_DIR / f"{style.name}_hualien.mid"
        wav_path = OUTPUT_DIR / f"{style.name}_hualien.wav"

        midi.write(str(midi_path))
        synthesize_and_write_audio(midi, wav_path)

        print("完成輸出:")
        print(f"- MIDI: {midi_path}")
        print(f"- WAV:  {wav_path}")
        print(f"- Tempo (BPM): {style.bpm:.2f}")
        print(f"- Piano notes: {piano_notes}")
        print(f"- Pad notes: {pad_notes}")
        print(f"- Detected events: {detected_events}")
        print(f"- Music duration (sec): {TARGET_MUSIC_DURATION_SEC:.2f}")
        print(
            f"- Phase boundaries (sec): quiet_end={QUIET_ZONE_END:.2f}, quake={EARTHQUAKE_MUSIC_TIME:.2f}, phase2_end={PHASE_2_END:.2f}"
        )
        print("MIDI diagnostics:")
        print(describe_track("Piano", piano_track))
        print(describe_track("Pad", pad_track))
        if drum_track is not None:
            print(describe_track("Drums", drum_track))
        else:
            print("- Drums: notes=0")

    relaxation_modes = [
        make_alpha_relax(),
        make_theta_meditation(),
        make_progressive_relax(),
    ]

    for style, entrainment in relaxation_modes:
        print(f"\n{'=' * 50}")
        print(f"生成放鬆模式: {style.name}")
        print(f"{'=' * 50}")

        piano_track, piano_notes = build_relaxation_piano_track(
            envelope,
            sampling_rate,
            total_source_seconds,
            style,
        )
        pad_track, pad_notes = build_relaxation_pad_track(weather_rows, style)
        drone_track, drone_notes = build_relaxation_drone_track(weather_rows, style)

        midi = pretty_midi.PrettyMIDI(initial_tempo=style.bpm)
        midi.instruments.append(piano_track)
        midi.instruments.append(pad_track)
        midi.instruments.append(drone_track)

        midi_path = OUTPUT_DIR / f"{style.name}_hualien.mid"
        wav_path = OUTPUT_DIR / f"{style.name}_hualien.wav"

        midi.write(str(midi_path))
        synthesize_and_write_audio(
            midi,
            wav_path,
            entrainment=entrainment,
            is_relaxation=True,
        )

        mode_name = (
            "固定頻率"
            if np.isclose(
                entrainment.entrainment_freq_start,
                entrainment.entrainment_freq_end,
            )
            else "掃頻"
        )

        print("完成輸出:")
        print(f"- MIDI: {midi_path}")
        print(f"- WAV:  {wav_path}")
        print(f"- Tempo (BPM): {style.bpm:.2f}")
        print(f"- Piano notes: {piano_notes}")
        print(f"- Pad notes: {pad_notes}")
        print(f"- Drone notes: {drone_notes}")
        print(f"- Music duration (sec): {TARGET_MUSIC_DURATION_SEC:.2f}")
        print(
            f"- Entrainment: {entrainment.entrainment_freq_start:.1f}->{entrainment.entrainment_freq_end:.1f} Hz, mode={mode_name}, isochronic_depth={entrainment.isochronic_depth:.2f}"
        )
        print("MIDI diagnostics:")
        print(describe_track("Piano", piano_track))
        print(describe_track("Pad", pad_track))
        print(describe_track("Drone", drone_track))
        print("- Drums: notes=0")


if __name__ == "__main__":
    main()
