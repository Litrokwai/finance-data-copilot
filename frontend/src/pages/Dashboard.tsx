import { Card, Col, Row, Statistic, Typography } from "antd";
import { BarChartOutlined, ExclamationCircleOutlined, FileSearchOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import * as echarts from "echarts";
import { useEffect, useRef } from "react";
import { getDashboardSummary } from "../api/dashboard";

export default function Dashboard() {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const { data } = useQuery({ queryKey: ["dashboard-summary"], queryFn: getDashboardSummary });

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);
    chart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 32, right: 16, top: 32, bottom: 32 },
      xAxis: { type: "category", data: data?.trend.map((item) => item.date) || [] },
      yAxis: { type: "value", minInterval: 1 },
      series: [
        {
          type: "line",
          smooth: true,
          data: data?.trend.map((item) => item.count) || [],
          areaStyle: {}
        }
      ]
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [data]);

  return (
    <>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="SQL 分析总次数" value={data?.total_analysis_count || 0} prefix={<FileSearchOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="高风险 SQL" value={data?.high_risk_count || 0} valueStyle={{ color: "#cf1322" }} prefix={<ExclamationCircleOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="中风险 SQL" value={data?.medium_risk_count || 0} valueStyle={{ color: "#d46b08" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="低风险 SQL" value={data?.low_risk_count || 0} valueStyle={{ color: "#389e0d" }} />
          </Card>
        </Col>
      </Row>
      <Card title="最近分析趋势" style={{ marginTop: 16 }} extra={<BarChartOutlined />}>
        <div ref={chartRef} style={{ height: 320, width: "100%" }} />
      </Card>
    </>
  );
}
