import Editor from "@monaco-editor/react";

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number;
}

export default function SqlEditor({ value, onChange, height = 320 }: SqlEditorProps) {
  return (
    <Editor
      height={height}
      defaultLanguage="sql"
      theme="vs"
      value={value}
      onChange={(next) => onChange(next || "")}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        wordWrap: "on",
        automaticLayout: true
      }}
    />
  );
}
