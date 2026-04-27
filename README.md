# ContraFlow

Sistema profissional de gestao de contratos e propostas com Django.

## Etapa atual

Backend modular com:

- Apps em ingles: `accounts`, `companies`, `clients`, `contracts`, `proposals`, `dashboard`, `core`.
- Modelos e regras em portugues.
- Usuario customizado com empresa e funcao.
- Empresa e clientes com isolamento por empresa.
- Permissoes base em `core/permissoes.py`.
- Superusuarios possuem escopo global e nao precisam estar vinculados a uma empresa.
- Configuracao preparada para PostgreSQL via variaveis de ambiente, com SQLite como fallback local.
- Contratos com auditoria e versionamento de arquivos.
- Propostas com conversao para contrato sem sincronizacao bidirecional.
- Dashboard com metricas por empresa.
- Views JSON para contratos, propostas e painel.
- Interface institucional server-rendered em `/` e `/painel/`.
- Formulario institucional para criar clientes, contratos e propostas sem sair para o Django Admin.
- Edicao institucional de clientes, contratos e propostas.
- Acoes institucionais para alterar status e converter propostas aceitas em contratos.
- Upload e listagem de arquivos versionados na tela de contrato.
- Cadastro de contatos na tela de cliente.
- Filtros funcionais nas listagens institucionais e nos endpoints JSON.

## Documentacao

- [ENDPOINTS.md](ENDPOINTS.md): rotas JSON disponiveis para integracao com frontend.

## Frontend

A primeira interface institucional esta disponivel em:

- `/`
- `/painel/`

O visual prioriza tabelas, tema claro, badges discretas e layout inspirado em sistemas academicos/corporativos.

As listagens de clientes, contratos e propostas aceitam filtros por campos de busca, status/tipo e datas conforme cada modulo.

Telas principais:

- `/clientes/`
- `/clientes/criar/`
- `/clientes/{id}/editar/`
- `/clientes/{id}/contatos/criar/`
- `/contratos/`
- `/contratos/criar/`
- `/contratos/{id}/editar/`
- `/propostas/`
- `/propostas/criar/`
- `/propostas/{id}/editar/`
- `/empresas/`
- `/contas/gestao-pessoas/`
- `/painel/administracao/`
- `/painel/central-servicos/`
- `/painel/relatorios/`

## Instalacao local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Testes

```bash
venv/bin/python manage.py test contracts proposals companies dashboard
```
