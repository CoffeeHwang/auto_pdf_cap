import time, sys

def getTimeStrSimple() -> str:
    now = time.localtime()
    return "{}-{:0>2}-{:0>2} {:0>2}:{:0>2}:{:0>2}".format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

def log(obj, clog=None):
    # lineNo = inspect.getlineno(inspect.getouterframes(inspect.currentframe())[-1][0])
    className = obj.__class__.__name__
    # caller_methodName = sys._getframe(2).f_code.co_name  # 이 주석 풀면 어디서 뻗을지 모르는 에러가 발생
    cur_methodName = sys._getframe(1).f_code.co_name
    # print(' < LOG >', className, '|', caller_methodName, '->', cur_methodName, '' if clog is None else clog)

    if 'ERROR' in str(clog).upper() or '에러' in str(clog).upper():
        print('<!! ERROR LOG !!>', getTimeStrSimple(), className, '|', cur_methodName, '' if clog is None else (' "' + str(clog) + '"'))
    else:
        print('<LOG>', getTimeStrSimple(), className, '|', cur_methodName, '' if clog is None else (' "' + str(clog) + '"'))
    pass


def log_start(obj):
    clog = '시작'
    className = obj.__class__.__name__
    cur_methodName = sys._getframe(1).f_code.co_name
    if 'ERROR' in str(clog).upper() or '에러' in str(clog).upper():
        print('<!! ERROR LOG !!>', getTimeStrSimple(), className, '|', cur_methodName, '' if clog is None else (': ' + str(clog)))
    else:
        print('<LOG>', getTimeStrSimple(), className, '|', cur_methodName, '' if clog is None else (': ' + str(clog)))
    pass


def log_end(obj):
    clog = '종료'
    className = obj.__class__.__name__
    cur_methodName = sys._getframe(1).f_code.co_name
    if 'ERROR' in str(clog).upper() or '에러' in str(clog).upper():
        print('<!! ERROR LOG !!>', getTimeStrSimple(), className, '|', cur_methodName, '' if clog is None else (': ' + str(clog)))
    else:
        print('<LOG>', getTimeStrSimple(), className, '|', cur_methodName, '' if clog is None else (': ' + str(clog)))
    pass

