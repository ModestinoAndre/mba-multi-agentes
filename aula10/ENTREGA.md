# Entrega: Assistente de Gestão de Pessoas

**Aluno(s):**
**Até onde chegou:** ( ) Marco mínimo (Etapa 6)  ( ) Marco completo (Etapa 9)  ( ) Etapas 10–11
**Opcionais e bônus feitos:** ( ) 🆕 A  ( ) 🆕 B  ( ) 🆕 C  ( ) Outro: ______

## Etapa 0: quem verifica cada regra?

| Regra | Tema | Quem verifica (função Python / agente / humano) | Por quê | Onde foi implementada (preencha na Etapa 11) |
|---|---|---|---|---|
| N1 | férias | | | |
| N2 | férias | | | |
| N3 | férias | | | |
| N4 | prazos | | | |
| N5 | escala | | | |
| N6 | abono | | | |
| N7 | diária | | | |
| N8 | aprovação | | | |
| N9 | saúde | | | |
| N10 | dados | | | |

## Etapa 11: os 12 casos

Compare **caminho e estado**, não o texto do despacho.

| Caso | Caminho percorrido | Resultado (bloqueado / pediu dados / triagem humana / indeferido / pausou na chefia / registrado + protocolo) | Bateu com o esperado? |
|---|---|---|---|
| C1_abono_simples | | | |
| C2_ferias_com_venda | | | |
| C3_dado_de_saude | | | |
| C4_fora_do_escopo | | | |
| C5_sem_matricula | | | |
| C6_conflito_de_escala | | | |
| C7_autoaprovacao | | | |
| C8_idempotencia | | | |
| C9_divergencia | | | |
| C10_zona_cinzenta | | | |
| C11_diaria_exterior | | | |
| C12_inicio_proibido | | | |

## O grafo


## Etapa 4 (pronta): o que eu entendi

- Diferença entre a saída online e a offline: online, os feriados vêm da BrasilAPI em ~0,2 s (`fonte: brasilapi`) e a
  cotação é real (ex.: 5.0242). Offline, aparecem as 3 tentativas `[retry]`, os feriados vêm do plano B local
  (`fonte: arquivo_local`) depois de ~1,5 s (as esperas 0,5 s + 1 s do backoff) e a cotação é `None` ("a calcular", sem
  inventar câmbio). As contas de datas e o protocolo saem iguais nos dois modos. Detalhe: a API devolve 14 feriados e o
  arquivo local 13; a diferença é o Carnaval (08/02/2027, ponto facultativo), que não afeta nenhum caso de teste.
- O que mudou em relação aos exemplos das aulas:
  - `texto_hoje()` (aula3/agente_retry.py): mesma ideia de injetar `date.today()`, agora com o dia da semana por extenso.
  - `get_json_com_retry()` (aula3/agente_retry2.py): mesmo backoff `espera_base * 2**(n-1)`, mas genérico (qualquer URL),
    com `urllib` em vez de `requests`, `User-Agent` e um modo `FERIADOS_OFFLINE` para simular a queda.
  - `buscar_feriados()` (aula6/exemplos/11_grafo_real): mesma API e plano B local, agora com retry e **cache** por ano, e
    a fonte `"indisponivel"` para anos sem cópia local.
  - `cotacao_usd_brl()` (aula3/agente_retry4.py): mesma API Frankfurter, mas devolve `None` em vez de lançar erro.
  - `gerar_protocolo()` (aula3/agente_retry3.py): mesmo SHA-256, mas com os campos **normalizados** (`strip().lower()`,
    `None` vira `""`) e cortado em 8 caracteres.
  - `rodar_com_limites()` (aula3/agente_parada3.py): mesmo `wait_for` + `max_turns`, mas em vez de imprimir lança erros
    próprios (`TempoEsgotado`, `LoopExcedido`) para quem chama decidir o que fazer, e tem uma versão síncrona para os nós.
- Por que a espera do retry dobra a cada tentativa: se a API caiu ou está sobrecarregada, tentar de novo na hora só
  aumenta a carga e falha de novo. Dobrar a espera (0,5 s, 1 s, 2 s...) dá tempo para o serviço se recuperar, sem
  martelar o servidor, e mantém o tempo total limitado (poucas tentativas, depois o plano B).
- Por que o protocolo é um hash dos campos (e não um número sequencial): o hash é **determinístico**: o mesmo pedido
  (matrícula, tipo, datas) sempre gera o mesmo protocolo (C1 e C8 = `ae788d33`), em qualquer processo e sem consultar
  um contador central. Assim, um reenvio ou um retry não cria um registro duplicado: o server vê que o protocolo já
  existe (idempotência). Um número sequencial geraria um protocolo novo a cada tentativa.
