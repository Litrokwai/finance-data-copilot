# Finance Data Copilot

Finance Data Copilot，中文名“金融数据 AI 开发助手”，是一个面向金融数据开发、SQL 分析、元数据管理和指标口径管理的 AI 数据工具。V1 聚焦 SQL 解释、SQL 风险检查、历史记录和 Dashboard，为个人职业发展、简历展示和后续企业内部数据开发场景扩展打基础。

## 技术栈

- 前端：React、TypeScript、Vite、Ant Design、React Router、TanStack Query、Axios、Monaco Editor、ECharts
- 后端：Python、FastAPI、Pydantic、SQLAlchemy、Alembic、SQLGlot
- 数据库：PostgreSQL、pgvector 预留
- 部署：Docker、Docker Compose

## V1 功能

- SQL 解释助手：解析 SQL 类型、表、字段、JOIN、WHERE，并生成摘要和建议。
- SQL 风险检查：检查 SELECT *、缺少 WHERE、DELETE、UPDATE、DROP、TRUNCATE、全表扫描和缺少日期条件等风险。
- SQL 分析历史：保存分析记录，支持前端列表和详情查看。
- Dashboard：展示分析总量、风险分布和最近趋势。
- 元数据全景：基于 PostgreSQL 中已同步的好股库元数据，展示表、字段、业务域、下线状态、敏感字段和业务域资产矩阵。
- 元数据质量：统计待治理分类、缺主键、字段中文名覆盖率、字段备注覆盖率、业务域质量和优先治理表。
- 存储过程血缘：基于链接服务器只读获取的存储过程定义，解析过程与表之间的读取、写入和临时表关系。
- 血缘复核工作台：聚合动态 SQL 过程和低置信度读写边，支持确认、标记需修正、忽略和备注。
- 数据库初始化：提供 schema.sql、seed.sql 和 Alembic 初始迁移。
- 公司元数据同步：支持从公司 SQL Server 的 `ai_platform` 元数据表只读同步好股库表、字段和指标口径。
- AI 模块预留：统一封装 `explain_sql_with_llm`，无 API Key 时返回 mock 结果。

## 目录结构

```text
finance-data-copilot/
├── backend/      # FastAPI 后端
├── frontend/     # React 前端
├── database/     # PostgreSQL 初始化 SQL
├── docs/         # 产品、技术、数据库和开发规范文档
├── docker-compose.yml
├── .env.example
└── README.md
```

当前产品阶段、数据规模、主线优先级和后续路线见 `docs/Product_Status.md`。当前阶段以元数据资产底座为优先主线，先确认可用表和可用字段，再继续完善血缘复核、影响分析和 AI 问答。

## 本地启动

1. 启动 PostgreSQL，并创建数据库 `finance_data_copilot`。如果本机已安装 PostgreSQL，可以执行：

```powershell
.\scripts\start_portable_postgres.ps1
.\scripts\init_local_postgres.ps1
```

2. 复制环境变量：

```bash
cp .env.example .env
```

3. 初始化后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. 启动前端：

```bash
cd frontend
npm install
npm run dev
```

前端默认访问 `http://localhost:5173`，后端默认访问 `http://localhost:8000`。

主要页面：

- `/dashboard`：SQL 分析统计 Dashboard
- `/metadata`：元数据全景
- `/metadata-quality`：元数据质量
- `/procedure-lineage`：存储过程血缘
- `/lineage-review`：血缘复核工作台
- `/sql-analyze`：SQL 解释
- `/sql-risk-check`：SQL 风险检查
- `/history`：SQL 分析历史

## Docker 启动

```bash
cp .env.example .env
docker compose up --build
```

启动后访问 `http://localhost:5173`。

## 同步公司元数据

当前已提供只读同步脚本，从公司 SQL Server 测试库中的 `howgow.ai_platform` 元数据表读取好股库数据字典，并写入本项目 PostgreSQL：

```powershell
.\backend\.venv\Scripts\python .\scripts\sync_howgow_metadata.py `
  --config "..\Annual_Strategy_Metrics\db_config.json"
```

同步范围默认包含 `system_key = 'howgow_link'` 下的全部好股库元数据，当前源端口径为 839 张表、24183 个字段和 2 个指标。脚本只读取元数据表，不读取真实业务明细数据。同步结果会写入 `metadata_table`、`metadata_column` 和 `metric_definition`。业务域为 `已下线表【禁止使用】` 的表和字段会保留入库，但 `is_valid` 标记为 `false`。

同步时会统一补齐常见固定字段说明：`SEQ`、`CREAT_TM`、`UPDT_TM`、`IS_VLD`、`RMRK`。这些字段只补充元数据解释，不读取或写入真实业务明细数据。字段展示顺序以源端 `catalog_columns.ordinal_position` 为准。

如需临时排除业务域为 `已下线表【禁止使用】` 的表，可增加参数：

```powershell
.\backend\.venv\Scripts\python .\scripts\sync_howgow_metadata.py `
  --config "..\Annual_Strategy_Metrics\db_config.json" `
  --exclude-offline
