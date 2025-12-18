"use server";

type LogResponseInput = {
  recipientId: string;
  body: string;
};

export async function logResponse({ recipientId, body }: LogResponseInput) {
  const trimmed = body?.toString().trim();

  if (!trimmed) {
    console.log(`[DM Response] ignored empty message for ${recipientId}`);
    return { ok: false };
  }

  console.log(`[DM Response] to ${recipientId}: ${trimmed}`);

  return {
    ok: true,
    recipientId,
    at: new Date().toISOString(),
  };
}
