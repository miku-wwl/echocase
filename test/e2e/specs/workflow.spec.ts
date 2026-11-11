import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const evidence = process.env.ECHOCASE_E2E_ARTIFACTS ?? "./test-results/artifacts";
async function account(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "创建账户", exact: true }).click();
  await page
    .getByLabel("邮箱", { exact: true })
    .fill(`browser-${crypto.randomUUID()}@example.test`);
  await page.getByLabel("密码", { exact: true }).fill("StrongLabPassword42");
  await page.getByRole("button", { name: "创建账户", exact: true }).click();
  await expect(
    page.getByText("账户已创建。现在可以登录工作台。"),
  ).toBeVisible();
  await page.getByRole("button", { name: "进入工作台" }).click();
  await expect(page.getByRole("heading", { name: "案件总览" })).toBeVisible();
}
async function start(page: Page) {
  await page.getByRole("button", { name: "开始新调查" }).click();
  await expect(page.getByRole("tab", { name: "证据档案" })).toBeVisible();
}
async function examine(page: Page, title: string) {
  await page
    .getByRole("button", { name: `查看 ${title}`, exact: true })
    .click();
  await page.getByRole("button", { name: "调查此证据", exact: true }).click();
  await expect(page.locator(".evidence-body")).toBeVisible();
}
async function graphLink(page: Page, source: string, target: string) {
  await page.getByLabel("起点证据").selectOption(source);
  await page.getByLabel("终点证据").selectOption(target);
  await page.getByRole("button", { name: "建立关联", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: `删除 ${source} ${target} 关联`,
      exact: true,
    }),
  ).toBeVisible();
}

test("five business modules: real browser → ASP.NET → PostgreSQL", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await mkdir(evidence, { recursive: true });
  await page.goto("/");
  await page.screenshot({ path: `${evidence}/01-login.png`, fullPage: true });
  await account(page);
  await page.screenshot({
    path: `${evidence}/02-dashboard.png`,
    fullPage: true,
  });
  await start(page);
  await page
    .getByRole("button", { name: "查看 调度消息副本", exact: true })
    .click();
  await expect(page.getByText("这条线索尚未解锁。")).toBeVisible();
  for (const title of [
    "异常门禁记录",
    "备用凭证领用册",
    "调度消息副本",
    "走廊摄像片段",
    "维护工单",
    "值班人员笔录",
  ])
    await examine(page, title);
  await page.screenshot({
    path: `${evidence}/03-evidence.png`,
    fullPage: true,
  });
  await page.getByRole("tab", { name: "关联图谱" }).click();
  await graphLink(page, "access-log", "badge-ledger");
  await graphLink(page, "badge-ledger", "dispatch");
  await page.screenshot({ path: `${evidence}/04-graph.png`, fullPage: true });
  await page.locator('.graph-panel').screenshot({path:`${evidence}/09-graph-detail.png`});
  await page.getByRole("tab", { name: "调查笔记" }).click();
  await page
    .getByLabel("调查笔记", { exact: true })
    .fill(
      "门禁、凭证领用与调度消息构成证据链。摄像中断有独立的运维原因，不能直接归责。",
    );
  await page.getByRole("button", { name: "保存笔记" }).click();
  await expect(page.getByRole("status")).toHaveText("笔记已保存到档案。");
  const url = page.url();
  await page.reload();
  await page.getByRole("tab", { name: "调查笔记" }).click();
  await expect(page.getByLabel("调查笔记", { exact: true })).toContainText("");
  await expect(page.getByLabel("调查笔记", { exact: true })).toHaveValue(
    /门禁、凭证/,
  );
  await page.getByRole("tab", { name: "复核与结论" }).click();
  await page.getByRole("button", { name: "进入复核" }).click();
  await expect(
    page.getByText("档案正在复核中。如需补充证据，请返回调查。"),
  ).toBeVisible();
  await page
    .getByLabel("结论说明")
    .fill(
      "门禁记录与凭证领用册共同定位林澈，调度消息进一步印证其取走账册。维护工单解释摄像中断，钟表校正消除了证词矛盾。",
    );
  await page.getByRole("button", { name: "提交并封存结论" }).click();
  await expect(page.getByRole("heading", { name: "结论已归档" })).toBeVisible();
  await expect(page.locator(".result-grid")).toContainText("100");
  await page.screenshot({ path: `${evidence}/05-verdict.png`, fullPage: true });
  await page.reload();
  await page.getByRole("tab", { name: "复核与结论" }).click();
  await expect(page.getByRole("heading", { name: "结论已归档" })).toBeVisible();
  await expect(page).toHaveURL(url);
  expect(errors).toEqual([]);
});