```

`database/seed.sql` 不再写入虚拟或演示业务元数据，公司表、字段和指标口径应以只读同步结果为准。

## 同步数据字典详情

主键、少数字段备注等信息需要从数据字典网页接口同步。该接口依赖浏览器登录态，因此脚本不会写死账号密码或 Cookie；使用前需要提供当前有效的浏览器会话 Cookie：

```powershell
$env:DATA_DICT_COOKIE="你的浏览器 Cookie"
.\backend\.venv\Scripts\python .\scripts\sync_data_dictionary_details.py --table EventThemeSubAI
```

如果不传 `--table`，脚本会尝试同步数据字典中可见的全部表。同步内容只写入本项目 PostgreSQL 的 `metadata_column.is_primary_key`、`column_comment`、`business_desc` 和 `is_nullable`，不会读取真实业务明细数据。

## 同步存储过程血缘

存储过程血缘同步脚本只读取好股库链接服务器的系统目录和过程定义，不执行存储过程，不读取真实业务明细数据。脚本使用 `OPENQUERY` 在链接服务器侧完成系统目录查询，并按批次写入 PostgreSQL，避免长时间大查询。同步结果写入 `procedure_lineage_record` 和 `procedure_lineage_edge`，前端页面展示解析后的读取表、写入表、临时表、表间链路和关系图。

```powershell
.\backend\.venv\Scripts\python .\scripts\sync_procedure_lineage.py
```

不传 `--procedure` 时默认全量同步当前可读取定义的好股库存储过程。可通过 `--batch-size` 控制批次大小，通过 `--limit` 做小批量验证。如需指定过程，可重复传入 `--procedure`。

## 元数据全景

元数据全景页面只读取本项目 PostgreSQL 中的 `metadata_table`、`metadata_column` 和 `metric_definition`，不连接公司业务库、不读取真实业务明细数据。当前支持：

- 总览统计：表数量、字段数量、可用表、指标口径。
- 业务域分布：按业务域统计表数量。
- 业务域资产矩阵：用独立的大尺寸矩形树图展示业务域和表的字段规模，点击业务域可下钻查看表分布。
- 表资产浏览：支持按关键字、业务域和状态筛选表，展示表名、中文名称、业务域、字段数和负责人。
- 服务端排序：表资产列表在后端全量排序后分页，默认按可用状态、业务域、字段数从高到低排列，避免只对当前页排序。
- 表详情：查看中文名称、字段序号、字段中文名、是否为空、主键、敏感字段标记、下线状态和关联指标。字段列表按源端 `ordinal_position` 排序；字段备注通过字段中文名旁的信息提示展示，不单独占用一列。

敏感字段当前由源端 `catalog_columns.pii_level` 映射到 `metadata_column.is_sensitive`。只要 `pii_level` 有有效分级且不是 `none`、`no`、`0`、`无`、`非敏感` 或 `public`，就会标记为敏感字段。现阶段不扫描字段内容，也不读取真实业务明细数据。

## 元数据质量

元数据质量页面读取本地 PostgreSQL 中的 `metadata_table`、`metadata_column` 和 `procedure_lineage_edge`，用于识别后续 AI 问答和血缘分析前需要优先治理的表和字段。当前不会修改源端分类，也不会覆盖 `metadata_table.business_domain`；空业务域、`未分类` 和 `好股库未分类` 会统一作为“待治理分类”参与统计。页面展示可用表、待治理分类、缺主键可用表、字段中文名覆盖率、表中文名覆盖率、业务域质量和优先治理表。

## 存储过程血缘

存储过程血缘页面读取本地 PostgreSQL 中的 `procedure_lineage_record` 和 `procedure_lineage_edge`，用于展示过程数量、读取表数量、写入表数量、血缘边数量、需复核数量、过程与表关系图、单过程详情和结构化血缘边。列表支持按过程名、涉及表和解析状态筛选，点击“需复核”统计卡可快速聚焦动态 SQL 或复杂语句。表影响分析支持从数据表视角查看读取该表的过程、写入该表的过程和相关表间链路，并过滤明显的 SQL 别名噪声。详情中会展示复核原因和语句片段。该页面不连接公司业务库，也不提供 SQL 或存储过程执行入口。

## 血缘复核工作台

血缘复核工作台读取本地 PostgreSQL 中的 `procedure_lineage_record`、`procedure_lineage_edge` 和 `lineage_review_record`。V1 默认把解析状态为 `REVIEW` 的过程、以及低置信度 `READ/WRITE` 边纳入候选，支持按状态、对象类型和关键词筛选，并可标记为已确认、需修正或已忽略。复核结果仅写入本项目 PostgreSQL，不连接公司业务库，不执行 SQL 或存储过程。

## 后续规划

- 接入真实大模型 API，增强 SQL 解释和优化建议。
- 增加数据字典 RAG 问答。
- 增加指标口径问答。
- 增强存储过程血缘解析，支持更多 T-SQL 语法、过程调用链和字段级血缘。
- 增加 Text-to-SQL。
- 增加受控 SQL Agent，但不直接连接真实公司生产库。
- 增加更完善的测试、CI 和部署配置。
