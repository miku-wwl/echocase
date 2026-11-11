import { test, expect } from "@playwright/test";
import type { BrowserContext, Page } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";

const evidence =
  process.env.ECHOCASE_E2E_ARTIFACTS ?? "./test-results/artifacts";
let cookies: Awaited<ReturnType<BrowserContext["cookies"]>>;
test.beforeAll(async ({ browser, baseURL }) => {
  await mkdir(evidence, { recursive: true });
  const context = await browser.newContext({ baseURL });
  const csrf = (await (await context.request.get("/api/auth/csrf")).json())
    .token;
  const data = {
    email: `phase2a-${crypto.randomUUID()}@example.test`,
    password: "StrongLabPassword42",
  };
  for (const action of ["register", "login"]) {
    const r = await context.request.post(`/api/auth/${action}`, {
      data,
      headers: { "X-CSRF-TOKEN": csrf },
    });
    expect(r.status()).toBe(200);
  }
  cookies = await context.cookies();
  await context.close();
});
test.beforeEach(async ({ context, page }) => {
  await context.addCookies(cookies);
  await page.goto("/");
  await page.getByRole("button", { name: "开始新调查" }).click();
  await expect(page.getByRole("tab", { name: "证据档案" })).toBeVisible();
});
const url = (page: Page) =>
  `/api/investigations/${new URL(page.url()).searchParams.get("case")}`;
const read = async (page: Page) => (await page.request.get(url(page))).json();
async function externalNotes(page: Page, notes: string) {
  const s = await read(page);
  const token = (await (await page.request.get("/api/auth/csrf")).json()).token;
  const r = await page.request.put(`${url(page)}/notes`, {
    data: { notes },
    headers: {
      "X-CSRF-TOKEN": token,
      "Idempotency-Key": crypto.randomUUID(),
      "If-Match": `"${s.version}"`,
    },
  });
  expect(r.status()).toBe(200);
  return r.json();
}
async function record(page: Page, name: string, observation: unknown) {
  await writeFile(
    `${evidence}/${name}.json`,
    JSON.stringify(observation, null, 2),
  );
  await page.screenshot({ path: `${evidence}/${name}.png`, fullPage: true });
}

test("draft typed while a real save response is delayed survives acknowledgement", async ({
  page,
}) => {
  await page.getByRole("tab", { name: "调查笔记" }).click();
  const input = page.getByLabel("调查笔记", { exact: true });
  let release!: () => void;
  const hold = new Promise<void>((resolve) => {
    release = resolve;
  });
  let committed!: () => void;
  const sent = new Promise<void>((resolve) => {
    committed = resolve;
  });
  await page.route("**/api/investigations/*/notes", async (route) => {
    const response = await route.fetch(); // Real API commits before the response is held.
    committed();
    await hold;
    await route.fulfill({ response });
  });
  await input.fill("先提交的观察");
  await page.getByRole("button", { name: "保存笔记" }).click();
  await sent;
  await input.fill("先提交的观察；等待时继续记录的新线索");
  release();
  await expect(page.locator(".version-label")).toHaveText("档案版本 2");
  const server = await read(page);
  await record(page, "inflight-draft", {
    server,
    draft: await input.inputValue(),
  });
  await expect(input).toHaveValue("先提交的观察；等待时继续记录的新线索");
  await expect(page.getByRole("button", { name: "保存笔记" })).toBeEnabled();
  expect(server.notes).toBe("先提交的观察");
  await page.unroute("**/api/investigations/*/notes");
  await page.getByRole("button", { name: "保存笔记" }).click();
  await expect(page.getByRole("status")).toHaveText("笔记已保存到档案。");
  expect((await read(page)).notes).toContain("继续记录");
});

test("dirty draft keeps its baseline across refetch and requires explicit conflict confirmation", async ({
  page,
}) => {
  await page.getByRole("tab", { name: "调查笔记" }).click();
  const input = page.getByLabel("调查笔记", { exact: true });
  await input.fill("本窗口的待核实推断");
  const other = await externalNotes(page, "另一窗口已经核实的事实");
  await page.getByRole("button", { name: "刷新档案" }).click();
  await expect(page.locator(".version-label")).toHaveText(
    `档案版本 ${other.version}`,
  );
  await record(page, "dirty-refetch", {
    server: await read(page),
    draft: await input.inputValue(),
  });
  await expect(input).toHaveValue("本窗口的待核实推断");
  await expect(page.getByRole("button", { name: "保存笔记" })).toBeDisabled();
  await expect(page.getByTestId("notes-conflict")).toContainText(
    "另一窗口已经核实的事实",
  );
  await page
    .getByRole("button", { name: "确认保留草稿并基于当前版本保存" })
    .click();
  await expect(page.getByRole("status")).toHaveText("笔记已保存到档案。");
  expect((await read(page)).notes).toBe("本窗口的待核实推断");
});

