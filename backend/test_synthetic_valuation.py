import ast
from copy import deepcopy
import json
from pathlib import Path
import random
import unittest
import synthetic_paper as p
import synthetic_valuation as v

AT='2030-01-02T12:00:00Z'
SESSION='SYNTH_MARK_SESSION'
class Fixture:
 def __init__(self,cash=1000):
  self.j=();self.add('INIT',cash_units=cash)
 def add(self,kind,**kw):
  self.j=p.append(self.j,{'event_id':f'SYNTH_E{len(self.j)}','at':AT,'kind':kind,**kw})
 def order(self,oid,side,qty,price,fee=0):
  self.add('INTENT',order_id=oid,candidate_id='SYNTH_C',instrument_id='SYNTH_A',side=side,quantity=qty,limit_units=price,fee_cap_units=fee,decision_at=AT,session_id='SYNTH_PRIOR_SESSION')
 def fill(self,oid,qty,price,fee=0):
  self.add('FILL',order_id=oid,quantity=qty,price_units=price,fee_units=fee,session_id='SYNTH_PRIOR_SESSION')
 def mark(self,price=12):return ({'instrument_id':'SYNTH_A','valuation_session':SESSION,'at':AT,'price_units':price},)
 def bought(self):self.order('SYNTH_B','BUY',10,10,3);self.fill('SYNTH_B',10,10,3)

