"""Bounded MPEG Layer III framing checks, before Fish output reaches FFmpeg.

No tag text is decoded or retained. Decoding still must succeed with FFmpeg's
strict error handling; frame headers alone do not establish valid audio.
"""


def inspect_mp3(data, facts, reject):
    position = 0
    if data[:3] == b"ID3":
        if len(data) < 10 or data[3] not in (2, 3, 4) or any(x & 128 for x in data[6:10]):
            reject("MALFORMED_MP3_METADATA")
        size = sum(value << shift for value, shift in zip(data[6:10], (21, 14, 7, 0)))
        position = 10 + size + (10 if data[3] == 4 and data[5] & 16 else 0)
        if position > len(data):
            reject("TRUNCATED_MP3_METADATA")
    end = len(data)
    if data[end - 128 : end - 125] == b"TAG":
        end -= 128
    first = position
    frames = 0
    signature = None
    declared_frames = declared_bytes = None
    while position < end:
        if position + 4 > end:
            reject("TRUNCATED_MP3_FRAME")
        header = int.from_bytes(data[position : position + 4], "big")
        version, layer = (header >> 19) & 3, (header >> 17) & 3
        bitrate_index, rate_index = (header >> 12) & 15, (header >> 10) & 3
        if (
            header >> 21 != 0x7FF
            or version == 1
            or layer != 1
            or bitrate_index in (0, 15)
            or rate_index == 3
            or header & 3 == 2  # reserved emphasis
        ):
            reject("INVALID_MP3_ENCODING")
        rates = (44100, 48000, 32000)
        rate = rates[rate_index] // {3: 1, 2: 2, 0: 4}[version]
        channels = 1 if (header >> 6) & 3 == 3 else 2
        bitrates = (
            (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
            if version == 3
            else (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
        )
        length = (144000 if version == 3 else 72000) * bitrates[bitrate_index - 1] // rate
        length += (header >> 9) & 1
        if position + length > end:
            reject("TRUNCATED_MP3_FRAME")
        if signature is not None and signature != (version, rate, channels):
            reject("INCONSISTENT_MP3_FORMAT")
        signature = version, rate, channels
        if frames == 0:
            facts.update(sample_rate=rate, channels=channels, encoding="mpeg_layer_iii")
            # Xing/Info occupies the first MPEG frame after its side information.
            # Its frame count excludes this tag frame; byte count includes it.
            offset = (
                position
                + 4
                + ((17 if channels == 1 else 32) if version == 3 else (9 if channels == 1 else 17))
            )
            if data[offset : offset + 4] in (b"Xing", b"Info"):
                cursor = offset + 8
                if cursor > position + length:
                    reject("MALFORMED_MP3_INDEX")
                flags = int.from_bytes(data[offset + 4 : cursor], "big")
                for bit in (1, 2):
                    if flags & bit:
                        if cursor + 4 > position + length:
                            reject("MALFORMED_MP3_INDEX")
                        value = int.from_bytes(data[cursor : cursor + 4], "big")
                        if bit == 1:
                            declared_frames = value
                        else:
                            declared_bytes = value
                        cursor += 4
            elif data[position + 36 : position + 40] == b"VBRI":
                if length < 54 or data[position + 40 : position + 42] != b"\x00\x01":
                    reject("MALFORMED_MP3_INDEX")
                declared_bytes = int.from_bytes(data[position + 46 : position + 50], "big")
                # VBRI counts its containing audio frame, unlike Xing.
                declared_frames = int.from_bytes(data[position + 50 : position + 54], "big") - 1
        frames += 1
        position += length
    if signature is None or frames < 2:
        reject("MISSING_AUDIO_SAMPLES")
    facts.update(mpeg_frames=frames, observed_mpeg_bytes=end - first)
    if declared_frames is not None:
        facts["declared_mpeg_frames"] = declared_frames
        if declared_frames != frames - 1:
            reject("MP3_FRAME_COUNT_MISMATCH")
    if declared_bytes is not None:
        facts["declared_mpeg_bytes"] = declared_bytes
        if declared_bytes != end - first:
            reject("MP3_BYTE_COUNT_MISMATCH")
    # Duration before decoder priming/end-padding removal, not billable speech.
    facts["duration_seconds"] = round(frames * (1152 if version == 3 else 576) / rate, 6)
    facts["length_mode"] = "indexed_mp3" if declared_frames is not None else "unindexed_mp3"
    return facts
