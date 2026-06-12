export type ChatResponse = {
  answer: string;
  mode: "facts" | "analysis" | "prediction" | "help";
  data: Record<string, unknown>;
  data_source: string;
};

export type Prediction = {
  team_a: string;
  team_b: string;
  team_a_win: number;
  draw: number;
  team_b_win: number;
  confidence: string;
  top_factors: string[];
  model_version: string;
  data_freshness: string;
};

export type Match = {
  date: string;
  stage: string;
  group?: string;
  team_a: string;
  team_b: string;
  status: string;
  score: string | null;
  venue: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

export async function sendChat(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, channel: "web" }),
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Chat request failed"));
  }

  return response.json();
}

export async function predictMatch(teamA: string, teamB: string): Promise<Prediction> {
  const response = await fetch(`${API_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ team_a: teamA, team_b: teamB }),
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Prediction request failed"));
  }

  return response.json();
}

export async function fetchMatches(): Promise<Match[]> {
  const response = await fetch(`${API_URL}/matches`);

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Schedule request failed"));
  }

  return response.json();
}

async function errorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall back to the status when the server does not return JSON.
  }
  return `${fallback} with status ${response.status}`;
}
