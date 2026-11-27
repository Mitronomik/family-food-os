import test from "node:test";
import assert from "node:assert/strict";
import {add,remove,payload,equal,reconcile,message,mustRefresh,describeFood,MAX} from "../features/exclusions/model.mjs";
test("active selection, duplicate, removal and inactive re-add rejection",()=>{
 const food={id:"a",is_active:true,canonical_name:"Морковь"}; const selected=add([],food);
 assert.deepEqual(selected,["a"]);assert.deepEqual(add(selected,food),selected);
 assert.deepEqual(remove(selected,"a",food),[]);assert.deepEqual(add([],{...food,is_active:false}),[]);
});
test("retained inactive and new active selection, full CAS and empty set",()=>{
 assert.deepEqual(payload(["old"],add(["old"],{id:"new",is_active:true,canonical_name:"Свёкла"})),{expected_excluded_food_ingredient_ids:["old"],excluded_food_ingredient_ids:["new","old"]});
 assert.deepEqual(payload(["old"],[]).excluded_food_ingredient_ids,[]);
 assert.equal(equal(["a","b"],["b","a"]),true);
});
test("explicit reconciliation preserves concurrent unrelated additions",()=>{
 assert.deepEqual(reconcile(["old","remove"],["old","mine"],["old","remove","theirs"]),["mine","old","theirs"]);
});
test("bounded selection and safe errors",()=>{
 const full=Array.from({length:MAX},(_,i)=>String(i));
 assert.deepEqual(add(full,{id:"new",is_active:true,canonical_name:"Свёкла"}),full);
 for(const s of [404,409,422,503,0])assert.match(message(s),/[А-Яа-я]/);
 for(const s of [409,503,0])assert.equal(mustRefresh(s),true);
});
test("the model distinguishes unavailable details from missing Russian text and guards removal", () => {
  const selected = ["a", "b"];
  const foreign = {id:"a",is_active:true,canonical_name:"Carrot"};
  const named = {...foreign,is_active:false,canonical_name:"Морковь"};
  assert.equal(describeFood(undefined).kind, "missing-details");
  assert.equal(describeFood(foreign).kind, "missing-russian-name");
  assert.deepEqual(describeFood(named), {kind:"identified",label:"Морковь"});
  assert.deepEqual(remove(selected,"a"), selected);
  assert.deepEqual(remove(selected,"a",foreign), selected);
  assert.deepEqual(remove(selected,"b",named), selected);
  assert.deepEqual(remove(selected,"a",named), ["b"]);
  assert.deepEqual(add([],foreign), []);
});
