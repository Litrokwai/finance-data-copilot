# Finance Data Copilot Agent Rules

## Project Overview

This project is Finance Data Copilot，中文名为“金融数据 AI 开发助手”。

项目定位：

面向金融数据开发场景的 AI 数据开发助手，支持 SQL 解释、SQL 风险检查、数据字典管理、指标口径管理、RAG 问答、Text-to-SQL 原型和 SQL Agent 后续扩展能力。

---

## Fixed Tech Stack

Do not change the following tech stack unless the user explicitly requests it.

Frontend:

- React
- TypeScript
- Vite
- Ant Design
- React Router
- TanStack Query
- Axios
- Monaco Editor
- ECharts

Backend:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLGlot

Database:

- PostgreSQL
- pgvector

Deployment:

- Docker
- Docker Compose

---

## Documentation Sync Rule

For every code, API, database, dependency, configuration, Docker, environment variable, or project structure change, use the `doc-sync-guard` skill.

Before modifying files, identify which documents may be affected.

After modifying files, update all relevant documentation, including but not limited to:

- README.md
- docs/PRD.md
- docs/Tech_Stack.md
- docs/Database_Design.md
- docs/AI_Coding_Rules.md
- docs/Project_Structure.md
- docs/API_Design.md, if present
- docs/Changelog.md, if present
- .env.example, if environment variables changed
- database/schema.sql, if database structure changed
- database/seed.sql, if seed data changed
- docker-compose.yml, if deployment changed

If a related document is checked but not updated, explain why.

Never complete a task with code changes only. A documentation sync report is required in the final response.

---

## Safety Rules

1. Do not connect to a real company database unless the user explicitly asks and confirms the security boundary.
2. Do not write real company database usernames, passwords, internal IPs, or sensitive fields into code or documentation.
3. Do not put real company business data into seed.sql.
4. If working with external SQL Server or MySQL sources, only collect metadata by default.
5. Do not collect real business detail data by default.
6. External data source operations must be read-only by default.
7. Do not implement SQL execution against production databases unless explicitly requested.
8. Do not implement write operations against external data sources.

---

## Development Rules

1. Do not replace the selected tech stack.
2. Do not remove existing functionality.
3. Do not introduce new dependencies unless necessary.
4. Keep backend code separated by api、schemas、models、services、core、ai、datasource.
5. Keep frontend code separated by api、components、pages、router、types.
6. Backend API response format should remain consistent.
7. Frontend UI should remain consistent with Ant Design admin style.
8. Database schema changes must be reflected in database/schema.sql and docs/Database_Design.md.
9. API changes must be reflected in docs/API_Design.md if the document exists.
10. Project structure changes must be reflected in docs/Project_Structure.md.

---

## Required Final Report Format

After each task, respond with:

### 本次完成内容

- Summary of completed work.

### 代码修改文件

- List changed code files.

### 文档同步情况

已更新：

- List updated documentation files and what changed.

已检查但未更新：

- List checked documentation files and why no update was needed.

### 验收方式

- How to run or verify the change.

### 风险与注意事项

- Any risk, limitation, or follow-up item.
