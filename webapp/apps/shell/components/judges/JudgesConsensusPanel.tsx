// Multi-judge consensus panel (SP-10).
//
// Renders the 4 judge cards in `.gc-doctrine-grid` (foundation class) plus
// the final consensus tile. Pure presentational, server-renderable.

import { Card, KpiCard, Pill } from "@growthcro/ui";
import { JudgeScoreCard } from "./JudgeScoreCard";
import { JUDGE_DISPLAY, type JudgesPayload } from "./types";
import { verdictTone } from "./judges-utils";

type Props = {
  payload: JudgesPayload;
};

export function JudgesConsensusPanel({ payload }: Props) {
  const presentJudges = JUDGE_DISPLAY.filter(
    (j) => payload.judges[j.key] !== undefined
  ).length;
  const consensusTone = verdictTone(payload.consensus.verdict);

  return (
    <>
      <Card
        title={`4 juges · consensus ${payload.consensus.verdict}`}
        actions={
          <>
            <Pill tone={consensusTone}>
              {Math.round(payload.consensus.score)}/100
            </Pill>{" "}
            <Pill tone="soft">{presentJudges}/4 ont voté</Pill>
          </>
        }
      >
        <div className="gc-grid-kpi" style={{ marginBottom: 14 }}>
          <KpiCard
            label="Score consensus"
            value={`${Math.round(payload.consensus.score)}/100`}
            hint={payload.consensus.verdict}
          />
          <KpiCard
            label="Juges présents"
            value={`${presentJudges}/4`}
            hint={presentJudges < 4 ? "incomplet" : "complet"}
          />
          <KpiCard
            label="Spread"
            value={spreadOf(payload).toFixed(0)}
            hint="écart max - min"
          />
          <KpiCard
            label="Généré"
            value={new Date(payload.generated_at).toLocaleDateString()}
          />
        </div>
        <div className="gc-doctrine-grid">
          {JUDGE_DISPLAY.map((j) => (
            <JudgeScoreCard
              key={j.key}
              label={j.label}
              accent={j.color}
              judge={payload.judges[j.key]}
            />
          ))}
        </div>
      </Card>

      <Card title="Lecture du consensus">
        <p style={{ color: "var(--gc-muted)", fontSize: 13, lineHeight: 1.55 }}>
          {explainConsensus(payload)}
        </p>
      </Card>
    </>
  );
}

function spreadOf(payload: JudgesPayload): number {
  const scores = Object.values(payload.judges)
    .filter((j): j is NonNullable<typeof j> => j !== undefined)
    .map((j) => j.score);
  if (scores.length < 2) return 0;
  return Math.max(...scores) - Math.min(...scores);
}

function explainConsensus(payload: JudgesPayload): string {
  const spread = spreadOf(payload);
  if (spread === 0) {
    return "Un seul juge a noté cet audit — pas encore de consensus à interpréter.";
  }
  if (spread <= 5) {
    return `Les juges sont alignés (spread ${spread.toFixed(0)} pts). Le consensus ${payload.consensus.verdict} est fiable.`;
  }
  if (spread <= 15) {
    return `Léger désaccord (spread ${spread.toFixed(0)} pts). Le consensus ${payload.consensus.verdict} reste utilisable mais regarde les juges hors-cible.`;
  }
  return `Désaccord significatif (spread ${spread.toFixed(0)} pts). Ne te fie pas au consensus brut — lis chaque juge et tranche manuellement.`;
}