test("committed write with lost response reuses its key and cannot regress a newer snapshot", async ({
  page,
}) => {
  await page.getByRole("tab", { name: "调查笔记" }).click();
  const input = page.getByLabel("调查笔记", { exact: true });
  const attempts: { key?: string; version?: string; body: string | null }[] =
    [];
  let drop = true;
  await page.route("**/api/investigations/*/notes", async (route) => {
    const req = route.request();
    attempts.push({
      key: req.headers()["idempotency-key"],
      version: req.headers()["if-match"],
      body: req.postData(),
    });
    const response = await route.fetch();
    if (drop) {
      drop = false;
      await route.abort("connectionfailed");
    } else await route.fulfill({ response });
  });
  await input.fill("提交成功但返回途中断开的观察");
  await page.getByRole("button", { name: "保存笔记" }).click();
  await expect(page.getByRole("alert")).toContainText("保存结果尚未确认");
  const committed = await read(page);
  expect(committed.notes).toBe("提交成功但返回途中断开的观察");
  // A later accepted write makes the stored receipt older than the current resource.
  const later = await externalNotes(page, "后来窗口补充的已保存事实");
  await page.getByRole("button", { name: "刷新档案" }).click();
  await expect(page.locator(".version-label")).toHaveText(
    `档案版本 ${later.version}`,
  );
  const observedVersions: number[] = [];
  await page.exposeFunction("observeVersion", (v: string) =>
    observedVersions.push(Number(v.replace(/\D/g, ""))),
  );
  await page.locator(".version-label").evaluate((el) => {
    new MutationObserver(() =>
      (
        window as unknown as { observeVersion: (v: string) => void }
      ).observeVersion(el.textContent ?? ""),
    ).observe(el, { childList: true, subtree: true, characterData: true });
  });
  await page.getByRole("button", { name: "重试同一次操作" }).click();
  await expect(
    page.getByRole("button", { name: "重试同一次操作" }),
  ).toHaveCount(0);
  await expect(page.locator(".version-label")).toHaveText(
    `档案版本 ${later.version}`,
  );
  await expect(input).toHaveValue("提交成功但返回途中断开的观察");
  expect(observedVersions.every((v) => v >= later.version)).toBe(true);
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
  expect((await read(page)).version).toBe(later.version);
  await record(page, "lost-response", {
    attempts,
    committed,
    later,
    observedVersions,
    final: await read(page),
  });
});

test("unreadable success body after a real commit retains the original retry intent", async ({
  page,
}) => {
  await page.getByRole("tab", { name: "调查笔记" }).click();
  const attempts: { key?: string; version?: string; body: string | null }[] =
    [];
  let corrupt = true;
  await page.route("**/api/investigations/*/notes", async (route) => {
    const req = route.request();
    attempts.push({
      key: req.headers()["idempotency-key"],
      version: req.headers()["if-match"],
      body: req.postData(),
    });
    const response = await route.fetch(); // Commit is real; only its successful JSON body is corrupted.
    if (corrupt) {
      corrupt = false;
      await route.fulfill({ response, body: '{"id":' });
    } else await route.fulfill({ response });
  });
  await page
    .getByLabel("调查笔记", { exact: true })
    .fill("已经提交但成功响应体无法解析的观察");
  await page.getByRole("button", { name: "保存笔记", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("保存结果尚未确认");
  await expect(
    page.getByRole("button", { name: "保存笔记", exact: true }),
  ).toBeDisabled();
  const committed = await read(page);
  expect(committed.notes).toBe("已经提交但成功响应体无法解析的观察");
  await page.getByRole("button", { name: "重试同一次操作" }).click();
  await expect(page.getByRole("status")).toHaveText("笔记已保存到档案。");
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
  const final = await read(page);
  expect(final.version).toBe(committed.version);
  await record(page, "unreadable-body", {
    injection:
      "HTTP 200 body deliberately corrupted after real API commit; not a wire-level packet truncation",
    attempts,
    committed,
    final,
  });
});

test("revise an existing link through the real graph editor without replacing its identity", async ({
  page,
}) => {
  for (const title of ["异常门禁记录", "备用凭证领用册"]) {
    await page
      .getByRole("button", { name: `查看 ${title}`, exact: true })
      .click();
    await page.getByRole("button", { name: "调查此证据", exact: true }).click();
    await expect(page.locator(".evidence-body")).toBeVisible();
  }
  await page.getByRole("tab", { name: "关联图谱" }).click();
  await page.getByLabel("起点证据").selectOption("access-log");
  await page.getByLabel("终点证据").selectOption("badge-ledger");
  await page.getByRole("button", { name: "建立关联", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: "修订 access-log badge-ledger 关联",
      exact: true,
    }),
  ).toBeVisible();
  const before = await read(page);
  await page
    .getByRole("button", {
      name: "修订 access-log badge-ledger 关联",
      exact: true,
    })
    .click();
  await page.getByLabel("修订关联类型").selectOption("Contradicts");
  const rationale =
    "核对门禁时钟后发现领用时间与通行时间无法互相印证，暂改为存在矛盾。";
  await page.getByLabel("修订解释").fill(rationale);
  await page.getByRole("button", { name: "保存关联修订", exact: true }).click();
  // The confirmed response renders before onSettled finishes and the editor
  // closes. Assert completion and the persisted presentation, not any equal text.
  await expect(page.getByLabel("修订解释")).toHaveCount(0);
  await expect(page.locator(".link-rationale")).toHaveText(rationale);
  const after = await read(page);
  expect(after.version).toBe(before.version + 1);
  expect(after.links[0]).toMatchObject({
    ...before.links[0],
    kind: "Contradicts",
    rationale,
    revisedAt: expect.any(String),
  });
  await page.reload();
  await page.getByRole("tab", { name: "关联图谱" }).click();
  await expect(page.locator(".link-rationale")).toHaveText(rationale);
  await record(page, "link-revision", { before, after });
});
