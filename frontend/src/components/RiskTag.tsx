import { Tag } from "antd";
import type { RiskLevel } from "../types/sql";

const riskConfig: Record<RiskLevel, { color: string; text: string }> = {
  HIGH: { color: "red", text: "高风险" },
  MEDIUM: { color: "orange", text: "中风险" },
  LOW: { color: "green", text: "低风险" }
};

export default function RiskTag({ level }: { level?: RiskLevel }) {
  if (!level) {
    return <Tag>未知</Tag>;
  }
  const config = riskConfig[level];
  return <Tag color={config.color}>{config.text}</Tag>;
}
