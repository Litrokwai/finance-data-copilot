import {
  ApartmentOutlined,
  DatabaseOutlined,
  FieldStringOutlined,
  FundProjectionScreenOutlined,
  InfoCircleOutlined,
  SearchOutlined,
  TableOutlined
} from "@ant-design/icons";
import { Button, Card, Col, Descriptions, Drawer, Empty, Input, Row, Select, Space, Statistic, Table, Tag, Tooltip, Typography } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import type { SorterResult } from "antd/es/table/interface";
import { useQuery } from "@tanstack/react-query";
import * as echarts from "echarts";
import { useEffect, useMemo, useRef, useState } from "react";
import { getMetadataGraph, getMetadataSummary, getMetadataTableDetail, getMetadataTables } from "../api/metadata";
import type { MetadataColumnItem, MetadataGraphNode, MetadataMetricItem, MetadataTableListItem } from "../types/metadata";

const pageSize = 12;
const chartFontFamily = '"Segoe UI", "Microsoft YaHei", "PingFang SC", Arial, sans-serif';
const domainPalette = ["#3568d4", "#287c89", "#4b8f67", "#8b6fcb", "#b7791f", "#5b7c99", "#7b8794", "#486581"];
const tableFill = "#eef4fb";
const tableFillAlt = "#f6f8fb";
const offlineTableFill = "#f1f3f5";

function validityTag(isValid: boolean) {
  return isValid ? <Tag color="green">可用</Tag> : <Tag color="default">下线</Tag>;
}

function nullableTag(value?: boolean | null) {
  if (value === true) return <Tag color="blue">可为空</Tag>;
  if (value === false) return <Tag color="volcano">非空</Tag>;
  return <Tag>未知</Tag>;
}

function fieldRemark(record: MetadataColumnItem) {
  const remark = record.business_desc?.trim();
  const title = record.column_comment?.trim();
  if (!remark || remark === title) return "";
  return remark;
}

