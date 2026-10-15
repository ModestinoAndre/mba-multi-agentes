"""
ETAPA 6 -- Os especialistas, cada um com UMA responsabilidade e SÓ as tools de que precisa.

ESQUELETO:
  ETAPA 6.1 -- criar_normas(), criar_escala(), criar_financeiro(), criar_redator()
  ETAPA 6.2 -- criar_coordenador(): usa Normas, Escala e Financeiro como TOOLS (as_tool)

As tools abaixo (PRONTAS) só repassam a chamada ao MCP Server do RH (cliente_mcp.chamar_mcp_async). Dar a cada agente
só as tools dele é o PRIVILÉGIO MÍNIMO (Etapa 9.1); o hook do 🆕 B (etapa10_governanca.py) confere isso em tempo de execução.

REFERÊNCIAS NAS AULAS
  aula4/ex03_agente_as_tool.py                         Coordenador que chama especialistas como tools    <- o mais parecido
  aula2/agente_handoff2.py                             as_tool com tool_name e tool_description
  aula4/ex02_handoff_roteamento.py                     handoff: compare (quem responde no fim?)
  aula7/exemplos/02_agentes_especializados/main.py     uma responsabilidade por agente
  aula7/agentes.py                                     ModelSettings(temperature=0) para respostas mais estáveis
  aula8/exemplos/06_excessive_agency/1_codigo_pronto/main.py   o problema de dar tools DEMAIS a um agente
"""
import json

from agents import Agent, ModelSettings, RunHooks, function_tool

from etapa05_cliente_mcp import chamar_mcp_async
from etapa04_ferramentas import cotacao_usd_brl

CONFIG = ModelSettings(temperature=0)


# ------------------------------------------------------------------ tools (PRONTAS)
@function_tool
async def consultar_normas(tema: str) -> str:
    """Regras da norma interna sobre um tema: férias, prazos, escala, abono, diária, aprovação, saúde ou dados."""
    return json.dumps(await chamar_mcp_async("consultar_normas", {"tema": tema}), ensure_ascii=False)


@function_tool
async def consultar_escala(equipe: str, inicio: str, fim: str) -> str:
    """Afastamentos da equipe que se sobrepõem ao período (AAAA-MM-DD) e o limite de afastados da regra N5."""
    return json.dumps(await chamar_mcp_async("consultar_escala", {"equipe": equipe, "inicio": inicio, "fim": fim}),
                      ensure_ascii=False)


@function_tool
async def tabela_diarias(tipo_destino: str) -> str:
    """Moeda e valor da diária para o tipo de destino: capital, interior ou exterior."""
    return json.dumps(await chamar_mcp_async("tabela_diarias", {"tipo_destino": tipo_destino}), ensure_ascii=False)


@function_tool
async def consultar_remuneracao(matricula: str) -> str:
    """[RESTRITA] Salário-base de um servidor. Só para calcular a venda de férias (N2)."""
    print(f"[tool] consultar_remuneracao({matricula}) EXECUTOU")  # o 🆕 B prova que, barrada, ela NÃO executa
    return json.dumps(await chamar_mcp_async("consultar_remuneracao", {"matricula": matricula}), ensure_ascii=False)


@function_tool
def cotacao_dolar() -> str:
    """Cotação atual do dólar em reais (USD->BRL). Devolve 'indisponível' se a API falhar: nunca invente o câmbio."""
    cotacao = cotacao_usd_brl()
    return f"{cotacao:.4f}" if cotacao else "indisponível"


# ------------------------------------------------------------------ ETAPA 6.1: especialistas
def criar_normas() -> Agent:
    # ETAPA 6.1 -- Agent(name="Normas", instructions=..., tools=[consultar_normas], model_settings=CONFIG)
    #   Responsabilidade: dizer QUAIS regras se aplicam ao pedido e explicá-las em linguagem simples.
    #   NÃO calcula valores, NÃO consulta a escala. Recebe também as violações objetivas (etapa06_regras.py) para explicá-las.
    return Agent(
        name="Normas",
        instructions=(
            "Você é o especialista em NORMAS de Gestão de Pessoas. Sua única responsabilidade é dizer quais regras da "
            "norma interna se aplicam ao pedido e explicá-las em linguagem simples. "
            "Consulte a tool consultar_normas para os temas pertinentes (férias, prazos, escala, abono, diária, "
            "aprovação) e cite as regras pelo código (N1, N2...). "
            "As VIOLAÇÕES OBJETIVAS já foram calculadas por código e vêm no texto: não as recalcule nem as contradiga; "
            "apenas explique cada uma. Se não houver violação, liste as regras cumpridas. "
            "Você NUNCA decide sozinho que uma regra foi violada: só é 'violada' uma regra que está na lista de "
            "violações objetivas recebida; se a lista vier vazia, 'nenhuma' ou não vier, a "
            "seção 'Regras violadas' é 'nenhuma' (as contas de datas, saldo, prazos e escala já foram feitas pelo "
            "sistema e estão certas: não refaça).  A N8 (aprovação da chefia) NUNCA é "
            "violação: é um passo do trâmite que vem depois. Férias e diárias sem violação 'dependem da chefia "
            "imediata'; abono que cumpre N4, N5 e N6 NÃO depende da chefia (N8), e pedido indeferido também não. "
            "Não calcule valores e não analise a escala. Responda em português, em tópicos curtos: "
            "'Regras cumpridas' e 'Regras violadas'."
        ),
        tools=[consultar_normas],
        model_settings=CONFIG,
    )


