class IndianName:
    def __init__(self, name):
        self.name = name
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(IndianName(*row))
        return result