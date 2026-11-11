> 历史记录：本文件对应已验证应用化基线3d192a3，文中旧路径记录当时布局；当前布局见根README。

# 退役与迁移的实际路径

这些路径从新分支当前树移除，原63c5872对象和Phase2A分支继续保存。不是删除历史，也不清理业务数据库。

## 迁移而非丢弃

| 原路径 | 当前路径 |
|---|---|
| `tests/EchoCase.Tests/DomainTests.cs` | `tests/unit/EchoCase.UnitTests/DomainTests.cs` |
| `tests/EchoCase.Tests/LinkRevisionTests.cs` | `tests/unit/EchoCase.UnitTests/LinkRevisionTests.cs` |
| `tests/EchoCase.Tests/MigrationTests.cs` | `tests/integration/EchoCase.IntegrationTests/MigrationTests.cs` |
| `tests/EchoCase.Tests/PostgresApiTests.cs` | `tests/integration/EchoCase.IntegrationTests/PostgresApiTests.cs` |
| `tests/EchoCase.Tests/PostgresApiTests.Phase2A.cs` | `tests/integration/EchoCase.IntegrationTests/PostgresApiTests.LinkRevision.cs` |
| `tests/EchoCase.Tests/SqlObservation.cs` | `tests/integration/EchoCase.IntegrationTests/SqlObservation.cs` |
| `frontend/tests/workflow.spec.ts` | `tests/e2e/specs/workflow.spec.ts` |
| `frontend/tests/phase2a.spec.ts` | `tests/e2e/specs/consistency.spec.ts` |
| `frontend/playwright.config.ts` | `tests/e2e/playwright.config.ts` |
| `experiments/phase2a/DbProbe/Program.cs` | `tests/integration/EchoCase.QueryProbe/Program.cs` |
| `experiments/phase2a/DbProbe/DbProbe.csproj` | `tests/integration/EchoCase.QueryProbe/EchoCase.QueryProbe.csproj` |
| `experiments/phase2a/DbProbe/packages.lock.json` | `tests/integration/EchoCase.QueryProbe/packages.lock.json` |

## 移除/替代

旧混合测试项目/锁文件由独立项目替代；旧测试/Phase2文档中的应用机制已重写到当前engineering/architecture。其他为历史运维、原证据和旧出版材料。完整清单：