def criar_escala() -> Agent:
    # ETAPA 6.1 -- tools=[consultar_escala]. Confere a N5 e, se houver conflito, SUGERE outro período
    #   (com o mesmo número de dias, começando num dia permitido).
    return Agent(
        name="Escala",
        instructions=(
            "Você é o especialista em ESCALA. Sua única responsabilidade é conferir a regra N5 (no máximo 30% da "
            "equipe afastada no mesmo dia, mínimo 1). "
            "Use a tool consultar_escala com a equipe e o período do pedido (datas AAAA-MM-DD). "
            "Desconsidere afastamentos do próprio servidor. Informe o tamanho da equipe, o limite e quem já está "
            "afastado no período. "
            "Se houver conflito, SUGIRA um novo período com o MESMO número de dias, começando depois do fim do "
            "afastamento que conflita, numa segunda, terça ou quarta-feira que não seja véspera nem antevéspera de "
            "feriado (N3); confira a sugestão chamando consultar_escala de novo. "
            "Não analise outras regras nem valores. Responda em português, em 2 a 4 linhas."
        ),
        tools=[consultar_escala],
        model_settings=CONFIG,
    )


def criar_financeiro() -> Agent:
    # ETAPA 6.1 -- tools=[tabela_diarias, consultar_remuneracao, cotacao_dolar].
    #   Venda de férias (N2): dias_vendidos x salario_base / 30. Diárias (N7): uma por pernoite + meia no retorno;
    #   no exterior, em USD convertido pela cotação. Mostre a conta. Câmbio indisponível -> "a calcular".
    #   É o ÚNICO agente que vê o salário.
    return Agent(
        name="Financeiro",
        instructions=(
            "Você é o especialista FINANCEIRO. Sua única responsabilidade é calcular valores, mostrando a conta.\n"
            "- Férias com venda de dias (N2): use consultar_remuneracao e calcule dias_vendidos x salario_base / 30. "
            "Informe só o valor total da venda (não repita o salário-base no texto). Sem dias vendidos, não há valor "
            "a pagar: não consulte a remuneração.\n"
            "- Diária (N7): uma diária por dia com pernoite e MEIA diária no dia do retorno (viagem de 08 a 11 = "
            "3 pernoites + 0,5 = 3,5 diárias). Use tabela_diarias com o tipo_destino recebido (capital, interior ou "
            "exterior) e use a moeda e o valor que ela devolver. No exterior o valor é em USD: mostre o total em USD, "
            "use cotacao_dolar e converta para reais; se a cotação vier 'indisponível', escreva 'valor em reais: "
            "a calcular' e nunca invente o câmbio.\n"
            "- Abono (folga) e férias sem venda: não há valor a pagar; diga isso sem chamar tools.\n"
            "Valores em reais no formato R$ 1.234,56. Responda em português, em 2 a 4 linhas."
        ),
        tools=[tabela_diarias, consultar_remuneracao, cotacao_dolar],
        model_settings=CONFIG,
    )


