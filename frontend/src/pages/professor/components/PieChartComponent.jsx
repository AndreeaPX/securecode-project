import { PieChart, Pie, Cell, Legend, Tooltip } from "recharts";

const data = [
  { name: "0-5", value: 10 },
  { name: "6-7", value: 30 },
  { name: "8-9", value: 25 },
  { name: "10", value: 5 },
];

const COLORS = ["#8884d8", "#8a2be2", "#a66cff", "#c2a9fa"];

export default function PieChartComponent() {
  return (
    <div>
      <h4>Score Distribution</h4>
      <PieChart width={300} height={250}>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          outerRadius={80}
          dataKey="value"
          label
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </div>
  );
}
