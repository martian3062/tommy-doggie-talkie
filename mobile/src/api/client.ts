import {
  AnalysisJob,
  AnalysisResult,
  BreedDetection,
  BreedProfile,
  Dog,
  DogPayload,
  HabitSummary,
} from '../types';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export type UploadInput = {
  dogId: string;
  contextTags: string[];
  file?: {
    uri: string;
    name: string;
    type: string;
  };
  storagePath?: string;
  storageSignedUrl?: string;
};

export class ApiClient {
  constructor(private ownerId: string) {}

  async listDogs(): Promise<Dog[]> {
    return this.request('/api/v1/dogs');
  }

  async createDog(payload: DogPayload): Promise<Dog> {
    return this.request('/api/v1/dogs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateDog(dogId: string, payload: DogPayload): Promise<Dog> {
    return this.request(`/api/v1/dogs/${dogId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async createAnalysisJob(input: UploadInput): Promise<AnalysisJob> {
    const form = new FormData();
    form.append('dog_id', input.dogId);
    form.append('context_tags', JSON.stringify(input.contextTags));
    if (input.storagePath) {
      form.append('storage_path', input.storagePath);
    }
    if (input.storageSignedUrl) {
      form.append('storage_signed_url', input.storageSignedUrl);
    }
    if (input.file) {
      form.append('file', input.file as unknown as Blob);
    }
    return this.request('/api/v1/analysis-jobs', {
      method: 'POST',
      body: form,
      skipJsonHeader: true,
    });
  }

  async getJob(jobId: string): Promise<AnalysisJob> {
    return this.request(`/api/v1/analysis-jobs/${jobId}`);
  }

  async getResult(jobId: string): Promise<AnalysisResult> {
    return this.request(`/api/v1/analysis-jobs/${jobId}/result`);
  }

  async sendFeedback(jobId: string, selectedLabel: string, isCorrect: boolean, note?: string) {
    return this.request(`/api/v1/analysis-jobs/${jobId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ selected_label: selectedLabel, is_correct: isCorrect, note }),
    });
  }

  async getHabits(dogId: string): Promise<HabitSummary> {
    return this.request(`/api/v1/dogs/${dogId}/habits`);
  }

  async listBreeds(): Promise<BreedProfile[]> {
    return this.request('/api/v1/breeds');
  }

  async detectBreed(dogId: string, file: { uri: string; name: string; type: string }): Promise<BreedDetection> {
    const form = new FormData();
    form.append('file', file as unknown as Blob);
    return this.request(`/api/v1/dogs/${dogId}/breed-detect`, {
      method: 'POST',
      body: form,
      skipJsonHeader: true,
    });
  }

  private async request<T>(
    path: string,
    init?: RequestInit & { skipJsonHeader?: boolean },
  ): Promise<T> {
    const headers = new Headers(init?.headers);
    headers.set('X-User-Id', this.ownerId);
    if (!init?.skipJsonHeader) {
      headers.set('Content-Type', 'application/json');
    }
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
  }
}
