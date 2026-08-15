---
description: Visualiza arquivos .md no terminal com formatação e cores usando glow.
---

## Papel ativo: Visualizador de Markdown

Renderiza qualquer arquivo `.md` no terminal com formatação completa — títulos, negrito, tabelas, blocos de código, badges e listas — usando o `glow`.

### Uso

Se a Yasmin passou um caminho como argumento, renderize diretamente. Caso contrário, pergunte qual arquivo visualizar antes de rodar qualquer comando.

```bash
glow <caminho-do-arquivo>
```

### Caminhos frequentes neste projeto

| Arquivo | Caminho |
|---|---|
| README do projeto | `/home/parallels/bookmind/README.md` |
| README do perfil GitHub | `/home/parallels/Documents/profile_README.md` |
| Arquitetura | `/home/parallels/bookmind/ARCHITECTURE.md` |
| Roadmap / Inspirações | `/home/parallels/bookmind/inspo/INSPIRACOES.md` |
| Instruções do projeto | `/home/parallels/bookmind/CLAUDE.md` |

### Opções úteis do glow

```bash
glow <arquivo>          # renderiza normal
glow -p <arquivo>       # modo paginado (navega com setas, sai com q)
glow -w 100 <arquivo>   # limita largura a 100 colunas
```

Use `-p` para arquivos longos como o `INSPIRACOES.md` ou o `profile_README.md`.

### Se o comando não for encontrado

O binário fica em `~/.local/bin/glow`. Rodar com o caminho completo:

```bash
~/.local/bin/glow <arquivo>
```

Ou adicionar ao PATH se ainda não estiver:

```bash
export PATH="$HOME/.local/bin:$PATH"
```
