"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardList, Plus, X } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { LoadingBlock } from "@/components/loading-block";
import { StatusBadge } from "@/components/status-badge";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Claim, Policy } from "@/lib/types";

const emptyClaim = { policy_id: "", claim_number: "", incident_date: "", incident_location: "", description: "", status: "EVIDENCE_PENDING" };

export default function ClaimsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState(emptyClaim);
  const claims = useQuery({ queryKey: ["claims"], queryFn: () => api<Claim[]>("/claims", { token }), enabled: Boolean(token) });
  const policies = useQuery({ queryKey: ["policies"], queryFn: () => api<Policy[]>("/policies", { token }), enabled: Boolean(token) });
  const createClaim = useMutation({
    mutationFn: () => api<Claim>("/claims", { token, method: "POST", body: JSON.stringify({ ...form, incident_date: new Date(form.incident_date).toISOString(), incident_location: form.incident_location || null }) }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["claims"] }); queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }); setForm(emptyClaim); setCreating(false); },
  });
  const policyNames = new Map(policies.data?.map((item) => [item.id, item.policy_number]));
  function submit(event: FormEvent) { event.preventDefault(); createClaim.mutate(); }

  return <div className="page">
    <div className="page-heading"><div><p className="eyebrow">Claim intake</p><h1>Claims</h1><p>Record incident context and move evidence through a visible review workflow.</p></div><button className="button button-primary" onClick={() => setCreating((value) => !value)}>{creating ? <X size={18} aria-hidden="true" /> : <Plus size={18} aria-hidden="true" />}{creating ? "Close form" : "New claim"}</button></div>
    {creating && <form className="create-panel form-grid" onSubmit={submit}>
      <div className="section-heading" style={{ padding: 0, border: 0 }}><h2>Open a claim</h2></div>
      {createClaim.error && <div className="error-box" role="alert">{readableError(createClaim.error)}</div>}
      <div className="form-columns">
        <div className="field"><label htmlFor="claim-policy">Policy</label><select id="claim-policy" required value={form.policy_id} onChange={(event) => setForm({ ...form, policy_id: event.target.value })}><option value="">Select a policy</option>{policies.data?.map((policy) => <option value={policy.id} key={policy.id}>{policy.policy_number}</option>)}</select></div>
        <div className="field"><label htmlFor="claim-number">Claim number</label><input id="claim-number" required value={form.claim_number} onChange={(event) => setForm({ ...form, claim_number: event.target.value })} /></div>
        <div className="field"><label htmlFor="incident-date">Incident date and time</label><input id="incident-date" type="datetime-local" required value={form.incident_date} onChange={(event) => setForm({ ...form, incident_date: event.target.value })} /></div>
        <div className="field"><label htmlFor="incident-location">Incident location</label><input id="incident-location" value={form.incident_location} onChange={(event) => setForm({ ...form, incident_location: event.target.value })} /></div>
        <div className="field form-span"><label htmlFor="description">Claimant description</label><textarea id="description" minLength={10} required value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /><span className="field-hint">Record the claimant’s own description. Phase 1 analyzes images only; narrative interpretation begins later.</span></div>
      </div>
      <div className="form-actions"><button type="button" className="button button-secondary" onClick={() => setCreating(false)}>Cancel</button><button className="button button-primary" disabled={createClaim.isPending || !policies.data?.length}>{createClaim.isPending ? "Creating…" : "Create claim"}</button></div>
    </form>}
    <section className="card section-card">{claims.isLoading ? <div className="section-body"><LoadingBlock /></div> : claims.error ? <div className="section-body"><div className="error-box" role="alert">{readableError(claims.error)}</div></div> : claims.data?.length ? <div className="table-wrap"><table><thead><tr><th>Claim</th><th>Policy</th><th>Incident</th><th>Status</th><th>Location</th></tr></thead><tbody>{claims.data.map((claim) => <tr key={claim.id}><td><Link className="primary-link" href={`/claims/${claim.id}`}>{claim.claim_number}</Link></td><td>{policyNames.get(claim.policy_id) ?? "—"}</td><td>{new Date(claim.incident_date).toLocaleString()}</td><td><StatusBadge value={claim.status} /></td><td>{claim.incident_location ?? "Not provided"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><div><span className="empty-icon"><ClipboardList aria-hidden="true" /></span><strong>No claims</strong><p className="muted">Create the first policy-linked claim.</p></div></div>}</section>
  </div>;
}
