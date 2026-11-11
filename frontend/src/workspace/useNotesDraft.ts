import { useEffect, useRef, useState } from "react";
import type { Session } from "../api/client";
import type { Operation } from "./useInvestigation";

export function useNotesDraft(
  current: Session,
  success?: { result: Session; operation: Operation },
) {
  const [draft, setDraft] = useState({
    text: current.notes,
    baseline: current.notes,
    version: current.version,
    revision: 0,
    dirty: false,
    saved: false,
  });
  const acknowledged = useRef<string | undefined>(undefined);
  useEffect(() => {
    setDraft((d) =>
      d.dirty || (d.version === current.version && d.text === current.notes)
        ? d
        : {
            ...d,
            text: current.notes,
            baseline: current.notes,
            version: current.version,
          },
    );
  }, [current.notes, current.version]);
  useEffect(() => {
    if (
      !success ||
      success.operation.route !== "notes" ||
      acknowledged.current === success.operation.key
    )
      return;
    acknowledged.current = success.operation.key;
    const { result, operation } = success;
    // A replay confirms that an earlier operation committed; it cannot say that
    // those notes are still current. Keep the draft for an explicit decision.
    if (result.version < current.version) return;
    setDraft((d) =>
      d.revision === operation.draftRevision
        ? {
            ...d,
            text: result.notes,
            baseline: result.notes,
            version: result.version,
            dirty: false,
            saved: true,
          }
        : {
            ...d,
            baseline: result.notes,
            version: result.version,
            dirty: true,
            saved: false,
          },
    );
  }, [success, current.version]);
  return {
    ...draft,
    conflict: draft.dirty && current.version > draft.version,
    edit: (text: string) =>
      setDraft((d) => ({
        ...d,
        text,
        dirty: true,
        saved: false,
        revision: d.revision + 1,
      })),
    discard: () =>
      setDraft((d) => ({
        text: current.notes,
        baseline: current.notes,
        version: current.version,
        revision: d.revision + 1,
        dirty: false,
        saved: false,
      })),
    operation: (confirmCurrent = false): Operation => ({
      route: "notes",
      method: "PUT",
      body: { notes: draft.text },
      key: crypto.randomUUID(),
      version: confirmCurrent ? current.version : draft.version,
      draftRevision: draft.revision,
    }),
  };
}
