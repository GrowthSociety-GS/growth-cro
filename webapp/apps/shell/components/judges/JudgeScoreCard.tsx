// Single-judge score card (SP-10). Reusable for Sonnet/Haiku/Opus/Doctrine.
//
// Pure presentational. Brand accent comes from the `accent` color prop. The
// score uses the existing ScoreBar primitive for visual parity with the rest
// of the dashboard.

import { ScoreBar } from "@growthcro/ui";
import type { Judge, JudgeVerdict } from "./types";
import { verdictTone } from "./judges-utils";

type Props = {
  label: string;
  accent: string;
  judge: Judge | undefined;
};

const VERDICT_COLOR: Record<JudgeVerdict, string> = {
  Bon: "var(--gc-green)",
  Moyen: "var(--gc-amber)",
  Faible: "var(--gc-red)",
};

export function JudgeScoreCard({ label, accent, judge }: Props) {
  return (
    <div
      className="gc-doctrine-bloc"
      style={{
        borderTop: `3px solid ${accent}`,
      }}
      role="group"
      aria-label={`${label} judge`}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
        }}
      >
        <h3 className="gc-doctrine-bloc__title" style={{ color: accent }}>
          {label}
        </h3>
        {judge ? (
          <span
            className={`gc-pill gc-pill--${verdictTone(judge.verdict)}`}
            aria-label={`Verdict ${judge.verdict}`}
          >
            {judge.verdict}
          </span>
        ) : (
          <span className="gc-pill gc-pill--soft">no data</span>
        )}
      </div>

      {judge ? (
        <>
          <p
            className="gc-doctrine-bloc__count"
            style={{ color: VERDICT_COLOR[judge.verdict] }}
          >
            {Math.round(judge.score)}
            <span
              style={{
                fontSize: 12,
                color: "var(--gc-muted)",
                marginLeft: 4,
                fontWeight: 500,
              }}
            >
              /100
            </span>
          </p>
          <ScoreBar label="" value={judge.score} color={accent} />
          {judge.remarks.length > 0 ? (
            <ul
              style={{
                margin: "10px 0 0",
                padding: 0,
                listStyle: "none",
                fontSize: 12,
                color: "var(--gc-muted)",
                lineHeight: 1.5,
              }}
            >
              {/* Wave C.4 (audit A.7 P0.1): stable key from content+index. */}
              {judge.remarks.slice(0, 3).map((r, i) => (
                <li
                  key={`${i}-${r.slice(0, 32)}`}
                  style={{
                    padding: "2px 0",
                    borderBottom:
                      i < Math.min(2, judge.remarks.length - 1)
                        ? "1px solid var(--gc-line-soft)"
                        : "none",
                  }}
                >
                  • {r}
                </li>
              ))}
              {judge.remarks.length > 3 ? (
                <li
                  style={{
                    color: "var(--gc-muted)",
                    fontSize: 11,
                    padding: "4px 0 0",
                  }}
                >
                  + {judge.remarks.length - 3} autres remarques
                </li>
              ) : null}
            </ul>
          ) : (
            <p
              style={{
                color: "var(--gc-muted)",
                fontSize: 12,
                margin: "10px 0 0",
                fontStyle: "italic",
              }}
            >
              Aucune remarque fournie par ce juge.
            </p>
          )}
        </>
      ) : (
        <p
          style={{
            color: "var(--gc-muted)",
            fontSize: 12,
            margin: "8px 0 0",
            fontStyle: "italic",
          }}
        >
          Ce juge n&apos;a pas encore noté cet audit.
        </p>
      )}
    </div>
  );
}
