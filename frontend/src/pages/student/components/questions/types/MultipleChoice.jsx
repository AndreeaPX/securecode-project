export default function MultipleChoice({ options, selected, onChange }) {
  const toggle = (id) => {
    if (selected.includes(id)) {
      onChange(selected.filter((val) => val !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="multiple-choice">
      {options.map((opt) => (
        <label key={opt.id} style={{ display: "block", marginBottom: "0.5rem" }}>
          <input
            type="checkbox"
            value={opt.id}
            checked={selected.includes(opt.id)}
            onChange={() => toggle(opt.id)}
          />
          {opt.text}
        </label>
      ))}
    </div>
  );
}
