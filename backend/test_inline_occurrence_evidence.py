"""Synthetic source-local occurrence grouping, not financial examples."""
import copy
import unittest
from decimal import localcontext
from inline_occurrence_evidence import group_occurrences

class OccurrenceTests(unittest.TestCase):
    def fact(self,id='one',value='1.00'):
        return {'raw_member_sha256':'a'*64,'fact_id':id,'concept':{'namespace':'http://fasb.org/us-gaap/2025','local_name':'Revenues'},'context_ref':'c','unit_ref':'u','context_serialization_sha256':'b'*64,'context_namespace_bindings':{},'context_descendant_namespace_bindings':[], 'issuer_identifier_as_filed':'123','issuer_identifier_scheme':'http://www.sec.gov/CIK','period':{'kind':'duration','startDate':'2025-01-01','endDate':'2025-03-31'},'unit':{'kind':'simple','measures':[{'namespace':'currency','local_name':'USD'}]},'dimension_or_scenario_present':False,'numeric_conversion_verified':True,'numeric_value':value,'decimals_as_filed':'2'}
    def test_equal_occurrences_retained(self):
        a=self.fact();b=self.fact('two','1');rows=[a,b];before=copy.deepcopy(rows)
        g=group_occurrences(rows);self.assertEqual(len(g),1);self.assertEqual(g[0]['numeric_relation'],'NUMERICALLY_EQUAL');self.assertEqual(g[0]['occurrences'],rows);self.assertEqual(rows,before);self.assertFalse(g[0]['canonical_fact_equivalence_verified'])
    def test_different_values_and_accuracy_preserved(self):
        b=self.fact('two','2');b['decimals_as_filed']='INF'
        g=group_occurrences([self.fact(),b])[0];self.assertEqual(g['numeric_relation'],'DIFFERENT_REPORTED_VALUES');self.assertFalse(g['declared_decimals_equal'])
    def test_missing_not_zero(self):
        b=self.fact('two',None);b['numeric_conversion_verified']=False
        self.assertEqual(group_occurrences([self.fact(value='0'),b])[0]['numeric_relation'],'UNAVAILABLE')
    def test_no_merging_other_refs_namespaces_or_members(self):
        for key,value in [('context_ref','d'),('unit_ref','v'),('raw_member_sha256','c'*64),('concept',{'namespace':'http://fasb.org/us-gaap/2026','local_name':'Revenues'})]:
            b=self.fact('two');b[key]=value
            self.assertEqual(len(group_occurrences([self.fact(),b])),2)
    def test_conflicts_and_duplicate_occurrences_rejected(self):
        with self.assertRaises(ValueError):group_occurrences([self.fact(),self.fact()])
        b=self.fact('two');b['period']['endDate']='2025-06-30'
        with self.assertRaises(ValueError):group_occurrences([self.fact(),b])
    def test_exact_comparison_low_precision(self):
        with localcontext() as c:
            c.prec=3
            g=group_occurrences([self.fact(value='123456789012345678901234567890'),self.fact('two','123456789012345678901234567891')])[0]
            self.assertEqual(g['numeric_relation'],'DIFFERENT_REPORTED_VALUES')
