// Documentary diagnostic only; no browser interaction or HTTP request.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createBirthForm } from "../../../../../../../src/exact_orb/http_api/ui/form.mjs";
const fixture=JSON.parse(readFileSync(new URL("../../../../../../../tests/fixtures/places.jsonl",import.meta.url),"utf8").split("\n")[0]);
const cases=[];
for(const [date,expected] of [["146464-03-20",false],["1985-09-02",true],["0001-01-01",true],["9999-12-31",true]]) {
 const form=createBirthForm(); form.setDate(date); form.setTime("00:45");
 form.selectPlace({place_id:fixture.place_id,display_name:fixture.name,admin1_name:fixture.admin1,country_code:fixture.country});
 form.acknowledge(true);
 const result=form.prepareSubmission(); assert.equal(result.ok,expected);
 if(!expected){assert.ok(result.errors.date);assert.equal("intent" in result,false);}
 cases.push({date,expected_ok:expected,actual_ok:result.ok,date_error:result.errors?.date??null,intent_present:"intent" in result,passed:true});
}
process.stdout.write(JSON.stringify({kind:"pure form diagnostic; not browser or HTTP evidence",cases,passed:true},null,2)+"\n");
