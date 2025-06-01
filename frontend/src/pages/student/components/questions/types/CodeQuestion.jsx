import { Editor } from "@monaco-editor/react";

export default function CodeQuestion({ starterCode, language, value, onChange }) {
  return (
    <div className="code-question">
    <Editor
      height="300px"
      language={language || "java"}
      value={value ?? starterCode}
      onChange={(val) => onChange(val)}
      theme="vs-dark"
    />
    </div>
  );
}
