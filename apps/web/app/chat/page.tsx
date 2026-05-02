"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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

type ReadyStatus = {
  status: string;
  checks?: {
    redis?: string;
    database?: string;
    provider?: {
      status: string;
      provider: string;
      detail?: string;
    };
  };
};

type MeResponse = {
  user_id: string;
  email: string;
  api_key_prefix: string;
  budget: {
    monthly_token_limit: number;
    used_tokens: number;
    remaining_tokens: number;
  };
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [apiKey, setApiKey] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }

    return localStorage.getItem("sentinel_api_key") || "";
  });

  const [saveKey, setSaveKey] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }

    return Boolean(localStorage.getItem("sentinel_api_key"));
  });
  const [prompt, setPrompt] = useState(
    "My email is sahil@example.com and my phone is 413-555-0199. Summarize this."
  );

  const [response, setResponse] = useState<SentinelResponse | null>(null);
  const [readyStatus, setReadyStatus] = useState<ReadyStatus | null>(null);
  const [me, setMe] = useState<MeResponse | null>(null);

  const [error, setError] = useState("");
  const [statusError, setStatusError] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);

  useEffect(() => {
    checkReadiness();
  }, []);

  useEffect(() => {
    if (saveKey && apiKey) {
      localStorage.setItem("sentinel_api_key", apiKey);
    }

    if (!saveKey) {
      localStorage.removeItem("sentinel_api_key");
    }
  }, [saveKey, apiKey]);

  function handleApiKeyChange(value: string) {
    setApiKey(value);
    setMe(null);
    setResponse(null);
    setError("");
  }

  async function checkReadiness() {
    setStatusLoading(true);
    setStatusError("");

    try {
      const res = await fetch(`${API_BASE_URL}/ready`);
      const data = await res.json();

      if (!res.ok) {
        setReadyStatus(data.detail || data);
        throw new Error("One or more backend dependencies are not ready.");
      }

      setReadyStatus(data);
    } catch (err) {
      setStatusError(
        err instanceof Error ? err.message : "Could not reach backend."
      );
    } finally {
      setStatusLoading(false);
    }
  }

  async function fetchMe() {
    if (!apiKey) {
      setMe(null);
      setError("Enter an API key first.");
      return;
    }

    setStatusLoading(true);
    setError("");
    setMe(null);

    try {
      const res = await fetch(`${API_BASE_URL}/v1/me`, {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(formatApiError(res.status, data.detail));
      }

      setMe(data);
    } catch (err) {
      setMe(null);
      setError(err instanceof Error ? err.message : "Could not load user.");
    } finally {
      setStatusLoading(false);
    }
  }

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
        setMe(null);
        throw new Error(formatApiError(res.status, data.detail));
      }

      setResponse(data);
      await fetchMe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function clearSession() {
    setApiKey("");
    setSaveKey(false);
    setMe(null);
    setResponse(null);
    setError("");
    localStorage.removeItem("sentinel_api_key");
  }

  const assistantText = response?.choices?.[0]?.message?.content;
  const isCurrentKeyVerified =
    me !== null && apiKey.length > 0 && apiKey.startsWith(me.api_key_prefix);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10">
        <header className="flex flex-col justify-between gap-6 lg:flex-row lg:items-start">
          <div className="space-y-3">
            <div className="inline-flex rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
              Local-first LLM security proxy
            </div>

            <div>
              <h1 className="text-4xl font-bold tracking-tight">
                SentinelProxy
              </h1>
              <Link
                href="/"
                className="text-sm text-emerald-300 hover:text-emerald-200"
              >
                ← Back to Home
              </Link>
            </div>

            <div>
              <a
                href="/admin"
                className="text-sm text-slate-400 hover:text-slate-200"
              >
                Admin Console →
              </a>
              <p className="mt-3 max-w-2xl text-slate-300">
                Redact sensitive data before inference, store temporary mappings
                in Redis, and restore protected responses safely.
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl lg:min-w-80">
            <div className="flex items-center justify-between gap-4">
              <h2 className="font-semibold">System Status</h2>
              <button
                onClick={checkReadiness}
                disabled={statusLoading}
                className="rounded-lg border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-800 disabled:opacity-50"
              >
                {statusLoading ? "Checking..." : "Refresh"}
              </button>
            </div>

            <div className="mt-4 space-y-2 text-sm">
              <StatusRow
                label="Backend"
                ok={!statusError && !!readyStatus}
                value={statusError ? "Unavailable" : readyStatus?.status || "Unknown"}
              />
              <StatusRow
                label="Redis"
                ok={readyStatus?.checks?.redis === "ok"}
                value={readyStatus?.checks?.redis || "Unknown"}
              />
              <StatusRow
                label="Database"
                ok={readyStatus?.checks?.database === "ok"}
                value={readyStatus?.checks?.database || "Unknown"}
              />
              <StatusRow
                label="Provider"
                ok={readyStatus?.checks?.provider?.status === "ok"}
                value={readyStatus?.checks?.provider?.provider || "Unknown"}
              />
            </div>

            {statusError && (
              <p className="mt-3 text-xs text-red-300">{statusError}</p>
            )}
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
              <div>
                <h2 className="text-xl font-semibold">Protected Chat</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Use your generated <code>sp_live_...</code> API key.
                </p>
              </div>

              <button
                onClick={clearSession}
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"
              >
                Clear session
              </button>
            </div>

            <label className="mt-6 block text-sm font-medium text-slate-300">
              API Key
            </label>
            <input
              value={apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder="sp_live_..."
              type="password"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            />

            <div className="mt-3 flex items-center justify-between gap-3">
              <label className="flex items-center gap-2 text-sm text-slate-400">
                <input
                  checked={saveKey}
                  onChange={(e) => setSaveKey(e.target.checked)}
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-700"
                />
                Save API key locally in this browser
              </label>

              <button
                onClick={fetchMe}
                disabled={!apiKey || statusLoading}
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Check key
              </button>
            </div>

            {isCurrentKeyVerified && me && (
              <div className="mt-4 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">
                Authenticated as <span className="font-semibold">{me.email}</span>
                <div className="mt-1 text-xs text-emerald-200/80">
                  Key prefix: {me.api_key_prefix}
                </div>
              </div>
            )}

            <label className="mt-5 block text-sm font-medium text-slate-300">
              Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={8}
              className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm leading-6 outline-none ring-emerald-400/40 focus:ring-2"
            />

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                onClick={sendPrompt}
                disabled={loading || !apiKey || !prompt}
                className="rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Protecting..." : "Send through SentinelProxy"}
              </button>

              <button
                onClick={() => {
                  setResponse(null);
                  setError("");
                }}
                className="rounded-xl border border-slate-700 px-5 py-3 font-semibold text-slate-300 transition hover:bg-slate-800"
              >
                Clear response
              </button>
            </div>

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
              Privacy, budget, rate limit, and gateway metadata.
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
                  label="User ID"
                  value={response.sentinel.user_id || "Unknown"}
                />
                <Metric
                  label="API Key Prefix"
                  value={response.sentinel.api_key_prefix || "Unknown"}
                />
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

                <Panel title="Entity Counts">
                  {Object.keys(response.sentinel.entity_counts || {}).length ===
                  0 ? (
                    <p className="text-slate-500">No entities detected.</p>
                  ) : (
                    <div className="space-y-2">
                      {Object.entries(response.sentinel.entity_counts).map(
                        ([key, value]) => (
                          <Metric key={key} label={key} value={String(value)} />
                        )
                      )}
                    </div>
                  )}
                </Panel>

                {response.sentinel.budget && (
                  <Panel title="Budget">
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
                  </Panel>
                )}

                {response.sentinel.rate_limit && (
                  <Panel title="Rate Limit">
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
                  </Panel>
                )}

                {(response.sentinel.unreplaced_placeholders?.length > 0 ||
                  response.sentinel.repaired_placeholders?.length > 0) && (
                  <Panel title="Placeholder Diagnostics">
                    <Metric
                      label="Unreplaced"
                      value={
                        response.sentinel.unreplaced_placeholders.join(", ") ||
                        "None"
                      }
                    />
                    <Metric
                      label="Repaired"
                      value={
                        response.sentinel.repaired_placeholders.join(", ") ||
                        "None"
                      }
                    />
                  </Panel>
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

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl bg-slate-950 p-4">
      <h3 className="mb-3 font-semibold text-slate-300">{title}</h3>
      {children}
    </div>
  );
}

function StatusRow({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-slate-400">{label}</span>
      <span className={ok ? "text-emerald-300" : "text-red-300"}>
        ● {value}
      </span>
    </div>
  );
}

function formatApiError(status: number, detail: string) {
  if (status === 401) {
    return detail || "Invalid or missing API key.";
  }

  if (status === 429) {
    return detail || "Rate limit or budget exceeded.";
  }

  if (status === 503) {
    return detail || "A backend dependency is unavailable.";
  }

  return detail || `Request failed with status ${status}.`;
}