class VeilButtonMixin:
    def create_veil_button_rows(self, veils):
        veil_button_rows = [[self.constant.persian.anonymous_name ]]
        for veil in veils:
            if len(veil_button_rows[-1]) == 1:
                veil_button_rows[-1].append(veil.name)
            else:
                veil_button_rows.append([veil.name])
        return veil_button_rows