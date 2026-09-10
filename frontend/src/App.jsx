const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function AuthScreen({ onAuthSuccess }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = mode === "login" ? apiLogin : apiRegister;
      const data = await fn(email, password);
      localStorage.setItem("access_token", data.access_token);
      onAuthSuccess(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">ChatLLM Lab</div>
      </header>
      <div className="auth-screen">
        <div className="auth-card">
          <h2>{mode === "login" ? "Entrar" : "Criar Conta"}</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="email"
              placeholder="Seu email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
            <input
              type="password"
              placeholder="Sua senha"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
            {error && <div className="note error">{error}</div>}
            <button type="submit" disabled={loading}>
              {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Cadastrar"}
            </button>
          </form>
          <p className="auth-toggle">
            {mode === "login" ? (
              <>Nao tem conta? <a href="#" onClick={(e) => { e.preventDefault(); setMode("register"); setError(""); }}>Cadastre-se</a></>
            ) : (
              <>Ja tem conta? <a href="#" onClick={(e) => { e.preventDefault(); setMode("login"); setError(""); }}>Faca login</a></>
            )}
          </p>
        </div>
      </div>
    </main>
  );
}

function Sidebar({ sessions, currentSessionId, onSelectSession, onCreateSession, onDeleteSession, onToggleSidebar, isOpen }) {
  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={() => onToggleSidebar()} />}
      <aside className={`sidebar ${isOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={onCreateSession} title="Nova conversa">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="8" y1="2" x2="8" y2="14" />
              <line x1="2" y1="8" x2="14" y2="8" />
            </svg>
            Nova conversa
          </button>
          <button className="close-sidebar-btn" onClick={() => onToggleSidebar()} title="Fechar">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="12" y1="4" x2="4" y2="12" />
              <line x1="4" y1="4" x2="12" y2="12" />
            </svg>
          </button>
        </div>
        <div className="sidebar-list">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`sidebar-item ${s.id === currentSessionId ? "active" : ""}`}
              onClick={() => onSelectSession(s.id)}
            >
              <span className="sidebar-item-title">{s.title}</span>
              <button
                className="sidebar-item-delete"
                onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); }}
                title="Excluir conversa"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <line x1="3" y1="3" x2="11" y2="11" />
                  <line x1="11" y1="3" x2="3" y2="11" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Carregar sessoes do backend
  const loadSessions = useCallback(async () => {
    try {
      const data = await apiListSessions();
      setSessions(data.sessions);
    } catch {
      // Ignora erro
    }
  }, []);

  // Carregar mensagens de uma sessao
  const loadMessages = useCallback(async (sessionId) => {
    try {
      const data = await apiGetSessionMessages(sessionId);
      setMessages(
        data.length > 0
          ? data.map((m) => ({ id: m.id, role: m.role, content: m.content }))
          : [{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]
      );
    } catch {
      setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      apiGetMe().then((u) => {
        if (u) {
          setUser(u);
          loadSessions().then(() => setCheckingAuth(false));
        } else {
          localStorage.removeItem("access_token");
          setCheckingAuth(false);
        }
      }).catch(() => {
        localStorage.removeItem("access_token");
        setCheckingAuth(false);
      });
    } else {
      setCheckingAuth(false);
    }
  }, [loadSessions]);

  // Quando as sessoes carregam, selecionar a primeira ou criar uma
  useEffect(() => {
    if (!checkingAuth && user && sessions.length > 0 && !currentSessionId) {
      setCurrentSessionId(sessions[0].id);
      loadMessages(sessions[0].id);
    }
  }, [checkingAuth, user, sessions, currentSessionId, loadMessages]);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const handleCreateSession = async () => {
    try {
      const data = await apiCreateSession();
      setSessions((prev) => [data, ...prev]);
      setCurrentSessionId(data.id);
      setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
      setSidebarOpen(false);
    } catch {
      // Ignora erro
    }
  };

  const handleSelectSession = async (sessionId) => {
    if (sessionId === currentSessionId) return;
    setCurrentSessionId(sessionId);
    setSidebarOpen(false);
    await loadMessages(sessionId);
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await apiDeleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId);
        if (remaining.length > 0) {
          const next = remaining[0];
          setCurrentSessionId(next.id);
          await loadMessages(next.id);
        } else {
          const data = await apiCreateSession();
          setSessions([data]);
          setCurrentSessionId(data.id);
          setMessages([{ id: createMessageId(), role: "assistant", content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?" }]);
        }
      }
    } catch {
      // Ignora erro
    }
  };

  // Gerar titulo automatico com base no contexto (mensagem + resposta do modelo)
  const generateTitle = async (sessionId, userMessage, assistantReply) => {
    if (!sessionId) return;
    const session = sessions.find((s) => s.id === sessionId);
    if (!session || session.title !== "Nova conversa") return;
    try {
      const updated = await apiGenerateSessionTitle(sessionId);
      if (updated) {
        setSessions((prev) => prev.map((s) => s.id === sessionId ? { ...s, title: updated.title } : s));
      }
    } catch {
      // Se falhar, a conversa continua normalmente
    }
  };

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    setError("");
    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();

    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantMessageId, role: "assistant", content: "" },
    ]);
    setText("");
    setBusy(true);
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await sendMessageStream({
        message: cleaned,
        sessionId: currentSessionId,
        history: chatHistory,
        signal: abortController.signal,
        onDelta: (delta) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: `${msg.content}${delta}` }
                : msg
            )
          );
        },
      });

      setMessages((prev) => {
        const finalMessage = prev.find((msg) => msg.id === assistantMessageId);
        const replyContent = finalMessage?.content?.trim() || "";

        // Gerar titulo automatico com o contexto da resposta
        if (currentSessionId && replyContent) {
          generateTitle(currentSessionId, cleaned, replyContent);
        }

        return prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        );
      });
    } catch (err) {
      const aborted = err?.name === "AbortError";
      if (!aborted) {
        setError(err.message || "Falha inesperada ao gerar resposta.");
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content.trim() ? msg.content : "Nao foi possivel obter resposta do modelo agora." }
              : msg
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId && !msg.content.trim()
              ? { ...msg, content: "Resposta interrompida." }
              : msg
          )
        );
      }
    } finally {
      abortControllerRef.current = null;
      setBusy(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch {
      // Ignora erro no logout
    }
    localStorage.removeItem("access_token");
    setUser(null);
    setSessions([]);
    setCurrentSessionId(null);
    setMessages([]);
  };

  if (checkingAuth) {
    return (
      <main className="app-shell">
        <header className="app-header">
          <div className="brand">ChatLLM Lab</div>
        </header>
        <div className="auth-screen">
          <div className="auth-card">
            <p>Verificando autenticacao...</p>
          </div>
        </div>
      </main>
    );
  }

  if (!user) {
    return <AuthScreen onAuthSuccess={(u) => setUser(u)} />;
  }

  return (
    <main className="app-shell">
      <div className="app-shell-row">
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          onDeleteSession={handleDeleteSession}
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
          isOpen={sidebarOpen}
        />

        <div className="chat-area">
          <header className="app-header">
            <button className="sidebar-toggle" onClick={() => setSidebarOpen((v) => !v)} title="Menu">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="2" y1="4" x2="16" y2="4" />
                <line x1="2" y1="9" x2="16" y2="9" />
                <line x1="2" y1="14" x2="16" y2="14" />
              </svg>
            </button>
            <div className="brand">ChatLLM Lab</div>
            <div className="user-info">
              <span className="user-email">{user.email}</span>
              <button className="logout-btn" onClick={handleLogout}>Sair</button>
            </div>
          </header>

          <section className="messages" aria-live="polite" ref={messagesRef}>
            <div className="messages-inner">
              {messages.map((msg) => (
                <article key={msg.id} className={`bubble ${msg.role}`}>
                  <MessageContent content={msg.content} />
              </article>
            ))}
          </div>
        </section>

        <Composer
          text={text}
          busy={busy}
          error={error}
          onChangeText={setText}
          onSubmit={onSubmit}
          onStop={onStop}
        />

        <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
      </div>
      </div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

