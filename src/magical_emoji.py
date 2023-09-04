import random

class MagicalEmoji:
    def __init__(self):
        # Unicode v.15
        self.magical_emoji_ranges = [
            ('\U00002626', '\U0000262A', 'sign'), # Religious and political
            ('\U0000262C', '\U0000262F', 'sign'), # Religious and political
            ('\U00002648', '\U00002653', 'sign'), # Zodiac
            ('\U000026E9', '\U000026EA', 'building'), # Map symbol
            ('\U0001F300', '\U0001F301', 'nature'), # Weather, landscape, and sky
            ('\U0001F303', '\U0001F30C', 'nature'), # Weather, landscape, and sky
            ('\U0001F324', '\U0001F32B', 'nature'), # Weather
            ('\U0001F330', '\U0001F344', 'nature'), # Plant
            ('\U0001F3B5', '\U0001F3BC', 'music'), # Music
            ('\U0001F3D4', '\U0001F3D6', 'nature'), # Building and map
            ('\U0001F3D8', '\U0001F3DB', 'building'), # Building and map
            ('\U0001F3DC', '\U0001F3DE', 'nature'), # Building and map
            ('\U0001F3E0', '\U0001F3E1', 'building'), # Building and map
            ('\U0001F3EE', '\U0001F3F0', 'building'), # Building and map
            ('\U0001F400', '\U0001F42C', 'animal'), # Animal
            ('\U0001F42D', '\U0001F43D', 'animal'), # Animal face
            ('\U0001F478', '\U0001F480', 'fantasy'), # Fairy tale
            ('\U0001F5FB', '\U0001F5FB', 'nature'), # Culture
            ('\U0001F5FF', '\U0001F5FF', 'nature'), # Culture
            ('\U0001F980', '\U0001F9AD', 'animal'), # Animal
            ('\U0001F9CC', '\U0001F9CC', 'fantasy'), # Fantasy
            ('\U0001F9D9', '\U0001F9DF', 'fantasy'), # Fantasy
            ('\U0001FA87', '\U0001FA88', 'music'), # Musical instrument
            ('\U0001FAAF', '\U0001FAAF', 'sign'), # Religoius
            ('\U0001FAB0', '\U0001FABD', 'animal'), # Animal and nature
            ('\U0001FABF', '\U0001FABF', 'animal'), # Animal and nature
            ('\U0001FACE', '\U0001FACF', 'animal'), # Animal and nature
        ]
        self.proboblity_distribution = {
            'sign': 0.0,
            'building': 0.15,
            'music': 0.1,
            'animal': 0.3,
            'nature': 0.3,
            'fantasy': 0.15,
        }

    def get_random_emoji(self):
        x, category = random.random(), None
        for key in self.proboblity_distribution:
            if x < self.proboblity_distribution[key]:
                category = key
                break
            x -= self.proboblity_distribution[key]
        
        e_ranges = [e_range for e_range in self.magical_emoji_ranges if e_range[2] == category]
        total_emojies = 0
        for e_range in e_ranges:
            total_emojies += ord(e_range[1]) - ord(e_range[0]) + 1

        selected_emoji = random.randint(1, total_emojies)
        for e_range in e_ranges:
            if selected_emoji <= ord(e_range[1]) - ord(e_range[0]) + 1:
                return chr(ord(e_range[0]) + selected_emoji - 1)
            selected_emoji -= ord(e_range[1]) - ord(e_range[0]) + 1
        
        return None
