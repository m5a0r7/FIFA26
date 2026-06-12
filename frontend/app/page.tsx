"use client";

import * as Tabs from "@radix-ui/react-tabs";
import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ChatResponse, Match, Prediction, fetchMatches, predictMatch, sendChat } from "../lib/api";

const quickPrompts = [
  "/predict Brazil vs Germany",
  "Show upcoming group matches",
  "Compare Argentina and France",
];

export default function Home() {
  const [message, setMessage] = useState("/predict Brazil vs Germany");
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [teamA, setTeamA] = useState("Brazil");
  const [teamB, setTeamB] = useState("Germany");
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [scheduleLoading, setScheduleLoading] = useState(true);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMatches() {
      try {
        const loadedMatches = await fetchMatches();
        if (!cancelled) {
          setMatches(loadedMatches);
        }
      } catch (caught) {
        if (!cancelled) {
          setScheduleError(caught instanceof Error ? caught.message : "Schedule request failed");
        }
      } finally {
        if (!cancelled) {
          setScheduleLoading(false);
        }
      }
    }

    loadMatches();
    return () => {
      cancelled = true;
    };
  }, []);

  const chartData = useMemo(() => {
    if (!prediction) return [];
    return [
      { name: prediction.team_a, probability: Math.round(prediction.team_a_win * 100), fill: "var(--primary)" },
      { name: "Draw", probability: Math.round(prediction.draw * 100), fill: "var(--warning)" },
      { name: prediction.team_b, probability: Math.round(prediction.team_b_win * 100), fill: "var(--accent)" },
    ];
  }, [prediction]);

  const leadingOutcome = useMemo(() => {
    if (!prediction) return null;
    const outcomes = [
      { label: prediction.team_a, value: prediction.team_a_win },
      { label: "Draw", value: prediction.draw },
      { label: prediction.team_b, value: prediction.team_b_win },
    ];
    return outcomes.sort((a, b) => b.value - a.value)[0];
  }, [prediction]);

  async function handleChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setChatLoading(true);
    setError(null);
    try {
      setChatResponse(await sendChat(message));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Chat request failed");
    } finally {
      setChatLoading(false);
    }
  }

  async function handlePrediction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPredictionLoading(true);
    setError(null);
    try {
      setPrediction(await predictMatch(teamA, teamB));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Prediction request failed");
    } finally {
      setPredictionLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-4 py-5 text-[var(--foreground)] sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--panel)] shadow-sm">
          <div className="grid gap-5 p-5 md:grid-cols-[minmax(0,1fr)_420px] md:p-6">
            <div className="flex flex-col justify-between gap-6">
              <div>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <StatusPill tone="blue">FIFA 2026 Agent</StatusPill>
                  <StatusPill tone="green">API ready</StatusPill>
                </div>
                <h1 className="max-w-3xl text-3xl font-semibold tracking-normal text-[var(--foreground)] sm:text-4xl">
                  Football intelligence console
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">
                  Ask tactical questions, run explainable match predictions, and scan the seeded tournament schedule from one workbench.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <Metric label="Model" value="v0" detail="Explainable baseline" />
                <Metric label="Benchmark" value="50%" detail="Historical accuracy" />
                <Metric label="Data" value="Mock" detail="Seeded sample set" />
              </div>
            </div>

            <div className="rounded-lg border border-[var(--border)] bg-[var(--panel-soft)] p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase text-[var(--muted)]">Current matchup</p>
                  <p className="mt-1 text-xl font-semibold">
                    {teamA} <span className="text-[var(--muted)]">vs</span> {teamB}
                  </p>
                </div>
                {leadingOutcome ? (
                  <div className="text-right">
                    <p className="text-xs font-semibold uppercase text-[var(--muted)]">Leader</p>
                    <p className="mt-1 text-xl font-semibold text-[var(--primary-dark)]">{leadingOutcome.label}</p>
                  </div>
                ) : null}
              </div>
              <div className="mt-5 grid grid-cols-3 gap-2">
                <Probability label={prediction?.team_a ?? teamA} value={prediction?.team_a_win} />
                <Probability label="Draw" value={prediction?.draw} />
                <Probability label={prediction?.team_b ?? teamB} value={prediction?.team_b_win} />
              </div>
            </div>
          </div>
        </header>

        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-800">{error}</div>
        ) : null}

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
          <Tabs.Root defaultValue="ask" className="rounded-lg border border-[var(--border)] bg-[var(--panel)] shadow-sm">
            <div className="flex flex-col gap-3 border-b border-[var(--border)] p-3 sm:flex-row sm:items-center sm:justify-between">
              <Tabs.List className="grid grid-cols-3 rounded-md bg-[var(--panel-muted)] p-1" aria-label="Agent workbench">
                <Tabs.Trigger className="tab-trigger" value="ask">
                  Ask
                </Tabs.Trigger>
                <Tabs.Trigger className="tab-trigger" value="predict">
                  Predict
                </Tabs.Trigger>
                <Tabs.Trigger className="tab-trigger" value="schedule">
                  Schedule
                </Tabs.Trigger>
              </Tabs.List>
              <StatusPill tone="amber">Web + Telegram ready</StatusPill>
            </div>

            <Tabs.Content value="ask" className="p-4 md:p-5">
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_300px]">
                <form onSubmit={handleChat} className="flex flex-col gap-3">
                  <label htmlFor="agent-message" className="text-sm font-semibold">
                    Agent prompt
                  </label>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <input
                      id="agent-message"
                      value={message}
                      onChange={(event) => setMessage(event.target.value)}
                      className="field min-h-12 flex-1"
                      placeholder="Predict Brazil vs Germany"
                    />
                    <button disabled={chatLoading} className="button-primary min-h-12">
                      {chatLoading ? "Asking..." : "Ask agent"}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {quickPrompts.map((prompt) => (
                      <button key={prompt} type="button" onClick={() => setMessage(prompt)} className="button-secondary text-xs">
                        {prompt}
                      </button>
                    ))}
                  </div>
                </form>

                <div className="rounded-lg border border-[var(--border)] bg-[var(--panel-soft)] p-4">
                  <p className="text-xs font-semibold uppercase text-[var(--muted)]">Response mode</p>
                  <p className="mt-2 text-2xl font-semibold capitalize">{chatResponse?.mode ?? "Ready"}</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">Source: {chatResponse?.data_source ?? "Waiting for a prompt"}</p>
                </div>
              </div>

              <div className="mt-5 min-h-52 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
                {chatResponse ? (
                  <div className="space-y-3">
                    <StatusPill tone="blue">{chatResponse.mode}</StatusPill>
                    <p className="text-base leading-7">{chatResponse.answer}</p>
                  </div>
                ) : (
                  <EmptyState
                    title="No answer yet"
                    copy="Send a prompt to see the agent answer with predictions, schedule notes, standings, or team comparisons."
                  />
                )}
              </div>
            </Tabs.Content>

            <Tabs.Content value="predict" className="p-4 md:p-5">
              <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
                <form onSubmit={handlePrediction} className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
                  <h2 className="text-lg font-semibold">Match predictor</h2>
                  <div className="mt-4 grid gap-3">
                    <label className="grid gap-2 text-sm font-semibold">
                      Team A
                      <input value={teamA} onChange={(event) => setTeamA(event.target.value)} className="field min-h-11" />
                    </label>
                    <label className="grid gap-2 text-sm font-semibold">
                      Team B
                      <input value={teamB} onChange={(event) => setTeamB(event.target.value)} className="field min-h-11" />
                    </label>
                    <button disabled={predictionLoading} className="button-accent min-h-11">
                      {predictionLoading ? "Running..." : "Run prediction"}
                    </button>
                  </div>
                </form>

                <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
                  {prediction ? (
                    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
                      <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                            <CartesianGrid stroke="var(--border)" vertical={false} />
                            <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis unit="%" width={42} fontSize={12} tickLine={false} axisLine={false} />
                            <Tooltip formatter={(value) => `${value}%`} cursor={{ fill: "rgba(12, 33, 54, 0.06)" }} />
                            <Bar dataKey="probability" radius={[6, 6, 0, 0]}>
                              {chartData.map((entry) => (
                                <Cell key={entry.name} fill={entry.fill} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="rounded-lg bg-[var(--panel-soft)] p-4">
                        <p className="text-xs font-semibold uppercase text-[var(--muted)]">Confidence</p>
                        <p className="mt-2 text-2xl font-semibold">{prediction.confidence}</p>
                        <p className="mt-1 text-xs text-[var(--muted)]">Model {prediction.model_version}</p>
                        <ul className="mt-4 space-y-2 text-sm leading-6 text-[var(--muted-strong)]">
                          {prediction.top_factors.map((factor) => (
                            <li key={factor} className="rounded-md bg-white px-3 py-2">
                              {factor}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <EmptyState title="Prediction pending" copy="Choose two teams and run the model to compare win, draw, and loss probabilities." />
                  )}
                </div>
              </div>
            </Tabs.Content>

            <Tabs.Content value="schedule" className="p-4 md:p-5">
              <ScheduleList matches={matches} loading={scheduleLoading} error={scheduleError} />
            </Tabs.Content>
          </Tabs.Root>

          <aside className="rounded-lg border border-[var(--border)] bg-[var(--panel)] p-4 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">Benchmark baseline</h2>
              <StatusPill tone="blue">v0</StatusPill>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Accuracy" value="0.50" detail="Target: higher" />
              <Metric label="Log loss" value="0.9678" detail="Lower is better" />
              <Metric label="Brier" value="0.5714" detail="Probability score" />
              <Metric label="Calibration" value="0.1867" detail="Reliability gap" />
            </div>
            <div className="mt-5 rounded-lg bg-[var(--panel-soft)] p-4">
              <p className="text-sm font-semibold">Data freshness</p>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                {prediction?.data_freshness ?? "Run a prediction to inspect model freshness and factor quality."}
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

function ScheduleList({ matches, loading, error }: { matches: Match[]; loading: boolean; error: string | null }) {
  if (loading) {
    return <EmptyState title="Loading schedule" copy="Fetching seeded tournament matches from the backend." />;
  }

  if (error) {
    return <EmptyState title="Schedule unavailable" copy={error} />;
  }

  if (matches.length === 0) {
    return <EmptyState title="No matches loaded" copy="The schedule endpoint returned an empty list." />;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-[var(--border)]">
      <div className="grid grid-cols-[120px_minmax(0,1fr)_130px] gap-3 bg-[var(--panel-soft)] px-4 py-3 text-xs font-semibold uppercase text-[var(--muted)] max-sm:hidden">
        <span>Date</span>
        <span>Match</span>
        <span className="text-right">Venue</span>
      </div>
      <div className="divide-y divide-[var(--border)] bg-white">
        {matches.map((match) => (
          <div
            key={`${match.date}-${match.team_a}-${match.team_b}`}
            className="grid gap-2 px-4 py-4 sm:grid-cols-[120px_minmax(0,1fr)_130px] sm:items-center"
          >
            <span className="text-sm font-medium text-[var(--muted)]">{match.date}</span>
            <div>
              <p className="font-semibold">
                {match.team_a} <span className="text-[var(--muted)]">vs</span> {match.team_b}
              </p>
              <p className="mt-1 text-xs uppercase text-[var(--muted)]">
                {match.stage}
                {match.group ? ` / ${match.group}` : ""}
              </p>
            </div>
            <span className="text-sm text-[var(--muted-strong)] sm:text-right">{match.venue}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-white px-3 py-3">
      <div className="text-xs font-semibold uppercase text-[var(--muted)]">{label}</div>
      <div className="mt-1 text-xl font-semibold text-[var(--foreground)]">{value}</div>
      <div className="mt-1 text-xs text-[var(--muted)]">{detail}</div>
    </div>
  );
}

function Probability({ label, value }: { label: string; value?: number }) {
  const percent = value === undefined ? "--" : `${Math.round(value * 100)}%`;

  return (
    <div className="min-w-0 rounded-lg bg-white p-3">
      <p className="truncate text-xs font-semibold uppercase text-[var(--muted)]">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{percent}</p>
    </div>
  );
}

function StatusPill({ children, tone }: { children: ReactNode; tone: "blue" | "green" | "amber" }) {
  return <span className={`status-pill status-pill-${tone}`}>{children}</span>;
}

function EmptyState({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center rounded-lg border border-dashed border-[var(--border)] bg-white px-5 py-8 text-center">
      <p className="text-base font-semibold">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-[var(--muted)]">{copy}</p>
    </div>
  );
}
