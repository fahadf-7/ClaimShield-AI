"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Plus, X } from "lucide-react";
import { FormEvent, useState } from "react";
import { LoadingBlock } from "@/components/loading-block";
import { StatusBadge } from "@/components/status-badge";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Policy, Vehicle } from "@/lib/types";

const emptyPolicy = { vehicle_id: "", policy_number: "", start_date: "", end_date: "", status: "ACTIVE" };

export default function PoliciesPage() {
  const { token, user } = useAuth();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState(emptyPolicy);
  const policies = useQuery({ queryKey: ["policies"], queryFn: () => api<Policy[]>("/policies", { token }), enabled: Boolean(token) });
  const vehicles = useQuery({ queryKey: ["vehicles"], queryFn: () => api<Vehicle[]>("/vehicles", { token }), enabled: Boolean(token) });
  const createPolicy = useMutation({
    mutationFn: () => api<Policy>("/policies", { token, method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["policies"] }); setForm(emptyPolicy); setCreating(false); },
  });
  const names = new Map(vehicles.data?.map((item) => [item.id, `${item.registration_number} · ${item.make} ${item.model}`]));
  const canCreate = user?.role === "ADMIN" || user?.role === "REVIEWER";
  function submit(event: FormEvent) { event.preventDefault(); createPolicy.mutate(); }

  return <div className="page">
    <div className="page-heading"><div><p className="eyebrow">Coverage registry</p><h1>Policies</h1><p>Connect each coverage period to one verified vehicle record.</p></div>{canCreate && <button className="button button-primary" onClick={() => setCreating((value) => !value)}>{creating ? <X size={18} aria-hidden="true" /> : <Plus size={18} aria-hidden="true" />}{creating ? "Close form" : "Add policy"}</button>}</div>
    {creating && <form className="create-panel form-grid" onSubmit={submit}>
      <div className="section-heading" style={{ padding: 0, border: 0 }}><h2>Create policy</h2></div>
      {createPolicy.error && <div className="error-box" role="alert">{readableError(createPolicy.error)}</div>}
      {!vehicles.data?.length && <div className="notice"><FileText size={19} aria-hidden="true" /><span>Add a vehicle before creating a policy.</span></div>}
      <div className="form-columns">
        <div className="field form-span"><label htmlFor="policy-vehicle">Vehicle</label><select id="policy-vehicle" required value={form.vehicle_id} onChange={(event) => setForm({ ...form, vehicle_id: event.target.value })}><option value="">Select a vehicle</option>{vehicles.data?.map((vehicle) => <option value={vehicle.id} key={vehicle.id}>{vehicle.registration_number} · {vehicle.make} {vehicle.model}</option>)}</select></div>
        <div className="field"><label htmlFor="policy-number">Policy number</label><input id="policy-number" required value={form.policy_number} onChange={(event) => setForm({ ...form, policy_number: event.target.value })} /></div>
        <div className="field"><label htmlFor="policy-status">Status</label><select id="policy-status" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>ACTIVE</option><option>DRAFT</option></select></div>
        <div className="field"><label htmlFor="policy-start">Start date</label><input id="policy-start" type="date" required value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} /></div>
        <div className="field"><label htmlFor="policy-end">End date</label><input id="policy-end" type="date" required value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} /></div>
      </div>
      <div className="form-actions"><button type="button" className="button button-secondary" onClick={() => setCreating(false)}>Cancel</button><button className="button button-primary" disabled={createPolicy.isPending || !vehicles.data?.length}>{createPolicy.isPending ? "Saving…" : "Save policy"}</button></div>
    </form>}
    <section className="card section-card">{policies.isLoading ? <div className="section-body"><LoadingBlock /></div> : policies.error ? <div className="section-body"><div className="error-box" role="alert">{readableError(policies.error)}</div></div> : policies.data?.length ? <div className="table-wrap"><table><thead><tr><th>Policy</th><th>Vehicle</th><th>Coverage</th><th>Status</th></tr></thead><tbody>{policies.data.map((policy) => <tr key={policy.id}><td><strong>{policy.policy_number}</strong></td><td>{names.get(policy.vehicle_id) ?? "Vehicle unavailable"}</td><td>{new Date(policy.start_date).toLocaleDateString()} – {new Date(policy.end_date).toLocaleDateString()}</td><td><StatusBadge value={policy.status} /></td></tr>)}</tbody></table></div> : <div className="empty-state"><div><span className="empty-icon"><FileText aria-hidden="true" /></span><strong>No policies</strong><p className="muted">Create a vehicle-linked policy to open claims.</p></div></div>}</section>
  </div>;
}

