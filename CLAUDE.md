# CLAUDE.md

Este arquivo é um bootstrap externo para Claude Code.

Todas as regras globais e skills específicas de projetos estão centralizadas em:

`/home/marcos/Documentos/Projects/claude-code-rules`

Quando este arquivo estiver dentro de um projeto de trabalho, o Claude Code deve usar esse diretório externo como fonte oficial de regras.

Não leia novamente:

`/home/marcos/Documentos/Projects/claude-code-rules/CLAUDE.md`

Esse arquivo é apenas o modelo/bootstrap mantido no repositório de regras.

Carregue na seguinte ordem:

1. Regras globais (sempre carregar todas):
   `/home/marcos/Documentos/Projects/claude-code-rules/global-rules/`

2. Skills globais (carregar por contexto da tarefa):
   `/home/marcos/Documentos/Projects/claude-code-rules/global-skills/README.md`
   Consultar o README para identificar qual skill carregar com base no tipo de tarefa solicitada.
   Não carregar todas as skills de uma vez; carregar apenas a(s) relevante(s).

3. Skills do projeto atual:
   Identificar o diretório de trabalho atual e carregar as skills do projeto correspondente.
   Se não houver correspondência, não carregar project-skills.

   Projetos registrados:

   - Diretório: QuickWindowsX | Projeto: QWX - QuickWindowsX
     `/home/marcos/Documentos/Projects/claude-code-rules/project-skills/quickwindowsx/`

Antes de executar qualquer tarefa:

1. Identifique o projeto atual.
2. Carregue as regras globais.
3. Verifique se alguma global-skill é relevante para a tarefa; se sim, carregue-a.
4. Carregue as skills específicas do projeto, se existirem.
5. Classifique o risco da tarefa.
6. Execute apenas dentro do escopo solicitado.
7. Valide antes de concluir.
