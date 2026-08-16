---
description: Mostra a última task concluída e a próxima a ser feita no roadmap do BookMind.
---

## O que fazer ao ser invocado

Ler o arquivo `/home/parallels/bookmind/inspo/INSPIRACOES.md` e fazer o seguinte:

### 1. Identificar a última task concluída

Percorrer a lista de tasks marcadas com `[x]`. A última `[x]` na ordem do roadmap é a task mais recentemente concluída.

### 2. Identificar a próxima task pendente

A primeira task marcada com `[ ]` na ordem de execução do roadmap (respeitando as fases e dependências listadas no arquivo).

### 3. Exibir o resultado neste formato

```
## Status do roadmap

**Última concluída:** TXX — [nome da task]
  Fase X — [nome da fase]

**Próxima task:** TXX — [nome da task]
  Fase X — [nome da fase]
  Depende de: [dependências, ou "nada"]
  
  [descrição do que precisa ser feito, extraída do roadmap]

**Para iniciar:** use `/task-start`
```

### Regras

- Não implementar nada — esta skill é só leitura e síntese
- Não pedir confirmação — executar direto e exibir o resultado
- Se houver decisões em aberto (`[~]`) na próxima task, listá-las claramente
- Responder sempre em português
