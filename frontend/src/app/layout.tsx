import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "CreditMate",
  description:
    "Understand, manage and pay down your credit card debt — and see what a purchase really costs.",
  applicationName: "CreditMate",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#f5f8fc",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en-GB" className={`${jakarta.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full">
        {/*
          Paint the stored colour scheme before anything renders, so a dark- or
          cream-mode user never sees a flash of the light theme. Mirrors the keys
          read by lib/state/theme.tsx.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var d=document.documentElement;var m=localStorage.getItem('creditmate-theme')||'light';var a=localStorage.getItem('creditmate-accent')||'indigo';d.dataset.theme=(m==='dark'||m==='cream')?m:'light';d.dataset.accent=(a==='ocean'||a==='rose'||a==='amber')?a:'indigo';d.style.colorScheme=d.dataset.theme==='dark'?'dark':'light';}catch(e){}})();",
          }}
        />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
