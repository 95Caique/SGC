# ContraFlow - Endpoints JSON

Todas as rotas exigem usuario autenticado. As consultas retornam apenas dados da empresa vinculada ao usuario autenticado.

## Clientes

### `GET /clientes/`

Lista clientes da empresa do usuario.

Query params:

- `texto`: busca por nome, email ou nome de contato.
- `tipo`: opcional, `pf` ou `pj`.
- `email`: busca parcial por email.
- `contato`: busca por nome, email ou telefone de contato.

### `POST /clientes/criar/`

Cria cliente.

Body:

```json
{
  "nome": "Cliente",
  "email": "cliente@example.com",
  "tipo": "pj"
}
```

### `GET /clientes/{id}/`

Detalha cliente e seus contatos.

### `POST /clientes/{id}/contatos/criar/`

Cria contato para o cliente.

Body:

```json
{
  "nome": "Contato Principal",
  "telefone": "11999990000",
  "email": "contato@example.com"
}
```

### `POST /clientes/{id}/editar/`

Edita cliente.

Body:

```json
{
  "nome": "Cliente atualizado",
  "email": "cliente@example.com",
  "tipo": "pj"
}
```

## Contratos

### `GET /contratos/`

Lista contratos da empresa do usuario.

Query params:

- `texto`: busca por titulo, descricao ou cliente.
- `cliente`: busca parcial pelo nome do cliente.
- `status`: opcional.
- `data_inicio`: filtra contratos com inicio a partir desta data.
- `data_fim`: filtra contratos com fim ate esta data.

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

### `POST /contratos/{id}/editar/`

Edita contrato e registra auditoria dos campos alterados.

Body parcial aceito:

```json
{
  "titulo": "Contrato atualizado",
  "valor_mensal": "1800.00",
  "data_fim": "2027-04-27"
}
```

### `POST /contratos/{id}/status/`

Altera status. Tambem aceita envio por formulario institucional.

Body:

```json
{"status": "suspenso"}
```

Status aceitos: `ativo`, `expirado`, `cancelado`, `suspenso`, `encerrado`.

### `POST /contratos/{id}/arquivos/`

Envia arquivo versionado. Por formulario institucional, redireciona para o detalhe do contrato. Para resposta JSON, use `?format=json`.

Form-data:

- `arquivo`: arquivo do contrato.

## Propostas

### `GET /propostas/`

Lista propostas da empresa do usuario.

Query params:

- `texto`: busca por titulo, descricao ou cliente.
- `cliente`: busca parcial pelo nome do cliente.
- `status`: opcional.
- `validade_inicio`: filtra propostas validas a partir desta data.
- `validade_fim`: filtra propostas validas ate esta data.

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

### `POST /propostas/{id}/editar/`

Edita proposta, recalcula `valor_final` e registra auditoria dos campos alterados.

Body parcial aceito:

```json
{
  "titulo": "Proposta atualizada",
  "valor": "2000.00",
  "desconto": "10.00"
}
```

### `POST /propostas/{id}/status/`

Altera status. Tambem aceita envio por formulario institucional.

Body:

```json
{"status": "enviada"}
```

Status aceitos: `rascunho`, `enviada`, `aceita`, `rejeitada`, `expirada`, `convertida`.

### `POST /propostas/{id}/converter/`

Converte proposta aceita em contrato. O contrato criado fica independente da proposta. Por formulario institucional, redireciona para o contrato criado.

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
