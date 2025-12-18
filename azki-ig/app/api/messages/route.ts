import { NextRequest, NextResponse } from "next/server";

type InboundMessagePayload = {
  from?: string;
  message?: string;
  threadId?: string;
};

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as InboundMessagePayload;
    const from = payload.from ?? "unknown";
    const body = payload.message ?? "";
    const thread = payload.threadId ?? "dm";

    if (!body.trim()) {
      return NextResponse.json(
        { ok: false, error: "Message body is required" },
        { status: 400 },
      );
    }

    console.log(`[Inbound DM] thread=${thread} from=${from}: ${body}`);

    return NextResponse.json({ ok: true, received: true });
  } catch (error) {
    console.error("[Inbound DM] failed to read payload", error);
    return NextResponse.json(
      { ok: false, error: "Invalid JSON payload" },
      { status: 400 },
    );
  }
}

export async function GET() {
  return NextResponse.json({
    ok: true,
    message: "Send a POST request with { from, message, threadId? }",
  });
}
