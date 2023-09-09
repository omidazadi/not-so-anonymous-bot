class Veil:
    def __init__(self, name, category, gen_reservation_status):
        self.name = name
        self.category = category
        self.gen_reservation_status = gen_reservation_status
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(Veil(*row))
        return result