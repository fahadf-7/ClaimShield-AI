"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Save, X } from "lucide-react";
import { FormEvent, useState } from "react";
import { api, readableError } from "@/lib/api";
import type { FindingCorrection, PartDetection } from "@/lib/types";

type FindingType = "PART" | "DAMAGE";

export function FindingReviewForm({
  runId,
  findingType,
  findingId,
  originalClass,
  originalSeverity,
  originalPartId,
  taxonomy,
  parts,
  latestCorrection,
  token,
  onClose,
}: {
  runId: string;
  findingType: FindingType;
  findingId: string;
  originalClass: string;
  originalSeverity?: string;
  originalPartId?: string | null;
  taxonomy: string[];
  parts: PartDetection[];
  latestCorrection?: FindingCorrection;
  token: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [action, setAction] = useState<"ACCEPT" | "REJECT" | "CORRECT">("ACCEPT");
  const [correctedClass, setCorrectedClass] = useState(originalClass);
  const [correctedSeverity, setCorrectedSeverity] = useState(originalSeverity ?? "UNKNOWN");
  const [correctedPart, setCorrectedPart] = useState(originalPartId ?? "");
  const [notes, setNotes] = useState("");
  const review = useMutation({
    mutationFn: () =>
      api<FindingCorrection>(`/analysis/findings/${findingType}/${findingId}/corrections`, {
        token,
        method: "POST",
        body: JSON.stringify({
          action,
          corrected_class: action === "CORRECT" ? correctedClass : null,
          corrected_part_detection_id:
            action === "CORRECT" && findingType === "DAMAGE" ? correctedPart || null : null,
          corrected_severity:
            action === "CORRECT" && findingType === "DAMAGE" ? correctedSeverity : null,
          notes,
        }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["analysis-result", runId] });
      onClose();
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    review.mutate();
  }

  return (
    <form className="finding-review-form" onSubmit={submit}>
      <div className="section-heading">
        <div>
          <h3>Review original {findingType.toLowerCase()} finding</h3>
          <span className="muted">The model output remains unchanged in history.</span>
        </div>
        <button className="button button-secondary" type="button" onClick={onClose}>
          <X size={17} aria-hidden="true" /> Close
        </button>
      </div>
      <div className="section-body form-grid">
        {latestCorrection && (
          <div className="notice" role="status">
            <Check size={18} aria-hidden="true" />
            <span>Latest review: {latestCorrection.action} · version {latestCorrection.version}</span>
          </div>
        )}
        {review.error && <div className="error-box" role="alert">{readableError(review.error)}</div>}
        <div className="form-columns">
          <div className="field">
            <label htmlFor={`action-${findingId}`}>Review action</label>
            <select id={`action-${findingId}`} value={action} onChange={(event) => setAction(event.target.value as typeof action)}>
              <option value="ACCEPT">Accept finding</option>
              <option value="REJECT">Reject finding</option>
              <option value="CORRECT">Correct finding</option>
            </select>
          </div>
          {action === "CORRECT" && (
            <div className="field">
              <label htmlFor={`class-${findingId}`}>Corrected class</label>
              <select id={`class-${findingId}`} value={correctedClass} onChange={(event) => setCorrectedClass(event.target.value)}>
                {taxonomy.map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}
              </select>
            </div>
          )}
          {action === "CORRECT" && findingType === "DAMAGE" && (
            <>
              <div className="field">
                <label htmlFor={`part-${findingId}`}>Corrected visible part</label>
                <select id={`part-${findingId}`} value={correctedPart} onChange={(event) => setCorrectedPart(event.target.value)}>
                  <option value="">Unknown / no reliable assignment</option>
                  {parts.map((part) => <option value={part.id} key={part.id}>{part.class_name.replaceAll("_", " ")} · {Math.round(part.confidence * 100)}%</option>)}
                </select>
              </div>
              <div className="field">
                <label htmlFor={`severity-${findingId}`}>Corrected rule severity</label>
                <select id={`severity-${findingId}`} value={correctedSeverity} onChange={(event) => setCorrectedSeverity(event.target.value)}>
                  {['UNKNOWN', 'MINOR', 'MODERATE', 'SEVERE'].map((item) => <option value={item} key={item}>{item}</option>)}
                </select>
              </div>
            </>
          )}
          <div className="field form-span">
            <label htmlFor={`notes-${findingId}`}>Reviewer notes</label>
            <textarea id={`notes-${findingId}`} maxLength={1000} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Explain acceptance, rejection, or correction." />
          </div>
        </div>
        <div className="form-actions">
          <button className="button button-primary" disabled={review.isPending} type="submit">
            <Save size={17} aria-hidden="true" /> {review.isPending ? "Saving…" : "Save review version"}
          </button>
        </div>
      </div>
    </form>
  );
}
