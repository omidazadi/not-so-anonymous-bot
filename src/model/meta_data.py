class MetaData:
    def __init__(self, meta_key, meta_value):
        self.meta_key = meta_key
        self.meta_value = meta_value

    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(MetaData(*row))
        return result