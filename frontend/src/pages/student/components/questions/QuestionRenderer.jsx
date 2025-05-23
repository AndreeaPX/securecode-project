import React from "react";
import OpenText from "./types/OpenText";
import SingleChoice from "./types/SingleChoice";
import MultipleChoice from "./types/MultipleChoice";
import CodeQuestion from "./types/CodeQuestion";
import {getFullUrl} from "../../../../components/urlHelper";

export default function QuestionRenderer({ question, answer, setAnswer }) {
  if (!question) return null;

    const renderAttachments = () => {
    if (!question.attachments || question.attachments.length === 0) return null;

    return (
      <div style={{ marginBottom: "1rem" }}>
        {question.attachments.map((att, index) => {
          const url = getFullUrl(att.file || att.file_url);
          const fileType = att.file_type || "unknown";

          if (fileType === "image") {
            return (
              <div key={index} style={{ marginBottom: "1rem" }}>
                <img
                  src={url}
                  alt={`Attachment ${index + 1}`}
                  style={{ maxWidth: "100%", borderRadius: "8px", border: "1px solid #ccc" }}
                />
              </div>
            );
          }

          return (
            <div key={index} style={{ marginBottom: "1rem" }}>
              <a href= {url}
                download = {att.file_name || `attachment-${index+1}`}
                target="_blank"
                rel = "noopener noreferrer"
                className="attachment-download"
              >
              Download file {index + 1}              
              </a>
            </div>
          );
        })}
      </div>
    );
  };


  const renderQuestionComponent = () => {
  switch (question.type) {
    case "open":
      return <OpenText value={answer} onChange={setAnswer} />;

    case "single":
      return (
        <SingleChoice
          options={question.options}
          selected={answer}
          onChange={setAnswer}
        />
      );

    case "multiple":
      return (
        <MultipleChoice
          options={question.options}
          selected={answer || []}
          onChange={setAnswer}
        />
      );

    case "code":
      return (
        <CodeQuestion
          starterCode={question.starter_code}
          language={question.language}
          value={answer}
          onChange={setAnswer}
        />
      );

    default:
      return <p>Unsupported question type: {question.type}</p>;
  }
};

return (
  <div>
    {renderAttachments()}
    {renderQuestionComponent()}
  </div>
);

}
