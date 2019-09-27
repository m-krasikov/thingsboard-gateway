import jsonpath_rw_ext as jp
from logging import getLogger
from json import dumps,loads
from re import search

log = getLogger(__name__)
log.setLevel(10)


class TBUtility:
    @staticmethod
    def get_parameter(data, param, default_value):
        if param not in data:
            return default_value
        else:
            return data[param]

    @staticmethod
    def validate_converted_data(data):
        json_data = dumps(data)
        if not data.get("deviceName") or data.get("deviceName") is None:
            log.error('deviceName is empty in data %s', json_data)
            return False
        # if not data.get("deviceType") or data.get("deviceType") is None:
        #     log.error('deviceType is empty in data: %s', json_data)
        #     return False
        if not data["attributes"] and not data["telemetry"]:
            log.error('No telemetry and attributes in data: %s', json_data)
            return False
        return True

    @staticmethod
    def topic_to_regex(topic):
        return topic.replace("+", "[^/]+").replace("#", ".+")

    @staticmethod
    def regex_to_topic(regex):
        return regex.replace("[^/]+", "+").replace(".+", "#")

    @staticmethod
    def get_value(expression, body, value_type="string"):
        if isinstance(body,str):
            body = loads(body)
        if not expression:
            return ''
        p1 = search(r'\${', expression)
        p2 = search(r'}', expression)
        if p1 is not None and p2 is not None:
            p1 = p1.end()
            p2 = p2.start()
        else:
            p1 = 0
            p2 = len(expression)
        target_str = str(expression[p1:p2])
        value = True
        try:
            if value_type == "string":
                x = target_str.split()[0]
                t_body = dumps(body)
                value = jp.match1(target_str.split()[0], dumps(body))
                if value is None and body.get(target_str):
                    full_value = expression[0: min(abs(p1-2), 0)] + body[target_str] + expression[p2+1:len(expression)]
                elif value is None:
                    full_value = expression[0: min(abs(p1-2), 0)] + jp.match1(target_str.split()[0], loads(body) if type(body)==str else body) + expression[p2+1:len(expression)]
                else:
                    full_value = expression[0: min(abs(p1-2), 0)] + value + expression[p2+1:len(expression)]
            else:
                full_value = jp.match1(target_str.split()[0], loads(body) if type(body)==str else body)

        except TypeError:
            if value is None:
                log.error('Value is None - Cannot find the pattern: %s in %s', target_str, dumps(body))
            return None
        except Exception as e:
            log.error(e)
            return None
        return full_value
