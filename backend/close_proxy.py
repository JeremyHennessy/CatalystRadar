"""Daily-close research proxy primitives. NOT an activated paper execution engine.
No network, brokerage, ledger mutation or price publication. Evidence remains private.
"""
import base64, hashlib, json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
from private_prices import metadata

SLIPPAGE=Decimal('0.0025'); FEE=Decimal('0.001'); CAP=Decimal('100')
MODEL='IDEALIZED_DAILY_CLOSE_PROXY_NOT_EXECUTABLE_FILL'

def amount(value):
 if isinstance(value,bool) or not isinstance(value,(str,int,float,Decimal)):raise ValueError('invalid amount')
 result=Decimal(str(value))
 if not result.is_finite() or result<=0:raise ValueError('positive finite amount required')
 return result

def instant(value):
 result=datetime.fromisoformat(value.replace('Z','+00:00'))
 if result.tzinfo is None:raise ValueError('timezone required')
 return result

class MissingSessionError(ValueError):pass

def read_envelope(path,*,symbol,session,now=None):
 """Admit exact raw-response integrity/identity only, NOT corporate actions or fills."""
 now=now or datetime.now(timezone.utc)
 envelope=json.loads(Path(path).read_text())
 if envelope.get('symbol')!=symbol:raise ValueError('wrong security')
 if envelope.get('source_endpoint')!='https://www.alphavantage.co/query' or envelope.get('source_function')!='TIME_SERIES_DAILY' or envelope.get('source_outputsize')!='compact':raise ValueError('wrong source')
 if envelope.get('scope')!='PRIVATE_PERSONAL_RESEARCH_ONLY':raise ValueError('wrong scope')
 observed=instant(envelope['observed_utc'])
 if observed>now:raise ValueError('future observation')
 raw=base64.b64decode(envelope['response_base64'],validate=True)
 if hashlib.sha256(raw).hexdigest()!=envelope['response_sha256']:raise ValueError('hash mismatch')
 quality=metadata(raw,symbol,observed)
 if quality!=envelope['quality']:raise ValueError('quality does not match source')
 payload=json.loads(raw);bar=payload['Time Series (Daily)'].get(session)
 if bar is None:raise MissingSessionError('missing target session')
 return {'symbol':symbol,'session':session,'close':str(amount(bar['4. close'])),'source_sha256':envelope['response_sha256'],'observed_utc':observed.isoformat(),'basis':'RAW_UNADJUSTED_DAILY','corporate_actions_verified':False,'halt_status_verified':False,'execution_eligible':False}

def size(prior_close,available_cash):
 """Whole-share predeclared size including fee; quantity zero is a recorded skip."""
 cash=Decimal(str(available_cash))
 if not cash.is_finite() or cash<0 or cash>500:raise ValueError('invalid remaining hypothetical cash')
 limit=(amount(prior_close)*Decimal('1.03')).quantize(Decimal('.01'),rounding=ROUND_FLOOR)
 if limit<=0:raise ValueError('invalid rounded limit')
 budget=min(CAP,cash);quantity=int(budget/(limit*(1+FEE)))
 return {'quantity':quantity,'limit':str(limit),'reserved':str(quantity*limit*(1+FEE)),'model':MODEL}

def cost_scenario(plan,close):
 """Pure sensitivity arithmetic, NOT a fill; callable without admitted sources."""
 if type(plan.get('quantity')) is not int or plan['quantity']<0:raise ValueError('invalid quantity')
 price=amount(close)*(1+SLIPPAGE);cost=price*plan['quantity']*(1+FEE)
 reserved=Decimal(plan['reserved']);limit=amount(plan['limit'])
 if not reserved.is_finite() or reserved<0 or reserved>CAP:raise ValueError('invalid reservation')
 if reserved!=plan['quantity']*limit*(1+FEE):raise ValueError('reservation mismatch')
 return {'model':MODEL,'scenario_only':True,'would_fit_limit_and_reservation':plan['quantity']>0 and price<=limit and cost<=reserved,'modeled_buy_price':str(price),'modeled_cost':str(cost),'orders_created':0,'fills_created':0}
