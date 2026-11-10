"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useCallback, useState, useSyncExternalStore } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Pause,
  Play,
  RotateCcw,
  Box,
} from "lucide-react";

const Stage = dynamic(() => import("./voice-stage"), { ssr: false });
const mobileQuery = "(max-width: 700px)";
const motionQuery = "(prefers-reduced-motion: reduce)";
function subscribe(query: string, notify: () => void) {
  const media = window.matchMedia(query);
  media.addEventListener("change", notify);
  return () => media.removeEventListener("change", notify);
}
const subscribeMobile = (notify: () => void) => subscribe(mobileQuery, notify);
const subscribeMotion = (notify: () => void) => subscribe(motionQuery, notify);
const getMobile = () => window.matchMedia(mobileQuery).matches;
const getMotion = () => window.matchMedia(motionQuery).matches;
const serverSnapshot = () => true;

function Still() {
  // Fixed geometry: server/browser trig precision must never affect hydration.
  // Regenerate the original artwork with scripts/generate-voice-still.mjs.
  return (
    <Image
      className="voice-still"
      src="/voice-sculpture-still.svg"
      width={500}
      height={420}
      alt=""
      aria-hidden="true"
      unoptimized
      loading="eager"
    />
  );
}

/** A procedural art object. Never consumes or implies speaker/financial evidence. */
export default function VoiceSculpture() {
  const compact = useSyncExternalStore(
    subscribeMobile,
    getMobile,
    serverSnapshot,
  );
  const reduced = useSyncExternalStore(
    subscribeMotion,
    getMotion,
    serverSnapshot,
  );
  const [requested, setRequested] = useState(false);
  const [failed, setFailed] = useState(false);
  const [paused, setPaused] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [resetKey, setResetKey] = useState(0);
  const onFailure = useCallback(() => setFailed(true), []);
  const enabled = (!compact || requested) && !failed;
  return (
    <div
      className="voice-sculpture"
      data-motion={reduced || paused ? "paused" : "playing"}
    >
      <div className="sculpture-caption">
        <span className="sculpture-cross">+</span> VOICEFORM / GENERATIVE STUDY{" "}
        <span>01</span>
      </div>
      <div className="sculpture-stage">
        <Still />
        {enabled && (
          <Stage
            paused={paused || reduced}
            rotation={rotation}
            resetKey={resetKey}
            onFailure={onFailure}
            lowPower={compact}
          />
        )}
        <span className="sculpture-axis axis-x" aria-hidden="true">
          X —
        </span>
        <span className="sculpture-axis axis-y" aria-hidden="true">
          — Y
        </span>
      </div>
      <div className="sculpture-footer">
        <div>
          <strong>
            {failed
              ? "Static illustration"
              : enabled
                ? "Interactive 3D sculpture"
                : "Voice sculpture"}
          </strong>
          <span>
            {failed
              ? "WebGL unavailable. The workspace remains fully functional."
              : enabled
                ? "Drag to rotate · arrow keys also work"
                : "A lighter view for smaller screens"}
          </span>
        </div>
        {enabled ? (
          <div className="sculpture-controls" aria-label="Sculpture controls">
            <button
              type="button"
              aria-label="Rotate sculpture left"
              onClick={() => setRotation((x) => x - 0.4)}
            >
              <ArrowLeft size={15} />
            </button>
            <button
              type="button"
              aria-label={
                paused || reduced
                  ? "Play sculpture motion"
                  : "Pause sculpture motion"
              }
              disabled={reduced}
              aria-pressed={!paused && !reduced}
              title={
                reduced
                  ? "Motion disabled by your reduced-motion preference"
                  : undefined
              }
              onClick={() => setPaused((x) => !x)}
            >
              {paused || reduced ? <Play size={15} /> : <Pause size={15} />}
            </button>
            <button
              type="button"
              aria-label="Rotate sculpture right"
              onClick={() => setRotation((x) => x + 0.4)}
            >
              <ArrowRight size={15} />
            </button>
            <button
              type="button"
              aria-label="Reset sculpture view"
              onClick={() => {
                setRotation(0);
                setResetKey((x) => x + 1);
              }}
            >
              <RotateCcw size={15} />
            </button>
          </div>
        ) : (
          !failed && (
            <button
              className="sculpture-enable"
              type="button"
              onClick={() => setRequested(true)}
            >
              <Box size={15} /> Explore in 3D
            </button>
          )
        )}
      </div>
      <p className="sculpture-disclosure">
        Artwork only. Not a voiceprint, identity check or audio measurement.
      </p>
    </div>
  );
}
