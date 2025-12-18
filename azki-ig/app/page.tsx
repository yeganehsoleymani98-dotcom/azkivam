"use client";

import { useMemo, useState, useTransition } from "react";
import { logResponse } from "./actions";

type Contact = {
  id: string;
  name: string;
  username: string;
  status: string;
  accent: string;
  preview: string;
  lastActivity: string;
  unreadCount?: number;
};

type Message = {
  id: string;
  from: "me" | "contact";
  text: string;
  time: string;
};

const CONTACTS: Contact[] = [
  {
    id: "leila",
    name: "Leila Rahimi",
    username: "leila.r",
    status: "Active now",
    accent: "from-[#8b5cf6] via-[#d946ef] to-[#fb7185]",
    preview: "Can we ship this today?",
    lastActivity: "1h",
  },
  {
    id: "dylan",
    name: "Dylan Fox",
    username: "dyl.foxx",
    status: "Online",
    accent: "from-[#22d3ee] to-[#6366f1]",
    preview: "Heading to the studio",
    lastActivity: "5m",
    unreadCount: 2,
  },
  {
    id: "maya",
    name: "Maya Costa",
    username: "maya.costa",
    status: "On mobile",
    accent: "from-[#f97316] to-[#f43f5e]",
    preview: "Let me know what you think.",
    lastActivity: "32m",
  },
  {
    id: "amir",
    name: "Amir Hosseini",
    username: "amir.h",
    status: "Notifications on",
    accent: "from-[#34d399] to-[#10b981]",
    preview: "Bringing snacks for the shoot.",
    lastActivity: "1d",
  },
];

const INITIAL_THREADS: Record<string, Message[]> = {
  leila: [
    {
      id: "l1",
      from: "contact",
      text: "Did you see the new landing mockups?",
      time: "9:58",
    },
    {
      id: "l2",
      from: "me",
      text: "Yep, iterating on the hero state now.",
      time: "10:01",
    },
    {
      id: "l3",
      from: "contact",
      text: "Can we ship this today?",
      time: "10:04",
    },
  ],
  dylan: [
    {
      id: "d1",
      from: "contact",
      text: "Heading to the studio now.",
      time: "8:14",
    },
    {
      id: "d2",
      from: "me",
      text: "Perfect, I'll prep the brief.",
      time: "8:16",
    },
  ],
  maya: [
    {
      id: "m1",
      from: "contact",
      text: "Uploaded the edit you wanted.",
      time: "Yesterday",
    },
    {
      id: "m2",
      from: "contact",
      text: "Let me know what you think.",
      time: "Yesterday",
    },
  ],
  amir: [
    {
      id: "a1",
      from: "contact",
      text: "Bringing snacks for the shoot.",
      time: "Mon",
    },
  ],
};

function Avatar({
  name,
  accent,
  size = "md",
}: {
  name: string;
  accent: string;
  size?: "sm" | "md";
}) {
  const initials = name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const sizeClass = size === "sm" ? "h-10 w-10 text-xs" : "h-12 w-12 text-sm";

  return (
    <div
      className={`flex items-center justify-center rounded-full bg-gradient-to-br ${accent} ${sizeClass} font-semibold uppercase text-white shadow-md shadow-zinc-300/60`}
    >
      {initials}
    </div>
  );
}

