export type DogPayload = {
  name: string;
  breed?: string;
  age_years?: number;
  sex?: string;
  routines?: Record<string, unknown>;
  known_habits?: Record<string, unknown>;
};

export type Dog = DogPayload & {
  id: string;
  owner_id: string;
  created_at: string;
};

export type AnalysisJob = {
  id: string;
  dog_id: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  progress: number;
  storage_path?: string | null;
  local_path?: string | null;
  context_tags: string[];
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export type Prediction = {
  label: string;
  confidence: number;
  evidence: string[];
};

export type AnalysisResult = {
  job_id: string;
  dog_id: string;
  top_predictions: Prediction[];
  uncertainty_reason?: string | null;
  needs_feedback: boolean;
  evidence_timeline: Array<Record<string, unknown>>;
  raw_signals: Record<string, unknown>;
};

export type HabitSummary = {
  dog_id: string;
  label_counts: Record<string, number>;
  recent_notes: string[];
  updated_at: string;
};
