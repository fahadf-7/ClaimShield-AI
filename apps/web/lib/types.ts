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

