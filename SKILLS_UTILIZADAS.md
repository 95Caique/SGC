# Skills e decisoes utilizadas

## Etapa 1 - Fundacao Django

- Leitura do projeto existente antes de editar.
- Preservacao dos apps em ingles ja existentes no repositorio.
- Dominio modelado em portugues: classes, campos, metodos e regras.
- Separacao inicial de responsabilidades:
  - `core/models.py` para `ModeloBase`.
  - `core/permissoes.py` para verificacoes e decorators.
  - `core/utils.py` para utilitarios compartilhados.
  - `core/excecoes.py` para excecoes de dominio.
- Multi-empresa desde a base:
  - `UsuarioCustomizado.empresa`.
  - `Cliente.empresa`.
  - `Empresa.total_usuarios()` e `Empresa.total_clientes()`.
- Configuracao preparada para PostgreSQL via `.env`, mantendo SQLite como fallback de desenvolvimento.
- Evitado bloqueio indevido de clientes sem email; unicidade por email sera tratada depois apenas quando houver regra explicita.

## Proximas etapas

- Expandir frontend com telas dedicadas de contratos, propostas e clientes.

## Etapa 2 - Contratos

- Criado dominio de contratos em `contracts/models.py`.
- Implementada auditoria estruturada em `ContratoHistorico`, no formato:
  - `campo.old`
  - `campo.new`
- Criado `ServicoContrato` para manter regra de negocio fora das views.
- Validacao multi-empresa aplicada nos services:
  - usuario precisa pertencer a empresa do contrato.
  - cliente precisa pertencer a mesma empresa do contrato.
- Implementado versionamento incremental de arquivos com `transaction.atomic()`.
- Caminho de arquivo preparado para storage local ou S3/MinIO:
  - `empresa_{id}/contratos/{contrato_id}/v{versao}.pdf`
- Testes adicionados para:
  - criacao de contrato.
  - historico.
  - edicao auditada.
  - permissao multi-empresa.
  - versionamento de arquivos.

## Etapa 3 - Propostas

- Criado dominio de propostas em `proposals/models.py`.
- `valor_final` calculado automaticamente a partir de `valor` e `desconto`.
- Valores monetarios normalizados com duas casas em `core/utils.py`.
- Criado `PropostaHistorico` com o mesmo padrao de auditoria dos contratos.
- Criado `ServicoProposta` para:
  - criar proposta.
  - editar proposta com historico apenas dos campos alterados.
  - marcar como enviada.
  - aceitar proposta.
  - rejeitar proposta.
  - converter proposta aceita em contrato.
- Conversao proposta -> contrato implementada sem sincronizacao bidirecional.
- Regra multi-empresa validada nos services.
- Testes adicionados para:
  - calculo de valor final.
  - historico.
  - bloqueio de cliente de outra empresa.
  - bloqueio de usuario de outra empresa.
  - conversao aceita -> contrato.
  - impedimento de conversao quando a proposta nao esta aceita.
  - independencia do contrato apos conversao.

## Etapa 4 - Services de empresas e dashboard

- Criado `companies/services.py` com:
  - dashboard por empresa.
  - faturamento por periodo.
  - relatorio de clientes por valor.
- Criado `dashboard/services.py` com:
  - metricas gerais.
  - contratos proximos do vencimento.
  - propostas pendentes.
  - faturamento por cliente.
  - saude de contratos.
  - saude de propostas.
- Mantida a regra multi-empresa por escopo de `empresa` em todas as consultas.
- Registrado `Empresa` no Django Admin.
- Testes adicionados para services de empresas e dashboard.

## Etapa 5 - Views de contratos

- Criado `contracts/urls.py`.
- Incluidas rotas de contratos em `config/urls.py`.
- Criadas views JSON para:
  - listar contratos.
  - criar contrato.
  - detalhar contrato.
  - alterar status.
  - upload de arquivo.
- Views mantidas finas, delegando regra de negocio para `ServicoContrato`.
- Multi-empresa aplicado nas queries das views com `empresa=request.user.empresa`.
- Testes adicionados para:
  - listagem por empresa.
  - criacao via endpoint.
  - bloqueio de detalhe de contrato de outra empresa.
  - alteracao de status.
  - upload com versionamento.

## Etapa 6 - Views de propostas

- Criado `proposals/urls.py`.
- Incluidas rotas de propostas em `config/urls.py`.
- Criadas views JSON para:
  - listar propostas.
  - criar proposta.
  - detalhar proposta.
  - alterar status.
  - converter proposta aceita em contrato.
