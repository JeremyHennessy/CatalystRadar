"""Hard date/year gate for scheduled public observations, independent of cron."""
from datetime import datetime,date,time,timezone
from zoneinfo import ZoneInfo

def allowed(now):
 if now.tzinfo is None:raise ValueError('timezone required')
 et=now.astimezone(ZoneInfo('America/New_York'))
 return date(2026,11,16)<=et.date()<=date(2026,11,20) and et.weekday()<5 and time(6)<=et.time()<=time(18,59,59)
if __name__=='__main__':print('true' if allowed(datetime.now(timezone.utc)) else 'false')
