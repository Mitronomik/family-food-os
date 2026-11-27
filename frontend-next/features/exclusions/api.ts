import { payload } from "./model.mjs";
export type Food = { id:string; canonical_name:string; is_active:boolean };
export type Member = { id:string; name:string; active:boolean };
export type Household = { id:string; name:string; members:Member[] };
export class ApiError extends Error { constructor(public status:number) { super("API request failed"); } }
async function request<T>(path:string, init:RequestInit={}, signal?:AbortSignal):Promise<T> {
  try {
    const timeout = AbortSignal.timeout(15000);
    const res = await fetch(path,{...init,cache:"no-store",credentials:"same-origin",signal:signal?AbortSignal.any([signal,timeout]):timeout});
    if (!res.ok) throw new ApiError(res.status);
    return await res.json() as T;
  } catch(error) { if (error instanceof ApiError) throw error; throw new ApiError(0); }
}
const segment = encodeURIComponent;
const endpoint = (h:string,m:string) => "/api/households/"+segment(h)+"/members/"+segment(m)+"/food-exclusions";
export const api = {
  household:(h:string,s?:AbortSignal)=>request<Household>("/api/households/"+segment(h),{},s),
  read:async(h:string,m:string,s?:AbortSignal)=>(await request<{excluded_food_ingredient_ids:string[]}>(endpoint(h,m),{},s)).excluded_food_ingredient_ids,
  food:(id:string,s?:AbortSignal)=>request<Food>("/api/food-ingredients/"+segment(id),{},s),
  search:async(q:string,s?:AbortSignal)=>(await request<{items:Food[]}>("/api/food-ingredients?"+new URLSearchParams({q,limit:"20"}),{},s)).items,
  save:(h:string,m:string,expected:string[],selected:string[])=>request<{excluded_food_ingredient_ids:string[];changed:boolean}>(endpoint(h,m),{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload(expected,selected))}),
};
