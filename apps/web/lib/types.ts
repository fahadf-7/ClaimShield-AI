export type User = {
  id: string;
  organization_id: string;
  name: string;
  email: string;
  role: "ADMIN" | "REVIEWER" | "CLAIMANT";
  status: string;
};

export type Vehicle = {
  id: string;
  organization_id: string;
  registration_number: string;
  vin: string | null;
  make: string;
  model: string;
  year: number | null;
  color: string | null;
  created_at: string;
  updated_at: string;
};

export type Policy = {
  id: string;
  organization_id: string;
  vehicle_id: string;
  policy_number: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
};

export type Claim = {
  id: string;
  organization_id: string;
  policy_id: string;
  claim_number: string;
  incident_date: string;
  incident_location: string | null;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type MediaItem = {
  id: string;
  filename: string;
  viewpoint: string;
  status: string;
  width: number;
  height: number;
};

export type JobItem = {
  id: string;
  type: string;
  state: string;
  progress: number;
  error_message: string | null;
  result: Record<string, unknown>;
};

export type Inspection = {
  id: string;
  organization_id: string;
  vehicle_id: string;
  policy_id: string | null;
  claim_id: string | null;
  type: string;
  status: string;
  submitted_at: string | null;
  created_at: string;
  media?: MediaItem[];
  jobs?: JobItem[];
};

export type DashboardSummary = {
  open_claims: number;
  evidence_pending: number;
  processing: number;
  review_pending: number;
  completed: number;
  vehicles: number;
};

export type AnalysisRun = {
  id: string;
  inspection_id: string;
  job_id: string | null;
  version: number;
  state: "QUEUED" | "RUNNING" | "SUCCEEDED" | "PARTIAL" | "FAILED";
  pipeline_version: string;
  threshold_version: string;
  device: string | null;
  warnings_json: string[];
  timings_json: Record<string, number>;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type AnalysisModel = {
  id: string;
  task: string;
  name: string;
  version: string;
  adapter: string;
  weights_checksum: string;
  source: string;
  license: string;
  preprocessing_json: Record<string, unknown>;
  thresholds_json: Record<string, unknown>;
  class_mapping_json: Record<string, string>;
  is_experimental: boolean;
};

export type AnalysisArtifact = {
  id: string;
  media_id: string;
  artifact_type: string;
  content_type: string;
  width: number;
  height: number;
  sha256: string;
};

export type PartDetection = {
  id: string;
  media_id: string;
  model_version_id: string;
  class_name: string;
  confidence: number;
  mask_area: number;
  bbox_json: number[];
};

export type DamageDetection = {
  id: string;
  media_id: string;
  model_version_id: string;
  vehicle_part_detection_id: string | null;
  class_name: string;
  confidence: number;
  severity: string;
  coverage: number | null;
  intersection_area: number;
  region_count: number;
  bbox_json: number[];
  raw_output_json: {
    part_assignment?: { part_class?: string; reason?: string | null; overlap_fraction?: number };
    evaluation_only?: boolean;
  };
};

export type FindingCorrection = {
  id: string;
  analysis_run_id: string;
  finding_type: "PART" | "DAMAGE";
  finding_id: string;
  reviewer_id: string;
  action: "ACCEPT" | "REJECT" | "CORRECT";
  corrected_class: string | null;
  corrected_part_detection_id: string | null;
  corrected_severity: string | null;
  notes: string;
  version: number;
  created_at: string;
};

export type AnalysisMedia = {
  id: string;
  filename: string;
  viewpoint: string;
  width: number;
  height: number;
  original_url: string;
};

export type AnalysisResult = {
  run: AnalysisRun;
  models: AnalysisModel[];
  artifacts: AnalysisArtifact[];
  parts: PartDetection[];
  damages: DamageDetection[];
  corrections: FindingCorrection[];
  media: AnalysisMedia[];
  taxonomy: { parts: string[]; damages: string[] };
};
