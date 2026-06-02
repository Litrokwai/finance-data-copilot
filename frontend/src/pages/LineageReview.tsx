import { CheckCircleOutlined, EditOutlined, ExclamationCircleOutlined, SearchOutlined, StopOutlined, WarningOutlined } from "@ant-design/icons";
import { Button, Card, Col, Input, Modal, Row, Select, Space, Statistic, Table, Tag, Tooltip, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { getLineageReviewItems, getLineageReviewSummary, updateLineageReviewItem } from "../api/lineage";
import type { LineageReviewItem, LineageReviewStatus, LineageReviewTargetType } from "../types/lineage";

function reviewStatusTag(status: LineageReviewStatus) {
  if (status === "CONFIRMED") return <Tag color="green">已确认</Tag>;
  if (status === "NEEDS_FIX") return <Tag color="red">需修正</Tag>;
  if (status === "IGNORED") return <Tag>已忽略</Tag>;
  return <Tag color="orange">待复核</Tag>;
}

function issueTypeTag(issueType: string) {
  if (issueType === "PARSE_REVIEW") return <Tag color="orange">过程解析</Tag>;
  return <Tag color="gold">低置信度边</Tag>;
}

function relationTag(value?: string) {
  if (!value) return "-";
  if (value === "READ") return <Tag>读取</Tag>;
  if (value === "WRITE") return <Tag color="cyan">写入</Tag>;
  return <Tag color="purple">表间链路</Tag>;
}

export default function LineageReview() {
  const queryClient = useQueryClient();
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState<LineageReviewStatus | undefined>("PENDING");
  const [targetType, setTargetType] = useState<LineageReviewTargetType | undefined>();
  const [noteTarget, setNoteTarget] = useState<{ item: LineageReviewItem; status: LineageReviewStatus } | null>(null);
  const [reviewNote, setReviewNote] = useState("");

  const summaryQuery = useQuery({
    queryKey: ["lineage-review-summary"],
    queryFn: () => getLineageReviewSummary({ confidence_threshold: 0.75 })
  });
  const itemsQuery = useQuery({
    queryKey: ["lineage-review-items", keyword, status, targetType],
    queryFn: () =>
      getLineageReviewItems({
        keyword: keyword || undefined,
        status,
        target_type: targetType,
        confidence_threshold: 0.75,
        limit: 300
      })
  });
  const updateMutation = useMutation({
    mutationFn: updateLineageReviewItem,
    onSuccess: async () => {
      message.success("复核状态已更新");
      setNoteTarget(null);
      setReviewNote("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["lineage-review-summary"] }),
        queryClient.invalidateQueries({ queryKey: ["lineage-review-items"] })
      ]);
    }
  });

  function markItem(item: LineageReviewItem, nextStatus: LineageReviewStatus, note?: string) {
    updateMutation.mutate({
      target_type: item.target_type,
      target_id: item.target_id,
      review_status: nextStatus,
      review_note: note ?? item.review_note,
      reviewer: "local"
    });
  }

  const columns: ColumnsType<LineageReviewItem> = [
    { title: "问题类型", dataIndex: "issue_type", width: 110, render: issueTypeTag },
    { title: "状态", dataIndex: "review_status", width: 96, render: reviewStatusTag },
    { title: "存储过程", dataIndex: "procedure_name", width: 220, ellipsis: true },
    {
      title: "关系",
      dataIndex: "relation_type",
      width: 100,
      render: relationTag
    },
    { title: "来源", dataIndex: "source_object", ellipsis: true, render: (value?: string) => value || "-" },
    { title: "目标", dataIndex: "target_object", ellipsis: true, render: (value?: string) => value || "-" },
    {
      title: "置信度",
      dataIndex: "confidence",
      width: 88,
      render: (value?: number) => (value == null ? "-" : `${Math.round(value * 100)}%`)
    },
    {
      title: "原因 / 语句",
      width: 260,
      render: (_, record) => {
        const text = record.statement_snippet || record.issue_reason;
        return (
          <Tooltip title={text}>
            <Typography.Text ellipsis style={{ maxWidth: 240 }}>
              {text}
            </Typography.Text>
          </Tooltip>
        );
      }
    },
    {
      title: "操作",
      width: 220,
      fixed: "right",
      render: (_, record) => (
        <Space size={6}>
          <Button size="small" icon={<CheckCircleOutlined />} onClick={() => markItem(record, "CONFIRMED")}>
            确认
          </Button>
          <Button
            size="small"
            danger
            icon={<EditOutlined />}
            onClick={() => {
              setNoteTarget({ item: record, status: "NEEDS_FIX" });
              setReviewNote(record.review_note || "");
            }}
          >
            修正
          </Button>
          <Button size="small" icon={<StopOutlined />} onClick={() => markItem(record, "IGNORED")}>
            忽略
          </Button>
        </Space>
      )
    }
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3}>血缘复核工作台</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="候选项" value={summaryQuery.data?.total_candidates || 0} prefix={<WarningOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="待复核" value={summaryQuery.data?.pending_count || 0} valueStyle={{ color: "#d46b08" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="已确认" value={summaryQuery.data?.confirmed_count || 0} valueStyle={{ color: "#389e0d" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="需修正" value={summaryQuery.data?.needs_fix_count || 0} valueStyle={{ color: "#cf1322" }} />
          </Card>
        </Col>
      </Row>

      <Card
        title="复核列表"
        extra={
          <Space wrap>
            <Input.Search
              allowClear
              enterButton={<SearchOutlined />}
              placeholder="搜索过程、来源表或目标表"
              style={{ width: 280 }}
              onSearch={(value) => setKeyword(value.trim())}
            />
            <Select
              allowClear
              placeholder="复核状态"
              style={{ width: 140 }}
              value={status}
              onChange={(value?: LineageReviewStatus) => setStatus(value)}
              options={[
                { label: "待复核", value: "PENDING" },
                { label: "已确认", value: "CONFIRMED" },
                { label: "需修正", value: "NEEDS_FIX" },
                { label: "已忽略", value: "IGNORED" }
              ]}
            />
            <Select
              allowClear
              placeholder="对象类型"
              style={{ width: 140 }}
              value={targetType}
              onChange={(value?: LineageReviewTargetType) => setTargetType(value)}
              options={[
                { label: "存储过程", value: "PROCEDURE" },
                { label: "血缘边", value: "EDGE" }
              ]}
            />
          </Space>
        }
      >
        <Table
          rowKey={(record) => `${record.target_type}-${record.target_id}`}
          loading={itemsQuery.isLoading || updateMutation.isPending}
          dataSource={itemsQuery.data || []}
          columns={columns}
          scroll={{ x: 1280 }}
          pagination={{ pageSize: 12 }}
        />
      </Card>

      <Modal
        title="标记为需修正"
        open={!!noteTarget}
        okText="保存"
        cancelText="取消"
        confirmLoading={updateMutation.isPending}
        onCancel={() => setNoteTarget(null)}
        onOk={() => noteTarget && markItem(noteTarget.item, noteTarget.status, reviewNote)}
      >
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Typography.Text type="secondary">
            请记录需要修正的原因，后续可据此优化解析规则或人工修正血缘。
          </Typography.Text>
          <Input.TextArea
            rows={4}
            value={reviewNote}
            onChange={(event) => setReviewNote(event.target.value)}
            placeholder="例如：动态 SQL 拼接表名，当前解析缺少真实写入表"
          />
        </Space>
      </Modal>
    </Space>
  );
}
