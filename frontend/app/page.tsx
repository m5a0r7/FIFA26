"use client";

import { FormEvent, useMemo, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ChatResponse, Prediction, predictMatch, sendChat } from "../lib/api";

const sampleMatches = [
  { date: "2026-06-11", teamA: "Mexico", teamB: "TBD", venue: "Estadio Azteca" },
  { date: "2026-06-12", teamA: "USA", teamB: "TBD", venue: "Los Angeles Stadium" },
  { date: "2026-06-12", teamA: "Canada", teamB: "TBD", venue: "Toronto Stadium" },
];

export default function Home() {
  const [message, setMessage] = useState("/predict Brazil vs Germany");
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [teamA, setTeamA] = useState("Brazil");
  const [teamB, setTeamB] = useState("Germany");
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chartData = useMemo(() => {
    if (!prediction) return [];
    return [
      { name: prediction.team_a, probability: Math.round(prediction.team_a_win * 100) },
      { name: "Draw", probability: Math.round(prediction.draw * 100) },
      { name: prediction.team_b, probability: Math.round(prediction.team_b_win * 100) },
    ];
  }, [prediction]);

  async function handleChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setChatResponse(await sendChat(message));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Chat request failed");
    } finally {
      setLoading(false);
    }
  }

  async function handlePrediction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setPrediction(await predictMatch(teamA, teamB));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Prediction request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-[var(--border)] pb-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-[var(--primary)]">FIFA 2026 Agent</p>
            <h1 className="mt-1 text-3xl font-semibold text-[var(--foreground)]">Football intelligence console</h1>
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <Metric label="Model" value="v0" />
            <Metric label="Benchmark" value="50%" />
            <Metric label="Data" value="Mock" />
          </div>
        </header>

        {error ? (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
        ) : null}

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
          <div className="rounded-lg border border-[var(--border)] bg-[var(--panel)] p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Ask the agent</h2>
              <span className="rounded-md bg-[var(--panel-muted)] px-2 py-1 text-xs font-medium text-slate-600">Web + Telegram ready</span>
            </div>
            <form onSubmit={handleChat} className="flex flex-col gap-3 sm:flex-row">
              <input
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                className="min-h-11 flex-1 rounded-md border border-[var(--border)] bg-white px-3 outline-none focus:border-[var(--primary)]"
                placeholder="Predict Brazil vs Germany"
              />
              <button
                disabled={loading}
                className="min-h-11 rounded-md bg-[var(--primary)] px-5 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                Ask
              </button>
            </form>

            <div className="mt-4 min-h-40 rounded-md border border-[var(--border)] bg-slate-50 p-4">
              {chatResponse ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded-md bg-white px-2 py-1 text-xs font-semibold text-[var(--primary-dark)]">
                      {chatResponse.mode}
                    </span>
                    <span className="text-xs text-slate-500">Source: {chatResponse.data_source}</span>
                  </div>
                  <p className="text-base leading-7">{chatResponse.answer}</p>
                </div>
              ) : (
                <p className="text-sm leading-6 text-slate-600">
                  Try prediction, schedule, standings, or team comparison questions. The backend currently uses seeded sample data.
                </p>
              )}
            </div>
          </div>

          <aside className="rounded-lg border border-[var(--border)] bg-[var(--panel)] p-4 shadow-sm">
            <h2 className="text-lg font-semibold">Predict a match</h2>
            <form onSubmit={handlePrediction} className="mt-4 grid gap-3">
              <input
                value={teamA}
                onChange={(event) => setTeamA(event.target.value)}
                className="min-h-11 rounded-md border border-[var(--border)] px-3 outline-none focus:border-[var(--primary)]"
              />
              <input
                value={teamB}
                onChange={(event) => setTeamB(event.target.value)}
                className="min-h-11 rounded-md border border-[var(--border)] px-3 outline-none focus:border-[var(--primary)]"
              />
              <button
                disabled={loading}
                className="min-h-11 rounded-md bg-[var(--accent)] px-5 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                Run prediction
              </button>
            </form>

            {prediction ? (
              <div className="mt-5 space-y-4">
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <XAxis dataKey="name" fontSize={12} />
                      <YAxis unit="%" width={42} fontSize={12} />
                      <Tooltip formatter={(value) => `${value}%`} />
                      <Bar dataKey="probability" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="rounded-md bg-[var(--panel-muted)] p-3 text-sm">
                  <p className="font-semibold">Confidence: {prediction.confidence}</p>
                  <ul className="mt-2 space-y-1 text-slate-700">
                    {prediction.top_factors.map((factor) => (
                      <li key={factor}>{factor}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
          </aside>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1fr_420px]">
          <div className="rounded-lg border border-[var(--border)] bg-[var(--panel)] p-4 shadow-sm">
            <h2 className="text-lg font-semibold">Sample schedule</h2>
            <div className="mt-4 divide-y divide-[var(--border)]">
              {sampleMatches.map((match) => (
                <div key={`${match.date}-${match.teamA}`} className="grid gap-2 py-3 sm:grid-cols-[130px_1fr_1fr]">
                  <span className="text-sm font-medium text-slate-500">{match.date}</span>
                  <span className="font-semibold">
                    {match.teamA} vs {match.teamB}
                  </span>
                  <span className="text-sm text-slate-600 sm:text-right">{match.venue}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border)] bg-[var(--panel)] p-4 shadow-sm">
            <h2 className="text-lg font-semibold">Benchmark baseline</h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Accuracy" value="0.50" />
              <Metric label="Log loss" value="0.9678" />
              <Metric label="Brier" value="0.5714" />
              <Metric label="Calibration" value="0.1867" />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[var(--border)] bg-white px-3 py-2">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-[var(--foreground)]">{value}</div>
    </div>
  );
}
