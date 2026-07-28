# CRM Pro - Sistema de Gestão de Clientes

Sistema CRM completo desenvolvido com Django e PostgreSQL.

## Funcionalidades

- **Dashboard** com métricas e gráficos
- **Gestão de Contatos** (leads, prospects, clientes)
- **Pipeline de Vendas** com Kanban drag-and-drop
- **Agenda e Tarefas** com calendário
- **Sistema de Autenticação** com múltiplos usuários
- **API REST** para integrações

## Tecnologias

- Python 3.10+
- Django 5.2
- PostgreSQL 14+
- Tailwind CSS (via CDN)
- Chart.js
- Alpine.js
- SortableJS

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd crm_project
```

2. Crie e ative o ambiente virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o banco de dados:
```bash
# PostgreSQL
createdb crm_db
```

5. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

6. Execute as migrações:
```bash
python manage.py migrate
```

7. Crie um superusuário:
```bash
python manage.py createsuperuser
```

8. Execute o servidor:
```bash
python manage.py runserver
```

9. Acesse o sistema:
- Aplicação: http://localhost:8000
- Admin: http://localhost:8000/admin

## Estrutura do Projeto

```
crm_project/
├── config/              # Configurações Django
├── apps/                # Aplicações
│   ├── accounts/        # Autenticação e usuários
│   ├── contacts/        # Gestão de contatos
│   ├── deals/           # Pipeline de vendas
│   ├── tasks/           # Agenda e tarefas
│   └── dashboard/       # Dashboard e API
├── templates/           # Templates HTML
├── static/              # Arquivos estáticos
└── manage.py
```

## API REST

A API está disponível em `/api/` com os seguintes endpoints:

- `GET/POST /api/contacts/` - Lista/criar contatos
- `GET/PUT/DELETE /api/contacts/<id>/` - Detalhes/atualizar/excluir contato
- `GET/POST /api/deals/` - Lista/criar negócios
- `GET/PUT/DELETE /api/deals/<id>/` - Detalhes/atualizar/excluir negócio
- `GET/POST /api/tasks/` - Lista/criar tarefas
- `GET/PUT/DELETE /api/tasks/<id>/` - Detalhes/atualizar/excluir tarefa
- `GET /api/dashboard/metrics/` - Métricas do dashboard

## Licença

MIT
