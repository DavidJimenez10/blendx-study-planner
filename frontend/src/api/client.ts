const BASE = import.meta.env.VITE_API_URL || "/api";

export type TokenPayload = { sub: string; name: string; exp: number };

let cachedToken: string | null = null;

const TOKEN_KEY = "token:v1";

export function getToken(): string | null {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    cachedToken = token;
    return token;
  } catch {
    return cachedToken;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {}
  cachedToken = token;
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {}
  cachedToken = null;
}

export function getTokenPayload(): TokenPayload | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1])) as TokenPayload;
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      clearToken();
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...init,
  });
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export type User = { id: number; name: string };
export type StudyPlan = {
  id: number;
  user_id: number;
  goal: string;
  hours_per_week: number;
  description: string | null;
  target_date: string | null;
};
export type StudyTask = {
  id: number;
  plan_id: number;
  title: string;
  estimated_hours: number;
  completed: boolean;
};
export type GenerateTasksResponse = {
  tasks: StudyTask[];
  total_estimated_hours: number;
  hours_match: boolean;
  warning: string | null;
  failed_generations: { title: string; estimated_hours: number; reason: string }[];
};
export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type PlanDocument = {
  id: number;
  plan_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  created_at: string;
};

export type ChatSource = {
  filename: string;
  content: string;
};

export type ChatResponse = {
  answer: string;
  sources: ChatSource[];
};

export const api = {
  register: (name: string, password: string) =>
    req<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, password }),
    }),

  login: (name: string, password: string) =>
    req<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ name, password }),
    }),

  getUsers: () => req<User[]>("/users"),

  getUser: (id: number) => req<User>(`/users/${id}`),

  getUserPlans: (userId: number) => req<StudyPlan[]>(`/users/${userId}/plans`),

  createPlan: (data: {
    user_id: number;
    goal: string;
    hours_per_week: number;
    description?: string | null;
    target_date?: string | null;
  }) =>
    req<StudyPlan>("/plans", { method: "POST", body: JSON.stringify(data) }),

  getPlan: (id: number) => req<StudyPlan>(`/plans/${id}`),

  updatePlan: (
    planId: number,
    data: Partial<Pick<StudyPlan, "description" | "target_date">>,
  ) =>
    req<StudyPlan>(`/plans/${planId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  createTask: (
    planId: number,
    data: { title: string; estimated_hours: number },
  ) =>
    req<StudyTask>(`/plans/${planId}/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getTasks: (planId: number) => req<StudyTask[]>(`/plans/${planId}/tasks`),

  toggleTask: (planId: number, taskId: number, completed: boolean) =>
    req<StudyTask>(`/plans/${planId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify({ completed }),
    }),

  generateTasks: (planId: number, maxTasks?: number) =>
    req<GenerateTasksResponse>(`/plans/${planId}/generate-tasks`, {
      method: "POST",
      body: JSON.stringify({ max_tasks: maxTasks ?? null }),
    }),

  uploadDocument: (planId: number, file: File) =>
    uploadFile<PlanDocument>(`/plans/${planId}/documents`, file),

  getDocuments: (planId: number) =>
    req<PlanDocument[]>(`/plans/${planId}/documents`),

  deleteDocument: (planId: number, documentId: number) =>
    req<void>(`/plans/${planId}/documents/${documentId}`, {
      method: "DELETE",
    }),

  chat: (planId: number, question: string) =>
    req<ChatResponse>(`/plans/${planId}/chat`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};