- Views mantidas finas, delegando regra de negocio para `ServicoProposta`.
- Multi-empresa aplicado nas queries das views com `empresa=request.user.empresa`.
- Conversao por endpoint preserva a regra de nao sincronizar contrato apos criacao.
- Testes adicionados para:
  - listagem por empresa.
  - criacao via endpoint.
  - bloqueio de detalhe de proposta de outra empresa.
  - alteracao de status.
  - conversao em contrato.

## Etapa 7 - Views de dashboard

- Criado `dashboard/urls.py`.
- Incluidas rotas do painel em `config/urls.py`.
- Criadas views JSON para:
  - metricas gerais.
  - contratos proximos do vencimento.
  - propostas pendentes.
  - faturamento por cliente.
  - saude de contratos e propostas.
- Views delegam consultas para `ServicoPainel`.
- Faturamento do dashboard considera apenas contratos ativos.
- Decimais serializados com duas casas para estabilidade da API.
- Testes adicionados para todos os endpoints do painel.

## Etapa 8 - Limpeza de propostas expiradas

- Criado `ServicoProposta.limpar_propostas_expiradas()`.
- Propostas expiradas sao marcadas explicitamente como `expirada`.
- Apenas propostas em `rascunho` ou `enviada` sao afetadas.
- Auditoria registrada com acao `expirada`.
- Criado management command:
  - `python manage.py limpar_propostas_expiradas`
- Criado `proposals/signals.py` apenas para log simples ao deletar proposta.
- Signal carregado em `ProposalsConfig.ready()`.
- Testes adicionados para:
  - limpeza de proposta expirada.
  - preservacao de proposta aceita vencida.
  - execucao do management command.

## Etapa 9 - Admin e documentacao de endpoints

- Registrado `UsuarioCustomizado` no Django Admin com campos de empresa e funcao.
- Registrado `Cliente` no Django Admin com contatos inline.
- Registrado `ContatoCliente` no Django Admin.
- Atualizado `README.md` com estado atual do backend e link para endpoints.
- Criado `ENDPOINTS.md` com rotas JSON de:
  - contratos.
  - propostas.
  - dashboard.
  - comando de limpeza de propostas expiradas.
- Backend ja possui superficie suficiente para iniciar frontend consumindo endpoints JSON.

## Etapa 10 - Frontend institucional inicial

- Criado frontend server-rendered com Django templates.
- Criado template base em `dashboard/templates/dashboard/base.html`.
- Criada tela institucional em `dashboard/templates/dashboard/interface_institucional.html`.
- Criado CSS organizado em `dashboard/static/dashboard/css/institucional.css`.
- Visual definido com:
  - tema claro.
  - sidebar branca e discreta.
  - tabelas como foco principal.
  - linhas zebradas.
  - linha de total obrigatoria.
  - badges suaves.
  - botoes cinza escuro arredondados.
  - layout responsivo com sidebar colapsavel.
- Rota principal adicionada em `/`.
- Rota do painel institucional mantida em `/painel/`.
- Teste adicionado para renderizacao da interface institucional.

## Etapa 11 - Frontend integrado ao backend

- Rotas principais passaram a renderizar o template institucional:
  - clientes.
  - contratos.
  - propostas.
  - empresas.
  - administracao.
  - gestao de pessoas.
  - central de servicos.
  - relatorios.
- JSON mantido via `?format=json` para integracao/API.
- Criados formularios Django para:
  - `ClienteForm`.
  - `ContratoForm`.
  - `PropostaForm`.
- Criado `ServicoCliente` para manter regra de criacao de cliente fora da view.
- Criacao de clientes, contratos e propostas agora funciona pelo frontend institucional.
- Menu lateral nao aponta mais para Admin/JSON nas telas principais.
- Staticfiles servidos no desenvolvimento mesmo quando `DEBUG=False`, via `SERVE_STATICFILES`.
- Testes adicionados para renderizacao e cadastro pelas telas institucionais.

## Etapa 12 - Filtros institucionais

- Filtros das telas principais passaram a consultar o backend de verdade.
- Contratos podem ser filtrados por:
  - texto.
  - cliente.
  - status.
  - data inicial minima.
  - data final maxima.
- Propostas podem ser filtradas por:
  - texto.
  - cliente.
  - status.
  - validade minima.
  - validade maxima.
- Clientes podem ser filtrados por:
  - texto.
  - tipo.
  - email.
  - contato.
