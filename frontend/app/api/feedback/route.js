import { NextResponse } from "next/server";

const backendBase =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://127.0.0.1:5050";

export async function POST(request) {
  try {
    const payload = await request.json();
    const res = await fetch(`${backendBase}/api/v1/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    const json = await res.json();
    return NextResponse.json(json, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { status: "error", message: "Feedback unavailable", detail: String(error) },
      { status: 502 }
    );
  }
}
