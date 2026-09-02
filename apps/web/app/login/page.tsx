"use client";

import { CheckCircle2, FileCheck2, LockKeyhole } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";
import { Brand } from "@/components/brand";
import { useAuth } from "@/lib/auth";
import { readableError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { login, user, ready } = useAuth();
  const [email, setEmail] = useState("reviewer@claimshield.local");
  const [password, setPassword] = useState("ClaimShield123!");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const errorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ready && user) router.replace("/dashboard");
  }, [ready, user, router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (caught) {
      setError(readableError(caught));
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-story" aria-labelledby="product-statement">
        <Brand />
        <div className="auth-copy">
          <p className="eyebrow">Verify first. Estimate second.</p>
          <h1 id="product-statement">Evidence you can review, not conclusions you must trust.</h1>
          <p>
            A human-led workspace for vehicle condition records, claim evidence, and transparent review.
          </p>
        </div>
        <div className="trust-row" aria-label="Platform principles">
          <span className="trust-item"><LockKeyhole size={16} aria-hidden="true" /> Private evidence</span>
          <span className="trust-item"><FileCheck2 size={16} aria-hidden="true" /> Auditable workflow</span>
          <span className="trust-item"><CheckCircle2 size={16} aria-hidden="true" /> Human decision</span>
        </div>
      </section>
      <section className="auth-panel" aria-labelledby="sign-in-heading">
        <div className="auth-card">
          <p className="eyebrow">Secure workspace</p>
          <h2 id="sign-in-heading">Welcome back</h2>
          <p>Sign in to review vehicle and claim evidence.</p>
          <form className="form-grid" onSubmit={submit} noValidate>
            {error && (
              <div className="error-box" role="alert" tabIndex={-1} ref={errorRef}>
                <strong>Sign-in failed.</strong> {error}
              </div>
            )}
            <div className="field">
              <label htmlFor="email">Email address</label>
              <input id="email" name="email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input id="password" name="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <button className="button button-primary button-block" type="submit" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in securely"}
            </button>
          </form>
          <div className="demo-credentials">
            Demo reviewer credentials are prefilled. Use only synthetic data in this environment.
          </div>
        </div>
      </section>
    </main>
  );
}

