"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Eye, Layers3, Play, RefreshCw, ScanSearch, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { FindingReviewForm } from "@/components/finding-review-form";
import { LoadingBlock } from "@/components/loading-block";
import { ProtectedImage } from "@/components/protected-image";
import { StatusBadge } from "@/components/status-badge";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AnalysisResult, AnalysisRun } from "@/lib/types";

function percent(value: number | null) {
  return value === null ? "UNKNOWN" : `${(value * 100).toFixed(1)}%`;
}

export function DamageAnalysisWorkspace({ inspectionId, inspectionStatus }: { inspectionId: string; inspectionStatus: string }) {
  const { token, user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedRunId, setSelectedRunId] = useState("");
  const [selectedMediaId, setSelectedMediaId] = useState("");
  const [showParts, setShowParts] = useState(true);
  const [showDamage, setShowDamage] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showConfidence, setShowConfidence] = useState(true);
  const [reviewFinding, setReviewFinding] = useState<{ type: "PART" | "DAMAGE"; id: string } | null>(null);
  const runs = useQuery({
    queryKey: ["analysis-runs", inspectionId],
    queryFn: () => api<AnalysisRun[]>(`/inspections/${inspectionId}/analysis`, { token }),
    enabled: Boolean(token),
    refetchInterval: (query) => query.state.data?.some((run) => ["QUEUED", "RUNNING"].includes(run.state)) ? 1800 : false,
  });
  const effectiveRunId = selectedRunId || runs.data?.[0]?.id || "";
  const result = useQuery({
    queryKey: ["analysis-result", effectiveRunId],
    queryFn: () => api<AnalysisResult>(`/analysis/${effectiveRunId}`, { token }),
    enabled: Boolean(token && effectiveRunId),
    refetchInterval: (query) => ["QUEUED", "RUNNING"].includes(query.state.data?.run.state ?? "") ? 1800 : false,
  });
  const start = useMutation({
    mutationFn: () => api<{ run: AnalysisRun; job_id: string }>(`/inspections/${inspectionId}/analysis`, {
      token,
      method: "POST",
      headers: { "Idempotency-Key": `web-analysis-${inspectionId}-${Date.now()}` },
    }),
    onSuccess: (data) => {
      setSelectedRunId(data.run.id);
      queryClient.invalidateQueries({ queryKey: ["analysis-runs", inspectionId] });
    },
  });
  const effectiveMediaId = result.data?.media.some((item) => item.id === selectedMediaId)
    ? selectedMediaId
    : result.data?.media[0]?.id ?? "";
  const selectedMedia = result.data?.media.find((item) => item.id === effectiveMediaId);
  const selectedArtifacts = result.data?.artifacts.filter((item) => item.media_id === effectiveMediaId) ?? [];
  const parts = result.data?.parts.filter((item) => item.media_id === effectiveMediaId) ?? [];
  const damages = result.data?.damages.filter((item) => item.media_id === effectiveMediaId) ?? [];
  const partOverlay = selectedArtifacts.find((item) => item.artifact_type === "PARTS_OVERLAY");
  const damageOverlay = selectedArtifacts.find((item) => item.artifact_type === "DAMAGE_OVERLAY");
  const workingSize = partOverlay ?? damageOverlay;
  const latestCorrections = useMemo(() => {
    const byFinding = new Map<string, AnalysisResult["corrections"][number]>();
    for (const correction of result.data?.corrections ?? []) {
      const current = byFinding.get(correction.finding_id);
      if (!current || correction.version > current.version) byFinding.set(correction.finding_id, correction);
    }
    return byFinding;
  }, [result.data?.corrections]);
  const selectedPart = reviewFinding?.type === "PART" ? parts.find((item) => item.id === reviewFinding.id) : undefined;
  const selectedDamage = reviewFinding?.type === "DAMAGE" ? damages.find((item) => item.id === reviewFinding.id) : undefined;
  const canReview = user?.role === "ADMIN" || user?.role === "REVIEWER";

  return (
    <section className="card section-card analysis-section">
      <div className="section-heading">
        <div>
          <h2>Damage intelligence</h2>
          <span className="muted">Versioned part and visible exterior-damage findings</span>
        </div>
        <div className="user-row">
          <button className="button button-secondary" type="button" onClick={() => { runs.refetch(); result.refetch(); }}>
            <RefreshCw size={17} aria-hidden="true" /> Refresh
          </button>
          {canReview && <button className="button button-primary" type="button" disabled={inspectionStatus !== "READY" || start.isPending || runs.data?.some((run) => ["QUEUED", "RUNNING"].includes(run.state))} onClick={() => start.mutate()}>
            <Play size={17} aria-hidden="true" /> {start.isPending ? "Starting…" : runs.data?.length ? "Run new version" : "Start analysis"}
          </button>}
        </div>
      </div>
      <div className="section-body stack">
        <div className="notice">
          <ShieldCheck size={20} aria-hidden="true" />
          <div><strong>Human review required.</strong><div>Findings describe visible image regions only. They do not determine claim validity, repair cost, structural damage, or fraud.</div></div>
        </div>
        {start.error && <div className="error-box" role="alert">{readableError(start.error)}</div>}
        {runs.error && <div className="error-box" role="alert">{readableError(runs.error)}</div>}
        {runs.isLoading && <LoadingBlock count={2} />}
        {!runs.isLoading && !runs.data?.length && <div className="analysis-empty"><ScanSearch size={28} aria-hidden="true" /><div><strong>No analysis version yet</strong><p>Submit and validate the inspection, then start a versioned analysis run.</p></div></div>}
        {!!runs.data?.length && (
          <div className="analysis-run-bar">
            <div className="field">
              <label htmlFor="analysis-version">Analysis version</label>
              <select id="analysis-version" value={effectiveRunId} onChange={(event) => { setSelectedRunId(event.target.value); setReviewFinding(null); }}>
                {runs.data.map((run) => <option key={run.id} value={run.id}>Version {run.version} · {run.state}</option>)}
              </select>
            </div>
            {result.data?.run && <div className="analysis-run-meta"><StatusBadge value={result.data.run.state} /><span>{result.data.run.pipeline_version}</span><span>{result.data.run.device ?? "Device pending"}</span></div>}
          </div>
        )}
        {result.isLoading && <LoadingBlock count={4} />}
        {result.error && <div className="error-box" role="alert">{readableError(result.error)}</div>}
        {result.data && (
          <>
            {result.data.models.some((model) => model.is_experimental) && <div className="warning-box" role="status"><AlertTriangle size={19} aria-hidden="true" /><span>Experimental baseline: verify every mask and finding. Fixture-adapter results are evaluation-only and real-photo accuracy is not implied.</span></div>}
            {result.data.run.error_message && <div className="error-box" role="alert">{result.data.run.error_message}</div>}
            {!!result.data.run.warnings_json.length && <div className="warning-list"><strong>Uncertainty and partial-result notes</strong><ul>{result.data.run.warnings_json.map((warning) => <li key={warning}>{warning}</li>)}</ul></div>}
            {!!result.data.media.length && selectedMedia && (
              <div className="analysis-viewer-grid">
                <div className="stack">
                  <div className="analysis-toolbar" aria-label="Analysis viewer controls">
                    <div className="field compact-field"><label htmlFor="analysis-media">Source image</label><select id="analysis-media" value={effectiveMediaId} onChange={(event) => { setSelectedMediaId(event.target.value); setReviewFinding(null); }}>{result.data.media.map((item) => <option value={item.id} key={item.id}>{item.filename} · {item.viewpoint.replaceAll("_", " ")}</option>)}</select></div>
                    <label className="toggle-control"><input type="checkbox" checked={showParts} onChange={(event) => setShowParts(event.target.checked)} /> Parts</label>
                    <label className="toggle-control"><input type="checkbox" checked={showDamage} onChange={(event) => setShowDamage(event.target.checked)} /> Damage</label>
                    <label className="toggle-control"><input type="checkbox" checked={showLabels} onChange={(event) => setShowLabels(event.target.checked)} /> Labels</label>
                    <label className="toggle-control"><input type="checkbox" checked={showConfidence} onChange={(event) => setShowConfidence(event.target.checked)} /> Confidence</label>
                  </div>
                  <div className="analysis-image-frame" style={{ aspectRatio: `${workingSize?.width ?? selectedMedia.width} / ${workingSize?.height ?? selectedMedia.height}` }}>
                    <ProtectedImage path={selectedMedia.original_url} token={token!} alt={`Original evidence: ${selectedMedia.filename}, ${selectedMedia.viewpoint.replaceAll("_", " ")} view`} priority />
                    {showParts && partOverlay && <ProtectedImage path={`/analysis/artifacts/${partOverlay.id}`} token={token!} alt="" className="analysis-mask-layer" />}
                    {showDamage && damageOverlay && <ProtectedImage path={`/analysis/artifacts/${damageOverlay.id}`} token={token!} alt="" className="analysis-mask-layer" />}
                    {showLabels && [...(showParts ? parts : []), ...(showDamage ? damages : [])].slice(0, 16).map((finding) => {
                      const box = finding.bbox_json;
                      if (box.length !== 4 || !workingSize) return null;
                      const isDamage = "severity" in finding;
                      return <span className={`analysis-label ${isDamage ? "damage-label" : "part-label"}`} style={{ left: `${(box[0] / workingSize.width) * 100}%`, top: `${(box[1] / workingSize.height) * 100}%` }} key={`${isDamage ? "damage" : "part"}-${finding.id}`}>{finding.class_name.replaceAll("_", " ")}{showConfidence ? ` · ${Math.round(finding.confidence * 100)}%` : ""}</span>;
                    })}
                  </div>
                  <p className="muted analysis-caption"><Eye size={15} aria-hidden="true" /> Overlay geometry is derived from this source image and analysis version.</p>
                </div>
                <aside className="analysis-summary card">
                  <h3>Version evidence</h3>
                  <dl><div><dt>Parts</dt><dd>{parts.length || "UNKNOWN"}</dd></div><div><dt>Damage regions</dt><dd>{damages.length || "None detected"}</dd></div><div><dt>Runtime</dt><dd>{result.data.run.timings_json.total_seconds ?? "—"}s</dd></div><div><dt>Thresholds</dt><dd>{result.data.run.threshold_version}</dd></div></dl>
                  {result.data.models.map((model) => <div className="model-card" key={model.id}><strong>{model.task.replaceAll("_", " ")}</strong><span>{model.name} · {model.version}</span><span>Checksum {model.weights_checksum.slice(0, 12)}…</span><span>{model.license}</span></div>)}
                </aside>
              </div>
            )}
            <div className="stack">
              <div><h3 className="analysis-subheading">Visible damage findings</h3><p className="muted">Coverage is intersection area divided by the visible part-mask area.</p></div>
              {damages.length ? <div className="table-wrap"><table><thead><tr><th>Source image</th><th>Part</th><th>Damage</th><th>Rule severity</th><th>Coverage</th><th>Confidence</th><th>Review</th></tr></thead><tbody>{damages.map((finding) => { const part = parts.find((item) => item.id === finding.vehicle_part_detection_id); const correction = latestCorrections.get(finding.id); return <tr key={finding.id}><td>{selectedMedia?.filename ?? "UNKNOWN"}</td><td>{part?.class_name.replaceAll("_", " ") ?? "UNKNOWN"}</td><td><strong>{finding.class_name.replaceAll("_", " ")}</strong>{correction && <span className="review-state">{correction.action} v{correction.version}</span>}</td><td><StatusBadge value={finding.severity} /></td><td>{percent(finding.coverage)}</td><td>{Math.round(finding.confidence * 100)}%</td><td><button className="button button-secondary" type="button" onClick={() => setReviewFinding({ type: "DAMAGE", id: finding.id })}>Review</button></td></tr>; })}</tbody></table></div> : <div className="analysis-empty"><ScanSearch size={24} aria-hidden="true" /><div><strong>No supported damage detected</strong><p>This is not proof that the vehicle is undamaged. The result remains limited to submitted views.</p></div></div>}
              <div><h3 className="analysis-subheading">Visible part findings</h3><p className="muted">Part and damage labels remain independent.</p></div>
              {parts.length ? <div className="part-finding-grid">{parts.map((part) => { const correction = latestCorrections.get(part.id); return <div className="part-finding" key={part.id}><Layers3 size={18} aria-hidden="true" /><div><strong>{part.class_name.replaceAll("_", " ")}</strong><span>{Math.round(part.confidence * 100)}% confidence{correction ? ` · ${correction.action} v${correction.version}` : ""}</span></div><button className="button button-secondary" type="button" onClick={() => setReviewFinding({ type: "PART", id: part.id })}>Review</button></div>; })}</div> : <div className="analysis-empty"><ScanSearch size={24} aria-hidden="true" /><div><strong>Part assignment is UNKNOWN</strong><p>The image may not show enough compatible vehicle context.</p></div></div>}
              {canReview && selectedPart && <FindingReviewForm runId={result.data.run.id} findingType="PART" findingId={selectedPart.id} originalClass={selectedPart.class_name} taxonomy={result.data.taxonomy.parts} parts={parts} latestCorrection={latestCorrections.get(selectedPart.id)} token={token!} onClose={() => setReviewFinding(null)} />}
              {canReview && selectedDamage && <FindingReviewForm runId={result.data.run.id} findingType="DAMAGE" findingId={selectedDamage.id} originalClass={selectedDamage.class_name} originalSeverity={selectedDamage.severity} originalPartId={selectedDamage.vehicle_part_detection_id} taxonomy={result.data.taxonomy.damages} parts={parts} latestCorrection={latestCorrections.get(selectedDamage.id)} token={token!} onClose={() => setReviewFinding(null)} />}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
