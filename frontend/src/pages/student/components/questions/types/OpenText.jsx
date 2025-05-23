export default function OpenText({ value, onChange }) {
  return (
    <textarea
      rows={6}
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Type your answer here..."
      style={{ width: "100%", marginTop: "1rem" }}
    />
  );
}