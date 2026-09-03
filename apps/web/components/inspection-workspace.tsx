"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileImage, LockKeyhole, RefreshCw, RotateCcw, Send, Trash2, UploadCloud } from "lucide-react";
import { FormEvent, useState } from "react";
import { LoadingBlock } from "@/components/loading-block";
import { StatusBadge } from "@/components/status-badge";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Inspection } from "@/lib/types";

const viewpoints = ["FRONT", "FRONT_LEFT", "LEFT", "REAR_LEFT", "REAR", "REAR_RIGHT", "RIGHT", "FRONT_RIGHT", "VIN", "PLATE", "ODOMETER", "DAMAGE_CLOSEUP", "UNKNOWN"];

export function InspectionWorkspace({ inspectionId }: { inspectionId: string }) {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [viewpoint, setViewpoint] = useState("FRONT");
  const inspection = useQuery({
    queryKey: ["inspection", inspectionId],
    queryFn: () => api<Inspection>(`/inspections/${inspectionId}`, { token }),
    enabled: Boolean(token && inspectionId),
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      return state === "PROCESSING" || state === "SUBMITTED" ? 1800 : false;
    },
  });
  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Choose an image first.");
      const body = new FormData();
      body.append("viewpoint", viewpoint);
      body.append("file", file);
      return api(`/inspections/${inspectionId}/media`, { token, method: "POST", body });
    },
    onSuccess: () => { setFile(null); queryClient.invalidateQueries({ queryKey: ["inspection", inspectionId] }); },
  });
  const submit = useMutation({
    mutationFn: () => api<Inspection>(`/inspections/${inspectionId}/submit`, { token, method: "POST", headers: { "Idempotency-Key": `web-submit-${inspectionId}` } }),
    onSuccess: (data) => { queryClient.setQueryData(["inspection", inspectionId], data); queryClient.invalidateQueries({ queryKey: ["claims"] }); queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }); },
  });
  const deleteMedia = useMutation({
    mutationFn: (mediaId: string) => api<void>(`/media/${mediaId}`, { token, method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspection", inspectionId] }),
  });
  const retryJob = useMutation({
    mutationFn: (jobId: string) => api(`/jobs/${jobId}/retry`, { token, method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspection", inspectionId] }),
  });

  function uploadFile(event: FormEvent) { event.preventDefault(); upload.mutate(); }
  if (inspection.isLoading) return <LoadingBlock count={4} />;
  if (inspection.error || !inspection.data) return <div className="error-box" role="alert">{readableError(inspection.error)}</div>;
  const item = inspection.data;
  const editable = item.status === "DRAFT";

  return <div className="stack">
    <div className="notice"><LockKeyhole size={20} aria-hidden="true" /><div><strong>Original evidence is private.</strong><div>Images can be removed while this inspection is a draft. Submission locks originals and validates them before damage analysis can begin.</div></div></div>
    <section className="card section-card">
      <div className="section-heading"><div><h2>{item.type.replaceAll("_", " ")} inspection</h2><span className="muted">Created {new Date(item.created_at).toLocaleString()}</span></div><StatusBadge value={item.status} /></div>
      {editable && <div className="section-body"><form className="form-grid" onSubmit={uploadFile}>
        {upload.error && <div className="error-box" role="alert">{readableError(upload.error)}</div>}
        <div className="form-columns">
          <div className="field"><label htmlFor="viewpoint">Viewpoint</label><select id="viewpoint" value={viewpoint} onChange={(event) => setViewpoint(event.target.value)}>{viewpoints.map((option) => <option key={option}>{option}</option>)}</select></div>
          <div className="field"><label htmlFor="evidence-file">Evidence image</label><input id="evidence-file" type="file" accept="image/jpeg,image/png,image/webp" required onChange={(event) => setFile(event.target.files?.[0] ?? null)} /><span className="field-hint">JPEG, PNG, or WebP · minimum 640×480 · maximum 15 MB</span></div>
        </div>
        <button className="button button-secondary" disabled={upload.isPending || !file}><UploadCloud size={18} aria-hidden="true" />{upload.isPending ? "Uploading…" : "Upload evidence"}</button>
      </form></div>}
    </section>

    <section className="card section-card">
      <div className="section-heading"><h2>Evidence files</h2><span className="muted">{item.media?.length ?? 0} uploaded</span></div>
      <div className="section-body">{deleteMedia.error && <div className="error-box" role="alert">{readableError(deleteMedia.error)}</div>}{item.media?.length ? <div className="media-list">{item.media.map((media) => <div className="media-item" key={media.id}><div className="user-row"><span className="empty-icon" style={{ width: 42, height: 42, margin: 0 }}><FileImage size={20} aria-hidden="true" /></span><div><strong>{media.filename}</strong><span>{media.viewpoint.replaceAll("_", " ")} · {media.width}×{media.height}</span></div></div><div className="user-row"><StatusBadge value={media.status} />{editable && <button className="button button-danger" aria-label={`Remove ${media.filename}`} disabled={deleteMedia.isPending} onClick={() => deleteMedia.mutate(media.id)}><Trash2 size={17} aria-hidden="true" /> Remove</button>}</div></div>)}</div> : <div className="empty-state" style={{ minHeight: 150 }}><div><span className="empty-icon"><FileImage aria-hidden="true" /></span><strong>No images uploaded</strong><p className="muted">Add at least one valid image before submission.</p></div></div>}</div>
    </section>

    {submit.error && <div className="error-box" role="alert">{readableError(submit.error)}</div>}
    {editable && <button className="button button-primary" disabled={submit.isPending || !item.media?.length} onClick={() => submit.mutate()}><Send size={18} aria-hidden="true" />{submit.isPending ? "Submitting…" : "Submit and lock evidence"}</button>}

    {!editable && <section className="card section-card"><div className="section-heading"><h2>Validation jobs</h2><button className="button button-secondary" onClick={() => inspection.refetch()}><RefreshCw size={17} aria-hidden="true" /> Refresh</button></div><div className="section-body">{retryJob.error && <div className="error-box" role="alert">{readableError(retryJob.error)}</div>}<div className="media-list">{item.jobs?.map((job) => <div className="job-item" key={job.id}><div><strong>{job.type.replaceAll("_", " ")}</strong><span>{job.error_message ?? (job.state === "SUCCEEDED" ? String(job.result.message ?? "Validation completed") : `${job.progress}% complete`)}</span></div><div className="user-row"><StatusBadge value={job.state} />{job.state === "FAILED" && <button className="button button-secondary" disabled={retryJob.isPending} onClick={() => retryJob.mutate(job.id)}><RotateCcw size={17} aria-hidden="true" /> Retry</button>}</div></div>)}</div></div></section>}
  </div>;
}
