import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FieldStringOutlined,
  PartitionOutlined,
  TableOutlined,
  WarningOutlined
} from "@ant-design/icons";
import { Card, Col, Progress, Row, Space, Statistic, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useQuery } from "@tanstack/react-query";
import { getMetadataQuality } from "../api/metadata";
import type { MetadataQualityDomainStat, MetadataQualityIssueStat, MetadataQualityTableItem } from "../types/metadata";

function scoreColor(score: number) {
  if (score >= 85) return "#389e0d";
  if (score >= 70) return "#d48806";
  return "#cf1322";
}

function validityTag(isValid: boolean) {
  return isValid ? <Tag color="green">可用</Tag> : <Tag>下线</Tag>;
}

function issueTag(tag: string) {
  if (tag === "待治理分类") return <Tag color="gold">{tag}</Tag>;
  if (tag === "缺主键" || tag === "字段类型异常") return <Tag color="red">{tag}</Tag>;
  if (tag === "下线表") return <Tag>{tag}</Tag>;
  return <Tag color="blue">{tag}</Tag>;
}

export default function MetadataQuality() {
  const qualityQuery = useQuery({ queryKey: ["metadata-quality"], queryFn: getMetadataQuality });
  const data = qualityQuery.data;

  const issueColumns: ColumnsType<MetadataQualityIssueStat> = [
    { title: "问题", dataIndex: "issue_name" },
    { title: "数量", dataIndex: "count", width: 120, sorter: (a, b) => a.count - b.count }
  ];

  const domainColumns: ColumnsType<MetadataQualityDomainStat> = [
    {
      title: "业务域",
      dataIndex: "business_domain",
      ellipsis: true,
      render: (value: string, record) => (
        <Space size={6}>
          <span>{value}</span>
          {record.unclassified ? <Tag color="gold">待治理</Tag> : null}
        </Space>
      )
    },
    { title: "表数", dataIndex: "table_count", width: 90, sorter: (a, b) => a.table_count - b.table_count },
    { title: "可用表", dataIndex: "valid_table_count", width: 90, sorter: (a, b) => a.valid_table_count - b.valid_table_count },
    {
      title: "平均质量分",
      dataIndex: "avg_quality_score",
      width: 150,
      sorter: (a, b) => a.avg_quality_score - b.avg_quality_score,
      render: (value: number) => <Progress percent={Math.round(value)} size="small" strokeColor={scoreColor(value)} />
    }
  ];

  const tableColumns: ColumnsType<MetadataQualityTableItem> = [
    {
      title: "表名",
      dataIndex: "table_name",
      width: 300,
      ellipsis: true
    },
    { title: "中文名称", dataIndex: "table_comment", width: 180, ellipsis: true, render: (value?: string) => value || "-" },
    { title: "业务域", dataIndex: "business_domain", width: 160, ellipsis: true, render: (value?: string) => value || "-" },
    { title: "状态", dataIndex: "is_valid", width: 84, render: validityTag },
    { title: "字段", dataIndex: "column_count", width: 80, sorter: (a, b) => a.column_count - b.column_count },
    { title: "主键", dataIndex: "primary_key_count", width: 80, sorter: (a, b) => a.primary_key_count - b.primary_key_count },
    {
      title: "血缘引用",
      dataIndex: "lineage_ref_count",
      width: 100,
      sorter: (a, b) => a.lineage_ref_count - b.lineage_ref_count
    },
    {
      title: "质量分",
      dataIndex: "quality_score",
      width: 130,
      sorter: (a, b) => a.quality_score - b.quality_score,
      render: (value: number) => <Progress percent={value} size="small" strokeColor={scoreColor(value)} />
    },
    {
      title: "问题标签",
      dataIndex: "issue_tags",
      render: (tags: string[]) => <Space size={[0, 4]} wrap>{tags.map((tag) => issueTag(tag))}</Space>
    }
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3}>元数据质量</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="可用表" value={data?.valid_tables || 0} prefix={<TableOutlined />} valueStyle={{ color: "#389e0d" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="待治理分类" value={data?.unclassified_tables || 0} prefix={<PartitionOutlined />} valueStyle={{ color: "#d48806" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="缺主键可用表" value={data?.tables_without_primary_key || 0} prefix={<WarningOutlined />} valueStyle={{ color: "#cf1322" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="字段中文名覆盖率" value={data?.column_comment_coverage || 0} suffix="%" prefix={<FieldStringOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card title="表中文名覆盖率">
            <Progress type="dashboard" percent={data?.table_comment_coverage || 0} strokeColor={scoreColor(data?.table_comment_coverage || 0)} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="主键覆盖率">
            <Progress type="dashboard" percent={data?.primary_key_coverage || 0} strokeColor={scoreColor(data?.primary_key_coverage || 0)} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="字段类型异常">
            <Statistic value={data?.columns_type_anomaly || 0} prefix={<CheckCircleOutlined />} valueStyle={{ color: data?.columns_type_anomaly ? "#cf1322" : "#389e0d" }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="质量问题分布" extra={<ExclamationCircleOutlined />}>
            <Table
              rowKey="issue_code"
              size="small"
              loading={qualityQuery.isLoading}
              dataSource={data?.issue_stats || []}
              columns={issueColumns}
              pagination={false}
            />
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="业务域质量">
            <Table
              rowKey="business_domain"
              size="small"
              loading={qualityQuery.isLoading}
              dataSource={data?.domain_quality || []}
              columns={domainColumns}
              pagination={{ pageSize: 8 }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="优先治理表">
        <Table
          rowKey="id"
          loading={qualityQuery.isLoading}
          dataSource={data?.top_issue_tables || []}
          columns={tableColumns}
          pagination={{ pageSize: 12 }}
          scroll={{ x: 1280 }}
        />
      </Card>
    </Space>
  );
}
