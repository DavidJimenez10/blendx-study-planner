import {
  ActionIcon,
  Loader,
  Text,
  TextInput,
} from "@mantine/core";
import { IconSend } from "@tabler/icons-react";
import { useMutation } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { api, type ChatSource } from "../../api/client";
import styles from "./ChatPanel.module.css";

type ChatMessage =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; sources: ChatSource[] };

interface Props {
  planId: number;
}

const EmptyState = (
  <div className={styles.empty}>
    <Text className={styles.emptyText}>
      Ask a question about your uploaded documents.
    </Text>
  </div>
);

export default function ChatPanel({ planId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  const chatMutation = useMutation({
    mutationFn: (q: string) => api.chat(planId, q),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
      setTimeout(() => {
        listRef.current?.scrollTo({
          top: listRef.current.scrollHeight,
          behavior: "smooth",
        });
      }, 100);
    },
  });

  function handleSend() {
    const q = question.trim();
    if (!q || chatMutation.isPending) return;
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    chatMutation.mutate(q);
  }

  return (
    <div className={styles.panel}>
      <div className={styles.messages} ref={listRef}>
        {messages.length === 0 ? EmptyState : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`${styles.message} ${
                msg.role === "user" ? styles.messageUser : styles.messageAssistant
              }`}
            >
              <Text className={styles.messageContent}>{msg.content}</Text>
              {msg.role === "assistant" && msg.sources.length > 0 && (
                <div className={styles.sources}>
                  <Text className={styles.sourcesLabel}>Sources</Text>
                  {msg.sources.map((source, si) => (
                    <div key={si} className={styles.sourceItem}>
                      <Text className={styles.sourceDocName}>
                        {source.filename}
                      </Text>
                      <Text className={styles.sourceContent}>
                        {source.content.slice(0, 200)}
                        {source.content.length > 200 ? "..." : ""}
                      </Text>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        {chatMutation.isPending && (
          <div className={styles.messageAssistant}>
            <Loader color="cyan" size="xs" />
          </div>
        )}
      </div>
      <div className={styles.inputRow}>
        <TextInput
          placeholder="Ask a question about your documents..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={chatMutation.isPending}
          className={styles.input}
          rightSection={
            <ActionIcon
              variant="subtle"
              color="cyan"
              onClick={handleSend}
              loading={chatMutation.isPending}
              disabled={!question.trim() || chatMutation.isPending}
            >
              <IconSend size={16} />
            </ActionIcon>
          }
        />
      </div>
      {chatMutation.isError && (
        <Text className={styles.error}>
          {chatMutation.error instanceof Error
            ? chatMutation.error.message
            : "Chat failed"}
        </Text>
      )}
    </div>
  );
}
