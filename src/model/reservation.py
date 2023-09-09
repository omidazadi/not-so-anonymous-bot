class Reservation:
    def __init__(self, user_id, veil_1, veil_2, veil_3):
        self.user_id = user_id
        self.veil_1 = veil_1
        self.veil_2 = veil_2
        self.veil_3 = veil_3
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(Reservation(*row))
        return result