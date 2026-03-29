class ParamParser:
    """param sample:
    path: D:\data\ImageDataManager; size: 1000,1000"""
    def __init__(self, param: str):
        self.param = param
        self.dict_param = {}
        self._parse()

    def _parse(self):
        for item in self.param.split(";"):
            key, value = item.split(":")
            formated_value = self._format_value(value.strip())
            self.dict_param[key.strip()] = formated_value

    def _format_value(self, value):
        if "," in value:
            val_list = []
            splited = value.split(",")
            for item in splited:
                item = item.strip()
                #end with f
                if item.endswith("f"):
                    val_list.append(float(item[:-1]))
                    # is digit
                elif item.isdigit():
                    val_list.append(int(item))

            return [int(item) for item in value.split(",")]
        return value
