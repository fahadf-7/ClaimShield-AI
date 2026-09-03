"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { DamageAnalysisWorkspace } from "@/components/damage-analysis-workspace";
import { InspectionWorkspace } from "@/components/inspection-workspace";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Inspection } from "@/lib/types";

export default function InspectionPage() {
  const { id } = useParams<{ id: string }>();
  const search = useSearchParams();
  const { token } = useAuth();
  const inspection = useQuery({ queryKey: ["inspection", id], queryFn: () => api<Inspection>(`/inspections/${id}`, { token }), enabled: Boolean(token && id) });
  const back = search.get("claim") ? `/claims/${search.get("claim")}` : search.get("vehicle") ? `/vehicles/${search.get("vehicle")}` : "/dashboard";
  return <div className="page"><div className="page-heading"><div><Link className="primary-link" href={back}><ArrowLeft size={16} aria-hidden="true" /> Back</Link><p className="eyebrow" style={{ marginTop: 18 }}>Evidence and analysis</p><h1>Inspection workspace</h1><p>Collect immutable evidence, run versioned damage analysis, and review every finding.</p></div></div><div className="stack"><InspectionWorkspace inspectionId={id} /><DamageAnalysisWorkspace inspectionId={id} inspectionStatus={inspection.data?.status ?? "LOADING"} /></div></div>;
}
