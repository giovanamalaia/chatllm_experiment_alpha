# Socratic Review Record

> Gerado pelo revisor socrático. Revisão da Tarefa 1 — Login e Logout (Controlada pelo Pipeline).

## Veredito Final

**Maestria: Aprovado**

O desenvolvedor demonstrou compreensão genuína do fluxo de autenticação implementado, incluindo:
- Escopo completo da tarefa (cadastro, login, logout, persistência, hash de senha)
- Interação entre os módulos (frontend → API → serviço → modelo → banco)
- Identificação correta da limitação de segurança (token não invalidado no logout)
- Compreensão dos trade-offs entre localStorage vs cookies HTTP-only
- Autocrítica sobre pontos a melhorar (invalidação de token, segurança do armazenamento)

---

## Registro das Perguntas e Respostas

### Pergunta 1 — O que foi implementado?

**Revisor:** O que foi implementado nesta tarefa? Descreva o escopo completo do que foi feito, em suas próprias palavras.

**Desenvolvedor:** Foi implementado um sistema de autenticação com cadastro, login e logout. Os dados dos usuários ficam persistidos no banco e a senha não é salva diretamente, usando hash. Também foi implementada a autenticação das requisições usando token, além da tela de login/cadastro no frontend e dos testes para validar esses fluxos.

---

### Pergunta 2 — Explicação dos Módulos

**Revisor:** Sem olhar o código-fonte, explique como os seguintes módulos interagem entre si: `backend/models.py` (User), `backend/services/auth.py`, `backend/routers/auth.py`, `backend/schemas/auth.py`, `frontend/src/api.js` e `frontend/src/App.jsx`. Quais funções chamam quais, e como os dados fluem do frontend até o banco e de volta?

**Desenvolvedor:** O App.jsx controla as telas e as ações do usuário. Quando ele faz cadastro ou login, o App chama as funções do api.js, que fazem as requisições para o backend. O router de autenticação recebe essas requisições e usa o serviço de auth para cuidar da lógica de autenticação. O User do models representa os dados que são salvos no banco. No login, depois de verificar a senha, o auth gera um token JWT, que volta para o frontend pelo api.js e depois é usado nas requisições para identificar o usuário.

---

### Pergunta 3 — Autonomia de Debugging

**Revisor:** Suponha que o seguinte bug seja reportado: "Depois de fazer logout, se eu pegar o token JWT de outra pessoa que está salvo no `localStorage`, eu ainda consigo usar esse token para acessar `/api/auth/me` e a API aceita." Como você investigaria e resolveria esse problema sem usar ferramentas de IA?

**Desenvolvedor:** Eu investigaria se o logout está realmente removendo o token e se o backend está invalidando ele também. Depois tentaria reproduzir o problema usando o token no /api/auth/me. Se o token continuar sendo aceito mesmo depois do logout, teria que verificar a validação do JWT e pensar em uma forma de invalidar o token no logout.

---

### Pergunta 4 — Justificativa de Decisão

**Revisor:** A implementação atual armazena o token JWT no `localStorage` do navegador e o envia como header Bearer. Você pode justificar essa decisão em vez de usar cookies HTTP-only para gerenciamento de sessão? Quais trade-offs você considerou?

**Desenvolvedor:** O localStorage foi usado principalmente pela simplicidade, já que fica fácil guardar o JWT e enviar ele como Bearer nas requisições. A desvantagem é que o token pode ser acessado por JavaScript, então fica mais vulnerável. Com um cookie HTTP-only isso seria mais seguro, mas a implementação da sessão seria um pouco diferente.

---

### Pergunta 5 — Capacidade de Onboarding

**Revisor:** Se um novo desenvolvedor entrasse no projeto agora, você conseguiria explicar a lógica interna deste recurso de autenticação sem que ele precisasse ler cada linha gerada por IA? Explique o fluxo completo dos dados: desde quando o usuário digita email e senha na tela de login até ver a interface de chat.

**Desenvolvedor:** O usuário digita o email e a senha na tela de login, e o App envia essas informações pela API. O backend verifica os dados e, se estiverem corretos, retorna um token JWT. Esse token é usado para identificar o usuário nas próximas requisições. Depois que a autenticação é confirmada, o App muda para a interface do chat.

---

### Pergunta 6 — Encerramento: Satisfação

**Revisor:** Olhando para os critérios de sucesso originais que você definiu no `TODO.md` — você sente que todos foram totalmente atendidos? Há algo que você mudaria ou melhoraria se tivesse mais tempo?

**Desenvolvedor:** Sim, acho que os critérios foram atendidos. Se eu tivesse mais tempo, talvez melhorasse a segurança do token, principalmente a questão de usar o localStorage e de invalidar o token depois do logout.