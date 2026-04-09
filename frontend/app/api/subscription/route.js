import { NextResponse } from "next/server";

const backendBase =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://127.0.0.1:5050";

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const email = searchParams.get("email") || "";
    const res = await fetch(
      `${backendBase}/api/v1/subscription?email=${encodeURIComponent(email)}`,
      { cache: "no-store" }
    );
    const json = await res.json();
    return NextResponse.json(json, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { status: "error", message: "Subscription lookup unavailable", detail: String(error) },
      { status: 502 }
    );
  }
}
