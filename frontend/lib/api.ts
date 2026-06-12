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
    throw new Error(`Chat request failed with status ${response.status}`);
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
    throw new Error(`Prediction request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchMatches(): Promise<Match[]> {
  const response = await fetch(`${API_URL}/matches`);

  if (!response.ok) {
    throw new Error(`Schedule request failed with status ${response.status}`);
  }

  return response.json();
}
