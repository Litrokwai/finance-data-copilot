# Database Design

## sql_analysis_record

保存 SQL 分析历史记录。

| 字段 | 含义 |
| --- | --- |
| id | 主键 |
| raw_sql | 原始 SQL |
| sql_type | SQL 类型 |
| summary | SQL 摘要 |
| involved_tables | 涉及表 |
| involved_columns | 涉及字段 |
| join_relations | JOIN 关系 |
| where_conditions | WHERE 条件 |
| risk_level | 风险等级 |
| risk_items | 风险项 |
| analysis_result_json | 完整分析结果 JSON |
| created_at | 创建时间 |

## metadata_table

保存数据字典表级元数据。V1 可由公司 SQL Server 测试库中的 `howgow.ai_platform.catalog_tables` 只读同步好股库表信息。

| 字段 | 含义 |
| --- | --- |
| id | 主键 |
| table_name | 表名 |
| table_comment | 表说明 |
| business_domain | 业务域 |
| owner | 负责人 |
| update_frequency | 更新频率 |
| source_collected_at | 源端元数据采集时间，来自 `catalog_tables.collected_at` |
| latest_creat_tm | 源端最近创建时间信号，来自 `catalog_tables.latest_creat_tm` |
| is_valid | 是否有效 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

好股库同步映射：

| 来源字段 | 目标字段 |
| --- | --- |
| server_name + table_catalog + table_schema + table_name | table_name |
| business_name 或 description | table_comment |
| business_domain | business_domain |
| owner | owner |
| refresh_frequency | update_frequency |
| collected_at | source_collected_at |
| latest_creat_tm | latest_creat_tm |

`created_at` 和 `updated_at` 是本项目 PostgreSQL 记录时间，不代表公司业务表真实创建或更新时间。判断表是否疑似长期未更新时，应优先使用源端同步来的 `latest_creat_tm`，并结合血缘引用、表名命名模式、表中文名和主键信息综合判断。

## metadata_column

保存字段级元数据。V1 可由公司 SQL Server 测试库中的 `howgow.ai_platform.catalog_columns` 只读同步好股库字段信息。

| 字段 | 含义 |
| --- | --- |
| id | 主键 |
| table_name | 表名 |
| column_name | 字段名 |
| ordinal_position | 源端字段序号 |
| data_type | 数据类型 |
| column_comment | 字段注释 |
| business_desc | 业务解释 |
| example_value | 示例值 |
| is_primary_key | 是否主键 |
| is_nullable | 是否允许为空 |
| is_sensitive | 是否敏感字段 |
| is_valid | 是否有效 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

好股库同步映射：

| 来源字段 | 目标字段 |
| --- | --- |
| column_name | column_name |
| data_type + char_length / numeric_precision / numeric_scale | data_type |
| ordinal_position | ordinal_position |
| business_name | column_comment |
| description | business_desc |
| is_nullable | is_nullable |
| pii_level | is_sensitive |

固定字段补充规则：

| 字段名 | 标准中文含义 |
| --- | --- |
| SEQ | 自增序号 |
| CREAT_TM | 创建时间 |
| UPDT_TM | 更新时间 |
| IS_VLD | 是否有效 |
| RMRK | 数据来源序号 |

同步脚本会将这些固定字段统一写入标准中文含义，覆盖源端空值或不完整说明，并写入 `metadata_column.column_comment` 和 `metadata_column.business_desc`。

SQL Server 字符和二进制大值类型长度为 `-1` 时代表 `max`，同步脚本会写入 `varchar(max)`、`nvarchar(max)` 或 `varbinary(max)`，避免在页面显示为 `varchar(-1)`。源端 `catalog_columns` 当前没有主键标记字段，因此主键不再用 `SEQ` 猜测生成，必须通过数据字典网页接口同步后写入 `is_primary_key`。

数据字典详情同步脚本 `scripts/sync_data_dictionary_details.py` 会读取网页接口中的 `dictCols.isPK`、`dictCols.rmrk`、`dictCols.colDescCN` 和 `dictCols.isNullable`，分别更新 `is_primary_key`、`business_desc`、`column_comment` 和 `is_nullable`。该脚本依赖浏览器登录态 Cookie，不会把 Cookie、账号或密码写入项目文件。

## metric_definition

保存指标口径管理信息。V1 可由公司 SQL Server 测试库中的 `howgow.ai_platform.metric_definitions` 和 `metric_lineage` 只读同步。

| 字段 | 含义 |
| --- | --- |
| id | 主键 |
| metric_code | 指标编码 |
| metric_name | 指标名称 |
| formula | 指标公式 |
| business_desc | 业务解释 |
| source_tables | 来源表 |
| source_columns | 来源字段 |
| dimension | 统计维度 |
| frequency | 统计频率 |
| example_sql | 示例 SQL |
| is_valid | 是否有效 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

好股库同步映射：

