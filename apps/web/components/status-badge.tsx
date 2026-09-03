import { Circle } from "lucide-react";

const success = new Set(["ACTIVE", "READY", "SUCCEEDED", "COMPLETED", "LOCKED", "MINOR"]);
const warning = new Set(["EVIDENCE_PENDING", "REVIEW_PENDING", "QUEUED", "DRAFT", "PARTIAL", "MODERATE"]);
const info = new Set(["PROCESSING", "RUNNING", "SUBMITTED", "UPLOADED"]);
const danger = new Set(["FAILED", "CANCELLED", "INVALID", "SEVERE"]);

export function StatusBadge({ value }: { value: string }) {
  const tone = success.has(value)
    ? "success"
    : warning.has(value)
      ? "warning"
      : info.has(value)
        ? "info"
        : danger.has(value)
          ? "danger"
          : "neutral";
  return (
    <span className={`badge badge-${tone}`}>
      <Circle size={7} fill="currentColor" aria-hidden="true" />
      {value.replaceAll("_", " ")}
    </span>
  );
}
