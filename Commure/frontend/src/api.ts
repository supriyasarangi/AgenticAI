import {
  Encounter,
  EncounterInput,
  ListResponse,
  GenerateNoteResponse,
} from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');
  let data;

  if (contentType?.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMessage =
      typeof data === 'object' && data?.error ? data.error : `HTTP ${response.status}`;
    throw new Error(errorMessage);
  }

  return data;
}

export async function createEncounter(input: EncounterInput): Promise<Encounter> {
  const response = await fetch(`${API_URL}/api/encounters`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  });

  return handleResponse<Encounter>(response);
}

export async function generateNote(id: number): Promise<GenerateNoteResponse> {
  const response = await fetch(`${API_URL}/api/encounters/${id}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<GenerateNoteResponse>(response);
}

export async function listEncounters(page = 1, limit = 20): Promise<ListResponse> {
  const response = await fetch(
    `${API_URL}/api/encounters?page=${page}&limit=${limit}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return handleResponse<ListResponse>(response);
}

export async function getEncounter(id: number): Promise<Encounter> {
  const response = await fetch(`${API_URL}/api/encounters/${id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<Encounter>(response);
}
