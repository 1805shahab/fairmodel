"use client";

import { useState, useRef, useCallback } from "react";
import { endpoint } from "./api";
import type { AudioResult } from "./types";

export default function RecordingPlayer({
  id,
  result,
  onPlayer,
  onSegment,
}: {
  id: string;
  result?: AudioResult;
  onPlayer: (node: HTMLAudioElement | null) => void;
  onSegment: (index: number) => void;
}) {
  const [time, setTime] = useState(0);
  const [mediaDuration, setMediaDuration] = useState(0);
  const [failed, setFailed] = useState(false);
  const player = useRef<HTMLAudioElement>(null);
  const connect = useCallback(
    (node: HTMLAudioElement | null) => {
      player.current = node;
      onPlayer(node);
    },
    [onPlayer],
  );
  const duration = Number(result?.duration_seconds) || mediaDuration;
  const segments =
    result?.speech_segments.filter(
      (s) =>
        Number.isFinite(s.start) &&
        Number.isFinite(s.end) &&
        s.start >= 0 &&
        s.end > s.start &&
        s.start < duration,
    ) || [];
  function sync() {
    const current = player.current?.currentTime || 0;
    setTime(current);
    onSegment(
      result?.timestamps.findIndex(
        (s) => current >= s.start && current < s.end,
      ) ?? -1,
    );
  }
  function seek(value: number) {
    if (!player.current || !duration) return;
    player.current.currentTime = Math.max(0, Math.min(duration, value));
    sync();
  }
  return (
    <div className="recording-controls">
      <audio
        ref={connect}
        aria-label="Submitted recording"
        controls
        preload="metadata"
        src={endpoint(`/assets/${id}/audio`)}
        onTimeUpdate={sync}
        onSeeked={sync}
        onLoadedMetadata={() => {
          setMediaDuration(
            Number.isFinite(player.current?.duration)
              ? player.current!.duration
              : 0,
          );
          setFailed(false);
        }}
        onError={() => setFailed(true)}
      >
        Your browser does not support audio playback.
      </audio>
      {failed && (
        <p className="alert warning" role="alert">
          Audio could not be loaded. Check the backend connection and reload
          this page.
        </p>
      )}
      {result && duration > 0 && (
        <div className="speech-timeline">
          <div className="speech-timeline-heading">
            <strong>Speech activity</strong>
            <span>
              <i aria-hidden="true" />
              {result.vad} intervals
            </span>
          </div>
          <div className="speech-track">
            <svg
              viewBox="0 0 1000 48"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <rect width="1000" height="48" rx="5" className="speech-ground" />
              {segments.map((s, i) => (
                <rect
                  key={i}
                  x={(s.start / duration) * 1000}
                  y="8"
                  width={
                    ((Math.min(duration, s.end) - s.start) / duration) * 1000
                  }
                  height="32"
                  rx="2"
                  className="speech-interval"
                />
              ))}
              <line
                x1={Math.min(time / duration, 1) * 1000}
                x2={Math.min(time / duration, 1) * 1000}
                y1="0"
                y2="48"
                className="speech-playhead"
              />
            </svg>
            <input
              type="range"
              min="0"
              max={duration}
              step="0.01"
              value={Math.min(time, duration)}
              aria-label="Seek recording"
              aria-valuetext={`${time.toFixed(2)} of ${duration.toFixed(2)} seconds`}
              disabled={failed}
              onChange={(e) => seek(Number(e.target.value))}
            />
          </div>
          <div className="speech-timeline-footer">
            <output aria-label="Playback position">
              {time.toFixed(2)}s / {duration.toFixed(2)}s
            </output>
            <label>
              Playback speed{" "}
              <select
                aria-label="Playback speed"
                defaultValue="1"
                onChange={(e) => {
                  if (player.current)
                    player.current.playbackRate = Number(e.target.value);
                }}
              >
                <option value="0.75">0.75×</option>
                <option value="1">1×</option>
                <option value="1.25">1.25×</option>
                <option value="1.5">1.5×</option>
                <option value="2">2×</option>
              </select>
            </label>
          </div>
          <p className="small">
            {segments.length
              ? "Colored intervals show measured speech activity, not a waveform or speaker identity. Drag or use arrow keys to seek."
              : "No usable speech intervals returned. The timeline shows recording position only."}
          </p>
        </div>
      )}
    </div>
  );
}
