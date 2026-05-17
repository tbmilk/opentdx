import struct

from opentdx.const import MARKET, PERIOD, ADJUST
from opentdx.parser.baseParser import register_parser
from opentdx.parser.quotation.kline import K_Line
from opentdx.utils.help import get_price, to_datetime


@register_parser(0x52d)
class K_Line_Offset(K_Line):
    """指数 K 线。

    `0x052d` 的 OHLC 是基于前收盘累积的差分编码，不能复用普通
    `K_Line` 的直接价格解析；但成交量/金额仍沿用当前服务器返回的
    float 语义。
    """

    def __init__(self, market: MARKET, code: str, period: PERIOD, times: int = 1,
                 start: int = 0, count: int = 800, adjust: ADJUST = ADJUST.NONE):
        super().__init__(market, code, period, times, start, count, adjust)

    def deserialize(self, data):
        count, = struct.unpack('<H', data[:2])
        pos = 2
        minute_category = self.period.value < 4 or self.period.value in (7, 8)
        pre_diff_base = 0
        bars = []

        for _ in range(count):
            date_num, = struct.unpack('<I', data[pos: pos + 4])
            pos += 4
            date_time = to_datetime(date_num, minute_category)

            open_diff, pos = get_price(data, pos)
            close_diff, pos = get_price(data, pos)
            high_diff, pos = get_price(data, pos)
            low_diff, pos = get_price(data, pos)

            vol, amount = struct.unpack('<ff', data[pos: pos + 8])
            pos += 8
            up_count, down_count = struct.unpack('<HH', data[pos: pos + 4])
            pos += 4

            open_base = open_diff + pre_diff_base
            bars.append({
                'datetime': date_time,
                'open': open_base / 1000,
                'close': (open_base + close_diff) / 1000,
                'high': (open_base + high_diff) / 1000,
                'low': (open_base + low_diff) / 1000,
                'vol': vol,
                'amount': amount,
                'up_count': up_count,
                'down_count': down_count,
            })
            pre_diff_base = open_base + close_diff

        return bars
