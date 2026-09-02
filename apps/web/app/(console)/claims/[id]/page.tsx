"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Camera, FileSearch, Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { LoadingBlock } from "@/components/loading-block";
import { StatusBadge } from "@/components/status-badge";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Claim, Inspection, Policy } from "@/lib/types";

export default function ClaimDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const claim = useQuery({ queryKey: ["claim", id], queryFn: () => api<Claim>(`/claims/${id}`, { token }), enabled: Boolean(token && id) });
  const inspections = useQuery({ queryKey: ["inspections", "claim", id], queryFn: () => api<Inspection[]>(`/inspections?claim_id=${id}`, { token }), enabled: Boolean(token && id) });
  const policy = useQuery({ queryKey: ["policy", claim.data?.policy_id], queryFn: () => api<Policy>(`/policies/${claim.data?.policy_id}`, { token }), enabled: Boolean(token && claim.data?.policy_id) });
  const createInspection = useMutation({
    mutationFn: () => api<Inspection>("/inspections", { token, method: "POST", body: JSON.stringify({ vehicle_id: policy.data?.vehicle_id, policy_id: claim.data?.policy_id, claim_id: id, type: "CLAIM" }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspections", "claim", id] }),
  });
  if (claim.isLoading) return <div className="page"><LoadingBlock count={4} /></div>;
  if (claim.error || !claim.data) return <div className="page"><div className="error-box" role="alert">{readableError(claim.error)}</div></div>;
  const item = claim.data;
  return <div className="page">
    <div className="page-heading"><div><Link className="primary-link" href="/claims"><ArrowLeft size={16} aria-hidden="true" /> Back to claims</Link><p className="eyebrow" style={{ marginTop: 18 }}>Claim record</p><h1>{item.claim_number}</h1><p>{new Date(item.incident_date).toLocaleString()} · {item.incident_location ?? "Location not provided"}</p></div><StatusBadge value={item.status} /></div>
    <div className="content-grid">
      <div className="stack"><section className="card section-card"><div className="section-heading"><h2>Incident description</h2></div><div className="section-body"><p style={{ margin: 0 }}>{item.description}</p><p className="muted">Stored as submitted. Narrative interpretation begins in Phase 6.</p></div></section>
      <section className="card section-card"><div className="section-heading"><h2>Claim inspections</h2><button className="button button-secondary" disabled={createInspection.isPending || !policy.data} onClick={() => createInspection.mutate()}><Plus size={17} aria-hidden="true" /> {createInspection.isPending ? "Creating…" : "New inspection"}</button></div><div className="section-body">{createInspection.error && <div className="error-box" role="alert">{readableError(createInspection.error)}</div>}{inspections.isLoading ? <LoadingBlock count={2} /> : inspections.data?.length ? <div className="media-list">{inspections.data.map((inspection) => <Link className="media-item" href={`/inspections/${inspection.id}?claim=${id}`} key={inspection.id}><div className="user-row"><span className="empty-icon" style={{ width: 42, height: 42, margin: 0 }}><Camera size={20} aria-hidden="true" /></span><div><strong>{inspection.type.replaceAll("_", " ")}</strong><span>Created {new Date(inspection.created_at).toLocaleString()}</span></div></div><StatusBadge value={inspection.status} /></Link>)}</div> : <div className="empty-state" style={{ minHeight: 170 }}><div><span className="empty-icon"><Camera aria-hidden="true" /></span><strong>No claim inspection</strong><p className="muted">Create one to upload and submit evidence.</p></div></div>}</div></section></div>
      <aside className="stack"><section className="card section-card"><div className="section-heading"><h2>Policy context</h2></div><div className="section-body compact-stack"><div><span className="muted">Policy</span><strong style={{ display: "block" }}>{policy.data?.policy_number ?? "Loading…"}</strong></div><div><span className="muted">Coverage</span><strong style={{ display: "block" }}>{policy.data ? `${new Date(policy.data.start_date).toLocaleDateString()} – ${new Date(policy.data.end_date).toLocaleDateString()}` : "—"}</strong></div></div></section><section className="card section-card"><div className="section-heading"><h2>Phase boundary</h2></div><div className="section-body"><div className="notice"><FileSearch size={20} aria-hidden="true" /><span>This phase validates the evidence workflow only. Damage, risk, and forensic findings are intentionally unavailable.</span></div></div></section></aside>
    </div>
  </div>;
}

