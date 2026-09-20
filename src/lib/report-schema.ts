/**
 * The report shape the model must return, plus a hand-rolled validator.
 * Nothing is saved to the database until it passes this.
 */

export type ThreeQuestionStatus = "answered" | "partial" | "unanswered";
export type FactorStatus = "fix_now" | "improve" | "solid";
export type FactorLetter = "C" | "O" | "N" | "V" | "E" | "R" | "T";
export type FactorType = "accelerator" | "blocker";

export type ThreeQuestionEntry = {
  question: string;
  score: number;
  status: ThreeQuestionStatus;
  explanation: string;
};

export type ConvertFactor = {
  letter: FactorLetter;
  name: string;
  type: FactorType;
  score: number;
  status: FactorStatus;
  findings: { check: string; finding: string }[];
  analysis: string;
};

export type TrustSignalRow = { signal: string; present: boolean; note: string };
export type DeadlySinRow = { sin: string; detected: boolean; note: string };

export type AuditReport = {
  url: string;
  overallScore: number;
  verdict: string;
  threeQuestions: ThreeQuestionEntry[];
  convertFactors: ConvertFactor[];
  trustSignalAudit: TrustSignalRow[];
  deadlySins: DeadlySinRow[];
  revenueImpact: { estimateRange: string; reasoning: string };
  topRecommendations: string[];
};

export const FACTOR_ORDER: { letter: FactorLetter; name: string; type: FactorType; weight: number }[] = [
  { letter: "C", name: "Clarity", type: "accelerator", weight: 1 },
  { letter: "O", name: "Offer", type: "accelerator", weight: 1 },
  { letter: "N", name: "Navigation", type: "blocker", weight: 1.5 },
  { letter: "V", name: "Validation", type: "blocker", weight: 1.5 },
  { letter: "E", name: "Emotion", type: "accelerator", weight: 1 },
  { letter: "R", name: "Relevance", type: "accelerator", weight: 1 },
  { letter: "T", name: "Traction", type: "blocker", weight: 1.5 },
];

export const TRUST_SIGNAL_ORDER = [
  "Visible phone number",
  "Real customer photos",
  "Specific, detailed testimonials",
  "Concrete social proof numbers",
  "Security badges or guarantees",
];

export const DEADLY_SINS_ORDER = [
  "Unclear call to action",
  "Too many choices",
  "Visual distractions",
  "Not keeping promises",
  "Too much text",
  "Asking for too much information",
  "Lack of trust and credibility",
];

export function statusForScore(score: number): FactorStatus {
  if (score < 6) return "fix_now";
  if (score < 8) return "improve";
  return "solid";
}

/** Blockers weigh more than accelerators: they stop conversion outright. */
export function weightedOverallScore(factors: ConvertFactor[]): number {
  let weightedSum = 0;
  let weightTotal = 0;
  for (const factor of factors) {
    const weight = FACTOR_ORDER.find((entry) => entry.letter === factor.letter)?.weight ?? 1;
    weightedSum += factor.score * weight;
    weightTotal += weight;
  }
  if (weightTotal === 0) return 0;
  return Math.round((weightedSum / weightTotal) * 10) / 10;
}

type ValidationResult =
  | { ok: true; report: AuditReport }
  | { ok: false; errors: string[] };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(value: unknown, path: string, errors: string[], minLength = 1): string {
  if (typeof value !== "string" || value.trim().length < minLength) {
    errors.push(`${path} must be a non-empty string`);
    return "";
  }
  return value.trim();
}

function readScore(value: unknown, path: string, errors: string[]): number {
  const score = typeof value === "string" ? Number(value) : value;
  if (typeof score !== "number" || !Number.isFinite(score) || score < 0 || score > 10) {
    errors.push(`${path} must be a number between 0 and 10`);
    return 0;
  }
  return Math.round(score * 10) / 10;
}

function readBoolean(value: unknown, path: string, errors: string[]): boolean {
  if (typeof value !== "boolean") {
    errors.push(`${path} must be true or false`);
    return false;
  }
  return value;
}

/**
 * Validates the model's JSON. Deterministic values (overall score, status
 * thresholds, factor names and ordering) are recomputed here rather than
 * trusted, so the report can never contradict its own rubric.
 */
