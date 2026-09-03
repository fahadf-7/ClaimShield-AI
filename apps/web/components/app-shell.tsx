"use client";

import {
  CarFront,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Brand } from "@/components/brand";
import { useAuth } from "@/lib/auth";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/vehicles", label: "Vehicles", icon: CarFront },
  { href: "/policies", label: "Policies", icon: FileText },
  { href: "/claims", label: "Claims", icon: ClipboardList },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, ready, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  if (!ready || !user) {
    return (
      <main className="page" aria-busy="true">
        <div className="skeleton" />
      </main>
    );
  }

  const title = navigation.find((item) => pathname.startsWith(item.href))?.label ?? "Workspace";
  const initials = user.name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("");

  return (
    <div className="console">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      {menuOpen && (
        <button
          className="mobile-drawer-scrim"
          aria-label="Close navigation"
          onClick={() => setMenuOpen(false)}
        />
      )}
      <aside className={`sidebar ${menuOpen ? "open" : ""}`} aria-label="Primary navigation">
        <Brand />
        <nav className="sidebar-nav">
          {navigation.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link className={`nav-link ${active ? "active" : ""}`} href={href} key={href} aria-current={active ? "page" : undefined} onClick={() => setMenuOpen(false)}>
                <Icon size={20} aria-hidden="true" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <div className="user-row">
            <span className="avatar" aria-hidden="true">{initials}</span>
            <span>
              <strong>{user.name}</strong>
              <span>{user.role.toLowerCase()}</span>
            </span>
          </div>
          <button
            className="button button-secondary logout-button"
            onClick={() => {
              logout();
              router.replace("/login");
            }}
          >
            <LogOut size={18} aria-hidden="true" />
            Sign out
          </button>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <div className="topbar-title">
            <button
              className="button button-secondary mobile-menu"
              aria-label={menuOpen ? "Close navigation" : "Open navigation"}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((value) => !value)}
            >
              {menuOpen ? <X size={20} aria-hidden="true" /> : <Menu size={20} aria-hidden="true" />}
            </button>
            <span>{title}</span>
          </div>
          <span className="phase-pill">
            <ShieldCheck size={15} aria-hidden="true" />
            Phase 1 · Damage intelligence
          </span>
        </header>
        <main id="main-content">{children}</main>
      </div>
    </div>
  );
}
