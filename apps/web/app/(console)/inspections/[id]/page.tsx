"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { InspectionWorkspace } from "@/components/inspection-workspace";

export default function InspectionPage() {
  const { id } = useParams<{ id: string }>();
  const search = useSearchParams();
  const back = search.get("claim") ? `/claims/${search.get("claim")}` : search.get("vehicle") ? `/vehicles/${search.get("vehicle")}` : "/dashboard";
  return <div className="page"><div className="page-heading"><div><Link className="primary-link" href={back}><ArrowLeft size={16} aria-hidden="true" /> Back</Link><p className="eyebrow" style={{ marginTop: 18 }}>Evidence collection</p><h1>Inspection workspace</h1><p>Upload, verify, and submit original vehicle evidence.</p></div></div><InspectionWorkspace inspectionId={id} /></div>;
}

