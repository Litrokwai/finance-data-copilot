import { Button, Card, Space, Typography } from "antd";
import { PlayCircleOutlined } from "@ant-design/icons";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { analyzeSql } from "../api/sql";
import ResultCard from "../components/ResultCard";
import SqlEditor from "../components/SqlEditor";

export default function SqlAnalyze() {
  const [sql, setSql] = useState("");
  const mutation = useMutation({ mutationFn: analyzeSql });

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3}>SQL 解释</Typography.Title>
      <Card>
        <SqlEditor value={sql} onChange={setSql} />
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          loading={mutation.isPending}
          disabled={!sql.trim()}
          onClick={() => mutation.mutate(sql)}
          style={{ marginTop: 16 }}
        >
          开始分析
        </Button>
      </Card>
      <ResultCard result={mutation.data} />
    </Space>
  );
}
