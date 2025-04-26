import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from "recharts";

const scores = [
  { test: "OOP", ai: 7.2, manual: 8.1 },
  { test: "DB", ai: 6.4, manual: 7.0 },
  { test: "ML", ai: 8.0, manual: 8.3 },
];

export default function BarChartComponent() {
  return (
    <div>
      <h4>AI vs Manual Scores</h4>
      <BarChart width={300} height={250} data={scores}>
        <XAxis dataKey="test" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="ai" fill="#8a2be2" />
        <Bar dataKey="manual" fill="#8884d8" />
      </BarChart>
    </div>
  );
}
