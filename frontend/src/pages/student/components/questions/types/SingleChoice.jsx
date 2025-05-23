export default function SingleChoice({ options, selected, onChange }) {
  return (
    <div className="single-choice">
      {options.map((opt) => (
        <label key={opt.id} style={{ display: "block", marginBottom: "0.5rem" }}>
          <input
            type="radio"
            name="single-choice"
            value={opt.id}
            checked={selected === opt.id}
            onChange={() => onChange(opt.id)}
          />
          {opt.text}
        </label>
      ))}
    </div>
  );
}