| 来源字段 | 目标字段 |
| --- | --- |
| metric_code | metric_code |
| metric_name | metric_name |
| calculation_logic | formula |
| business_definition | business_desc |
| source_tables | source_tables |
| metric_lineage.upstream_type = column | source_columns |
| dimensions | dimension |
| update_frequency | frequency |
| sql_example | example_sql |

## procedure_lineage_record

保存存储过程血缘解析结果。V1 通过测试库连接和好股库链接服务器只读读取系统目录中的存储过程定义，解析后写入 PostgreSQL；不执行存储过程，不读取真实业务明细数据。

| 字段 | 含义 |
| --- | --- |
| id | 主键 |
| procedure_name | 存储过程名称 |
| procedure_schema | 存储过程 schema |
| database_name | 来源数据库名称 |
| source_system | 来源系统标识 |
| definition_hash | 存储过程定义哈希，用于判断定义是否变化 |
| read_tables | 解析出的读取表 |
| write_tables | 解析出的写入表 |
| temp_tables | 解析出的临时表 |
| lineage_edges | 过程与表之间的 READ/WRITE 关系边 |
| statement_count | 解析出的语句数量 |
| parse_status | 解析状态 |
| parse_message | 解析提示 |
| synced_at | 同步时间 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

V1 不在 API 中返回存储过程正文，只展示解析后的表关系。后续可扩展过程调用链、字段级血缘和解析置信度。

## procedure_lineage_edge

保存结构化血缘边，支撑全量存储过程查询、过滤和图谱展示。

| 字段 | 含义 |
| --- | --- |
| id | 主键 |
| procedure_id | 关联 `procedure_lineage_record.id` |
| procedure_name | 存储过程名称 |
| source_object | 来源对象 |
| target_object | 目标对象 |
| relation_type | 关系类型：`READ`、`WRITE`、`TABLE_FLOW` |
| source_kind | 来源对象类型：`procedure`、`table`、`temp_table` |
| target_kind | 目标对象类型：`procedure`、`table`、`temp_table` |
| statement_index | 语句序号 |
| statement_type | 语句类型 |
| confidence | 解析置信度 |
| statement_snippet | 语句片段，便于人工复核 |
| created_at | 创建时间 |

`procedure_lineage_edge` 在每次同步单个过程时先删除该过程旧边，再写入新边。动态 SQL、变量表名等场景会降低置信度或标记为需复核。

## lineage_review_record

保存血缘复核工作台的人工复核状态。该表只存在于本项目 PostgreSQL，用于标记已同步血缘结果是否确认、需修正或忽略，不写入公司 SQL Server，也不触发任何 SQL 或存储过程执行。

| 字段 | 含义 |
| --- | --- |
| id | 主键 |
| target_type | 复核对象类型：`PROCEDURE` 或 `EDGE` |
| target_id | 复核对象 ID，对应 `procedure_lineage_record.id` 或 `procedure_lineage_edge.id` |
| review_status | 复核状态：`PENDING`、`CONFIRMED`、`NEEDS_FIX`、`IGNORED` |
| review_note | 复核备注 |
| reviewer | 复核人标识 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

`target_type` 和 `target_id` 组合唯一，避免同一复核对象重复生成多条状态记录。V1 的复核候选由服务层动态计算：解析状态为 `REVIEW` 的过程，以及低置信度 `READ/WRITE` 边；人工状态记录只保存用户操作结果。统计口径只纳入当前仍然有效的候选项，避免血缘重跑或阈值变化后旧复核记录污染工作台统计。

## 表关系

V1 暂不强制建立元数据表外键，避免元数据录入不完整时影响演示。后续可按 `metadata_column.table_name` 与 `metadata_table.table_name` 建立逻辑关系，指标表通过 JSONB 保存来源表和字段。存储过程血缘保留 `procedure_lineage_record.lineage_edges` 作为兼容 JSON，同时通过 `procedure_lineage_edge` 保存结构化边；血缘复核状态通过 `lineage_review_record.target_type + target_id` 逻辑关联到过程或边。

## 初始化数据规则

`database/seed.sql` 不再写入虚拟或演示业务元数据。好股库表、字段和指标口径应通过只读同步脚本从 `ai_platform` 元数据表写入 PostgreSQL，默认同步 `system_key = 'howgow_link'` 下的完整源端口径。

完整同步会保留业务域为 `已下线表【禁止使用】` 的元数据以便数量与源端一致，但这类表和字段的 `is_valid` 会标记为 `false`，后续问答或推荐逻辑应避免优先使用。

元数据全景页面直接读取 `metadata_table`、`metadata_column` 和 `metric_definition`，用于展示表资产列表、字段详情、业务域分布、敏感字段统计、下线状态和关联指标。该页面不新增数据库表，也不读取真实业务明细数据。

敏感字段定义当前来自 `catalog_columns.pii_level` 到 `metadata_column.is_sensitive` 的同步映射。只要 `pii_level` 有有效分级且不是 `none`、`no`、`0`、`无`、`非敏感` 或 `public`，就会标记为敏感字段。后续如需更严格的数据安全分级，应补充敏感级别字典、字段命名规则、数据类型规则、展示脱敏规则和审批边界。
