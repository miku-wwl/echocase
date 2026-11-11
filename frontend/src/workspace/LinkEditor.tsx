import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { Session, ReviseLinkRequest } from "../api/client";

export default function LinkEditor({
  link,
  version,
  disabled,
  onSave,
}: {
  link: Session["links"][number];
  version: number;
  disabled: boolean;
  onSave: (
    id: string,
    body: ReviseLinkRequest,
    version: number,
  ) => Promise<unknown>;
}) {
  const [draft, setDraft] = useState<{
    kind: string;
    rationale: string;
    version: number;
  } | null>(null);
  if (!draft)
    return (
      <Button
        size="sm"
        variant="outline"
        disabled={disabled}
        aria-label={`修订 ${link.sourceId} ${link.targetId} 关联`}
        onClick={() =>
          setDraft({
            kind: link.kind,
            rationale: link.rationale ?? "",
            version,
          })
        }
      >
        修订关联
      </Button>
    );
  const length = Array.from(draft.rationale.trim()).length;
  const changed =
    draft.kind !== link.kind || draft.rationale.trim() !== link.rationale;
  const conflict = version !== draft.version;
  return (
    <div className="link-editor">
      <label>
        修订关联类型
        <select
          aria-label="修订关联类型"
          value={draft.kind}
          disabled={disabled}
          onChange={(e) => setDraft({ ...draft, kind: e.target.value })}
        >
          <option value="Corroborates">相互印证</option>
          <option value="Contradicts">存在矛盾</option>
        </select>
      </label>
      <label>
        修订解释
        <Textarea
          aria-label="修订解释"
          value={draft.rationale}
          disabled={disabled}
          onChange={(e) => setDraft({ ...draft, rationale: e.target.value })}
        />
      </label>
      <p className="subtle">
        {length} / 500 字符；至少填写 20 个字符。保留关联端点。
      </p>
      {conflict && (
        <p>档案版本已变化，请保留或复制解释，取消后核对当前关联再修订。</p>
      )}
      <Button
        disabled={
          disabled || conflict || length < 20 || length > 500 || !changed
        }
        onClick={async () => {
          try {
            await onSave(
              link.id,
              { kind: draft.kind, rationale: draft.rationale },
              draft.version,
            );
            setDraft(null);
          } catch {
            /* Workspace displays the protocol error. Keep this draft. */
          }
        }}
      >
        保存关联修订
      </Button>
      <Button
        variant="outline"
        disabled={disabled}
        onClick={() => setDraft(null)}
      >
        取消修订
      </Button>
    </div>
  );
}
