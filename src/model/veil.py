class Veil:
    def __init__(self, name, category, reserved_by, owned_by, reservation_status):
        self.name = name
        self.category = category
        self.reserved_by = reserved_by
        self.owned_by = owned_by
        self.reservation_status = reservation_status
    
    @staticmethod
    def cook(db_result):
        result = []
        for row in db_result:
            result.append(Veil(*row))
        return result