export default function MetadataPanorama() {
  const domainChartRef = useRef<HTMLDivElement | null>(null);
  const graphChartRef = useRef<HTMLDivElement | null>(null);
  const [searchText, setSearchText] = useState("");
  const [keyword, setKeyword] = useState("");
  const [businessDomain, setBusinessDomain] = useState<string | undefined>();
  const [validFilter, setValidFilter] = useState<string | undefined>();
  const [sortBy, setSortBy] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<"ascend" | "descend" | undefined>();
  const [page, setPage] = useState(1);
  const [currentTable, setCurrentTable] = useState<MetadataTableListItem | null>(null);

  const summaryQuery = useQuery({ queryKey: ["metadata-summary"], queryFn: getMetadataSummary });
  const graphQuery = useQuery({ queryKey: ["metadata-graph"], queryFn: getMetadataGraph });
  const tableQuery = useQuery({
    queryKey: ["metadata-tables", keyword, businessDomain, validFilter, sortBy, sortOrder, page],
    queryFn: () =>
      getMetadataTables({
        keyword: keyword || undefined,
        business_domain: businessDomain,
        is_valid: validFilter === undefined ? undefined : validFilter === "true",
        sort_by: sortBy,
        sort_order: sortOrder === "ascend" ? "asc" : sortOrder === "descend" ? "desc" : undefined,
        page,
        page_size: pageSize
      })
  });
  const detailQuery = useQuery({
    queryKey: ["metadata-table-detail", currentTable?.id],
    queryFn: () => getMetadataTableDetail(currentTable!.id),
    enabled: !!currentTable
  });

  const domainOptions = useMemo(
    () =>
      (summaryQuery.data?.domain_distribution || []).map((item) => ({
        label: `${item.business_domain} (${item.table_count})`,
        value: item.business_domain
      })),
    [summaryQuery.data]
  );

  const matrixData = useMemo(
    () =>
      (graphQuery.data?.tree.children || []).map((domain, domainIndex) => {
        const domainColor = domainPalette[domainIndex % domainPalette.length];
        return {
          ...domain,
          itemStyle: { color: domainColor, borderColor: "#ffffff", borderWidth: 3, gapWidth: 3 },
          label: {
            color: "#ffffff",
            fontFamily: chartFontFamily,
            fontSize: 13,
            fontWeight: 600
          },
          children: (domain.children || []).map((table, tableIndex): MetadataGraphNode & { itemStyle: object; label: object; emphasis: object } => {
            const isOffline = table.is_valid === false;
            return {
              ...table,
              itemStyle: {
                color: isOffline ? offlineTableFill : tableIndex % 2 === 0 ? tableFill : tableFillAlt,
                borderColor: "#ffffff",
                borderWidth: 1,
                gapWidth: 1
              },
              label: {
                color: isOffline ? "#8c8c8c" : "#334155",
                fontFamily: chartFontFamily,
                fontSize: 11,
                fontWeight: 500
              },
              emphasis: {
                itemStyle: {
                  color: isOffline ? "#e9ecef" : "#d9eafd",
                  borderColor: "#4c8ed9",
                  borderWidth: 1
                },
                label: {
                  color: "#102a43",
                  fontWeight: 600
                }
              }
            };
          })
        };
      }),
    [graphQuery.data]
  );

  useEffect(() => {
    if (!domainChartRef.current || !summaryQuery.data) return;
    const chart = echarts.init(domainChartRef.current);
    const data = summaryQuery.data.domain_distribution.slice(0, 12).reverse();
    chart.setOption({
      textStyle: { fontFamily: chartFontFamily, color: "#334155" },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      grid: { left: 96, right: 24, top: 16, bottom: 32 },
      xAxis: { type: "value", minInterval: 1 },
      yAxis: { type: "category", data: data.map((item) => item.business_domain) },
      series: [{ type: "bar", data: data.map((item) => item.table_count), itemStyle: { color: "#3568d4", borderRadius: [0, 4, 4, 0] } }]
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [summaryQuery.data]);

  useEffect(() => {
    if (!graphChartRef.current || !graphQuery.data) return;
    const chart = echarts.init(graphChartRef.current);
    chart.setOption({
      textStyle: { fontFamily: chartFontFamily },
      tooltip: {
        trigger: "item",
        formatter: (params: { data?: { table_name?: string; table_comment?: string; table_count?: number; value?: number; is_valid?: boolean }; name: string }) => {
          const tableName = params.data?.table_name;
          const tableComment = params.data?.table_comment;
          const value = params.data?.value ?? 0;
          if (tableName) {
            return `
              <div class="metadata-chart-tooltip">
                <div class="metadata-chart-tooltip-title">${tableComment || params.name}</div>
                <div>${tableName}</div>
                <div>字段数：${value}</div>
                <div>状态：${params.data?.is_valid ? "可用" : "下线"}</div>
              </div>
            `;
          }
          return `
            <div class="metadata-chart-tooltip">
              <div class="metadata-chart-tooltip-title">${params.name}</div>
              <div>表数量：${params.data?.table_count ?? 0}</div>
              <div>字段数量：${value}</div>
            </div>
          `;
        }
      },
      series: [
        {
          type: "treemap",
          data: matrixData,
          leafDepth: 1,
          roam: true,
          nodeClick: "zoomToNode",
          visibleMin: 120,
          top: 8,
          left: 8,
          right: 8,
          bottom: 36,
          breadcrumb: {
            show: true,
            bottom: 4,
            height: 24,
            itemStyle: { color: "#f5f7fa", borderColor: "#d9d9d9", textStyle: { color: "#595959", fontFamily: chartFontFamily } },
            emphasis: { itemStyle: { color: "#e6f4ff", textStyle: { color: "#0958d9", fontFamily: chartFontFamily } } }
          },
          label: {
            show: true,
            overflow: "truncate",
            minMargin: 6
          },
          upperLabel: { show: true, height: 28, color: "#262626", fontWeight: 600 },
          itemStyle: { borderColor: "#fff", borderWidth: 2, gapWidth: 2 },
          levels: [
            {
              itemStyle: { borderColor: "#f5f7fa", borderWidth: 4, gapWidth: 4 },
              upperLabel: { show: false }
            },
            {
              itemStyle: { borderColor: "#fff", borderWidth: 3, gapWidth: 3 },
              label: {
                color: "#fff",
                fontFamily: chartFontFamily,
                fontSize: 13,
                fontWeight: 600,
                formatter: (params: { name: string; data?: { table_count?: number; value?: number } }) =>
                  `${params.name}\n${params.data?.table_count ?? 0} 表 / ${params.data?.value ?? 0} 字段`
              }
            },
            {
              itemStyle: { borderColor: "rgba(255,255,255,0.88)", borderWidth: 1, gapWidth: 1 },
              label: {
                color: "#334155",
                fontFamily: chartFontFamily,
                fontSize: 11,
                fontWeight: 500,
                formatter: "{b}"
              }
            }
          ],
          animationDuration: 400,
          animationDurationUpdate: 600
        }
      ]
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [graphQuery.data, matrixData]);

  const tableColumns: ColumnsType<MetadataTableListItem> = [
    { title: "表名", dataIndex: "table_name", ellipsis: true, width: 280, sorter: true, sortOrder: sortBy === "table_name" ? sortOrder : null },
    { title: "中文名称", dataIndex: "table_comment", ellipsis: true, width: 220, sorter: true, sortOrder: sortBy === "table_comment" ? sortOrder : null },
    { title: "业务域", dataIndex: "business_domain", width: 160, ellipsis: true, sorter: true, sortOrder: sortBy === "business_domain" ? sortOrder : null },
    { title: "字段数", dataIndex: "column_count", width: 96, sorter: true, sortOrder: sortBy === "column_count" ? sortOrder : null },
    { title: "敏感字段", dataIndex: "sensitive_column_count", width: 100, sorter: true, sortOrder: sortBy === "sensitive_column_count" ? sortOrder : null },
    { title: "负责人", dataIndex: "owner", width: 120, ellipsis: true },
    { title: "状态", dataIndex: "is_valid", width: 88, render: validityTag },
    {
      title: "操作",
      width: 96,
      render: (_, record) => (
        <Button type="link" onClick={() => setCurrentTable(record)}>
          详情
        </Button>
      )
    }
  ];

  const handleTableChange = (
    pagination: TablePaginationConfig,
    _: Record<string, unknown>,
    sorter: SorterResult<MetadataTableListItem> | SorterResult<MetadataTableListItem>[]
  ) => {
    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter;
    setPage(pagination.current || 1);
    if (activeSorter?.order && activeSorter.field) {
      setSortBy(String(activeSorter.field));
      setSortOrder(activeSorter.order);
    } else {
      setSortBy(undefined);
      setSortOrder(undefined);
    }
  };

  const columnColumns: ColumnsType<MetadataColumnItem> = [
    { title: "序号", dataIndex: "ordinal_position", width: 72 },
    {
      title: "字段名",
      dataIndex: "column_name",
      width: 180,
      ellipsis: true,
      render: (value: string, record) => (
        <Space size={6}>
          <span>{value}</span>
          {record.is_primary_key ? <Tag color="gold">PK</Tag> : null}
        </Space>
      )
    },
    { title: "类型", dataIndex: "data_type", width: 120 },
    {
      title: "字段中文名",
      dataIndex: "column_comment",
      ellipsis: true,
      render: (value: string, record) => {
        const remark = fieldRemark(record);
        return (
          <Space size={6}>
            <span>{value || "-"}</span>
            {remark ? (
              <Tooltip title={remark}>
                <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
              </Tooltip>
            ) : null}
          </Space>
        );
      }
    },
    { title: "是否为空", dataIndex: "is_nullable", width: 100, render: nullableTag },
    { title: "敏感", dataIndex: "is_sensitive", width: 88, render: (value: boolean) => (value ? <Tag color="red">敏感</Tag> : <Tag>否</Tag>) },
    { title: "状态", dataIndex: "is_valid", width: 88, render: validityTag }
  ];

  const metricColumns: ColumnsType<MetadataMetricItem> = [
    { title: "指标编码", dataIndex: "metric_code", width: 180, ellipsis: true },
    { title: "指标名称", dataIndex: "metric_name", width: 180, ellipsis: true },
    { title: "口径说明", dataIndex: "business_desc", ellipsis: true },
    { title: "频率", dataIndex: "frequency", width: 96 },
    { title: "状态", dataIndex: "is_valid", width: 88, render: validityTag }
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3}>元数据全景</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="表总数" value={summaryQuery.data?.total_tables || 0} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="字段总数" value={summaryQuery.data?.total_columns || 0} prefix={<FieldStringOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="可用表" value={summaryQuery.data?.valid_tables || 0} valueStyle={{ color: "#389e0d" }} prefix={<TableOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="指标口径" value={summaryQuery.data?.total_metrics || 0} prefix={<FundProjectionScreenOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={8}>
          <Card title="业务域表分布" extra={<ApartmentOutlined />}>
            {summaryQuery.data?.domain_distribution.length ? <div ref={domainChartRef} style={{ height: 360 }} /> : <Empty />}
          </Card>
        </Col>
        <Col xs={24} xl={16}>
          <Card title="敏感字段口径" extra={<InfoCircleOutlined />}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="当前来源">catalog_columns.pii_level</Descriptions.Item>
              <Descriptions.Item label="当前方式">源端元数据映射</Descriptions.Item>
              <Descriptions.Item label="后续扩展">pii_level 分级字典、enum_values 取值知识、命名规则</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

      <Card
        title="业务域资产矩阵"
        extra={
          <Space size={8}>
            <Tag color="blue">{graphQuery.data?.tree.children?.length || 0} 个业务域</Tag>
            <Tag color="green">{graphQuery.data?.tree.value || 0} 个字段</Tag>
          </Space>
        }
      >
        {graphQuery.data ? <div className="metadata-matrix-chart" ref={graphChartRef} /> : <Empty />}
      </Card>

      <Card title="表资产浏览">
        <Space wrap style={{ marginBottom: 16 }}>
          <Input.Search
            allowClear
            placeholder="搜索表名、说明、业务域或负责人"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(event) => {
              setSearchText(event.target.value);
              if (!event.target.value) setKeyword("");
            }}
            onSearch={(value) => {
              setPage(1);
              setKeyword(value.trim());
            }}
            style={{ width: 320 }}
          />
          <Select
            allowClear
            showSearch
            placeholder="业务域"
            optionFilterProp="label"
            value={businessDomain}
            options={domainOptions}
            onChange={(value) => {
              setPage(1);
              setBusinessDomain(value);
            }}
            style={{ width: 260 }}
          />
          <Select
            allowClear
            placeholder="状态"
            value={validFilter}
            options={[
              { label: "可用", value: "true" },
              { label: "下线", value: "false" }
            ]}
            onChange={(value) => {
              setPage(1);
              setValidFilter(value);
            }}
            style={{ width: 140 }}
          />
        </Space>
        <Table
          rowKey="id"
          loading={tableQuery.isLoading}
          dataSource={tableQuery.data?.items || []}
          columns={tableColumns}
          onChange={handleTableChange}
          pagination={{
            current: page,
            pageSize,
            total: tableQuery.data?.total || 0,
            showSizeChanger: false
          }}
        />
      </Card>

      <Drawer title="表详情" open={!!currentTable} width={920} onClose={() => setCurrentTable(null)}>
        {detailQuery.data && (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="表名" span={2}>
                {detailQuery.data.table.table_name}
              </Descriptions.Item>
              <Descriptions.Item label="中文名称" span={2}>
                {detailQuery.data.table.table_comment || "-"}
              </Descriptions.Item>
              <Descriptions.Item label="业务域">{detailQuery.data.table.business_domain || "-"}</Descriptions.Item>
              <Descriptions.Item label="状态">{validityTag(detailQuery.data.table.is_valid)}</Descriptions.Item>
              <Descriptions.Item label="负责人">{detailQuery.data.table.owner || "-"}</Descriptions.Item>
              <Descriptions.Item label="字段数">{detailQuery.data.table.column_count}</Descriptions.Item>
            </Descriptions>
            <Table
              rowKey="id"
              size="small"
              title={() => "字段列表"}
              dataSource={detailQuery.data.columns}
              columns={columnColumns}
              pagination={{ pageSize: 12 }}
            />
            <Table
              rowKey="id"
              size="small"
              title={() => "关联指标"}
              dataSource={detailQuery.data.related_metrics}
              columns={metricColumns}
              pagination={false}
              locale={{ emptyText: "暂无直接关联指标" }}
            />
          </Space>
        )}
      </Drawer>
    </Space>
  );
}
