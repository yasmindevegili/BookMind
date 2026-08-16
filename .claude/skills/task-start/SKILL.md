---
description: Inicia a próxima task do roadmap — cria a branch correta e abre o modo de desenvolvimento.
---

## O que fazer ao ser invocado

### Passo 1 — Identificar a próxima task

Ler `/home/parallels/bookmind/inspo/INSPIRACOES.md` e encontrar a primeira task com `[ ]` respeitando a ordem e dependências do roadmap.

### Passo 2 — Verificar pré-condições

Antes de criar qualquer branch:

1. Rodar `git status` — se houver mudanças não commitadas, avisar a Yasmin e parar. Não continuar com trabalho pendente na branch atual.
2. Confirmar que as dependências da task estão marcadas como `[x]` no roadmap. Se não estiverem, avisar e sugerir qual task fazer antes.

### Passo 3 — Criar a branch

Nomear a branch seguindo a convenção do projeto:
- Features novas: `feat/tXX-descricao-curta`
- Bugs: `fix/tXX-descricao-curta`
- Infraestrutura/config: `chore/tXX-descricao-curta`

Exemplo para T02: `feat/t02-auto-embedding`

Comando a executar:
```bash
git checkout -b <nome-da-branch>
```

### Passo 4 — Abrir o modo de desenvolvimento

Após criar a branch com sucesso, apresentar um briefing de desenvolvimento com:

```
## Task TXX iniciada — [nome da task]

**Branch criada:** feat/tXX-descricao-curta

**Objetivo:** [o que essa task entrega]

**Arquivos afetados (provável):**
- [listar arquivos relevantes com base na descrição da task]

**Critério de aceite:**
- [ ] [condição 1]
- [ ] [condição 2]
- ...

**Decisões em aberto:** [se houver, listar aqui — senão omitir]

**Próximo passo:** me diga para continuar e vamos implementar.
```

### Regras

- Nunca executar `git push` — só criar a branch localmente
- Se a task tiver `[~]` (decisão em aberto), listar as opções e perguntar à Yasmin antes de continuar
- Não começar a implementar sem confirmar o briefing com a Yasmin
- Responder sempre em português
- Ao final do briefing, aguardar confirmação antes de escrever qualquer código
