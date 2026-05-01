export default function LandingPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-10">
        <nav className="flex items-center justify-between">
          <div className="text-lg font-bold tracking-tight">
            SentinelProxy
          </div>

          <div className="flex items-center gap-3 text-sm">
            <a
              href="/chat"
              className="rounded-lg border border-slate-700 px-4 py-2 text-slate-300 hover:bg-slate-900"
            >
              Open Chat
            </a>
            <a
              href="/admin"
              className="rounded-lg bg-emerald-400 px-4 py-2 font-semibold text-slate-950 hover:bg-emerald-300"
            >
              Admin Console
            </a>
          </div>
        </nav>

        <section className="grid flex-1 items-center gap-12 py-20 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <div className="inline-flex rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
              Local-first privacy gateway for LLM apps
            </div>

            <h1 className="mt-6 max-w-4xl text-5xl font-bold tracking-tight text-slate-50 md:text-6xl">
              Protect sensitive data before it reaches an AI model.
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              SentinelProxy is an OpenAI-compatible security proxy that redacts
              PII locally, stores temporary mappings in Redis, forwards only
              protected placeholders to the model, then restores the response
              safely for the user.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <a
                href="/chat"
                className="rounded-xl bg-emerald-400 px-6 py-3 font-semibold text-slate-950 shadow-lg shadow-emerald-400/10 hover:bg-emerald-300"
              >
                Use Protected Chat
              </a>

              <a
                href="/admin"
                className="rounded-xl border border-slate-700 px-6 py-3 font-semibold text-slate-300 hover:bg-slate-900"
              >
                Manage Users & Keys
              </a>
            </div>

            <p className="mt-5 text-sm text-slate-500">
              Need access? Ask your SentinelProxy admin for a{" "}
              <code className="rounded bg-slate-900 px-1.5 py-0.5 text-slate-300">
                sp_live_...
              </code>{" "}
              API key.
            </p>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl">
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
              <div className="mb-4 flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-red-400" />
                <span className="h-3 w-3 rounded-full bg-yellow-400" />
                <span className="h-3 w-3 rounded-full bg-emerald-400" />
              </div>

              <div className="space-y-4 text-sm">
                <div>
                  <p className="mb-2 text-slate-500">Raw user prompt</p>
                  <div className="rounded-xl border border-red-400/20 bg-red-400/10 p-4 text-red-100">
                    My email is sahil@example.com and my phone is 413-555-0199.
                    Summarize this.
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-slate-500">Model receives</p>
                  <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-emerald-100">
                    My email is &lt;&lt;SP_EMAIL_1&gt;&gt; and my phone is
                    &lt;&lt;SP_PHONE_1&gt;&gt;. Summarize this.
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-slate-500">Sentinel Report</p>
                  <div className="grid grid-cols-2 gap-3">
                    <MiniStat label="Redactions" value="2" />
                    <MiniStat label="Risk Score" value="0.2" />
                    <MiniStat label="Mapping Store" value="Redis" />
                    <MiniStat label="Provider" value="Ollama" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 pb-12 md:grid-cols-3">
          <FeatureCard
            title="For users"
            description="Paste your assigned API key and use the protected chat UI to safely send prompts containing sensitive information."
          />
          <FeatureCard
            title="For admins"
            description="Create users, issue API keys, revoke access, update budgets, and monitor safe usage analytics."
          />
          <FeatureCard
            title="For developers"
            description="Call the OpenAI-compatible /v1/chat/completions endpoint with Bearer auth and get redaction, budgets, and audits built in."
          />
        </section>
      </div>
    </main>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 font-semibold text-slate-100">{value}</p>
    </div>
  );
}

function FeatureCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <h2 className="font-semibold text-slate-100">{title}</h2>
      <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
    </div>
  );
}