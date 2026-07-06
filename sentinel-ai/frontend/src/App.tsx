import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { fetchInvestigationCases, generateNarrative } from "./api/client";
import { CaseDetail } from "./components/CaseDetail";
import { DashboardSummary } from "./components/DashboardSummary";
import { InvestigationQueue } from "./components/InvestigationQueue";
import { mockCases } from "./mockData";
import { mockTimelineByCase } from "./mockTimelineData";
import type { InvestigationCase, InvestigationNarrative } from "./types";
import "./styles.css";

export default function App() {
  const [cases, setCases] = useState<InvestigationCase[]>(mockCases);
  const [selectedCase, setSelectedCase] = useState<InvestigationCase | null>(mockCases[0]);
  const [narrative, setNarrative] = useState<InvestigationNarrative | null>(null);
  const [apiStatus, setApiStatus] = useState("demo data");

  useEffect(() => {
    fetchInvestigationCases()
      .then((items) => {
        if (items.length > 0) {
          setCases(items);
          setSelectedCase(items[0]);
          setApiStatus("live API");
        }
      })
      .catch(() => {
        setApiStatus("demo data");
      });
  }, []);

  const handleGenerateNarrative = async () => {
    if (!selectedCase) return;

    try {
      const generated = await generateNarrative(selectedCase.case_id);
      setNarrative(generated);
    } catch {
      setNarrative({
        case_id: selectedCase.case_id,
        executive_summary: "Demo narrative generated locally because the workflow API is unavailable.",
        key_findings: selectedCase.evidence_links.map((item) => item.summary),
        evidence_summary: selectedCase.evidence_links.map((item) => `${item.source}: ${item.summary}`),
        recommended_next_steps: ["Review source activities.", "Validate operational exceptions.", "Document final decision."],
        limitations: ["This fallback narrative is based only on loaded case data."]
      });
    }
  };

  return (
    <main className="app-shell">
      <header>
        <div className="brand">
          <ShieldCheck size={28} />
          <div>
            <h1>Sentinel AI</h1>
            <p>Enterprise Workforce Integrity Platform</p>
          </div>
        </div>
        <span className="api-status">Source: {apiStatus}</span>
      </header>

      <DashboardSummary cases={cases} />

      <div className="content-grid">
        <InvestigationQueue
          cases={cases}
          selectedCaseId={selectedCase?.case_id ?? null}
          onSelect={(item) => {
            setSelectedCase(item);
            setNarrative(null);
          }}
        />
        <CaseDetail
          selectedCase={selectedCase}
          narrative={narrative}
          onGenerateNarrative={handleGenerateNarrative}
          timelineData={selectedCase ? mockTimelineByCase[selectedCase.case_id] ?? null : null}
        />
      </div>
    </main>
  );
}