export default function ChatPage() {
  const [selectedId, setSelectedId] = useState(CONTACTS[0]?.id ?? "");
  const [threads, setThreads] =
    useState<Record<string, Message[]>>(INITIAL_THREADS);
  const [input, setInput] = useState("");
  const [isPending, startTransition] = useTransition();

  const contactsWithPreview = useMemo(
    () =>
      CONTACTS.map((contact) => {
        const thread = threads[contact.id];
        const lastMessage = thread?.[thread.length - 1];
        return {
          ...contact,
          preview: lastMessage?.text ?? contact.preview,
          lastActivity: lastMessage?.time ?? contact.lastActivity,
        };
      }),
    [threads],
  );

  const activeContact =
    contactsWithPreview.find((contact) => contact.id === selectedId) ??
    contactsWithPreview[0];

  const activeMessages = activeContact
    ? threads[activeContact.id] ?? []
    : [];

  const handleSend = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const text = input.trim();

    if (!text || !activeContact) return;

    const timestamp = new Date().toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });

    const outgoing: Message = {
      id: `${activeContact.id}-${Date.now()}`,
      from: "me",
      text,
      time: timestamp,
    };

    setThreads((prev) => {
      const thread = prev[activeContact.id] ?? [];
      return {
        ...prev,
        [activeContact.id]: [...thread, outgoing],
      };
    });
    setInput("");

    startTransition(async () => {
      await logResponse({ recipientId: activeContact.id, body: text });
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-100 via-white to-white text-zinc-900">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 lg:px-6">
        <div className="flex flex-col gap-2">
          <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
            Direct
          </p>
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-semibold tracking-tight">Messages</h1>
            <button className="hidden rounded-full bg-black px-4 py-2 text-sm font-medium text-white shadow-lg shadow-black/10 transition hover:-translate-y-0.5 hover:shadow-xl active:translate-y-0 lg:inline-flex">
              New message
            </button>
          </div>
          <p className="text-sm text-zinc-500">
            A clean inbox styled after Instagram DMs.
          </p>
        </div>

        <div className="flex h-[76vh] flex-col overflow-hidden rounded-3xl border border-zinc-200 bg-white shadow-xl shadow-zinc-200/60 ring-1 ring-zinc-100/60 lg:flex-row">
          <aside className="flex flex-row gap-3 border-b border-zinc-100 bg-zinc-50/80 px-4 py-3 lg:h-full lg:w-[320px] lg:flex-col lg:border-b-0 lg:border-r">
            <div className="flex w-full items-center gap-2 rounded-2xl border border-zinc-200 bg-white px-3 py-2 shadow-sm">
              <span className="text-xs font-semibold text-zinc-400">Search</span>
              <input
                className="w-full bg-transparent text-sm text-zinc-600 placeholder:text-zinc-400 focus:outline-none"
                placeholder="Find a conversation"
              />
            </div>

            <div className="hidden flex-1 flex-col gap-2 overflow-y-auto pt-1 lg:flex">
              {contactsWithPreview.map((contact) => (
                <button
                  key={contact.id}
                  onClick={() => setSelectedId(contact.id)}
                  className={`group flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition ${
                    contact.id === activeContact?.id
                      ? "bg-white shadow-sm ring-1 ring-zinc-200"
                      : "hover:bg-white/70"
                  }`}
                >
                  <Avatar name={contact.name} accent={contact.accent} />
                  <div className="flex flex-1 flex-col">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-zinc-900">
                        {contact.name}
                      </span>
                      {contact.unreadCount ? (
                        <span className="rounded-full bg-rose-500 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-tight text-white">
                          {contact.unreadCount}
                        </span>
                      ) : null}
                    </div>
                    <p className="text-xs text-zinc-500">{contact.preview}</p>
                  </div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-zinc-400">
                    {contact.lastActivity}
                  </span>
                </button>
              ))}
            </div>

            <div className="flex w-full gap-2 overflow-x-auto lg:hidden">
              {contactsWithPreview.map((contact) => (
                <button
                  key={contact.id}
                  onClick={() => setSelectedId(contact.id)}
                  className={`flex min-w-[120px] flex-col items-center gap-2 rounded-2xl border px-3 py-3 text-center transition ${
                    contact.id === activeContact?.id
                      ? "border-zinc-300 bg-white shadow-sm"
                      : "border-transparent bg-white/60"
                  }`}
                >
                  <Avatar name={contact.name} accent={contact.accent} size="sm" />
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold text-zinc-800">
                      {contact.name.split(" ")[0]}
                    </span>
                    <span className="text-[10px] text-zinc-500">
                      {contact.lastActivity}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <section className="flex flex-1 flex-col">
            <header className="flex items-center justify-between border-b border-zinc-100 px-6 py-4">
              <div className="flex items-center gap-3">
                {activeContact ? (
                  <>
                    <Avatar
                      name={activeContact.name}
                      accent={activeContact.accent}
                      size="sm"
                    />
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold text-zinc-900">
                        {activeContact.name}{" "}
                        <span className="text-zinc-400">
                          @{activeContact.username}
                        </span>
                      </span>
                      <span className="text-xs text-emerald-500">
                        {activeContact.status}
                      </span>
                    </div>
                  </>
                ) : (
                  <span className="text-sm text-zinc-500">
                    Select a thread
                  </span>
                )}
              </div>
              <div className="hidden items-center gap-2 lg:flex">
                {["Call", "Video", "More"].map((label) => (
                  <button
                    key={label}
                    className="rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-600 transition hover:-translate-y-0.5 hover:border-black hover:text-black active:translate-y-0"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </header>

            <div className="flex-1 space-y-6 overflow-y-auto bg-gradient-to-b from-white via-white to-zinc-50 px-4 py-6 sm:px-8">
              <div className="flex justify-center">
                <span className="rounded-full bg-zinc-100 px-3 py-1 text-[11px] font-medium uppercase tracking-tight text-zinc-500">
                  Today
                </span>
              </div>

              {activeMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.from === "me" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[72%] rounded-2xl px-4 py-3 text-sm shadow-sm transition ${
                      message.from === "me"
                        ? "bg-gradient-to-r from-indigo-500 to-fuchsia-500 text-white shadow-indigo-100"
                        : "bg-zinc-100 text-zinc-900"
                    }`}
                  >
                    <p className="leading-relaxed">{message.text}</p>
                    <div
                      className={`mt-2 flex items-center gap-2 text-[11px] ${
                        message.from === "me"
                          ? "text-white/70"
                          : "text-zinc-500"
                      }`}
                    >
                      <span>{message.time}</span>
                      {message.from === "me" && (
                        <>
                          <span className="h-1 w-1 rounded-full bg-white/50" />
                          <span>Seen</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {activeMessages.length === 0 && (
                <div className="flex h-full items-center justify-center text-sm text-zinc-500">
                  Start the conversation with a quick hello.
                </div>
              )}
            </div>

            <form
              onSubmit={handleSend}
              className="border-t border-zinc-100 bg-white/90 px-4 py-4 backdrop-blur sm:px-8"
            >
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  className="hidden h-10 w-10 items-center justify-center rounded-full border border-zinc-200 text-lg font-semibold text-zinc-500 transition hover:-translate-y-0.5 hover:border-black hover:text-black active:translate-y-0 sm:flex"
                  aria-label="Add media"
                >
                  +
                </button>
                <div className="flex flex-1 items-center gap-3 rounded-full border border-zinc-200 bg-zinc-50 px-4 py-2 shadow-inner shadow-zinc-200 focus-within:border-indigo-500 focus-within:bg-white">
                  <input
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    placeholder={
                      activeContact
                        ? `Message ${activeContact.name}`
                        : "Choose a conversation"
                    }
                    className="w-full bg-transparent text-sm text-zinc-700 placeholder:text-zinc-400 focus:outline-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="rounded-full bg-gradient-to-r from-indigo-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-fuchsia-200 transition hover:-translate-y-0.5 hover:shadow-xl active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Send
                </button>
              </div>
              <p className="mt-2 text-[11px] text-zinc-400">
                Responses are logged server-side for now.{" "}
                {isPending ? "Sending..." : ""}
              </p>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