class Valuation(unittest.TestCase):
 def test_fees_partial_sell_reservations_and_cancel(self):
  f=Fixture();f.bought();f.order('SYNTH_S','SELL',4,11,2);f.fill('SYNTH_S',2,11,1)
  f.order('SYNTH_B2','BUY',3,10,1)
  r=v.report(f.j,SESSION,AT,f.mark())
  self.assertEqual((r['cash_units'],r['reserved_cash_units'],r['available_cash_units']),(918,31,887))
  self.assertEqual((r['remaining_cost_units'],r['realized_pnl_units'],r['unrealized_pnl_units']),(83,1,13))
  self.assertEqual(r['hypothetical_equity_units'],1014)
  self.assertEqual(r['positions'][0]['sell_reserved_quantity'],2)
  f.add('CANCEL',order_id='SYNTH_B2');f.add('CANCEL',order_id='SYNTH_S')
  after=v.report(f.j,SESSION,AT,f.mark())
  self.assertEqual(after['hypothetical_equity_units'],r['hypothetical_equity_units'])
  self.assertEqual(after['available_cash_units'],918)
 def test_partial_buy_reserved_cash_not_double_subtracted(self):
  f=Fixture();f.order('SYNTH_B','BUY',10,10,3);f.fill('SYNTH_B',4,9,1)
  r=v.report(f.j,SESSION,AT,f.mark(10))
  self.assertEqual((r['cash_units'],r['reserved_cash_units'],r['available_cash_units']),(963,62,901))
  self.assertEqual(r['hypothetical_equity_units'],1003)
 def test_flat_and_final_residual(self):
  f=Fixture();self.assertEqual(v.report(f.j,SESSION,AT,())['hypothetical_equity_units'],1000)
  f.bought();f.order('SYNTH_S','SELL',10,11,2);f.fill('SYNTH_S',3,11,1);f.fill('SYNTH_S',7,11,1)
  r=v.report(f.j,SESSION,AT,());self.assertEqual(r['remaining_cost_units'],0)
  self.assertEqual((r['realized_pnl_units'],r['hypothetical_equity_units']),(5,1005))
  with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,f.mark())
 def test_kill_immutability_and_zero_mark(self):
  f=Fixture();f.bought();f.add('KILL');marks=f.mark(0);before=deepcopy((f.j,marks))
  r=v.report(f.j,SESSION,AT,marks)
  self.assertTrue(r['journal_killed']);self.assertFalse(r['execution_authorized'])
  self.assertEqual(r['unrealized_pnl_units'],-103);self.assertEqual((f.j,marks),before)
  r['positions'][0]['quantity']=999
  self.assertEqual(p.replay(f.j)['positions']['SYNTH_A']['quantity'],10)
 def test_bad_coverage_schema_identifiers_and_units(self):
  f=Fixture();f.bought()
  for marks in [(),f.mark()*2,list(f.mark()),tuple([dict(f.mark()[0],instrument_id='SYNTH_UNKNOWN')]),tuple([dict(f.mark()[0],instrument_id='AMD')]),tuple([dict(f.mark()[0],extra=1)])]:
   with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,marks)
  for price in [True,1.0,'12',-1,10**15+1,float('nan')]:
   with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,f.mark(price))
 def test_exact_clocks_and_scenario_only_session(self):
  f=Fixture();f.bought()
  for field,value in [('at','2030-01-02T11:59:59Z'),('at','2030-01-02T12:00:01Z'),('valuation_session','SYNTH_OTHER')]:
   with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,(dict(f.mark()[0],**{field:value}),))
  for at in ['2029-01-01T00:00:00Z','bad']:
   with self.assertRaises(ValueError):v.report(Fixture().j,SESSION,at,())
  later='2030-01-03T00:00:00Z'
  r=v.report(f.j,SESSION,later,(dict(f.mark()[0],at=later),))
  self.assertTrue(r['valuation_session_is_caller_scenario_only']);self.assertFalse(r['actual_market_session_verified'])
  with self.assertRaises(ValueError):v.report(f.j,'NYSE',AT,f.mark())
 def test_tampered_journal_and_no_cached_state(self):
  f=Fixture();f.bought();r=json.loads(f.j[-1]);r['event']['price_units']=1
  with self.assertRaises(ValueError):v.report(f.j[:-1]+(p.canonical(r),),SESSION,AT,f.mark())
  with self.assertRaises(ValueError):v.report(p.replay(f.j),SESSION,AT,f.mark())
 def test_actual_large_valid_journal_aggregate_rejected(self):
  n=10**15;f=Fixture(n);f.order('SYNTH_B','BUY',n,1);f.fill('SYNTH_B',n,1)
  f.order('SYNTH_S','SELL',1,n);f.fill('SYNTH_S',1,n)
  f.order('SYNTH_B2','BUY',n,1);f.fill('SYNTH_B2',n,1)
  p.replay(f.j)
  with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,f.mark(n))
 def test_many_exact_accounting_paths(self):
  rng=random.Random(18)
  for _ in range(80):
   f=Fixture(100000);q=rng.randint(2,50);price=rng.randint(1,100);fee=rng.randint(0,9)
   f.order('SYNTH_B','BUY',q,price,fee);f.fill('SYNTH_B',q,price,fee)
   sell=rng.randint(1,q-1);sp=rng.randint(10,100)
   f.order('SYNTH_S','SELL',sell,sp,1);f.fill('SYNTH_S',sell,sp,1)
   mark=rng.randint(0,100);r=v.report(f.j,SESSION,AT,f.mark(mark))
   originalcost=q*price+fee;allocated=originalcost*sell//q
   self.assertEqual(r['remaining_cost_units'],originalcost-allocated)
   self.assertEqual(r['realized_pnl_units'],sell*sp-1-allocated)
   self.assertEqual(r['hypothetical_equity_units'],r['initial_cash_units']+r['realized_pnl_units']+r['unrealized_pnl_units'])
 def test_multiple_instruments_order_and_complete_coverage(self):
  f=Fixture();f.bought()
  f.add('INTENT',order_id='SYNTH_B2',candidate_id='SYNTH_C2',instrument_id='SYNTH_B',side='BUY',quantity=2,limit_units=20,fee_cap_units=0,decision_at=AT,session_id='SYNTH_PRIOR_SESSION')
  f.fill('SYNTH_B2',2,20)
  f.order('SYNTH_S','SELL',2,11)
  marks=f.mark(12)+(dict(f.mark(15)[0],instrument_id='SYNTH_B'),)
  a=v.report(f.j,SESSION,AT,marks);b=v.report(f.j,SESSION,AT,marks[::-1])
  self.assertEqual(a,b)
  self.assertEqual(a['unrealized_pnl_units'],7)
  self.assertEqual(a['hypothetical_equity_units'],1007)
  self.assertEqual(a['positions'][0]['sell_reserved_quantity'],2)
  with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,marks[1:])
  with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,marks[:1])
  with self.assertRaises(ValueError):v.report(f.j,SESSION,AT,marks*501)
 def test_no_io_cli_or_execution_imports(self):
  tree=ast.parse(Path(v.__file__).read_text())
  imports=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
   if isinstance(n,ast.ImportFrom):imports.append(n.module)
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,{'open','eval','exec','print'})
  self.assertEqual(set(imports),{'copy','json','synthetic_paper'})
if __name__=='__main__':unittest.main()
