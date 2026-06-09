export type DogPayload = {
  name: string;
  breed?: string;
  breed_source?: string;
  breed_confidence?: number;
  breed_predictions?: BreedPrediction[];
  breed_behavior_profile?: BreedProfile;
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

export type BreedPrediction = {
  breed: string;
  confidence: number;
  source: string;
};

export type BreedProfile = {
  slug: string;
  display_name: string;
  group: string;
  energy_level: string;
  behavior_biases: Record<string, number>;
  common_patterns: string[];
  health_watch: string[];
  interpretation_notes: string[];
};

export type BreedDetection = {
  dog_id: string;
  breed_predictions: BreedPrediction[];
  selected_breed?: string | null;
  breed_source: string;
  behavior_profile?: BreedProfile | null;
};
