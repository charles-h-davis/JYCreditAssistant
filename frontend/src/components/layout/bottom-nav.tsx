"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, GraduationCap, Home, MessageSquare, Tag } from "lucide-react";

const ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: Home, match: ["/dashboard"] },
  { href: "/purchase", label: "Check Purchase", icon: Tag, match: ["/purchase"] },
  { href: "/assistant", label: "AI Assistant", icon: MessageSquare, match: ["/assistant"] },
  {
    href: "/transactions",
    label: "Transactions",
    icon: BarChart3,
    match: ["/transactions"],
  },
  { href: "/learning", label: "Learning", icon: GraduationCap, match: ["/learning"] },
];

/**
 * The five-item bottom nav from the dashboard design ref. The active tab gets a
 * soft-filled rounded square — a subtle highlight rather than a colour block.
 */
export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main"
      className="pointer-events-auto fixed inset-x-0 bottom-0 z-40 mx-auto w-full max-w-[430px] px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))]"
    >
      <ul className="flex items-center justify-between gap-1 rounded-full bg-surface/95 px-2 py-2 shadow-soft backdrop-blur-md">
        {ITEMS.map((item) => {
          const active = item.match.some((prefix) => pathname.startsWith(prefix));
          const Icon = item.icon;
          return (
            <li key={item.href} className="flex-1">
              <Link
                href={item.href}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className="flex h-11 items-center justify-center"
              >
                <span
                  className={`grid size-11 place-items-center rounded-[14px] transition-colors duration-200 ${
                    active ? "bg-accent-soft text-ink" : "text-ink-soft/70"
                  }`}
                >
                  <Icon
                    size={22}
                    strokeWidth={active ? 2.1 : 1.8}
                    aria-hidden
                  />
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