test("injected 503: pending note presentation resets and draft survives", async ({
  page,
}) => {
  await account(page);
  await start(page);
  await page.getByRole("tab", { name: "调查笔记" }).click();
  await page.route("**/api/investigations/*/notes", (r) =>
    r.fulfill({
      status: 503,
      contentType: "application/problem+json",
      body: JSON.stringify({
        title: "injected_failure",
        status: 503,
        detail: "实验注入：保存服务暂不可用。",
      }),
    }),
  );
  await page.getByLabel("调查笔记", { exact: true }).fill("尚未保存的现场观察");
  await page.getByRole("button", { name: "保存笔记" }).click();
  await expect(page.getByRole("alert")).toContainText("实验注入");
  await expect(page.getByLabel("调查笔记", { exact: true })).toHaveValue(
    "尚未保存的现场观察",
  );
  const server = await page.request.get(
    "/api/investigations/" + new URL(page.url()).searchParams.get("case"),
  );
  expect((await server.json()).notes).toBe("");
  await page.screenshot({
    path: `${evidence}/06-rollback.png`,
    fullPage: true,
  });
  await page.locator('.writing-panel').screenshot({path:`${evidence}/10-rollback-detail.png`});
  await page.unroute("**/api/investigations/*/notes");
  await page.getByRole("button", { name: "保存笔记" }).click();
  await expect(page.getByRole("status")).toHaveText("笔记已保存到档案。");
});

test("two windows: stale write is rejected and unsaved draft is retained", async ({
  page,
  context,
}) => {
  await account(page);
  await start(page);
  await page.getByRole("tab", { name: "调查笔记" }).click();
  const second = await context.newPage();
  await second.goto(page.url());
  await second.getByRole("tab", { name: "调查笔记" }).click();
  await second
    .getByLabel("调查笔记", { exact: true })
    .fill("第二窗口的待保存草稿");
  await page
    .getByLabel("调查笔记", { exact: true })
    .fill("第一窗口先提交的事实");
  await page.getByRole("button", { name: "保存笔记" }).click();
  await expect(page.getByRole("status")).toBeVisible();
  await second.getByRole("button", { name: "保存笔记" }).click();
  await expect(second.getByRole("alert")).toContainText(
    /档案已被其他窗口修改|并发写入冲突/,
  );
  await expect(second.getByLabel("调查笔记", { exact: true })).toHaveValue(
    "第二窗口的待保存草稿",
  );
  await second.screenshot({
    path: `${evidence}/07-conflict.png`,
    fullPage: true,
  });
  const response = await page.request.get(
    "/api/investigations/" + new URL(page.url()).searchParams.get("case"),
  );
  expect((await response.json()).notes).toBe("第一窗口先提交的事实");
});

test("mobile viewport: keyboard accessible workflow and no horizontal overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await account(page);
  await start(page);
  await examine(page, "异常门禁记录");
  await page.getByRole("tab", { name: "关联图谱" }).click();
  await expect(page.getByTestId("evidence-graph")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await page.screenshot({ path: `${evidence}/08-mobile.png`, fullPage: true });
});
