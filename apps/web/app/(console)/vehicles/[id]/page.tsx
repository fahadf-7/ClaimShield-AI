"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, CarFront, Plus } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { LoadingBlock } from "@/components/loading-block";
import { StatusBadge } from "@/components/status-badge";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Inspection, Vehicle } from "@/lib/types";

type History = { vehicle: Vehicle; policies: { id: string; policy_number: string; status: string }[]; claims: { id: string; claim_number: string; status: string }[]; inspections: { id: string; type: string; status: string; created_at: string }[] };

export default function VehicleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { token } = useAuth();
  const history = useQuery({ queryKey: ["vehicle-history", id], queryFn: () => api<History>(`/vehicles/${id}/history`, { token }), enabled: Boolean(token && id) });
  const createBaseline = useMutation({
    mutationFn: () => api<Inspection>("/inspections", {
      token,
      method: "POST",
      body: JSON.stringify({ vehicle_id: id, policy_id: history.data?.policies[0]?.id, claim_id: null, type: "POLICY_INCEPTION" }),
    }),
    onSuccess: (inspection) => router.push(`/inspections/${inspection.id}?vehicle=${id}`),
  });
  if (history.isLoading) return <div className="page"><LoadingBlock count={4} /></div>;
  if (history.error || !history.data) return <div className="page"><div className="error-box" role="alert">{readableError(history.error)}</div></div>;
  const { vehicle } = history.data;
  return <div className="page">
    <div className="page-heading"><div><Link className="primary-link" href="/vehicles"><ArrowLeft size={16} aria-hidden="true" /> Back to vehicles</Link><p className="eyebrow" style={{ marginTop: 18 }}>Vehicle history</p><h1>{vehicle.registration_number}</h1><p>{vehicle.year ?? "Year unknown"} {vehicle.make} {vehicle.model} · {vehicle.color ?? "Color not recorded"}</p></div><span className="empty-icon"><CarFront aria-hidden="true" /></span></div>
    <div className="content-grid">
      <section className="card section-card"><div className="section-heading"><h2>Evidence timeline</h2><button className="button button-secondary" disabled={createBaseline.isPending || !history.data.policies.length} onClick={() => createBaseline.mutate()}><Plus size={17} aria-hidden="true" /> {createBaseline.isPending ? "Creating…" : "New baseline"}</button></div><div className="section-body">{createBaseline.error && <div className="error-box" role="alert">{readableError(createBaseline.error)}</div>}{history.data.inspections.length ? <div className="timeline">{history.data.inspections.map((item) => <div className="timeline-item" key={item.id}><Link className="primary-link" href={`/inspections/${item.id}?vehicle=${id}`}>{item.type.replaceAll("_", " ")}</Link><span>{new Date(item.created_at).toLocaleString()} · {item.status}</span></div>)}</div> : <p className="muted">No inspections have been created for this vehicle.</p>}</div></section>
      <div className="stack"><section className="card section-card"><div className="section-heading"><h2>Policies</h2></div><div className="section-body compact-stack">{history.data.policies.length ? history.data.policies.map((item) => <div className="media-item" key={item.id}><strong>{item.policy_number}</strong><StatusBadge value={item.status} /></div>) : <p className="muted">Create a policy before starting a baseline inspection.</p>}</div></section><section className="card section-card"><div className="section-heading"><h2>Claims</h2></div><div className="section-body compact-stack">{history.data.claims.length ? history.data.claims.map((item) => <div className="media-item" key={item.id}><Link className="primary-link" href={`/claims/${item.id}`}>{item.claim_number}</Link><StatusBadge value={item.status} /></div>) : <p className="muted">No claims recorded.</p>}</div></section></div>
    </div>
  </div>;
}
