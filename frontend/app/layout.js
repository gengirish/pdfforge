import "./globals.css";

export const metadata = {
  title: "PDFforge | Local-First PDF Ops",
  description:
    "Local-first PDF workflow platform for ops teams. Merge, split, rotate, extract, encrypt, and validate demand with a built-in waitlist funnel.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
