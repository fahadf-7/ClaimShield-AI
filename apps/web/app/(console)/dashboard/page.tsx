"use client";

import { useQuery } from "@tanstack/react-query";
import { CarFront, CircleDotDashed, ClipboardCheck, Clock3, Plus } from "lucide-react";
import Link from "next/link";
import { LoadingBlock } from "@/components/loading-block";
import { StatusBadge } from "@/components/status-badge";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Claim, DashboardSummary } from "@/lib/types";

export default function DashboardPage() {
  const { token } = useAuth();
  const summary = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => api<DashboardSummary>("/claims/dashboard/summary", { token }),
    enabled: Boolean(token),
  });
  const claims = useQuery({
    queryKey: ["claims", "recent"],
    queryFn: () => api<Claim[]>("/claims?limit=6", { token }),
    enabled: Boolean(token),
  });

  const cards = [
    { label: "Open claims", value: summary.data?.open_claims ?? 0, icon: CircleDotDashed },
    { label: "Evidence pending", value: summary.data?.evidence_pending ?? 0, icon: Clock3 },
    { label: "Completed reviews", value: summary.data?.completed ?? 0, icon: ClipboardCheck },
    { label: "Vehicles on record", value: summary.data?.vehicles ?? 0, icon: CarFront },
  ];

  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Operations overview</p>
          <h1>Evidence workspace</h1>
          <p>Track submitted evidence and open each inspection to run versioned, reviewer-correctable damage analysis.</p>
        </div>
        <Link className="button button-primary" href="/claims">
          <Plus size={18} aria-hidden="true" /> New claim
        </Link>
      </div>

      {summary.isLoading ? (
        <LoadingBlock count={4} />
      ) : summary.error ? (
        <div className="error-box" role="alert">{readableError(summary.error)}</div>
      ) : (
        <section className="kpi-grid" aria-label="Claim overview">
          {cards.map(({ label, value, icon: Icon }) => (
            <article className="card kpi-card" key={label}>
              <span className="kpi-label"><Icon size={17} aria-hidden="true" /> {label}</span>
              <strong className="kpi-value">{value}</strong>
            </article>
          ))}
        </section>
      )}

      <div className="content-grid">
        <section className="card section-card">
          <div className="section-heading">
            <h2>Recent claims</h2>
            <Link className="primary-link" href="/claims">View all</Link>
          </div>
          {claims.isLoading ? (
            <div className="section-body"><LoadingBlock count={3} /></div>
          ) : claims.error ? (
            <div className="section-body"><div className="error-box" role="alert">{readableError(claims.error)}</div></div>
          ) : claims.data?.length ? (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Claim</th><th>Incident</th><th>Status</th><th>Location</th></tr></thead>
                <tbody>
                  {claims.data.map((claim) => (
                    <tr key={claim.id}>
                      <td><Link className="primary-link" href={`/claims/${claim.id}`}>{claim.claim_number}</Link></td>
                      <td>{new Date(claim.incident_date).toLocaleDateString()}</td>
                      <td><StatusBadge value={claim.status} /></td>
                      <td>{claim.incident_location ?? "Not provided"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state"><div><span className="empty-icon"><ClipboardCheck aria-hidden="true" /></span><strong>No claims yet</strong><p className="muted">Create a vehicle and policy, then add the first claim.</p></div></div>
          )}
        </section>

        <aside className="card section-card">
          <div className="section-heading"><h2>Phase 1 workflow</h2></div>
          <div className="section-body">
            <div className="timeline">
              <div className="timeline-item"><strong>1. Register vehicle</strong><span>Capture policy-linked identity details.</span></div>
              <div className="timeline-item"><strong>2. Create policy</strong><span>Define the covered vehicle and period.</span></div>
              <div className="timeline-item"><strong>3. Open claim</strong><span>Record incident context and status.</span></div>
              <div className="timeline-item"><strong>4. Submit inspection</strong><span>Upload immutable evidence and observe validation.</span></div>
              <div className="timeline-item"><strong>5. Analyze and review</strong><span>Inspect overlays, confidence, severity, and correction history.</span></div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
