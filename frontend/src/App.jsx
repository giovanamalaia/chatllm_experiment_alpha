const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function AuthScreen({ onAuthSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
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

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [messages, setMessages] = useState([
    {
      id: createMessageId(),
      role: "assistant",
      content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
    },
  ]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      apiGetMe().then((u) => {
        if (u) setUser(u);
        else localStorage.removeItem("access_token");
        setCheckingAuth(false);
      }).catch(() => {
        localStorage.removeItem("access_token");
        setCheckingAuth(false);
      });
    } else {
      setCheckingAuth(false);
    }
  }, []);

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

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        )
      );
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
    setMessages([
      {
        id: createMessageId(),
        role: "assistant",
        content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
      },
    ]);
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
      <header className="app-header">
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
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

