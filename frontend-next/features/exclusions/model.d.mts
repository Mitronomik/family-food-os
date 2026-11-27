export const MAX: number;
export function sorted(ids: string[]): string[];
export function equal(a: string[], b: string[]): boolean;
export function payload(expected: string[], selected: string[]): {expected_excluded_food_ingredient_ids:string[];excluded_food_ingredient_ids:string[]};
type FoodIdentity = { id: string; canonical_name: string };
export function add(ids: string[], food: FoodIdentity & { is_active: boolean }): string[];
export function remove(ids: string[], id: string, food?: FoodIdentity): string[];
export function reconcile(original:string[],draft:string[],latest:string[]):string[];
export function message(status:number):string;
export function mustRefresh(status:number):boolean;
export function describeFood(food?: { canonical_name: string }): {
  kind: "identified" | "missing-details" | "missing-russian-name";
  label: string;
};
