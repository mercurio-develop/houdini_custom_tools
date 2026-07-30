import Link from "next/link";

export const metadata = {
  title: "Production Hub Dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui", margin: 0 }}>
        <div style={{ padding: "1.5rem 2rem", maxWidth: 960, margin: "0 auto" }}>
          <nav
            style={{
              display: "flex",
              gap: "1.25rem",
              marginBottom: "1.5rem",
              borderBottom: "1px solid #ddd",
              paddingBottom: "0.75rem",
            }}
          >
            <Link href="/">Tasks</Link>
            <Link href="/about">Pipeline</Link>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
