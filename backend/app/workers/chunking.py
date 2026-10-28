from datetime import date, timedelta
from app.workers.scan_models import ScanChunk

def split_date_range(scan_id, date_from:date, date_to:date, chunk_days:int=1)->tuple[ScanChunk,...]:
    if date_to < date_from: raise ValueError("date_to must be on or after date_from")
    if chunk_days < 1: raise ValueError("chunk_days must be >= 1")
    out=[]; current=date_from; index=0
    while current<=date_to:
        end=min(date_to,current+timedelta(days=chunk_days-1))
        out.append(ScanChunk(scan_id=scan_id,chunk_index=index,date_from=current,date_to=end))
        current=end+timedelta(days=1); index+=1
    return tuple(out)

def progress(total:int, completed:int, failed:int=0, cancelled:int=0):
    from app.workers.scan_models import ScanProgress
    done=completed+failed+cancelled
    pct=100.0 if total==0 else round(min(100,done*100/total),2)
    return ScanProgress(total_chunks=total,completed_chunks=completed,failed_chunks=failed,cancelled_chunks=cancelled,percent_complete=pct)