- `.dockerignore`
- `.github/workflows/engineering.yml`
- `.github/workflows/phase2a.yml`
- `Dockerfile`
- `compose.yaml`
- `docs/ACCEPTANCE-REPORT.md`
- `docs/deployment/DEPLOYMENT.md`
- `docs/experiments/E01.md`
- `docs/experiments/E02.md`
- `docs/experiments/E03.md`
- `docs/experiments/E04.md`
- `docs/experiments/E05.md`
- `docs/experiments/E06.md`
- `docs/experiments/E07.md`
- `docs/experiments/E08.md`
- `docs/experiments/E09.md`
- `docs/experiments/E10.md`
- `docs/experiments/E11.md`
- `docs/experiments/E12.md`
- `docs/experiments/E13.md`
- `docs/experiments/E14.md`
- `docs/experiments/E15.md`
- `docs/experiments/E16.md`
- `docs/experiments/E17.md`
- `docs/experiments/E18.md`
- `docs/experiments/E19.md`
- `docs/experiments/E20.md`
- `docs/experiments/E21.md`
- `docs/experiments/E22.md`
- `docs/experiments/E23.md`
- `docs/experiments/E24.md`
- `docs/experiments/E25.md`
- `docs/experiments/E26.md`
- `docs/learning/LEARNING-JOURNAL.md`
- `docs/phase2a/ACCEPTANCE.md`
- `docs/phase2a/AZURE-DESIGN.md`
- `docs/phase2a/FINDINGS.md`
- `docs/phase2a/PLAN.md`
- `docs/phase2a/PUBLICATION-INVENTORY.md`
- `docs/phase2a/RELEASE-NOTES.md`
- `docs/phase2a/REPRODUCE.md`
- `docs/phase2a/TEMPLATE-COMPARISON.md`
- `docs/phase2a/TRACEABILITY.md`
- `docs/testing/TEST-STRATEGY.md`
- `evidence/backend/backend.trx`
- `evidence/backend/before-concurrency-fix.trx`
- `evidence/backend/before-concurrency-fix.txt`
- `evidence/backend/dependency-audit.json`
- `evidence/backend/initial-missing-migration.trx`
- `evidence/backend/run.txt`
- `evidence/backup/results.json`
- `evidence/browser/01-login.png`
- `evidence/browser/02-dashboard.png`
- `evidence/browser/03-evidence.png`
- `evidence/browser/04-graph.png`
- `evidence/browser/05-verdict.png`
- `evidence/browser/06-rollback.png`
- `evidence/browser/07-conflict.png`
- `evidence/browser/08-mobile.png`
- `evidence/browser/09-graph-detail.png`
- `evidence/browser/10-rollback-detail.png`
- `evidence/browser/before-auth-cache-fix.json`
- `evidence/browser/results.json`
- `evidence/ci/baseline-run.json`
- `evidence/ci/rejected-run.json`
- `evidence/ci/rejected.txt`
- `evidence/ci/results.json`
- `evidence/container/build.txt`
- `evidence/container/migrate.txt`
- `evidence/container/results.json`
- `evidence/database/plan-summary.json`
- `evidence/database/results.json`
- `evidence/frontend-audit.json`
- `evidence/manifest.json`
- `evidence/phase2a/backend/backend.trx`
- `evidence/phase2a/before/context.json`
- `evidence/phase2a/before/dirty-refetch.json`
- `evidence/phase2a/before/dirty-refetch.png`
- `evidence/phase2a/before/inflight-draft.json`
- `evidence/phase2a/before/inflight-draft.png`
- `evidence/phase2a/before/problem-trace.json`
- `evidence/phase2a/before/results.json`
- `evidence/phase2a/before/timestamp-precision.json`
- `evidence/phase2a/before/timestamp.trx`
- `evidence/phase2a/before/traces/.last-run.json`
- `evidence/phase2a/before/traces/phase2a-dirty-draft-keeps--6bce5-licit-conflict-confirmation-edge/error-context.md`
- `evidence/phase2a/before/traces/phase2a-dirty-draft-keeps--6bce5-licit-conflict-confirmation-edge/test-failed-1.png`
- `evidence/phase2a/before/traces/phase2a-dirty-draft-keeps--6bce5-licit-conflict-confirmation-edge/trace.zip`
- `evidence/phase2a/before/traces/phase2a-draft-typed-while--20a2b-ed-survives-acknowledgement-edge/error-context.md`
- `evidence/phase2a/before/traces/phase2a-draft-typed-while--20a2b-ed-survives-acknowledgement-edge/test-failed-1.png`
- `evidence/phase2a/before/traces/phase2a-draft-typed-while--20a2b-ed-survives-acknowledgement-edge/trace.zip`
- `evidence/phase2a/browser/01-login.png`
- `evidence/phase2a/browser/02-dashboard.png`
- `evidence/phase2a/browser/03-evidence.png`
- `evidence/phase2a/browser/04-graph.png`
- `evidence/phase2a/browser/05-verdict.png`
- `evidence/phase2a/browser/06-rollback.png`
- `evidence/phase2a/browser/07-conflict.png`
- `evidence/phase2a/browser/08-mobile.png`
- `evidence/phase2a/browser/09-graph-detail.png`
- `evidence/phase2a/browser/10-rollback-detail.png`
- `evidence/phase2a/browser/dirty-refetch.json`
- `evidence/phase2a/browser/dirty-refetch.png`
- `evidence/phase2a/browser/inflight-draft.json`
- `evidence/phase2a/browser/inflight-draft.png`
- `evidence/phase2a/browser/link-revision.json`
- `evidence/phase2a/browser/link-revision.png`
- `evidence/phase2a/browser/lost-response.json`
- `evidence/phase2a/browser/lost-response.png`
- `evidence/phase2a/browser/results.json`
- `evidence/phase2a/browser/unreadable-body.json`
- `evidence/phase2a/browser/unreadable-body.png`
- `evidence/phase2a/ci/failed-42976782644/browser-results.json`
- `evidence/phase2a/ci/failed-42976782644/run.json`
- `evidence/phase2a/ci/results.json`
- `evidence/phase2a/ci/run-42975558898/backend/backend.trx`
- `evidence/phase2a/ci/run-42975558898/browser/dirty-refetch.json`
- `evidence/phase2a/ci/run-42975558898/browser/inflight-draft.json`
- `evidence/phase2a/ci/run-42975558898/browser/link-revision.json`
- `evidence/phase2a/ci/run-42975558898/browser/lost-response.json`
- `evidence/phase2a/ci/run-42975558898/browser/results.json`
- `evidence/phase2a/ci/run-42975558898/database/application-query-plan.json`
- `evidence/phase2a/ci/run-42975558898/database/migration-tracking.json`
- `evidence/phase2a/ci/run-42975558898/database/store-race.json`
- `evidence/phase2a/ci/run-42975558898/database/timestamp-precision.json`
- `evidence/phase2a/ci/run-42975558898/delivery/20261111T065335Z-4fba16c1/results.json`
- `evidence/phase2a/ci/run-42975558898/delivery/latest.json`
- `evidence/phase2a/ci/run-42975558898/frontend-audit.json`
- `evidence/phase2a/database/application-query-plan.json`
- `evidence/phase2a/database/migration-tracking.json`
- `evidence/phase2a/database/store-race.json`
- `evidence/phase2a/database/timestamp-precision.json`
- `evidence/phase2a/delivery/20261111T062240Z-62cf22ee/application-final.txt`
- `evidence/phase2a/delivery/20261111T062240Z-62cf22ee/build-new.txt`
- `evidence/phase2a/delivery/20261111T062240Z-62cf22ee/build-old.txt`
- `evidence/phase2a/delivery/20261111T062240Z-62cf22ee/migration-expanded.txt`
- `evidence/phase2a/delivery/20261111T062240Z-62cf22ee/migration-old.txt`
- `evidence/phase2a/delivery/20261111T062240Z-62cf22ee/migration-repeat.txt`
- `evidence/phase2a/delivery/20261111T062240Z-62cf22ee/results.json`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/application-final.txt`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/application-outage.txt`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/build-new.txt`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/build-old.txt`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/migration-expanded.txt`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/migration-old.txt`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/migration-repeat.txt`
- `evidence/phase2a/delivery/20261111T063025Z-fe0d2092/results.json`
- `evidence/phase2a/delivery/latest.json`
- `evidence/phase2a/frontend-audit.json`
- `evidence/phase2a/preservation.json`
- `evidence/phase2a/qa/gate-selftest.json`
- `evidence/phase2a/upstream-source.json`
- `evidence/publication-audit.json`
- `evidence/qa/book-layout.json`
- `evidence/qa/book-links.json`
- `evidence/qa/gate-selftest.json`
- `evidence/qa/pdf-selftest.json`
- `evidence/qa/report-layout.json`
- `evidence/qa/report-links.json`
- `evidence/qa/visual-review.json`
- `evidence/reliability/before-error-mapping-fix.txt`
- `evidence/reliability/results.json`
- `evidence/summary.json`
- `experiments/backup.py`
- `experiments/ci-drill.ps1`
- `experiments/container.py`
- `experiments/database.py`
- `experiments/phase2a/delivery.py`
- `experiments/reliability.py`
- `manual/assets/book.css`
- `manual/chapters/16-reliability.md`
- `manual/chapters/17-delivery.md`
- `manual/claims.json`
- `manual/dist/EchoCase-Acceptance-Report.pdf`
- `manual/dist/Enterprise-Full-Stack-Engineering.pdf`
- `manual/package-lock.json`
- `manual/package.json`
- `manual/requirements.txt`
- `manual/tools/build.mjs`
- `manual/tools/pdfqa.py`
- `manual/tools/test_pdfqa.py`
- `scripts/check.py`
- `scripts/dev-db.ps1`
- `scripts/dev.ps1`
- `tests/EchoCase.Tests/EchoCase.Tests.csproj`
- `tests/EchoCase.Tests/packages.lock.json`
- `tools/catalog.py`
- `tools/ci_record.py`
- `tools/handoff.py`
- `tools/test_gate.py`
- `tools/test_phase2a_gate.py`
- `tools/verify.py`
- `tools/verify_phase2a.py`
