import  re
from urllib import parse


def validateTitle(title):
    """
    处理不合法文件名字
    """
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title



def zJ_PE( t: str):
    """
    实现js0.8.3.js中的zJ_PE函数python版本,[`js0.8.3.js`](https://www.talkcc.net/incs/js0.8.3.js)
    """
    e = t[:3]
    if '*' != e[1] or '@' != e[2]:
        return t

    # 定义转换字典
    conv = dict(
        [("@", '%2'), ('#', '%3'), ('$', '%4'), ('?', '%5'), ('^', '%6'), ('[', '%7'), ('=', '%8'), ('<', '%9'),
         ('>', '%A'), ('{', '%B'), ('}', '%C'), ('|', '%D'), (':', '%E'), (';', '%F'), (',', 'e')]
    )

    t = t[3:]

    if 0 < int(e[0]):
        for k, v in conv.items():
            t = t.replace(str(k), str(v), -1)
        return parse.unquote(t)

    return t


def getContentInSep( old: str, startIndex: int = 0, lsep: str = '"', rsep: str = '"'):
    """
    抽取界定符sep框定的内容
    如果不存在返回None，否则返回不包括界定符的最大长度内容
    """

    old = old[startIndex:]

    output = ""
    count: int = 0
    # 左右界定符号相同情况
    if lsep == rsep:
        if old.count(lsep) % 2 != 0:
            return None
        s = old.find(lsep)
        e = old.rfind(rsep)
        return old[s+1:e]

    # 左右界定符号不同
    for i in range(len(old)):
        if old[i] == lsep:
            count += 1

        if count != 0:
            output = output + old[i]

        if old[i] == rsep:
            count -= 1
            if count == 0:
                break
    if count != 0:
        return None

    length = len(output)
    return output[1:length-1]
