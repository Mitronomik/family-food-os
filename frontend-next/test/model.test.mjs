import test from "node:test";
import assert from "node:assert/strict";
import {add,remove,payload,equal,reconcile,message,mustRefresh,displayName,MAX} from "../features/exclusions/model.mjs";
test("active selection, duplicate, removal and inactive re-add rejection",()=>{
 const food={id:"a",is_active:true}; const selected=add([],food);
 assert.deepEqual(selected,["a"]);assert.deepEqual(add(selected,food),selected);
 assert.deepEqual(remove(selected,"a"),[]);assert.deepEqual(add([],{...food,is_active:false}),[]);
});
test("retained inactive and new active selection, full CAS and empty set",()=>{
 assert.deepEqual(payload(["old"],add(["old"],{id:"new",is_active:true})),{expected_excluded_food_ingredient_ids:["old"],excluded_food_ingredient_ids:["new","old"]});
 assert.deepEqual(payload(["old"],[]).excluded_food_ingredient_ids,[]);
 assert.equal(equal(["a","b"],["b","a"]),true);
});
test("explicit reconciliation preserves concurrent unrelated additions",()=>{
 assert.deepEqual(reconcile(["old","remove"],["old","mine"],["old","remove","theirs"]),["mine","old","theirs"]);
});
test("bounded selection, safe errors and missing Russian text",()=>{
 const full=Array.from({length:MAX},(_,i)=>String(i));
 assert.deepEqual(add(full,{id:"new",is_active:true}),full);
 for(const s of [404,409,422,503,0])assert.match(message(s),/[А-Яа-я]/);
 for(const s of [409,503,0])assert.equal(mustRefresh(s),true);
 assert.equal(displayName({canonical_name:"Carrot"}),"Название недоступно");
 assert.equal(displayName({canonical_name:"Морковь"}),"Морковь");
});
