# ContraFlow

Sistema profissional de gestao de contratos e propostas com Django.

## Etapa atual

Fundacao do projeto:

- Apps em ingles: `accounts`, `companies`, `clients`, `contracts`, `proposals`, `dashboard`, `core`.
- Modelos e regras em portugues.
- Usuario customizado com empresa e funcao.
- Empresa e clientes com isolamento por empresa.
- Permissoes base em `core/permissoes.py`.
- Configuracao preparada para PostgreSQL via variaveis de ambiente, com SQLite como fallback local.

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
