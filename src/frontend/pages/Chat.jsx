import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";

import AppLayout from "../components/AppLayout";
import Loading from "../components/Loading";

import { sendChatMessage } from "../api/aiApi";
import {
  getConversationMessages,
  saveConversationMessage,
} from "../api/accountsApi";

import { getToken } from "../utils/storage";

export default function Chat() {
  const { conversationId } = useParams();
  const location = useLocation();

  const chatTitle = location.state?.title || `Conversa #${conversationId}`;

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function cleanMessages(data) {
    return data.filter(
      (message) =>
        message.content &&
        message.content !== "Nova conversa criada."
    );
  }

  async function loadMessages() {
    try {
      const token = getToken();

      const response = await getConversationMessages(
        token,
        Number(conversationId)
      );

      let loadedMessages = [];

      if (Array.isArray(response)) {
        loadedMessages = response;
      } else if (Array.isArray(response?.messages)) {
        loadedMessages = response.messages;
      }

      setMessages(cleanMessages(loadedMessages));
    } catch (err) {
      console.error("Erro ao carregar mensagens:", err);
      setMessages([]);
    }
  }

  async function handleSend(event) {
    event.preventDefault();

    const userText = question.trim();

    if (!userText || loading) {
      return;
    }

    setError("");
    setLoading(true);

    const token = getToken();

    try {
      const userMessage = {
        role: "user",
        content: userText,
      };

      setMessages((prev) => [...prev, userMessage]);
      setQuestion("");

      await saveConversationMessage({
        token,
        conversation_id: Number(conversationId),
        role: "user",
        content: userText,
      });

      const aiResponse = await sendChatMessage({
        token,
        conversation_id: Number(conversationId),
        question: userText,
      });

      const answer = aiResponse?.answer || "A IA não retornou resposta.";

      const assistantMessage = {
        role: "assistant",
        content: answer,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      await saveConversationMessage({
        token,
        conversation_id: Number(conversationId),
        role: "assistant",
        content: answer,
      });
    } catch (err) {
      console.error("Erro real:", err);
      setError(err.message || "Erro ao enviar mensagem.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      const form = event.currentTarget.form;

      if (form) {
        form.requestSubmit();
      }
    }
  }

  useEffect(() => {
    loadMessages();
  }, [conversationId]);

  return (
    <AppLayout>
      <section className="chatgpt-page">
        <header className="chatgpt-header">
          <h1>DataPilot AI</h1>
          <p>{chatTitle}</p>
        </header>

        <div className="chatgpt-messages">
          {messages.length === 0 ? (
            <div className="chatgpt-empty">
              <h2>Comece uma conversa</h2>
              <p>Faça perguntas, peça explicações ou continue o contexto do chat.</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`chat-message ${
                  message.role === "user"
                    ? "chat-message-user"
                    : "chat-message-ai"
                }`}
              >
                <strong>{message.role === "user" ? "Você" : "IA"}</strong>
                <p>{message.content}</p>
              </div>
            ))
          )}

          {loading && (
            <Loading
              compact
              label="Analisando sua mensagem"
              description="A IA está preparando uma resposta."
            />
          )}
        </div>

        {error && <p className="error-message">{error}</p>}

        <form className="chatgpt-input-area" onSubmit={handleSend}>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Digite sua mensagem..."
            rows={1}
          />

          <button
            type="submit"
            className="chat-send-button"
            disabled={loading || !question.trim()}
            aria-label="Enviar mensagem"
          >
            ↑
          </button>
        </form>
      </section>
    </AppLayout>
  );
}