def criar_redator() -> Agent:
    # ETAPA 6.1 -- sem tools. Escreve o DESPACHO (deferimento ou indeferimento) usando SÓ os fatos recebidos:
    #   matrícula, período, decisão, regras citadas, valores e, no indeferimento, a sugestão de datas.
    #   Nunca escreve CPF nem dado de saúde (N10). Se receber um feedback (da validação ou da chefia), corrige.
    return Agent(
        name="Redator",
        instructions=(
            "Você é o REDATOR de despachos de Gestão de Pessoas. Escreva um despacho formal e curto (até 8 linhas), "
            "em português, usando SOMENTE os fatos recebidos; não invente regras, valores ou datas.\n"
            "O despacho deve conter: a matrícula do servidor, o tipo de pedido, o período (datas DD/MM/AAAA), a decisão "
            "em palavra explícita (DEFERIDO ou INDEFERIDO), as regras que fundamentam a decisão (N1, N2...) e os "
            "valores calculados, quando houver: se o parecer do Financeiro trouxer valores (R$ ou USD), copie-os "
            "no despacho (venda de férias, quantidade de diárias e total). A DECISÃO vem pronta no campo 'decisao' dos fatos: copie-a, nunca a "
            "mude, mesmo que o parecer dos especialistas sugira outra coisa (a dependência da chefia, N8, não é motivo "
            "de indeferimento). Cite como violadas SOMENTE as regras de 'violacoes_objetivas'. "
            "Só diga que depende da chefia se 'depende_da_chefia_imediata' for true. No indeferimento, informe o motivo e a sugestão de novo período, se "
            "recebida. Se o pedido depende da chefia imediata, diga que o deferimento fica sujeito à aprovação dela.\n"
            "Não invente número de despacho, ano, nome ou assinatura (nada de '[Seu Nome]'); termine com "
            "'Gestão de Pessoas'.\n"
            "NUNCA escreva CPF, CID, diagnóstico, salário-base ou qualquer informação de saúde (N10).\n"
            "Se receber um FEEDBACK (da validação ou da chefia), reescreva o despacho corrigindo exatamente o que foi "
            "apontado."
        ),
        model_settings=CONFIG,
    )


# ------------------------------------------------------------------ ETAPA 6.2: coordenador
def criar_coordenador(hooks: RunHooks | None = None, tools_extras: list | None = None) -> Agent:
    # ETAPA 6.2 -- Agent(name="Coordenador", instructions=..., tools=[
    #       criar_normas().as_tool(tool_name="parecer_normas", tool_description=..., hooks=hooks,
    #                              failure_error_function=None),
    #       criar_escala().as_tool(tool_name="parecer_escala", ..., hooks=hooks, failure_error_function=None),
    #       criar_financeiro().as_tool(tool_name="parecer_financeiro", ..., hooks=hooks, failure_error_function=None),
    #       *(tools_extras or [])])
    #   O Coordenador decide QUAIS especialistas consultar (abono não precisa do Financeiro) e junta os pareceres.
    #   hooks=hooks nas as_tool faz o hook do 🆕 B enxergar também as tools DENTRO de cada especialista.
    #   failure_error_function=None: sem isso, um erro dentro do especialista (inclusive o bloqueio do 🆕 B) vira só
    #   um texto de erro para o Coordenador, que segue em frente. Com None, o erro interrompe a execução.
    #   tools_extras serve só para o teste do 🆕 B (dar de propósito consultar_remuneracao ao Coordenador).
    #   Referência: aula4/ex03_agente_as_tool.py
    return Agent(
        name="Coordenador",
        instructions=(
            "Você coordena a análise de um pedido de Gestão de Pessoas. Você NÃO consulta dados diretamente: "
            "consulte os especialistas (tools) e junte as respostas num parecer único.\n"
            "Quem consultar, conforme o tipo do pedido:\n"
            "- abono: parecer_normas e parecer_escala.\n"
            "- ferias sem dias vendidos: parecer_normas e parecer_escala.\n"
            "- ferias com dias_vendidos > 0: parecer_normas, parecer_escala e parecer_financeiro.\n"
            "- diaria: parecer_normas e parecer_financeiro (SEMPRE há valor a calcular; não consulte a escala).\n"
            "Ao chamar parecer_normas, copie SEMPRE a linha 'Violações objetivas: <lista exata ou nenhuma>'. "
            "Repasse a cada especialista os fatos de que ele precisa (tipo, matrícula, equipe, datas AAAA-MM-DD, dias "
            "vendidos, destino e tipo_destino (capital/interior/exterior), violações objetivas). "
            "As violações objetivas vêm do sistema e são definitivas: não as contradiga nem acrescente outras. "
            "A aprovação da chefia (N8) não é violação: é um passo posterior do trâmite. "
            "Responda em português com uma seção por especialista consultado (Normas, Escala, Financeiro) e uma "
            "conclusão: 'deferível' se não houver violação objetiva, senão 'indeferir', com a sugestão de datas da "
            "Escala, se houver."
        ),
        tools=[
            criar_normas().as_tool(
                tool_name="parecer_normas",
                tool_description="Especialista em normas: diz quais regras (N1..N10) se aplicam e explica as violações.",
                hooks=hooks, failure_error_function=None),
            criar_escala().as_tool(
                tool_name="parecer_escala",
                tool_description="Especialista em escala: confere a N5 na equipe e sugere outro período se houver conflito.",
                hooks=hooks, failure_error_function=None),
            criar_financeiro().as_tool(
                tool_name="parecer_financeiro",
                tool_description="Especialista financeiro: calcula a venda de férias (N2) ou as diárias (N7).",
                hooks=hooks, failure_error_function=None),
            *(tools_extras or []),
        ],
        model_settings=CONFIG,
    )
