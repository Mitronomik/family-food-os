import { devices, expect, test, type APIResponse } from "@playwright/test";

const householdId = "11111111-1111-4111-8111-111111111111";
const backend = "http://127.0.0.1:8000";
type Member = { id: string; name: string };
type Selection = { excluded_food_ingredient_ids: string[] };

async function readJson<T>(response: APIResponse): Promise<T> {
  expect(response.ok(), `API status for ${response.url()}`).toBe(true);
  return response.json() as Promise<T>;
}

test("real FastAPI persists isolated member exclusions and rejects stale saves", async ({
  page, request, browser,
}, info) => {
  const householdApi = `${backend}/api/households/${householdId}`;
  const { members } = await readJson<{ members: Member[] }>(await request.get(householdApi));
  const anna = members.find(member => member.name === "Анна")!;
  const boris = members.find(member => member.name === "Борис")!;
  const annaApi = `${householdApi}/members/${anna.id}/food-exclusions`;
  const borisApi = `${householdApi}/members/${boris.id}/food-exclusions`;
  const selection = async (url: string) =>
    (await readJson<Selection>(await request.get(url))).excluded_food_ingredient_ids;
  const catalogueId = async (q: string) => {
    const { items } = await readJson<{ items: { id: string }[] }>(
      await request.get(`${backend}/api/food-ingredients`, { params: { q } }),
    );
    expect(items).toHaveLength(1);
    return items[0].id;
  };
  const [carrot] = await selection(annaApi);
  const beef = await catalogueId("тестовый мясной продукт");
  const beet = await catalogueId("свёкла");
  expect(carrot).toBeDefined();
  expect(await selection(borisApi)).toEqual([]);

  const path = `/?household=${householdId}`;
  await page.setViewportSize({ width: 1440, height: 900 });
  const navigation = await page.goto(path);
  expect(navigation?.headers()["cache-control"]).toContain("no-store");
  await page.getByRole("button", { name: "Анна", exact: true }).click();
  const saved = page.getByRole("region", { name: "Выбрано", exact: false });
  await expect(saved.getByText("Морковь")).toBeVisible();
  await expect(saved.getByText(/Больше не в каталоге/)).toBeVisible();

  const search = page.getByRole("searchbox");
  await search.fill("ТЕСТОВЫЙ МЯСНОЙ ПРОДУКТ");
  await page.getByRole("button", { name: "Добавить: Говядина" }).click();
  await page.getByRole("button", { name: "Борис", exact: true }).click();
  await expect(page.getByText(/Нет исключённых продуктов/)).toBeVisible();
  await page.getByRole("button", { name: /Анна/ }).click();
  await expect(saved.getByText("Говядина")).toBeVisible();
  expect(await selection(annaApi)).toEqual([carrot]);

  await readJson(await request.put(annaApi, { data: {
    expected_excluded_food_ingredient_ids: [carrot],
    excluded_food_ingredient_ids: [carrot, beet],
  } }));
  const initialSave = page.waitForResponse(response =>
    response.url().endsWith("/food-exclusions") && response.request().method() === "PUT");
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  expect((await initialSave).status()).toBe(409);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Список изменился");
  await page.getByRole("button", { name: "Обновить актуальный список" }).click();
  await expect(page.getByRole("region", { name: "Проверка актуального списка" }))
    .toContainText("Свёкла");
  await page.getByRole("button", { name: "Перенести мои изменения" }).click();
  expect(await selection(annaApi)).toEqual([carrot, beet].sort());

  const confirmed = page.waitForResponse(response =>
    response.url().endsWith("/food-exclusions") && response.request().method() === "PUT");
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  const response = await confirmed;
  expect(response.status()).toBe(200);
  expect(response.headers()["cache-control"]).toContain("no-store");
  expect(response.request().postDataJSON()).toEqual({
    expected_excluded_food_ingredient_ids: [carrot, beet].sort(),
    excluded_food_ingredient_ids: [carrot, beef, beet].sort(),
  });
  await expect(page.getByRole("status")).toContainText("Изменения сохранены");
  await expect(saved.getByText("Свёкла")).toBeVisible();
  expect(await selection(annaApi)).toEqual([carrot, beef, beet].sort());
  expect(await selection(borisApi)).toEqual([]);

  await search.fill("мясной");
  await expect(page.getByRole("button", { name: "Добавить: Говядина" })).toBeDisabled();
  await page.screenshot({ path: info.outputPath("real-backend-desktop-1440.png"), fullPage: true });

  const mobile = await browser.newContext({
    ...devices["Pixel 7"],
    viewport: { width: 390, height: 844 },
  });
  try {
    const phone = await mobile.newPage();
    await phone.goto(new URL(path, page.url()).href);
    await phone.getByRole("button", { name: "Анна", exact: true }).click();
    for (const name of ["Морковь", "Говядина", "Свёкла"]) {
      await expect(phone.getByRole("button", { name: `Удалить: ${name}` })).toBeVisible();
    }
    expect(await phone.evaluate(() => ({
      width: window.innerWidth,
      overflow: document.documentElement.scrollWidth > window.innerWidth,
      local: localStorage.length,
      session: sessionStorage.length,
    }))).toEqual({ width: 390, overflow: false, local: 0, session: 0 });
    await phone.screenshot({ path: info.outputPath("real-backend-phone-390.png"), fullPage: true });
  } finally {
    await mobile.close();
  }

  await page.reload();
  await page.getByRole("button", { name: "Анна", exact: true }).click();
  for (const name of ["Морковь", "Говядина", "Свёкла"]) {
    await page.getByRole("button", { name: `Удалить: ${name}` }).click();
  }
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Изменения сохранены");
  expect(await selection(annaApi)).toEqual([]);
  expect(await selection(borisApi)).toEqual([]);
  await search.fill("морковь");
  await expect(page.getByRole("status").filter({ hasText: "Ничего не найдено" })).toBeVisible();
});
