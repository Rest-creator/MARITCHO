import type { Metadata } from "next";

import { ChatScreen } from "@/features/messaging/ChatScreen";

export const metadata: Metadata = { title: "Messages" };

type Props = { params: Promise<{ jobId: string }> };

export default async function ChatPage({ params }: Props) {
  const { jobId } = await params;
  return <ChatScreen jobId={jobId} />;
}
