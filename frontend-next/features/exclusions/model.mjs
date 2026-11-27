export const MAX = 128;
export const sorted = (ids) => [...new Set(ids)].sort();
export const equal = (a,b) => JSON.stringify(sorted(a)) === JSON.stringify(sorted(b));
export function payload(expected, selected) {
  return {expected_excluded_food_ingredient_ids: sorted(expected), excluded_food_ingredient_ids: sorted(selected)};
}
export function add(ids, food) {
  return food.is_active && !ids.includes(food.id) && ids.length < MAX ? sorted([...ids,food.id]) : ids;
}
export function remove(ids,id) { return ids.filter(x=>x!==id); }
export function reconcile(original,draft,latest) {
  const removed = new Set(original.filter(x=>!draft.includes(x)));
  return sorted([...latest.filter(x=>!removed.has(x)),...draft.filter(x=>!original.includes(x))]);
}
export function message(status) {
  return ({404:"Участник или продукт не найден. Обновите список.",409:"Список изменился или продукт недоступен. Обновите данные и проверьте выбор.",422:"Не удалось проверить выбор. Уточните продукты и попробуйте снова.",503:"Сохранение временно недоступно. Обновите данные перед повторной попыткой."})[status] || "Не удалось связаться с сервисом. Проверьте соединение и повторите попытку.";
}
export function mustRefresh(status) { return status===409 || status===503 || status===0 || status>=500; }
export function displayName(food) {
  return food && /[А-Яа-яЁё]/.test(food.canonical_name) ? food.canonical_name : "Название недоступно";
}
