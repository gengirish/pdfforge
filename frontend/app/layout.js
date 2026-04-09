import "./globals.css";

export const metadata = {
  title: "PDFforge | Local-First PDF Ops",
  description:
    "Local-first PDF workflow platform for ops teams. Merge, split, rotate, extract, encrypt, and validate demand with a built-in waitlist funnel.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://hire-with-giri.vercel.app"
  ),
  openGraph: {
    title: "PDFforge | Local-First PDF Ops",
    description:
      "Fix broken document workflows in minutes. Merge, split, rotate, extract, encrypt PDFs locally.",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "PDFforge",
    description:
      "Local-first PDF ops for lean teams. No cloud upload by default.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
