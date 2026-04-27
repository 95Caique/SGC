# ContraFlow - Endpoints JSON

Todas as rotas exigem usuario autenticado. As consultas retornam apenas dados da empresa vinculada ao usuario autenticado.

## Contratos

### `GET /contratos/`

Lista contratos da empresa do usuario.

Query params:

- `status`: opcional.

Resposta:

```json
{
  "resultados": [
    {
      "id": 1,
      "empresa_id": 1,
      "cliente": {"id": 1, "nome": "Cliente"},
      "titulo": "Contrato",
      "descricao": "",
      "valor_mensal": "1500.00",
      "data_inicio": "2026-04-27",
      "data_fim": null,
      "status": "ativo",
      "criado_por_id": 1,
      "criado_em": "2026-04-27T10:00:00+00:00",
      "atualizado_em": "2026-04-27T10:00:00+00:00"
    }
  ]
}
```

### `POST /contratos/criar/`

Cria contrato.

Body:

```json
{
  "cliente_id": 1,
  "titulo": "Contrato de Servicos",
  "descricao": "Opcional",
  "valor_mensal": "1500.00",
  "data_inicio": "2026-04-27",
  "data_fim": "2027-04-27"
}
```

### `GET /contratos/{id}/`

Detalha contrato e inclui historico.

### `POST /contratos/{id}/status/`

Altera status.

Body:

```json
{"status": "suspenso"}
```

Status aceitos: `ativo`, `expirado`, `cancelado`, `suspenso`, `encerrado`.

### `POST /contratos/{id}/arquivos/`

Envia arquivo versionado.

Form-data:

- `arquivo`: arquivo do contrato.

## Propostas

### `GET /propostas/`

Lista propostas da empresa do usuario.

Query params:

- `status`: opcional.

### `POST /propostas/criar/`

Cria proposta.

Body:

```json
{
  "cliente_id": 1,
  "titulo": "Proposta de Servicos",
  "descricao": "Opcional",
  "valor": "2000.00",
  "desconto": "5.00",
  "valido_ate": "2026-05-27"
}
```

### `GET /propostas/{id}/`

Detalha proposta e inclui historico.

### `POST /propostas/{id}/status/`

Altera status.

Body:

```json
{"status": "enviada"}
```

Status aceitos: `rascunho`, `enviada`, `aceita`, `rejeitada`, `expirada`, `convertida`.

### `POST /propostas/{id}/converter/`

Converte proposta aceita em contrato. O contrato criado fica independente da proposta.

## Dashboard

### `GET /painel/metricas/`

Retorna totais de contratos ativos, clientes, faturamento mensal e propostas pendentes.

### `GET /painel/contratos-vencimento/`

Lista contratos ativos proximos do vencimento.

Query params:

- `dias`: opcional, padrao `30`.

### `GET /painel/propostas-pendentes/`

Lista propostas em `rascunho` ou `enviada`.

### `GET /painel/faturamento-clientes/`

Retorna faturamento mensal por cliente, considerando contratos ativos.

### `GET /painel/saude/`

Retorna distribuicao de contratos e propostas por status.

## Automacao

### Management command

```bash
python manage.py limpar_propostas_expiradas
```

Marca propostas vencidas como `expirada` quando estiverem em `rascunho` ou `enviada`.
