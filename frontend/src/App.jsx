import { useMemo, useState } from "react";
import { generateEmail } from "./api";

const initialForm = {
  sender_name: "",
  sender_role: "",
  recipient_name: "",
  recipient_role: "",
  company: "",
  purpose: "",
  key_points: "",
  additional_context: "",
  call_to_action: "",
  tone: "Professional",
  length: "Medium",
  language: "English"
};

function App() {
  const [formData, setFormData] = useState(initialForm);
  const [email, setEmail] = useState({ subject: "", body: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = useMemo(() => {
    return (
      formData.sender_name.trim() &&
      formData.recipient_name.trim() &&
      formData.purpose.trim() &&
      formData.key_points.trim()
    );
  }, [formData]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((previous) => ({ ...previous, [name]: value }));
  };

  const handleGenerate = async (event) => {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    setLoading(true);
    setError("");
    try {
      const generated = await generateEmail(formData);
      setEmail(generated);
    } catch (generationError) {
      setError(generationError.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (value) => {
    await navigator.clipboard.writeText(value);
  };

  return (
    <div className="page">
      <main className="container">
        <header className="hero">
          <h1>Email Generator AI</h1>
          <p>
            Provide context, tone, and goals. The AI will generate a polished, ready-to-send email.
          </p>
        </header>

        <section className="panel">
          <form className="grid-form" onSubmit={handleGenerate}>
            <label>
              Sender name *
              <input name="sender_name" value={formData.sender_name} onChange={handleChange} />
            </label>
            <label>
              Sender role
              <input name="sender_role" value={formData.sender_role} onChange={handleChange} />
            </label>
            <label>
              Recipient name *
              <input name="recipient_name" value={formData.recipient_name} onChange={handleChange} />
            </label>
            <label>
              Recipient role
              <input name="recipient_role" value={formData.recipient_role} onChange={handleChange} />
            </label>
            <label>
              Company
              <input name="company" value={formData.company} onChange={handleChange} />
            </label>
            <label>
              Tone
              <select name="tone" value={formData.tone} onChange={handleChange}>
                <option>Professional</option>
                <option>Friendly</option>
                <option>Persuasive</option>
                <option>Formal</option>
                <option>Concise</option>
              </select>
            </label>
            <label>
              Length
              <select name="length" value={formData.length} onChange={handleChange}>
                <option>Short</option>
                <option>Medium</option>
                <option>Long</option>
              </select>
            </label>
            <label>
              Language
              <input name="language" value={formData.language} onChange={handleChange} />
            </label>
            <label className="full">
              Purpose *
              <textarea name="purpose" rows="2" value={formData.purpose} onChange={handleChange} />
            </label>
            <label className="full">
              Key points *
              <textarea
                name="key_points"
                rows="4"
                placeholder="List bullet points or sentence fragments."
                value={formData.key_points}
                onChange={handleChange}
              />
            </label>
            <label className="full">
              Additional context
              <textarea
                name="additional_context"
                rows="3"
                value={formData.additional_context}
                onChange={handleChange}
              />
            </label>
            <label className="full">
              Call to action
              <textarea
                name="call_to_action"
                rows="2"
                value={formData.call_to_action}
                onChange={handleChange}
              />
            </label>

            <div className="actions full">
              <button type="submit" disabled={!canSubmit || loading}>
                {loading ? "Generating..." : "Generate Email"}
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setFormData(initialForm);
                  setEmail({ subject: "", body: "" });
                  setError("");
                }}
              >
                Clear
              </button>
            </div>
          </form>
        </section>

        {error ? <p className="error">{error}</p> : null}

        <section className="panel output">
          <div className="output-header">
            <h2>Generated Email</h2>
            {email.subject || email.body ? (
              <button className="secondary" onClick={() => handleCopy(`Subject: ${email.subject}\n\n${email.body}`)}>
                Copy Full Email
              </button>
            ) : null}
          </div>

          <div className="subject-box">
            <div className="output-title">
              <h3>Subject</h3>
              {email.subject ? (
                <button className="secondary mini" onClick={() => handleCopy(email.subject)}>
                  Copy
                </button>
              ) : null}
            </div>
            <p>{email.subject || "Your AI-generated subject line will appear here."}</p>
          </div>

          <div className="body-box">
            <div className="output-title">
              <h3>Body</h3>
              {email.body ? (
                <button className="secondary mini" onClick={() => handleCopy(email.body)}>
                  Copy
                </button>
              ) : null}
            </div>
            <pre>{email.body || "Your AI-generated email body will appear here."}</pre>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