export function validateReport(input: unknown, canonicalUrl: string): ValidationResult {
  const errors: string[] = [];

  if (!isRecord(input)) {
    return { ok: false, errors: ["response was not a JSON object"] };
  }

  const verdict = readString(input.verdict, "verdict", errors, 10);

  /* three questions */
  const threeQuestionsRaw = input.threeQuestions;
  const threeQuestions: ThreeQuestionEntry[] = [];
  if (!Array.isArray(threeQuestionsRaw) || threeQuestionsRaw.length !== 3) {
    errors.push("threeQuestions must be an array of exactly 3 entries");
  } else {
    threeQuestionsRaw.forEach((entry, index) => {
      const path = `threeQuestions[${index}]`;
      if (!isRecord(entry)) {
        errors.push(`${path} must be an object`);
        return;
      }
      const status = entry.status;
      if (status !== "answered" && status !== "partial" && status !== "unanswered") {
        errors.push(`${path}.status must be answered, partial or unanswered`);
      }
      threeQuestions.push({
        question: readString(entry.question, `${path}.question`, errors),
        score: readScore(entry.score, `${path}.score`, errors),
        status: (status as ThreeQuestionStatus) ?? "unanswered",
        explanation: readString(entry.explanation, `${path}.explanation`, errors, 10),
      });
    });
  }

  /* CONVERT factors */
  const factorsRaw = input.convertFactors;
  const convertFactors: ConvertFactor[] = [];
  if (!Array.isArray(factorsRaw) || factorsRaw.length !== 7) {
    errors.push("convertFactors must be an array of exactly 7 entries");
  } else {
    factorsRaw.forEach((entry, index) => {
      const expected = FACTOR_ORDER[index];
      const path = `convertFactors[${index}] (${expected.letter})`;
      if (!isRecord(entry)) {
        errors.push(`${path} must be an object`);
        return;
      }
      if (entry.letter !== expected.letter) {
        errors.push(`${path}.letter must be "${expected.letter}" - factors must be in C,O,N,V,E,R,T order`);
      }

      const findingsRaw = entry.findings;
      const findings: { check: string; finding: string }[] = [];
      if (!Array.isArray(findingsRaw) || findingsRaw.length < 2 || findingsRaw.length > 4) {
        errors.push(`${path}.findings must hold 2 to 4 entries`);
      } else {
        findingsRaw.forEach((finding, findingIndex) => {
          const findingPath = `${path}.findings[${findingIndex}]`;
          if (!isRecord(finding)) {
            errors.push(`${findingPath} must be an object`);
            return;
          }
          findings.push({
            check: readString(finding.check, `${findingPath}.check`, errors),
            finding: readString(finding.finding, `${findingPath}.finding`, errors, 10),
          });
        });
      }

      const score = readScore(entry.score, `${path}.score`, errors);
      convertFactors.push({
        letter: expected.letter,
        name: typeof entry.name === "string" && entry.name.trim() ? entry.name.trim() : expected.name,
        type: expected.type,
        score,
        status: statusForScore(score),
        findings,
        analysis: readString(entry.analysis, `${path}.analysis`, errors, 10),
      });
    });
  }

  /* trust signals */
  const trustRaw = input.trustSignalAudit;
  const trustSignalAudit: TrustSignalRow[] = [];
  if (!Array.isArray(trustRaw) || trustRaw.length !== 5) {
    errors.push("trustSignalAudit must be an array of exactly 5 entries");
  } else {
    trustRaw.forEach((entry, index) => {
      const path = `trustSignalAudit[${index}]`;
      if (!isRecord(entry)) {
        errors.push(`${path} must be an object`);
        return;
      }
      trustSignalAudit.push({
        signal:
          typeof entry.signal === "string" && entry.signal.trim()
            ? entry.signal.trim()
            : TRUST_SIGNAL_ORDER[index],
        present: readBoolean(entry.present, `${path}.present`, errors),
        note: readString(entry.note, `${path}.note`, errors, 5),
      });
    });
  }

  /* deadly sins */
  const sinsRaw = input.deadlySins;
  const deadlySins: DeadlySinRow[] = [];
  if (!Array.isArray(sinsRaw) || sinsRaw.length !== 7) {
    errors.push("deadlySins must be an array of exactly 7 entries");
  } else {
    sinsRaw.forEach((entry, index) => {
      const path = `deadlySins[${index}]`;
      if (!isRecord(entry)) {
        errors.push(`${path} must be an object`);
        return;
      }
      deadlySins.push({
        sin:
          typeof entry.sin === "string" && entry.sin.trim() ? entry.sin.trim() : DEADLY_SINS_ORDER[index],
        detected: readBoolean(entry.detected, `${path}.detected`, errors),
        note: readString(entry.note, `${path}.note`, errors, 5),
      });
    });
  }

  /* revenue impact */
  const revenueRaw = input.revenueImpact;
  let revenueImpact = { estimateRange: "", reasoning: "" };
  if (!isRecord(revenueRaw)) {
    errors.push("revenueImpact must be an object");
  } else {
    revenueImpact = {
      estimateRange: readString(revenueRaw.estimateRange, "revenueImpact.estimateRange", errors, 3),
      reasoning: readString(revenueRaw.reasoning, "revenueImpact.reasoning", errors, 10),
    };
  }

  /* recommendations */
  const recommendationsRaw = input.topRecommendations;
  const topRecommendations: string[] = [];
  if (!Array.isArray(recommendationsRaw) || recommendationsRaw.length < 3 || recommendationsRaw.length > 5) {
    errors.push("topRecommendations must hold 3 to 5 items");
  } else {
    recommendationsRaw.forEach((entry, index) => {
      topRecommendations.push(readString(entry, `topRecommendations[${index}]`, errors, 10));
    });
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return {
    ok: true,
    report: {
      url: canonicalUrl,
      overallScore: weightedOverallScore(convertFactors),
      verdict,
      threeQuestions,
      convertFactors,
      trustSignalAudit,
      deadlySins,
      revenueImpact,
      topRecommendations,
    },
  };
}

export function parseStoredReport(reportJson: string): AuditReport | null {
  try {
    const parsed: unknown = JSON.parse(reportJson);
    const validated = validateReport(parsed, isRecord(parsed) && typeof parsed.url === "string" ? parsed.url : "");
    return validated.ok ? validated.report : null;
  } catch {
    return null;
  }
}
