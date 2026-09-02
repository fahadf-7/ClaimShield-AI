import { ShieldCheck } from "lucide-react";

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand" aria-label="ClaimShield AI">
      <span className="brand-mark" aria-hidden="true">
        <ShieldCheck size={23} strokeWidth={2} />
      </span>
      {!compact && <span>ClaimShield AI</span>}
    </div>
  );
}