- Os mesmos filtros funcionam nas respostas JSON via `?format=json`.
- Templates preservam os valores filtrados apos envio do formulario.
- Campos de status e tipo usam seletores com choices dos modelos.
- Testes adicionados para filtros server-rendered e JSON.

## Etapa 13 - Acesso global para superusuarios

- Removida a trava visual que exigia empresa vinculada para superuser acessar o painel.
- `is_superuser` passou a ter escopo global nas verificacoes de permissao.
- Superusuarios podem listar dados de todas as empresas em:
  - painel.
  - clientes.
  - contratos.
  - propostas.
  - empresas.
  - gestao de pessoas.
- Services de clientes, contratos e propostas permitem criacao por superuser sem exigir `usuario.empresa`.
- Formularios de contratos e propostas exibem clientes de todas as empresas para superuser.
- Formulario de cliente exibe selecao de empresa para superuser.
- Sidebar mostra `Acesso global` para superuser sem empresa vinculada.
- Testes adicionados para painel e clientes com superuser sem empresa.

## Etapa 14 - Edicao institucional

- Botao de editar deixou de ser apenas visual nas listagens.
- Criadas rotas institucionais de edicao:
  - `/clientes/{id}/editar/`
  - `/contratos/{id}/editar/`
  - `/propostas/{id}/editar/`
- Formularios de criacao foram reaproveitados para edicao com titulo, breadcrumb e texto de botao dinamicos.
- Criado `ServicoCliente.editar_cliente()`.
- Edicao de contratos e propostas usa os services existentes para manter auditoria.
- Detalhes de clientes, contratos e propostas passaram a exibir acoes de editar e voltar.
- Superuser preserva acesso global, mas edicao de contratos/propostas mantem cliente dentro da empresa do recurso.
- Testes adicionados para edicao institucional de clientes, contratos e propostas.

## Etapa 15 - Acoes institucionais de status

- Telas de detalhe passaram a expor acoes operacionais por formulario.
- Contratos podem ter status alterado pela interface institucional.
- Propostas podem ter status alterado pela interface institucional.
- Propostas aceitas podem ser convertidas em contrato pela interface.
- Endpoints JSON de status e conversao foram preservados.
- Formularios institucionais usam marcador explicito para diferenciar fluxo HTML de API.
- Ajustada deteccao de JSON em POST para nao confundir formulario HTML com API por cabecalho `Accept`.
- Testes adicionados para:
  - alteracao de status de contrato via formulario.
  - alteracao de status de proposta via formulario.
  - conversao de proposta via formulario.
  - compatibilidade da conversao JSON existente.

## Etapa 16 - Arquivos versionados no frontend

- Tela de detalhe do contrato passou a exibir arquivos versionados.
- Adicionado formulario institucional para upload de arquivo do contrato.
- Upload pela interface redireciona de volta para o detalhe do contrato.
- Upload via API JSON foi preservado com `?format=json`.
- Listagem de arquivos mostra:
  - versao.
  - caminho do arquivo.
  - usuario que enviou.
  - data de envio.
  - link para abrir o arquivo.
- Historico de contrato continua registrando `arquivo_adicionado`.
- Testes adicionados para:
  - upload por formulario institucional.
  - exibicao de arquivos versionados no detalhe.
  - compatibilidade do upload JSON.

## Etapa 17 - Contatos de clientes

- Criado `ContatoClienteForm`.
- Criado `ServicoCliente.criar_contato()`.
- Criada rota institucional e JSON:
  - `/clientes/{id}/contatos/criar/`
- Tela de detalhe do cliente passou a permitir cadastro de contato.
- Cadastro de contato respeita permissao de edicao e escopo da empresa.
- Superuser permanece com acesso global.
- Listagem de contatos no detalhe foi mantida junto ao novo formulario.
- Testes adicionados para:
  - criacao de contato por formulario.
  - criacao de contato via JSON.
  - bloqueio de contato em cliente de outra empresa.

## Etapa 18 - Relatorios operacionais

- Tela de relatorios deixou de ser apenas resumo agregado.
- Relatorios passaram a exibir dados operacionais vindos de `ServicoPainel`.
- Adicionada tabela de faturamento por cliente.
- Adicionada tabela de contratos proximos do vencimento.
- Adicionada tabela de propostas pendentes.
- Relatorios respeitam escopo da empresa para usuarios comuns.
- Superuser continua visualizando dados globais.
- Estados vazios foram mantidos nas tabelas.
- Teste de renderizacao de relatorios passou a validar os blocos operacionais.
