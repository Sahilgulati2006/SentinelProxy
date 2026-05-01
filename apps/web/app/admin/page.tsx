"use client";

import { useEffect, useState } from "react";

type User = {
  id: string;
  email: string;
  monthly_token_limit: number;
  is_active: boolean;
  created_at: string;
};

type ApiKey = {
  id: string;
  user_id: string;
  key_prefix: string;
  name: string;
  is_active: boolean;
  created_at: string;
};

type CreatedApiKey = ApiKey & {
  api_key: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState("");
  const [saveAdminKey, setSaveAdminKey] = useState(false);

  const [users, setUsers] = useState<User[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);

  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserBudget, setNewUserBudget] = useState("100000");

  const [selectedUserId, setSelectedUserId] = useState("");
  const [newKeyName, setNewKeyName] = useState("default");

  const [budgetUserId, setBudgetUserId] = useState("");
  const [updatedBudget, setUpdatedBudget] = useState("100000");

  const [createdApiKey, setCreatedApiKey] = useState<CreatedApiKey | null>(
    null
  );

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem("sentinel_admin_key");
    if (stored) {
      setAdminKey(stored);
      setSaveAdminKey(true);
    }
  }, []);

  useEffect(() => {
    if (saveAdminKey && adminKey) {
      localStorage.setItem("sentinel_admin_key", adminKey);
    }

    if (!saveAdminKey) {
      localStorage.removeItem("sentinel_admin_key");
    }
  }, [saveAdminKey, adminKey]);

  function adminHeaders() {
    return {
      "Content-Type": "application/json",
      "X-Admin-Key": adminKey,
    };
  }

  function resetNotices() {
    setMessage("");
    setError("");
  }

  async function loadAdminData() {
    if (!adminKey) {
      setError("Enter your admin key first.");
      return;
    }

    setLoading(true);
    resetNotices();

    try {
      const [usersRes, keysRes] = await Promise.all([
        fetch(`${API_BASE_URL}/v1/admin/users`, {
          headers: {
            "X-Admin-Key": adminKey,
          },
        }),
        fetch(`${API_BASE_URL}/v1/admin/api-keys`, {
          headers: {
            "X-Admin-Key": adminKey,
          },
        }),
      ]);

      const usersData = await usersRes.json();
      const keysData = await keysRes.json();

      if (!usersRes.ok) {
        throw new Error(formatApiError(usersRes.status, usersData.detail));
      }

      if (!keysRes.ok) {
        throw new Error(formatApiError(keysRes.status, keysData.detail));
      }

      setUsers(usersData);
      setApiKeys(keysData);
      setMessage("Admin data loaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  }

  async function createUser() {
    if (!newUserEmail) {
      setError("Enter an email for the new user.");
      return;
    }

    setLoading(true);
    resetNotices();

    try {
      const res = await fetch(`${API_BASE_URL}/v1/admin/users`, {
        method: "POST",
        headers: adminHeaders(),
        body: JSON.stringify({
          email: newUserEmail,
          monthly_token_limit: Number(newUserBudget),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(formatApiError(res.status, data.detail));
      }

      setMessage(`Created user: ${data.email}`);
      setNewUserEmail("");
      setNewUserBudget("100000");
      await loadAdminData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create user.");
    } finally {
      setLoading(false);
    }
  }

  async function createApiKey() {
    if (!selectedUserId) {
      setError("Select a user first.");
      return;
    }

    setLoading(true);
    resetNotices();
    setCreatedApiKey(null);

    try {
      const res = await fetch(`${API_BASE_URL}/v1/admin/api-keys`, {
        method: "POST",
        headers: adminHeaders(),
        body: JSON.stringify({
          user_id: selectedUserId,
          name: newKeyName || "default",
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(formatApiError(res.status, data.detail));
      }

      setCreatedApiKey(data);
      setMessage("API key created. Copy it now. It will not be shown again.");
      setNewKeyName("default");
      await loadAdminData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create API key.");
    } finally {
      setLoading(false);
    }
  }

  async function revokeApiKey(keyId: string) {
    const confirmed = window.confirm(
      "Are you sure you want to revoke this API key?"
    );

    if (!confirmed) {
      return;
    }

    setLoading(true);
    resetNotices();

    try {
      const res = await fetch(
        `${API_BASE_URL}/v1/admin/api-keys/${keyId}/revoke`,
        {
          method: "POST",
          headers: {
            "X-Admin-Key": adminKey,
          },
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(formatApiError(res.status, data.detail));
      }

      setMessage(`Revoked API key: ${data.key_prefix}`);
      await loadAdminData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke API key.");
    } finally {
      setLoading(false);
    }
  }

  async function deactivateUser(userId: string) {
    const confirmed = window.confirm(
        "Are you sure you want to delete this user? This will deactivate the user and revoke all their API keys."
    );

    if (!confirmed) {
        return;
    }

    setLoading(true);
    resetNotices();

    try {
        const res = await fetch(
        `${API_BASE_URL}/v1/admin/users/${userId}/deactivate`,
        {
            method: "POST",
            headers: {
            "X-Admin-Key": adminKey,
            },
        }
        );

        const data = await res.json();

        if (!res.ok) {
        throw new Error(formatApiError(res.status, data.detail));
        }

        setMessage(`Deleted user: ${data.email}`);
        await loadAdminData();
    } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete user.");
    } finally {
        setLoading(false);
    }
    }

  async function updateBudget() {
    if (!budgetUserId) {
      setError("Select a user first.");
      return;
    }

    setLoading(true);
    resetNotices();

    try {
      const res = await fetch(
        `${API_BASE_URL}/v1/admin/users/${budgetUserId}/budget`,
        {
          method: "PATCH",
          headers: adminHeaders(),
          body: JSON.stringify({
            monthly_token_limit: Number(updatedBudget),
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(formatApiError(res.status, data.detail));
      }

      setMessage(`Updated budget for ${data.email}.`);
      await loadAdminData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update budget.");
    } finally {
      setLoading(false);
    }
  }

  function clearAdminSession() {
    setAdminKey("");
    setSaveAdminKey(false);
    setUsers([]);
    setApiKeys([]);
    setCreatedApiKey(null);
    setMessage("");
    setError("");
    localStorage.removeItem("sentinel_admin_key");
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10">
        <header className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
          <div>
            <a
              href="/"
              className="text-sm text-emerald-300 hover:text-emerald-200"
            >
              ← Back to Protected Chat
            </a>

            <h1 className="mt-4 text-4xl font-bold tracking-tight">
              SentinelProxy Admin
            </h1>
            <p className="mt-3 max-w-2xl text-slate-300">
              Manage users, API keys, revocation, and monthly token budgets.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl lg:min-w-96">
            <h2 className="font-semibold">Admin Access</h2>

            <label className="mt-4 block text-sm font-medium text-slate-300">
              Admin Key
            </label>
            <input
              value={adminKey}
              onChange={(e) => {
                setAdminKey(e.target.value);
                setUsers([]);
                setApiKeys([]);
                setCreatedApiKey(null);
                setMessage("");
                setError("");
              }}
              placeholder="sp_admin_..."
              type="password"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            />

            <div className="mt-3 flex items-center justify-between gap-3">
              <label className="flex items-center gap-2 text-sm text-slate-400">
                <input
                  checked={saveAdminKey}
                  onChange={(e) => setSaveAdminKey(e.target.checked)}
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-700"
                />
                Save admin key locally
              </label>

              <button
                onClick={clearAdminSession}
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"
              >
                Clear
              </button>
            </div>

            <button
              onClick={loadAdminData}
              disabled={!adminKey || loading}
              className="mt-5 w-full rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Loading..." : "Load Admin Data"}
            </button>
          </div>
        </header>

        {message && (
          <div className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 p-4 text-sm text-emerald-100">
            {message}
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-400/30 bg-red-400/10 p-4 text-sm text-red-200">
            {error}
          </div>
        )}

        {createdApiKey && (
          <section className="rounded-2xl border border-yellow-400/30 bg-yellow-400/10 p-6 shadow-xl">
            <h2 className="text-xl font-semibold text-yellow-100">
              New API Key Created
            </h2>
            <p className="mt-2 text-sm text-yellow-100/80">
              Copy this key now. It will not be shown again.
            </p>

            <div className="mt-4 rounded-xl border border-yellow-400/20 bg-slate-950 p-4">
              <code className="break-all text-yellow-100">
                {createdApiKey.api_key}
              </code>
            </div>

            <button
              onClick={() => navigator.clipboard.writeText(createdApiKey.api_key)}
              className="mt-4 rounded-lg bg-yellow-300 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-yellow-200"
            >
              Copy key
            </button>
          </section>
        )}

        <section className="grid gap-6 lg:grid-cols-3">
          <Panel title="Create User">
            <label className="block text-sm font-medium text-slate-300">
              Email
            </label>
            <input
              value={newUserEmail}
              onChange={(e) => setNewUserEmail(e.target.value)}
              placeholder="user@example.com"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            />

            <label className="mt-4 block text-sm font-medium text-slate-300">
              Monthly Token Limit
            </label>
            <input
              value={newUserBudget}
              onChange={(e) => setNewUserBudget(e.target.value)}
              type="number"
              min="1"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            />

            <button
              onClick={createUser}
              disabled={!adminKey || loading}
              className="mt-5 w-full rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Create User
            </button>
          </Panel>

          <Panel title="Create API Key">
            <label className="block text-sm font-medium text-slate-300">
              User
            </label>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            >
              <option value="">Select user</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.email}
                </option>
              ))}
            </select>

            <label className="mt-4 block text-sm font-medium text-slate-300">
              Key Name
            </label>
            <input
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="production-key"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            />

            <button
              onClick={createApiKey}
              disabled={!adminKey || !selectedUserId || loading}
              className="mt-5 w-full rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Create API Key
            </button>
          </Panel>

          <Panel title="Update Budget">
            <label className="block text-sm font-medium text-slate-300">
              User
            </label>
            <select
              value={budgetUserId}
              onChange={(e) => setBudgetUserId(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            >
              <option value="">Select user</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.email}
                </option>
              ))}
            </select>

            <label className="mt-4 block text-sm font-medium text-slate-300">
              New Monthly Token Limit
            </label>
            <input
              value={updatedBudget}
              onChange={(e) => setUpdatedBudget(e.target.value)}
              type="number"
              min="1"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-emerald-400/40 focus:ring-2"
            />

            <button
              onClick={updateBudget}
              disabled={!adminKey || !budgetUserId || loading}
              className="mt-5 w-full rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Update Budget
            </button>
          </Panel>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <Panel title={`Users (${users.length})`}>
            <div className="space-y-3">
              {users.length === 0 ? (
                <p className="text-sm text-slate-400">
                  No users loaded. Click Load Admin Data.
                </p>
              ) : (
                users.map((user) => (
                  <div
                    key={user.id}
                    className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-medium text-slate-100">
                          {user.email}
                        </p>
                        <p className="mt-1 break-all text-xs text-slate-500">
                          {user.id}
                        </p>
                      </div>
                      <StatusBadge active={user.is_active} />
                    </div>

                    <div className="mt-3 text-sm text-slate-400">
                      Monthly limit:{" "}
                      <span className="text-slate-200">
                        {user.monthly_token_limit}
                      </span>
                    </div>

                    {user.is_active && (
                        <button
                            onClick={() => deactivateUser(user.id)}
                            disabled={loading}
                            className="mt-4 rounded-lg border border-red-400/30 px-3 py-2 text-sm text-red-200 hover:bg-red-400/10 disabled:opacity-50"
                        >
                            Delete User
                        </button>
                        )}
                  </div>
                ))
              )}
            </div>
          </Panel>

          <Panel title={`API Keys (${apiKeys.length})`}>
            <div className="space-y-3">
              {apiKeys.length === 0 ? (
                <p className="text-sm text-slate-400">
                  No API keys loaded. Click Load Admin Data.
                </p>
              ) : (
                apiKeys.map((key) => (
                  <div
                    key={key.id}
                    className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-medium text-slate-100">{key.name}</p>
                        <p className="mt-1 text-sm text-slate-400">
                          Prefix:{" "}
                          <span className="text-slate-200">
                            {key.key_prefix}
                          </span>
                        </p>
                        <p className="mt-1 break-all text-xs text-slate-500">
                          Key ID: {key.id}
                        </p>
                        <p className="mt-1 break-all text-xs text-slate-500">
                          User ID: {key.user_id}
                        </p>
                      </div>

                      <StatusBadge active={key.is_active} />
                    </div>

                    {key.is_active && (
                      <button
                        onClick={() => revokeApiKey(key.id)}
                        disabled={loading}
                        className="mt-4 rounded-lg border border-red-400/30 px-3 py-2 text-sm text-red-200 hover:bg-red-400/10 disabled:opacity-50"
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </Panel>
        </section>
      </div>
    </main>
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
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
      <h2 className="mb-5 text-xl font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span
      className={
        active
          ? "rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300"
          : "rounded-full border border-red-400/30 bg-red-400/10 px-3 py-1 text-xs text-red-300"
      }
    >
      {active ? "Active" : "Inactive"}
    </span>
  );
}

function formatApiError(status: number, detail: string) {
  if (status === 401) {
    return detail || "Invalid or missing admin key.";
  }

  if (status === 404) {
    return detail || "Resource not found.";
  }

  if (status === 409) {
    return detail || "Resource already exists.";
  }

  if (status === 422) {
    return detail || "Invalid request payload.";
  }

  return detail || `Request failed with status ${status}.`;
}