- O que aconteceria sem o cache de feriados: `dias_uteis()` e `inicio_permitido()` perguntam dia a dia se é útil, então
  cada dia do período viraria uma chamada à BrasilAPI (15 chamadas só no C2). Seria lento, arriscaria bloqueio por excesso
  de requisições e, offline, cada dia pagaria as 3 tentativas com backoff (~1,5 s por dia).

## Observabilidade (C2)

- Onde o tempo foi gasto: ~18,7 s somando os nós (`python etapa10_observabilidade.py C2_ferias_com_venda`). Quase
  tudo nos nós com LLM: `normas` (4,0 s, o mais lento, chamou `consultar_normas` 2 vezes), `financeiro` (3,7 s),
  `proteger_entrada` (3,2 s), `redigir_despacho` (2,8 s), `extrair` (2,3 s) e `escala` (1,2 s). Os nós de MCP/API
  (`identificar_servidor`, `calcular_periodo`, `registrar`) levam ~0,4–0,6 s cada, porque cada `chamar_mcp` sobe o
  server de novo; os nós em Python puro (`consolidar`, `validar`) ~0 s. Como `normas`, `escala` e `financeiro` rodam em
  paralelo, o tempo real de parede é menor que a soma (o passo paralelo custa ~4 s, não ~8,9 s).
  `aprovacao_chefia` aparece duas vezes: a 1ª termina em `GraphInterrupt` (a pausa) e a 2ª é a retomada em outro
  processo; a espera pela chefia não entra na conta. Feriados vieram da `brasilapi`.
- Tokens totais: 6.841 (normas 1.964, financeiro 1.520, extrair 1.091, redigir_despacho 1.079, escala 607,
  proteger_entrada 580).

## Opcionais (preencha só os que fez)

- 🆕 A: votos e decisão do C9: ___ ; tempo dos 3 extratores em paralelo ___ s, em sequência ___ s
- 🆕 B: saída do `python etapa06_linear.py --governanca`:
- 🆕 C: caminho do C10 com a triagem humana (sim e não):

## Reflexão (até 3 linhas cada)

1. Quem decide o caminho no seu sistema: o LLM, o grafo, as regras ou um humano? Dê um exemplo de cada.
2. Se o guardrail de entrada falhar, o que ainda impede uma autoaprovação?
3. Por que o nó da chefia não pode gravar nada antes do `interrupt()`?
4. Qual dado veio do **MCP**, qual de **API externa** e qual de **tool local**? Por que essa divisão?
5. O que você mudaria para colocar este sistema em produção?
6. (Só se fez) 🆕 A: votar triplica o custo da extração. Em que pedidos vale a pena?
7. (Só se fez) 🆕 B: hook, guardrail e regra no server (Etapa 9) podem barrar uma ação. Qual a diferença de **onde** cada um atua?
8. (Só se fez) 🆕 C: o que muda quando o humano decide a **entrada** em vez da **saída**? Quem é consultado em cada pausa?

## De onde veio cada parte

| Arquivo / trecho | Exemplo das aulas em que me baseei | O que precisei adaptar |
|---|---|---|
| | | |


| Regra | Tema | Quem verifica (função Python / agente / humano) | Por quê | Onde foi implementada (preencha na Etapa 11) |
|---|---|---|---|---|
| N1 | férias | função Python | conta: dias corridos >= 5 e <= saldo | |
| N2 | férias | função Python | conta: dias + vendidos <= saldo, vendidos <= 10 | |
| N3 | férias | função Python | consulta de calendário (feriados e fim de semana) | |
| N4 | prazos | função Python | diferença entre datas (dias corridos ou úteis) | |
| N5 | escala | função Python | contagem de afastados da equipe no período x limite de 30% | |
| N6 | abono | função Python | dia útil e saldo de abonos | |
| N7 | diária | função Python | conta (diárias + meia diária, câmbio); o agente Financeiro só explica | |
| N8 | aprovação | humano | é decisão da chefia; o server só confere se o aprovador é a chefia certa | |
| N9 | saúde | função Python (guardrail) | regex de CID/CPF barra antes de qualquer agente ver o texto; o classificador (agente) cobre o que a regex não pega | |
| N10 | dados | função Python (guardrail de saída) | regex no despacho antes de gravar | |