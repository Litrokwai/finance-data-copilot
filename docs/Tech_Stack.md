# Tech Stack

## 前端

React 和 TypeScript 适合构建可维护的后台系统。Vite 启动快、配置轻，适合个人项目和后续扩展。Ant Design 提供成熟的企业后台组件，能快速实现菜单、表格、卡片、抽屉和表单。React Router 管理页面路由，TanStack Query 负责请求缓存和状态，Axios 统一封装请求。Monaco Editor 提供专业 SQL 编辑体验，ECharts 用于 Dashboard 图表和元数据体系可视化。

## 后端

FastAPI 提供清晰的 API 开发体验和自动文档能力。Pydantic 用于请求和响应数据校验。SQLAlchemy 负责 ORM 建模，Alembic 负责数据库迁移。SQLGlot 是成熟 SQL 解析库，适合做 SQL 类型识别、表字段提取和基础结构分析。SQL Server 元数据同步使用 `pyodbc` 连接公司测试库，只读取 `ai_platform` 元数据表。存储过程血缘同步也复用 `pyodbc`，通过链接服务器只读读取好股库系统目录中的过程定义，并使用 `OPENQUERY` 分批拉取，解析后写入本地 PostgreSQL。

元数据全景和存储过程血缘接口复用 FastAPI、Pydantic 和 SQLAlchemy，直接读取本项目 PostgreSQL 中的元数据和血缘缓存表，不新增外部数据源依赖。

## 数据库

PostgreSQL 是最终主库，适合结构化业务数据、JSONB 分析结果和后续企业场景。pgvector 在 V1 先预留扩展能力，后续可以用于数据字典、指标口径和文档向量检索。

公司 SQL Server 不是本项目主库，现阶段只作为外部元数据来源。同步范围限定为好股库 `system_key = 'howgow_link'` 的表、字段和指标口径；下线表会保留入库用于源端口径对齐，但在 PostgreSQL 中标记为不可用。

## 部署

Docker 和 Docker Compose 能统一本地开发和演示环境，包含 PostgreSQL、backend 和 frontend，降低项目交付和复现成本。
