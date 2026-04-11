import "./globals.css";

export const metadata = {
  title: "PDFforge — Open-source PDF toolkit for privacy-first teams",
  description:
    "Open-source PDF toolkit by IntelliForge AI. Merge, split, rotate, extract, encrypt PDFs on your own infrastructure. No cloud uploads.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://pdfforge.intelliforge.tech"
  ),
  openGraph: {
    title: "PDFforge — Open-source PDF toolkit",
    description:
      "Stop routing sensitive PDFs through someone else's cloud. Self-host or use our hosted plan.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PDFforge",
    description:
      "Open-source, privacy-first PDF ops. Merge, split, encrypt — your files never leave your machine.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
