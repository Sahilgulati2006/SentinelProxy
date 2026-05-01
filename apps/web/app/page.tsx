"use client";

import { useState } from "react";

type SentinelResponse = {
  id: string;
  model: string;
  choices: {
    message: {
      role: string;
      content: string;
    };
  }[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  sentinel?: {
    request_id: string;
    user_id?: string;
    api_key_prefix?: string;
    redactions_applied: number;
    risk_score: number;
    provider_used: string;
    entity_counts: Record<string, number>;
    reidentification_applied: boolean;
    unreplaced_placeholders: string[];
    repaired_placeholders: string[];
    mapping_store: string;
    budget?: {
      monthly_token_limit: number;
      used_tokens: number;
      remaining_tokens: number;
    };
    rate_limit?: {
      limit: number;
      window_seconds: number;
      used: number;
      remaining: number;
      reset_seconds: number;
    };
  };
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [apiKey, setApiKey] = useState("");
  const [prompt, setPrompt] = useState(
    "My email is sahil@example.com and my phone is 413-555-0199. Summarize this."
  );
  const [response, setResponse] = useState<SentinelResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendPrompt() {
    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const res = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          messages: [
            {
              role: "user",
              content: prompt,
            },
          ],
          temperature: 0.2,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Request failed");
      }

      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const assistantText = response?.choices?.[0]?.message?.content;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <header className="space-y-3">
          <div className="inline-flex rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
            Local-first LLM security proxy
          </div>

          <div>
            <h1 className="text-4xl font-bold tracking-tight">
              SentinelProxy
            </h1>
            <p className="mt-3 max-w-2xl text-slate-300">
              Send prompts through a privacy gateway that redacts sensitive data
              before inference, stores temporary mappings in Redis, and restores
              the response safely.
            </p>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
            <h2 className="text-xl font-semibold">Protected Chat</h2>
            <p className="mt-1 text-sm text-slate-400">
              Use your generated <code>sp_live_...</code> API key.
            </p>

            <label className="mt-6 block text-sm font-medium text-slate-300">
              API Key
            </label>
            <input
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sp_live_..."
              type="password"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            />

            <label className="mt-5 block text-sm font-medium text-slate-300">
              Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={8}
              className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm leading-6 outline-none ring-emerald-400/40 focus:ring-2"
            />

            <button
              onClick={sendPrompt}
              disabled={loading || !apiKey || !prompt}
              className="mt-5 rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Protecting..." : "Send through SentinelProxy"}
            </button>

            {error && (
              <div className="mt-5 rounded-xl border border-red-400/30 bg-red-400/10 p-4 text-sm text-red-200">
                {error}
              </div>
            )}

            {assistantText && (
              <div className="mt-6 rounded-xl border border-slate-700 bg-slate-950 p-5">
                <h3 className="mb-2 text-sm font-semibold text-slate-400">
                  Assistant Response
                </h3>
                <p className="whitespace-pre-wrap leading-7 text-slate-100">
                  {assistantText}
                </p>
              </div>
            )}
          </div>

          <aside className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
            <h2 className="text-xl font-semibold">Sentinel Report</h2>
            <p className="mt-1 text-sm text-slate-400">
              Privacy, budget, and gateway metadata.
            </p>

            {!response?.sentinel ? (
              <div className="mt-6 rounded-xl border border-dashed border-slate-700 p-5 text-sm text-slate-400">
                Send a request to see redactions, risk score, budget, and rate
                limit data.
              </div>
            ) : (
              <div className="mt-6 space-y-4 text-sm">
                <Metric label="Request ID" value={response.sentinel.request_id} />
                <Metric label="Provider" value={response.sentinel.provider_used} />
                <Metric
                  label="Redactions"
                  value={String(response.sentinel.redactions_applied)}
                />
                <Metric
                  label="Risk Score"
                  value={String(response.sentinel.risk_score)}
                />
                <Metric
                  label="Re-identified"
                  value={response.sentinel.reidentification_applied ? "Yes" : "No"}
                />
                <Metric label="Mapping Store" value={response.sentinel.mapping_store} />

                <div className="rounded-xl bg-slate-950 p-4">
                  <h3 className="mb-3 font-semibold text-slate-300">
                    Entity Counts
                  </h3>
                  {Object.keys(response.sentinel.entity_counts || {}).length ===
                  0 ? (
                    <p className="text-slate-500">No entities detected.</p>
                  ) : (
                    <div className="space-y-2">
                      {Object.entries(response.sentinel.entity_counts).map(
                        ([key, value]) => (
                          <div
                            key={key}
                            className="flex justify-between text-slate-300"
                          >
                            <span>{key}</span>
                            <span>{value}</span>
                          </div>
                        )
                      )}
                    </div>
                  )}
                </div>

                {response.sentinel.budget && (
                  <div className="rounded-xl bg-slate-950 p-4">
                    <h3 className="mb-3 font-semibold text-slate-300">Budget</h3>
                    <Metric
                      label="Used Tokens"
                      value={String(response.sentinel.budget.used_tokens)}
                    />
                    <Metric
                      label="Remaining"
                      value={String(response.sentinel.budget.remaining_tokens)}
                    />
                    <Metric
                      label="Monthly Limit"
                      value={String(response.sentinel.budget.monthly_token_limit)}
                    />
                  </div>
                )}

                {response.sentinel.rate_limit && (
                  <div className="rounded-xl bg-slate-950 p-4">
                    <h3 className="mb-3 font-semibold text-slate-300">
                      Rate Limit
                    </h3>
                    <Metric
                      label="Used"
                      value={String(response.sentinel.rate_limit.used)}
                    />
                    <Metric
                      label="Remaining"
                      value={String(response.sentinel.rate_limit.remaining)}
                    />
                    <Metric
                      label="Reset Seconds"
                      value={String(response.sentinel.rate_limit.reset_seconds)}
                    />
                  </div>
                )}
              </div>
            )}
          </aside>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-800 py-2 last:border-b-0">
      <span className="text-slate-400">{label}</span>
      <span className="break-all text-right font-medium text-slate-200">
        {value}
      </span>
    </div>
  );
}